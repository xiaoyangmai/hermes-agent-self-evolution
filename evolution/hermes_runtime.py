"""Remote execution adapter. Optimization policy belongs to dspy_loop and the project.

All mutations use the existing control-plane API; this is a finite CLI client, not
a server. Each candidate/case has a durable idempotent receipt and downloaded data.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import subprocess
import time
import urllib.error
import urllib.request
import uuid


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def write_json(path: Path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")
    temporary.replace(path)


def git(repo: Path, *args: str) -> str:
    return subprocess.check_output(["git", "-C", str(repo), *args], text=True, encoding="utf-8").strip()


class HermesRuntime:
    def __init__(self, repo: Path, project, output: Path):
        self.repo, self.project, self.output = repo, project, output
        self.base = os.environ["HERMES_CONTROL_URL"].rstrip("/")
        self.gateway = os.environ.get("HERMES_GATEWAY_URL", self.base + "/gateway").rstrip("/")
        self.token = os.environ["HERMES_CONTROL_TOKEN"]
        self.key = None
        self.failure = None
        self.experiment_id = ""
        self.prefix = "/v1/projects/" + project.PROJECT
        self.skill_path = repo / project.SKILL
        raw = self.skill_path.read_text(encoding="utf-8")
        _, self.frontmatter, self.initial_body = raw.split("---", 2)
        self.initial_body = self.initial_body.strip()
        self.max_runs = project.POLICY["max_remote_runs"]
        self.timeout = project.POLICY["run_timeout_seconds"]
        self.output.mkdir(parents=True, exist_ok=True)

    def __deepcopy__(self, memo):
        # DSPy clones candidate programs. They still share one remote deployment
        # and its durable trial ledger; cloning it cannot create a new environment.
        return self

    def request(self, path, body=None, *, gateway=False, key=None):
        token = self.key if gateway else self.token
        headers = {"Authorization": "Bearer " + token}
        data = None
        if body is not None:
            data = json.dumps(body, ensure_ascii=False).encode()
            headers["Content-Type"] = "application/json"
        if key:
            headers["Idempotency-Key"] = key
        req = urllib.request.Request((self.gateway if gateway else self.base) + path, data=data, headers=headers)
        for attempt in range(3):
            try:
                with urllib.request.urlopen(req, timeout=60) as response:
                    return json.load(response)
            except urllib.error.URLError as exc:
                # Observed transient TLS disconnects during rollout polling.
                # Only reads or explicitly idempotent writes are safe to repeat.
                transient = not isinstance(exc, urllib.error.HTTPError) or exc.code in (502, 503, 504)
                if attempt == 2 or not transient or (body is not None and not key):
                    raise
                time.sleep(attempt + 1)

    def operation(self, path, receipt: Path, key: str, body=None):
        if receipt.exists():
            record = json.loads(receipt.read_text(encoding="utf-8"))
        else:
            record = self.request(path, {} if body is None else body, key=key)
            write_json(receipt, record)
        deadline = time.monotonic() + 900
        while record["status"] not in ("succeeded", "failed", "cancelled"):
            if time.monotonic() > deadline:
                raise TimeoutError("Operation remains pending; resume using receipt " + str(receipt))
            time.sleep(2)
            record = self.request("/v1/operations/" + record["id"])
            write_json(receipt, record)
        if record["status"] != "succeeded":
            raise RuntimeError("Control operation failed: " + str(receipt))
        return record["result"]

    def environment(self, folder: Path, name: str):
        state = self.operation(self.prefix + "/environment/check", folder / (name + ".json"), name + "-" + uuid.uuid4().hex)
        # The project owns these facts; control-plane only executes its fixed script.
        report = self.project.environment_report(state)
        if not report["ready"]:
            raise RuntimeError("Environment not ready; run the project's controlled prepare step")
        return report

    def deploy(self, body: str):
        if not body.strip() or len(body) > 15000:
            raise ValueError("Candidate Skill must contain 1..15000 characters")
        full = "---\n" + self.frontmatter.strip() + "\n---\n\n" + body.strip() + "\n"
        expected_hash = digest(full.encode())
        if self.skill_path.read_text(encoding="utf-8") != full:
            if git(self.repo, "status", "--porcelain", "--untracked-files=no"):
                raise RuntimeError("Commit project changes before optimizing")
            self.skill_path.write_bytes(full.encode())
            git(self.repo, "add", "--", self.project.SKILL)
            git(self.repo, "commit", "-m", "Evaluate DSPy Skill " + expected_hash[:12])
        revision = git(self.repo, "rev-parse", "HEAD")
        git(self.repo, "push", "origin", "HEAD")
        folder = self.output / "releases" / revision
        sync = self.operation(self.prefix + "/sync", folder / "sync.json", "sync-" + revision)
        if sync["revision"] != revision:
            raise RuntimeError("Remote HEAD differs from candidate revision")
        check = self.operation(self.prefix + "/environment/check", folder / "environment-before.json", "check-" + revision)
        if not self.project.environment_report(check)["ready"]:
            self.operation(self.prefix + "/environment/prepare", folder / "prepare.json", "prepare-" + revision)
            self.environment(folder, "prepared")
        for profile in self.project.PROFILES:
            self.key = self.request(self.prefix + "/profiles/" + profile + "/gateway-key")["api_server_key"]
            health = self.request("/p/" + profile + "/health/detailed", gateway=True)
            if health["active_agents"]:
                raise RuntimeError("Gateway refresh would interrupt an active run: " + profile)
        self.operation(self.prefix + "/gateway/refresh", folder / "refresh.json", "refresh-" + revision)
        # A previous receipt does not establish the CURRENT installed state.
        state = self.environment(folder, "effective-" + uuid.uuid4().hex)
        relative = self.project.SKILL.split("/", 2)[2]
        if state["revision"] != revision or state["files"].get(relative) != expected_hash:
            raise RuntimeError("Installed Skill is not the candidate that DSPy evaluated")
        fixed = {k: v for k, v in state["files"].items() if k != relative}
        fixed_path = self.output / "fixed-runtime.json"
        if fixed_path.exists() and json.loads(fixed_path.read_text()) != fixed:
            raise RuntimeError("Non-optimized runtime context changed; start a new controlled experiment")
        write_json(fixed_path, fixed)
        self.key = self.request(self.prefix + "/profiles/" + self.project.PROFILE + "/gateway-key")["api_server_key"]
        caps = self.request("/p/" + self.project.PROFILE + "/v1/capabilities", gateway=True)
        write_json(folder / "capabilities.json", caps)
        features = caps["features"]
        if not all(features.get(k) for k in ("run_submission", "run_status", "run_stop", "session_resources")) or not features["runs_idempotency"]["durable"]:
            raise RuntimeError("Gateway lacks required execution/recovery capabilities")
        return revision, state

    def execute(self, instructions: str, task_input: str) -> str:
        case = json.loads(task_input)
        if self.failure:
            raise RuntimeError("Experiment stopped after infrastructure failure") from self.failure
        identity = digest((self.experiment_id + "\0" + instructions + "\0" + task_input).encode())
        folder = self.output / "trials" / identity
        receipt_file = folder / "receipt.json"
        if receipt_file.exists():
            receipt = json.loads(receipt_file.read_text(encoding="utf-8"))
            if receipt["status"] == "collected":
                return json.dumps({"trial": str(folder), "trace": receipt["trace_summary"]}, ensure_ascii=False)
            if receipt["status"] == "failed":
                raise RuntimeError("Failed execution retained at " + str(folder))
        else:
            count = len(list((self.output / "trials").glob("*/receipt.json")))
            if count >= self.max_runs:
                raise RuntimeError("Remote run budget exhausted")
            delivery = "dspy-" + identity[:24]
            receipt = {"status": "prepared", "delivery_id": delivery,
                       "case": case, "candidate_sha256": digest(instructions.encode())}
            write_json(receipt_file, receipt)
        if self.key is None:
            self.key = self.request(self.prefix + "/profiles/" + self.project.PROFILE + "/gateway-key")["api_server_key"]
        prefix = "/p/" + self.project.PROFILE + "/v1/runs"
        if "gateway_run_id" not in receipt:
            # A resumed prepared trial may find another candidate installed.
            revision, before = self.deploy(instructions)
            receipt.update(revision=revision, before=before)
            write_json(receipt_file, receipt)
            if hasattr(self, 'project_home'):
                task = self.project.task(case, receipt["delivery_id"], receipt["revision"], project_home=self.project_home)
            else:
                task = self.project.task(case, receipt["delivery_id"], receipt["revision"])
            write_json(folder / "task.json", task)
            submitted = self.request(prefix, task, gateway=True, key=receipt["delivery_id"])
            receipt.update(gateway_run_id=submitted["run_id"], status="running", deadline=time.time() + self.timeout)
            write_json(receipt_file, receipt)
        path = prefix + "/" + receipt["gateway_run_id"]
        while True:
            status = self.request(path, gateway=True)
            write_json(folder / "status.json", status)
            if status["status"] in ("completed", "failed", "cancelled", "canceled"):
                break
            if time.time() > receipt["deadline"]:
                self.request(path + "/stop", {}, gateway=True)
                raise TimeoutError("Run stop requested; resume to collect terminal state: " + str(folder))
            time.sleep(3)
        receipt["terminal"] = status
        session = status.get("session_id", receipt["gateway_run_id"])
        rows, offset = [], 0
        while True:
            page = self.request("/p/" + self.project.PROFILE + "/api/sessions/" + session + "/messages?order=oldest&limit=500&offset=" + str(offset), gateway=True)
            rows.extend({k: v for k, v in r.items() if k not in ("reasoning", "reasoning_content")} for r in page["data"])
            if page["pagination"]["returned"] < page["pagination"]["limit"]:
                break
            offset += page["pagination"]["returned"]
        write_json(folder / "trace.json", rows)
        receipt["trace_summary"] = self.project.trace_summary(rows)
        if status["status"] != "completed":
            receipt["status"] = "failed"
            write_json(receipt_file, receipt)
            raise RuntimeError("Hermes execution failed: " + str(folder))
        self.project.verify_trace(receipt["trace_summary"])
        after = self.environment(folder, "effective-after")
        if after["files"] != receipt["before"]["files"] or after["revision"] != receipt["revision"]:
            raise RuntimeError("Runtime context changed during execution; trial is invalid")
        self.collect(receipt, folder)
        receipt["status"] = "collected"
        write_json(receipt_file, receipt)
        print("Collected", receipt["delivery_id"], flush=True)
        return json.dumps({"trial": str(folder), "trace": receipt["trace_summary"]}, ensure_ascii=False)

    def collect(self, receipt, folder: Path):
        path = self.prefix + "/runs/" + receipt["delivery_id"]
        self.operation(path + "/finalize", folder / "finalize.json", "finalize-" + receipt["delivery_id"])
        record = self.request(path + "/result")
        result = record["result"]
        if (result.get("delivery_id") != receipt["delivery_id"] or result.get("source_revision") != receipt["revision"]
                or result.get("profile") != self.project.PROFILE):
            raise RuntimeError("Producer result does not identify this trial's revision/profile/delivery")
        write_json(folder / "result.json", record)
        items = self.request(path + "/artifacts")["artifacts"]
        names = set()
        for item in items:
            name = item["name"]
            relative = PurePosixPath(name)
            if relative.is_absolute() or ".." in relative.parts or "\\" in name or ":" in name or name in names:
                raise ValueError("Invalid artifact filename")
            names.add(name)
            req = urllib.request.Request(self.base + "/v1/artifacts/" + item["artifact_id"] + "/download",
                                         headers={"Authorization": "Bearer " + self.token})
            with urllib.request.urlopen(req, timeout=60) as response:
                data = response.read()
                if (digest(data) != item["sha256"] or response.headers["X-Artifact-Sha256"] != item["sha256"]
                        or response.headers["X-Artifact-Id"] != item["artifact_id"]):
                    raise ValueError("Downloaded artifact checksum mismatch")
            target = folder / "artifacts" / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(data)
        write_json(folder / "artifacts.json", items)

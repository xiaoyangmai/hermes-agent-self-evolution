"""Run frozen candidate revisions in two isolated Hermes experiment instances."""
import json
import subprocess
import threading
import uuid
from pathlib import Path

from evolution.hermes_runtime import HermesRuntime, digest, git, write_json


class ExperimentSlot(HermesRuntime):
    def __init__(self, repo, project, output, slot, revisions, fixed_lock):
        super().__init__(repo, project, output)
        self.slot = slot
        self.revisions = revisions
        self.fixed_lock = fixed_lock
        self.prefix += '/experiments/' + slot
        self.gateway = self.base + '/gateway-experiment-' + slot
        self.project_home = '/opt/data/projects/' + project.PROJECT
        self.installed = None
        self.install_lock = threading.Lock()

    def deploy(self, body):
        revision = self.revisions(body)
        with self.install_lock:
            if self.installed and self.installed[0] == revision:
                return self.installed
            folder = self.output / 'releases' / self.slot / revision
            token = uuid.uuid4().hex
            result = self.operation(self.prefix + '/release', folder / ('release-' + token + '.json'),
                                    'release-' + self.slot + '-' + token,
                                    {'revision': revision})
            if result['revision'] != revision:
                raise RuntimeError('Experiment instance installed a different revision')
            self.project_home = result['project_home']
            check = self.operation(self.prefix + '/environment/check', folder / ('before-' + token + '.json'),
                                   'check-' + token)
            if not self.project.environment_report(check)['ready']:
                self.operation(self.prefix + '/environment/prepare', folder / ('prepare-' + token + '.json'),
                               'prepare-' + token)
            state = self.environment(folder, 'effective-' + token)
            full = '---\n' + self.frontmatter.strip() + '\n---\n\n' + body.strip() + '\n'
            relative = self.project.SKILL.split('/', 2)[2]
            if state['revision'] != revision or state['files'].get(relative) != digest(full.encode()):
                raise RuntimeError('Experiment instance Skill does not match candidate')
            fixed = {k: v for k, v in state['files'].items() if k != relative}
            fixed_path = self.output / 'fixed-runtime.json'
            with self.fixed_lock:
                if fixed_path.exists() and json.loads(fixed_path.read_text()) != fixed:
                    raise RuntimeError('Non-optimized runtime context changed; start a new experiment')
                write_json(fixed_path, fixed)
            self.key = self.request(self.prefix + '/profiles/' + self.project.PROFILE + '/gateway-key')['api_server_key']
            caps = self.request('/p/' + self.project.PROFILE + '/v1/capabilities', gateway=True)['features']
            if not all(caps.get(k) for k in ('run_submission', 'run_status', 'run_stop', 'session_resources')) or not caps['runs_idempotency']['durable']:
                raise RuntimeError('Gateway lacks required execution/recovery capabilities')
            self.installed = (revision, state)
            return self.installed


class ParallelExperimentRuntime:
    """Coordinate two instances, up to four active tasks, and a shared run budget."""
    def __init__(self, repo: Path, project, output: Path):
        self.repo, self.project, self.output = repo, project, output
        self.production = HermesRuntime(repo, project, output)
        self.initial_body, self.frontmatter = self.production.initial_body, self.production.frontmatter
        self.max_runs = project.POLICY['max_remote_runs']
        self.experiment_id = ''
        self.failure = None
        self.condition = threading.Condition()
        self.git_lock = threading.Lock()
        self.fixed_lock = threading.Lock()
        self.slots = {name: ExperimentSlot(repo, project, output, name, self.candidate_revision, self.fixed_lock) for name in ('a', 'b')}
        self.active = {'a': 0, 'b': 0}
        self.bodies = {'a': None, 'b': None}
        self.inflight = set()
        self.uncertain = {}
        self.baseline_revision = git(repo, 'rev-parse', 'HEAD')

    def __deepcopy__(self, memo):
        return self

    def has_search_capacity(self, next_iteration, holdout):
        used = len(list((self.output / 'trials').glob('*/receipt.json')))
        return used + next_iteration + holdout <= self.max_runs

    def candidate_revision(self, body):
        if body.strip() == self.initial_body:
            return self.baseline_revision
        identity = digest(body.encode())
        folder = self.output / 'candidates' / identity
        receipt = folder / 'candidate.json'
        with self.git_lock:
            if receipt.exists():
                return json.loads(receipt.read_text(encoding='utf-8'))['revision']
            checkout = folder / 'checkout'
            checkout.parent.mkdir(parents=True, exist_ok=True)
            if not checkout.exists():
                subprocess.run(['git', 'clone', '--quiet', '--no-hardlinks', str(self.repo), str(checkout)], check=True)
                for key in ('user.name', 'user.email'):
                    git(checkout, 'config', key, git(self.repo, 'config', key))
            git(checkout, 'checkout', '--detach', self.baseline_revision)
            skill = checkout / self.project.SKILL
            skill.write_bytes(('---\n' + self.frontmatter.strip() + '\n---\n\n' + body.strip() + '\n').encode())
            git(checkout, 'add', '--', self.project.SKILL)
            git(checkout, 'commit', '-m', 'Evaluate DSPy Skill ' + identity[:12])
            revision = git(checkout, 'rev-parse', 'HEAD')
            remote = git(self.repo, 'remote', 'get-url', 'origin')
            git(checkout, 'remote', 'set-url', 'origin', remote)
            git(checkout, 'push', 'origin', 'HEAD:refs/heads/evolution/' + self.experiment_id + '/' + identity[:16])
            write_json(receipt, {'revision': revision, 'body_sha256': identity})
            return revision

    def resume_pending(self):
        # Finish previously submitted runs before any slot can install another
        # candidate. Receipts retain the original run ID and deadline.
        self.failure = None
        for path in (self.output / 'trials').glob('*/receipt.json'):
            receipt = json.loads(path.read_text(encoding='utf-8'))
            if receipt['status'] not in ('submitting', 'running'):
                continue
            identity = receipt['candidate_sha256']
            if identity == digest(self.initial_body.encode()):
                body = self.initial_body
            else:
                skill = self.output / 'candidates' / identity / 'checkout' / self.project.SKILL
                body = skill.read_text(encoding='utf-8').split('---', 2)[2].strip()
                if digest(body.encode()) != identity:
                    raise RuntimeError('Pending run candidate does not match its saved body hash')
            task_input = json.dumps(receipt['case'], ensure_ascii=False, sort_keys=True)
            self.execute(body, task_input)
        self.failure = None

    def execute(self, instructions, task_input):
        identity = digest((self.experiment_id + '\0' + instructions + '\0' + task_input).encode())
        receipt_file = self.output / 'trials' / identity / 'receipt.json'
        with self.condition:
            while identity in self.inflight:
                self.condition.wait()
            if self.failure and identity not in self.uncertain:
                raise RuntimeError('Experiment stopped after infrastructure failure') from self.failure
            if receipt_file.exists():
                receipt = json.loads(receipt_file.read_text(encoding='utf-8'))
                if receipt['status'] == 'collected':
                    return json.dumps({'trial': str(receipt_file.parent), 'trace': receipt['trace_summary']}, ensure_ascii=False)
                prior_slot = receipt.get('slot')
            else:
                if len(list((self.output / 'trials').glob('*/receipt.json'))) >= self.max_runs:
                    raise RuntimeError('Remote run budget exhausted')
                receipt = {'status': 'prepared', 'delivery_id': 'dspy-' + identity[:24],
                           'case': json.loads(task_input), 'candidate_sha256': digest(instructions.encode())}
                prior_slot = None
                write_json(receipt_file, receipt)
            already_reserved = identity in self.uncertain
            while True:
                if self.failure and not already_reserved:
                    raise RuntimeError('Experiment stopped after infrastructure failure') from self.failure
                available = [s for s in self.slots if (not prior_slot or prior_slot == s)
                             and (not self.active[s] or self.bodies[s] == instructions)]
                if (already_reserved or sum(self.active.values()) < 4) and available:
                    slot = min(available, key=lambda s: (self.bodies[s] != instructions, self.active[s]))
                    self.inflight.add(identity)
                    if not already_reserved:
                        self.active[slot] += 1
                    self.bodies[slot] = instructions
                    receipt['slot'] = slot
                    write_json(receipt_file, receipt)
                    break
                self.condition.wait()
        try:
            runtime = self.slots[slot]
            runtime.experiment_id = self.experiment_id
            return runtime.execute(instructions, task_input)
        except Exception as exc:
            with self.condition:
                self.failure = exc
            raise
        finally:
            with self.condition:
                latest = json.loads(receipt_file.read_text(encoding='utf-8'))
                if latest['status'] in ('submitting', 'running') and not latest.get('terminal'):
                    self.uncertain[identity] = slot
                else:
                    self.uncertain.pop(identity, None)
                    self.active[slot] -= 1
                self.inflight.remove(identity)
                self.condition.notify_all()

    def deploy(self, body):
        return self.production.deploy(body)

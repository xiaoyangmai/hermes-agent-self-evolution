#!/usr/bin/env python3
"""Small local HTTP client for the existing Hermes and control-plane APIs.

The producer must create result.json and manifest.json in its registered
project's result directory. A delivery ID is distinct from a Gateway run ID.
"""
import argparse
import hashlib
import json
import os
import re
import sys
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid
from pathlib import Path, PurePosixPath, PureWindowsPath


class OperatorError(Exception):
    pass


def project_identifier(value):
    if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.-]{0,63}', value):
        raise argparse.ArgumentTypeError('invalid project or profile identifier')
    return value


def run_identifier(value):
    if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9._:-]{0,127}', value):
        raise argparse.ArgumentTypeError('invalid run or idempotency identifier')
    return value


def full_revision(value):
    if not re.fullmatch(r'(?:[0-9a-f]{40}|[0-9a-f]{64})', value):
        raise argparse.ArgumentTypeError('expected a full lowercase Git revision')
    return value


def request(base, path, token, data=None, extra=None, timeout=30):
    headers = {'Authorization': 'Bearer ' + token, **(extra or {})}
    req = urllib.request.Request(base.rstrip('/') + path, data=data, headers=headers)
    for attempt in range(2):
        try:
            return urllib.request.urlopen(req, timeout=timeout)
        except urllib.error.HTTPError as exc:
            raise OperatorError(f'{path}: HTTP {exc.code}') from exc
        except (urllib.error.URLError, ConnectionResetError, TimeoutError) as exc:
            if data is not None or attempt:
                raise OperatorError(f'{path}: network error') from exc
            print('GET network error; retrying once', file=sys.stderr)


def json_request(base, path, token, data=None, extra=None):
    with request(base, path, token, data, extra) as response:
        return json.load(response)


def wait_operation(base, token, operation, poll, deadline, observe):
    while operation['status'] not in ('succeeded', 'failed', 'cancelled'):
        if time.monotonic() >= deadline:
            raise OperatorError('operation timed out: ' + operation['id'])
        time.sleep(poll)
        operation = json_request(base, '/v1/operations/' + operation['id'], token)
        observe(operation)
    if operation['status'] != 'succeeded':
        raise OperatorError('operation did not succeed: ' + operation['id'] + ' (' + operation['status'] + ')')
    return operation


def operation(base, token, path, key, poll, timeout, observe):
    result = json_request(base, path, token, b'', {'Idempotency-Key': key})
    observe(result)
    return wait_operation(base, token, result, poll, time.monotonic() + timeout, observe)


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def release(args):
    base, token = os.environ['HERMES_CONTROL_URL'], os.environ['HERMES_CONTROL_TOKEN']
    prefix = '/v1/projects/' + args.project
    request_id = uuid.uuid4().hex
    receipt = {'project': args.project, 'expected_revision': args.expected_revision, 'steps': [], 'status': 'in_progress'}

    def observe(record):
        if receipt['steps'] and receipt['steps'][-1]['id'] == record['id']:
            receipt['steps'][-1] = record
        else:
            receipt['steps'].append(record)
        write_json(args.receipt, receipt)

    try:
        sync = operation(base, token, prefix + '/sync', 'sync-' + request_id, args.poll, args.timeout, observe)
        actual = sync.get('result', {}).get('revision')
        receipt['observed_sync_revision'] = actual
        if actual != args.expected_revision:
            raise OperatorError('sync revision did not match expected revision')
        check = operation(base, token, prefix + '/environment/check', 'check-' + request_id, args.poll, args.timeout, observe)
        if not check.get('result', {}).get('ready'):
            raise OperatorError('environment check did not report ready; prepare separately')
        receipt['environment_check_skipped'] = bool(check.get('result', {}).get('skipped'))
        operation(base, token, prefix + '/gateway/refresh', 'refresh-' + request_id, args.poll, args.timeout, observe)
        receipt['status'] = 'succeeded'
    except Exception:
        receipt['status'] = 'incomplete'
        raise
    finally:
        write_json(args.receipt, receipt)
    print('release succeeded; sync SHA recorded; effective runtime contents not verified')


def run(args):
    base = os.environ['HERMES_GATEWAY_URL']
    token = os.environ.get('HERMES_GATEWAY_API_KEY')
    if not token:
        if not args.project:
            raise OperatorError('set HERMES_GATEWAY_API_KEY or specify --project for control-plane key delivery')
        credential = json_request(os.environ['HERMES_CONTROL_URL'],
                                  '/v1/projects/' + args.project + '/profiles/' + args.profile + '/gateway-key',
                                  os.environ['HERMES_CONTROL_TOKEN'])
        if (credential.get('project') != args.project or credential.get('profile') != args.profile
                or not isinstance(credential.get('api_server_key'), str) or not credential['api_server_key']):
            raise OperatorError('control-plane did not return the requested profile key')
        token = credential['api_server_key']
    if args.events.exists():
        raise OperatorError('events output already exists; choose a new file')
    body = json.loads(args.input.read_text(encoding='utf-8'))
    if not isinstance(body, dict) or not isinstance(body.get('input'), str):
        raise OperatorError('input file must be a JSON object with string input')
    prefix = '/p/' + args.profile + '/v1/runs'
    submitted = json_request(base, prefix, token, json.dumps(body, ensure_ascii=False).encode('utf-8'),
                             {'Content-Type': 'application/json', 'Idempotency-Key': args.request_key})
    run_id = submitted['run_id']
    receipt = {'profile': args.profile, 'gateway_run_id': run_id, 'submission': submitted, 'status': 'in_progress',
               'events': {'path': str(args.events), 'scope': 'Gateway SSE subset; neither complete trace nor proof that all early events were captured',
                          'terminal_event_seen': False, 'stream_error': None}}
    write_json(args.receipt, receipt)
    args.events.parent.mkdir(parents=True, exist_ok=True)
    done = threading.Event()

    def capture():
        try:
            with request(base, prefix + '/' + run_id + '/events', token, timeout=args.timeout) as response, args.events.open('wb') as out:
                for line in response:
                    out.write(line)
                    out.flush()
                    if line.startswith(b'data: '):
                        event = json.loads(line[6:])
                        if event.get('event') in ('run.completed', 'run.failed', 'run.cancelled'):
                            receipt['events']['terminal_event_seen'] = True
                done.set()
        except (OperatorError, OSError, ValueError) as exc:
            receipt['events']['stream_error'] = type(exc).__name__
            done.set()

    thread = threading.Thread(target=capture, daemon=True)
    thread.start()
    try:
        deadline = time.monotonic() + args.timeout
        while True:
            status = json_request(base, prefix + '/' + run_id, token)
            if status.get('status') in ('completed', 'failed', 'cancelled', 'canceled'):
                receipt['terminal_status'] = status
                break
            if time.monotonic() >= deadline:
                raise OperatorError('run timed out; no stop was requested: ' + run_id)
            time.sleep(args.poll)
        done.wait(timeout=min(10, args.timeout))
        receipt['events']['capture_reached_terminal'] = bool(done.is_set() and receipt['events']['terminal_event_seen'] and not receipt['events']['stream_error'])
        receipt['status'] = status['status']
    except Exception:
        receipt['events']['capture_reached_terminal'] = False
        receipt['status'] = 'incomplete'
        raise
    finally:
        write_json(args.receipt, receipt)
    print('run ' + run_id + ': ' + receipt['status'] + '; SSE capture reached terminal: '
          + str(receipt['events']['capture_reached_terminal']) + ' (limited subset)')
    if receipt['status'] != 'completed':
        raise OperatorError('run ended with status ' + receipt['status'])


def collect(args):
    base, token = os.environ['HERMES_CONTROL_URL'], os.environ['HERMES_CONTROL_TOKEN']
    prefix = '/v1/projects/' + args.project + '/runs/' + args.delivery_id
    key = args.finalize_key or 'finalize-' + hashlib.sha256((args.project + ':' + args.delivery_id).encode()).hexdigest()[:32]
    receipt = {'project': args.project, 'delivery_id': args.delivery_id,
               'gateway_run_id': args.gateway_run_id, 'binding': 'caller supplied; not verified by control-plane',
               'finalize_key': key, 'artifacts': [], 'status': 'in_progress'}

    def observe(record):
        receipt['finalize'] = record
        write_json(args.receipt, receipt)

    try:
        operation(base, token, prefix + '/finalize', key, args.poll, args.timeout, observe)
        receipt['result'] = json_request(base, prefix + '/result', token)
        listing = json_request(base, prefix + '/artifacts', token)
        root = args.output.resolve()
        names = set()
        downloads = []
        for item in listing['artifacts']:
            name = item['name']
            if (not isinstance(name, str) or not name or '\\' in name or PureWindowsPath(name).drive
                    or PurePosixPath(name).is_absolute() or any(part in ('', '.', '..') for part in name.split('/'))):
                raise OperatorError('artifact name must be a safe relative path')
            if name in names:
                raise OperatorError('duplicate artifact name: ' + name)
            names.add(name)
            target = root.joinpath(*PurePosixPath(name).parts).resolve()
            if not target.is_relative_to(root):
                raise OperatorError('artifact name escapes output directory')
            downloads.append((item, target))
        root.mkdir(parents=True, exist_ok=True)
        for item, target in downloads:
            artifact_id = item['artifact_id']
            if not re.fullmatch(r'art_[a-f0-9]{32}', artifact_id):
                raise OperatorError('invalid artifact ID')
            with request(base, '/v1/artifacts/' + artifact_id + '/download', token) as response:
                contents = response.read()
                header_hash = response.headers.get('X-Artifact-Sha256')
                header_id = response.headers.get('X-Artifact-Id')
            digest = hashlib.sha256(contents).hexdigest()
            if digest != item['sha256'] or digest != header_hash or artifact_id != header_id:
                raise OperatorError('artifact checksum or ID mismatch: ' + artifact_id)
            target.parent.mkdir(parents=True, exist_ok=True)
            if target.exists():
                if hashlib.sha256(target.read_bytes()).hexdigest() != digest:
                    raise OperatorError('refusing to overwrite different file: ' + item['name'])
            else:
                target.write_bytes(contents)
            receipt['artifacts'].append({'artifact_id': artifact_id, 'name': item['name'], 'sha256': digest, 'path': str(target)})
        receipt['status'] = 'succeeded'
    except Exception:
        receipt['status'] = 'incomplete'
        raise
    finally:
        write_json(args.receipt, receipt)
    print('collection succeeded; caller-supplied run/delivery binding is not verified')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    p = commands.add_parser('release')
    p.add_argument('--project', type=project_identifier, required=True)
    p.add_argument('--expected-revision', type=full_revision, required=True)
    p.add_argument('--receipt', type=Path, required=True)
    p.set_defaults(func=release)
    p = commands.add_parser('run')
    p.add_argument('--profile', type=project_identifier, required=True)
    p.add_argument('--project', type=project_identifier, help='registered project for control-plane key delivery when no Gateway key is set')
    p.add_argument('--input', type=Path, required=True)
    p.add_argument('--request-key', type=run_identifier, required=True)
    p.add_argument('--events', type=Path, required=True)
    p.add_argument('--receipt', type=Path, required=True)
    p.set_defaults(func=run)
    p = commands.add_parser('collect')
    p.add_argument('--project', type=project_identifier, required=True)
    p.add_argument('--delivery-id', type=run_identifier, required=True)
    p.add_argument('--gateway-run-id', type=run_identifier, required=True)
    p.add_argument('--finalize-key', type=run_identifier, help='new request key after a confirmed failed finalize has been fixed')
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--receipt', type=Path, required=True)
    p.set_defaults(func=collect)
    for subparser in commands.choices.values():
        subparser.add_argument('--poll', type=float, default=2)
        subparser.add_argument('--timeout', type=float, default=300)
    args = parser.parse_args()
    try:
        args.func(args)
    except (OperatorError, KeyError, OSError, ValueError) as exc:
        print('operator failed: ' + str(exc), file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())

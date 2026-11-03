import json
import time
from concurrent.futures import ThreadPoolExecutor
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from threading import Thread

import dspy
import pytest
from litellm import ModelResponse

from evolution.usage import AccountingLM, UsageLedger


def test_concurrent_provider_usage_is_recorded_without_prompts_or_estimated_cost(tmp_path, monkeypatch):
    def forward(self, *args, **kwargs):
        return ModelResponse(model='test', choices=[{'message': {'role': 'assistant', 'content': 'private answer'}}],
                             usage={'prompt_tokens': 5, 'completion_tokens': 2, 'total_tokens': 7},
                             _hidden_params={'response_cost': 99})
    monkeypatch.setattr(dspy.LM, 'forward', forward)
    ledger = UsageLedger(tmp_path / 'model-usage.jsonl')
    lm = AccountingLM('openai/test', ledger=ledger, role='evaluation', api_key='private-key', cache=False)
    with ThreadPoolExecutor(max_workers=4) as pool:
        outputs = list(pool.map(lambda n: lm(prompt='private prompt ' + str(n)), range(12)))
    assert len(outputs) == 12
    raw = ledger.path.read_text(encoding='utf-8')
    rows = [json.loads(line) for line in raw.splitlines()]
    assert len(rows) == 12
    assert all(row['role'] == 'evaluation' and row['tokens']['total_tokens'] == 7 for row in rows)
    assert all(row['cost'] is None and row['cost_source'] == 'unknown' for row in rows)
    assert all(secret not in raw for secret in ('private prompt', 'private answer', 'private-key', '99'))


def test_missing_provider_usage_and_failed_call_are_unknown(tmp_path, monkeypatch):
    ledger = UsageLedger(tmp_path / 'model-usage.jsonl')
    ledger.record('calibration', ModelResponse(model='test', choices=[]))
    def fail(self, *args, **kwargs):
        raise ConnectionError('credential and prompt must not be recorded')
    monkeypatch.setattr(dspy.LM, '__call__', fail)
    lm = AccountingLM('openai/test', ledger=ledger, role='reflection', api_key='unused', cache=False)
    try:
        lm(prompt='private')
    except ConnectionError:
        pass
    rows = [json.loads(line) for line in ledger.path.read_text().splitlines()]
    assert rows[0]['tokens'] is None and rows[0]['cost'] is None
    assert rows[1]['role'] == 'reflection' and rows[1]['status'] == 'failed' and rows[1]['tokens'] is None


def test_dspy_predict_usage_is_recorded_in_independent_threads(tmp_path, monkeypatch):
    def forward(self, *args, **kwargs):
        return ModelResponse(model='test', choices=[{'message': {'role': 'assistant',
             'content': '[[ ## answer ## ]]\nyes\n[[ ## completed ## ]]'}}],
             usage={'prompt_tokens': 4, 'completion_tokens': 2, 'total_tokens': 6})
    monkeypatch.setattr(dspy.LM, 'forward', forward)
    ledger = UsageLedger(tmp_path / 'model-usage.jsonl')
    lm = AccountingLM('openai/test', ledger=ledger, role='calibration', api_key='unused', cache=False)
    def evaluate(n):
        with dspy.context(lm=lm, adapter=dspy.ChatAdapter()):
            return dspy.Predict('question -> answer')(question='private ' + str(n)).answer
    with ThreadPoolExecutor(max_workers=2) as pool:
        assert list(pool.map(evaluate, range(4))) == ['yes'] * 4
    rows = [json.loads(line) for line in ledger.path.read_text().splitlines()]
    assert len(rows) == 4 and all(row['role'] == 'calibration' for row in rows)


def test_unwritable_ledger_does_not_interrupt_model_response(tmp_path, monkeypatch):
    def forward(self, *args, **kwargs):
        return ModelResponse(model='test', choices=[{'message': {'role': 'assistant', 'content': 'ok'}}],
                             usage={'prompt_tokens': 1, 'completion_tokens': 1})
    monkeypatch.setattr(dspy.LM, 'forward', forward)
    blocker = tmp_path / 'file'
    blocker.write_text('not a directory')
    ledger = UsageLedger(blocker / 'model-usage.jsonl')
    lm = AccountingLM('openai/test', ledger=ledger, role='evaluation', api_key='unused', cache=False)
    with pytest.warns(RuntimeWarning, match='usage could not be recorded'):
        assert lm(prompt='private') == ['ok']
    assert ledger.recording_failed


@pytest.mark.parametrize('controlled', [False, True])
def test_litellm_transmits_separate_headers_and_no_retry_on_error(tmp_path, controlled):
    requests = []
    class Handler(BaseHTTPRequestHandler):
        def do_POST(self):
            body = json.loads(self.rfile.read(int(self.headers['Content-Length'])))
            requests.append((self.headers.get('Authorization'), self.headers.get('X-Hermes-Control-Authorization'), body))
            self.send_response(500 if controlled else 200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'error': {'message': 'test'}} if controlled else
                {'id': 'test', 'model': 'test', 'choices': [{'index': 0, 'message':
                    {'role': 'assistant', 'content': 'ok'}, 'finish_reason': 'stop'}]}).encode())
        def log_message(self, *args):
            pass
    server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        options = {'api_base': f'http://127.0.0.1:{server.server_port}/v1',
                   'api_key': 'selector-test', 'cache': False}
        if controlled:
            options.update(extra_headers={'X-Hermes-Control-Authorization': 'Bearer control-test'},
                           num_retries=0, max_retries=0, timeout=30)
        ledger = UsageLedger(tmp_path / 'model-usage.jsonl')
        lm = AccountingLM('openai/test', ledger=ledger, role='evaluation', **options)
        if controlled:
            with pytest.raises(dspy.LMError):
                lm(prompt='test')
            assert len(requests) == 1 and requests[0][:2] == ('Bearer selector-test', 'Bearer control-test')
            assert json.loads(ledger.path.read_text())['status'] == 'failed'
        else:
            assert lm(prompt='test') == ['ok']
            assert len(requests) == 1 and requests[0][:2] == ('Bearer selector-test', None)
        assert not {'max_retries', 'num_retries', 'extra_headers', 'timeout'} & requests[0][2].keys()
        assert 'control-test' not in json.dumps(requests[0][2])
        assert 'control-test' not in ledger.path.read_text() and 'selector-test' not in ledger.path.read_text()
    finally:
        server.shutdown()
        thread.join()
        server.server_close()


def test_model_timeout_is_failed_once_with_unknown_usage(tmp_path):
    requests = []
    class Handler(BaseHTTPRequestHandler):
        def do_POST(self):
            self.rfile.read(int(self.headers['Content-Length']))
            requests.append(True)
            time.sleep(0.5)
        def log_message(self, *args):
            pass
    server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        ledger = UsageLedger(tmp_path / 'model-usage.jsonl')
        lm = AccountingLM('openai/test', ledger=ledger, role='evaluation',
                          api_base=f'http://127.0.0.1:{server.server_port}/v1',
                          api_key='selector-test', cache=False, timeout=0.1,
                          num_retries=0, max_retries=0)
        with pytest.raises(dspy.LMError):
            lm(prompt='test')
        assert len(requests) == 1
        record = json.loads(ledger.path.read_text())
        assert record['status'] == 'failed' and record['tokens'] is None and record['cost'] is None
    finally:
        server.shutdown()
        thread.join()
        server.server_close()

import json
from concurrent.futures import ThreadPoolExecutor

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
        with dspy.context(lm=lm):
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

"""Record model-provider usage without recording prompts or model responses."""
import json
import threading
import warnings
from pathlib import Path

import dspy


class UsageLedger:
    def __init__(self, path: Path):
        self.path = path
        self.lock = threading.Lock()
        self.recording_failed = False

    def record(self, role, response=None):
        usage = dict(getattr(response, 'usage', None) or {})
        # Only a provider-returned cost is eligible; DSPy/LiteLLM's hidden
        # response_cost can be a local estimate and is deliberately ignored.
        cost = usage.get('cost')
        cost = cost if isinstance(cost, (int, float)) and not isinstance(cost, bool) else None
        tokens = {key: usage[key] for key in ('prompt_tokens', 'completion_tokens', 'input_tokens', 'output_tokens', 'total_tokens')
                  if type(usage.get(key)) is int and usage[key] >= 0}
        row = {'role': role, 'status': 'completed' if response is not None else 'failed',
               'tokens': tokens if tokens else None, 'cost': cost,
               'cost_source': 'provider_usage' if cost is not None else 'unknown',
               'cost_currency': usage.get('currency') if cost is not None and usage.get('currency') in ('USD', 'CNY', 'EUR') else None,
               'cache_hit': bool(getattr(response, 'cache_hit', False)) if response is not None else None}
        try:
            with self.lock:
                self.path.parent.mkdir(parents=True, exist_ok=True)
                with self.path.open('a', encoding='utf-8') as stream:
                    stream.write(json.dumps(row, ensure_ascii=False) + '\n')
        except OSError:
            self.recording_failed = True
            warnings.warn('Model usage could not be recorded; evaluation continues and usage is incomplete.', RuntimeWarning)


class AccountingLM(dspy.LM):
    def __init__(self, model, *, ledger, role, **kwargs):
        super().__init__(model, **kwargs)
        self.ledger = ledger
        self.usage_role = role

    def _process_lm_response(self, response, prompt, messages, **kwargs):
        outputs = super()._process_lm_response(response, prompt, messages, **kwargs)
        self.ledger.record(self.usage_role, response)
        return outputs

    def __call__(self, *args, **kwargs):
        try:
            return super().__call__(*args, **kwargs)
        except Exception:
            self.ledger.record(self.usage_role)
            raise

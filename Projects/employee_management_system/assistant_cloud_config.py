"""Server-only cloud eligibility evidence and bounded application limits."""
import json
import os
import time
from pathlib import Path


def limit(name, default, environment=None):
    env = os.environ if environment is None else environment
    raw = env.get('ABAP_ASSISTANT_' + name, str(default))
    if not str(raw).isdigit() or not 1 <= int(raw) <= 100000:
        raise ValueError('Invalid assistant usage limit.')
    return int(raw)


def evidence(environment=None):
    env = os.environ if environment is None else environment
    path = env.get('ABAP_ASSISTANT_CLOUD_VALIDATION_FILE', '')
    if not path:
        return {}
    try:
        with Path(path).open(encoding='utf-8') as stream:
            records = json.loads(stream.read(131073))
        if not isinstance(records, list) or len(records) > 100:
            raise ValueError()
        return {r['id']: r for r in records if isinstance(r, dict) and isinstance(r.get('id'), str)}
    except (OSError, ValueError, TypeError, KeyError):
        raise ValueError('Cloud validation evidence is unavailable.') from None


def verified(model_id, records):
    row = records.get(model_id, {})
    checked = row.get('checked_at', 0)
    return (type(checked) in (float, int) and 0 <= time.time()-checked <= 86400
            and row.get('free_eligible') is True and row.get('access_verified') is True
            and row.get('business_protocol_verified') is True)


class AssistantLimitError(ValueError):
    """Safe, user-facing application quota or concurrency rejection."""

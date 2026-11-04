"""Operator-only discovery/validation. Never creates billing or paid fallbacks.

Run from the application directory. Environment/secret files supply keys; output
contains only model metadata, credential fingerprints and synthetic test outcomes.
"""
import argparse
import hashlib
import http.client
import json
import os
import re
import time
from decimal import Decimal, InvalidOperation
from pathlib import Path

from assistant_gateway import Gateway, Model, configured_models


def get_catalog(host, path, headers=None):
    connection = http.client.HTTPSConnection(host, timeout=20)
    try:
        connection.request('GET', path, headers=headers or {})
        response = connection.getresponse()
        if response.status != 200:
            raise ValueError('Provider catalog is unavailable or authentication failed.')
        raw = response.read(8388609)
        if len(raw) > 8388608:
            raise ValueError('Catalog exceeded the size limit.')
        return json.loads(raw)
    finally:
        connection.close()


def free_openrouter(catalog):
    result = []
    for row in catalog.get('data', []):
        pricing = row.get('pricing', {})
        try:
            zero = pricing and all(Decimal(str(value)) == 0 for value in pricing.values())
        except (InvalidOperation, TypeError):
            zero = False
        if (isinstance(row.get('id'), str) and row['id'].endswith(':free') and zero
                and row.get('architecture', {}).get('output_modalities', ['text']) == ['text']):
            result.append({'id': 'openrouter:'+row['id'], 'provider': 'openrouter',
                'model': row['id'], 'free_eligible': True,
                'native_tools_advertised': 'tools' in row.get('supported_parameters', [])})
    return result


def validate(model, metadata):
    # This bypasses the stale manifest ONLY inside this explicit operator validation.
    gateway = Gateway([Model(model.id, model.provider, model.model, model.key, model.endpoint, True)])
    english, _ = gateway.generate(model.id, 'Respond briefly in English.', 'Say CLOUD_OK.')
    japanese, _ = gateway.generate(model.id, '日本語だけで短く回答してください。', '業務の確認について一文で回答してください。')
    structured, _ = gateway.generate(model.id,
        'Return only the exact JSON object {"tool":"leads"}. No prose or markdown.',
        'Select the read-only leads tool for synthetic validation. Do not execute any action.')
    cleaned = re.sub(r'^```(?:json)?\s*|\s*```$', '', structured.strip())
    passed = english.strip().rstrip('.!') == 'CLOUD_OK' and bool(re.search(r'[ぁ-んァ-ヶ]', japanese)) and json.loads(cleaned) == {'tool':'leads'}
    if not passed:
        raise ValueError('Synthetic language/business-protocol validation failed.')
    return {**metadata, 'id': model.id, 'provider': model.provider, 'model': model.model,
        'checked_at': time.time(), 'key_fingerprint': hashlib.sha256(model.key.encode()).hexdigest(),
        'access_verified': True, 'business_protocol_verified': True,
        'english_verified': True, 'japanese_verified': True,
        'native_tools_verified': False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--discover-openrouter', action='store_true')
    parser.add_argument('--output', required=True)
    args = parser.parse_args()
    if args.discover_openrouter:
        catalog = free_openrouter(get_catalog('openrouter.ai', '/api/v1/models'))
        Path(args.output).write_text(json.dumps(catalog, indent=2), encoding='utf-8')
        print(f'Discovered {len(catalog)} zero-price :free candidates; account access is not verified.')
        return
    environment = dict(os.environ)
    environment.pop('ABAP_ASSISTANT_CLOUD_VALIDATION_FILE', None)
    models = [model for model in configured_models(environment) if model.provider != 'local']
    if len(models) > 5:
        raise ValueError('Validate at most five explicitly configured cloud models per invocation.')
    try:
        catalog = free_openrouter(get_catalog('openrouter.ai', '/api/v1/models')) if any(m.provider == 'openrouter' for m in models) else []
    except Exception:
        catalog = []
    checked = []
    failures = []
    for model in models:
        try:
            if not model.key or os.environ.get('ABAP_ASSISTANT_REMOTE_APPROVED') != 'true':
                raise ValueError('Missing server credential or remote approval.')
            if model.provider == 'openrouter':
                metadata = next((r for r in catalog if r['id'] == model.id), None)
                if metadata is None:
                    raise ValueError('Model is not currently zero-price :free.')
            else:
                prefix = 'ABAP_ASSISTANT_'+model.provider.upper()
                reviewed = os.environ.get(prefix+'_FREE_ACCOUNT_REVIEWED') == 'true'
                eligible = {m.strip() for m in os.environ.get(prefix+'_FREE_MODELS', '').split(',')}
                if not reviewed or model.model not in eligible:
                    raise ValueError('Requires reviewed free-tier model and billing-disabled account evidence.')
                metadata = {'free_eligible': True, 'native_tools_advertised': False}
                if model.provider == 'gemini':
                    # Authentication/model access alone never establishes free-tier pricing.
                    available = get_catalog('generativelanguage.googleapis.com', '/v1beta/models/'+model.model, {'x-goog-api-key':model.key})
                    if available.get('name') != 'models/'+model.model or 'generateContent' not in available.get('supportedGenerationMethods', []):
                        raise ValueError('Model is not available to this Gemini key.')
            checked.append(validate(model, metadata))
        except Exception:
            # Never serialize remote exception bodies, headers or credentials.
            failures.append({'id':model.id, 'status':'Not validated; check server configuration, free eligibility and provider access.'})
    Path(args.output).write_text(json.dumps(checked, indent=2), encoding='utf-8')
    print(json.dumps({'validated_models':[r['id'] for r in checked], 'failures':failures,
                      'blocked_no_configured_models':not models}))
    if not checked:
        raise SystemExit(2)


if __name__ == '__main__':
    main()

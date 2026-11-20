"""Explicit DEBUG-only payload capture in a private directory."""
import json
import os
from pathlib import Path
import re


SECRET_KEY = re.compile(r'api[-_ ]?key|authorization|password|secret|credential|access[-_ ]?token', re.I)
SECRET_TEXT = re.compile(r'''(?i)(bearer\s+|(?:api[_ -]?key|password|authorization)["']?\s*[:=]\s*["']?)[^\s,;"']+''')


def capture_payload(root: Path, run_id: str, call_id: str, phase: str, value, secret: str):
    if os.getenv('RESUME_LOG_LEVEL', '').upper() != 'DEBUG' or os.getenv('RESUME_LOG_PAYLOADS') != 'true':
        return None, None

    def redact(item):
        if isinstance(item, dict):
            return {key: '[redacted]' if SECRET_KEY.search(str(key)) else redact(member)
                    for key, member in item.items()}
        if isinstance(item, (list, tuple)):
            return [redact(member) for member in item]
        if isinstance(item, str):
            text = item.replace(secret, '[redacted]') if secret else item
            return SECRET_TEXT.sub(r'\1[redacted]', text)
        return item

    try:
        directory = root / run_id / 'private-payloads'
        directory.mkdir(parents=True, exist_ok=True, mode=0o700)
        path = directory / f'{call_id}-{phase}.json'
        payload = json.dumps(redact(value), indent=2, ensure_ascii=True, default=str)
        with open(path, 'x', encoding='utf-8', opener=lambda name, flags: os.open(name, flags, 0o600)) as stream:
            stream.write(payload)
    except (OSError, TypeError, ValueError, RecursionError):
        return None, None
    return payload[:1800], str(path)

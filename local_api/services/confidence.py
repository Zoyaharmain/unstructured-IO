"""Optional JSON calibration artifacts annotate logs; they never route or decide."""
import json
import math
import os
from pathlib import Path


def confidence_for(score, *, task, model_revision, anchor_sha256):
    result = {'state': 'not_calibrated', 'probability': None, 'method': None,
              'calibration_version': None, 'target': 'ml_candidate_correct'}
    filename = os.getenv('RESUME_CALIBRATION_FILE')
    if os.getenv('RESUME_CALIBRATION_DIR'):
        filename = str(Path(os.environ['RESUME_CALIBRATION_DIR']) / (task + '.json'))
    if not filename:
        return result
    try:
        artifact = json.loads(Path(filename).read_text())
        if (artifact['task'] != task or artifact['model_revision'] != model_revision
                or artifact['anchor_sha256'] != anchor_sha256
                or artifact['target'] != 'ml_candidate_correct'
                or artifact['label_source'] != 'human_verified'
                or not artifact.get('evaluation') or not math.isfinite(score)):
            return result
        if artifact['method'] == 'platt':
            z = artifact['coefficient'] * score + artifact['intercept']
            probability = 1 / (1 + math.exp(-max(-700, min(700, z))))
        elif artifact['method'] == 'isotonic':
            import numpy as np
            probability = float(np.interp(score, artifact['x'], artifact['y']))
        else:
            return result
        if not math.isfinite(probability) or not 0 <= probability <= 1:
            return result
        result.update(state='calibrated', probability=probability, method=artifact['method'],
                      calibration_version=artifact['version'])
    except Exception:
        pass
    return result

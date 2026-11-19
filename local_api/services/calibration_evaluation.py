"""Offline grouped calibration evaluation, independent of resume decisions."""
import math


def fit_calibration(rows, *, method='platt'):
    import numpy as np
    from sklearn.model_selection import GroupShuffleSplit
    from sklearn.linear_model import LogisticRegression
    from sklearn.isotonic import IsotonicRegression
    if any(r.get('label_source') != 'human_verified' or r['correct'] not in (0, 1)
           or not math.isfinite(r['score']) for r in rows):
        raise ValueError('Finite raw scores and human-verified correctness labels are required')
    if len({r['document_group'] for r in rows}) < 4:
        raise ValueError('At least four independent document groups are required for a split; more are needed for reliable calibration')
    if len({r['task'] for r in rows}) != 1:
        raise ValueError('Evaluate decision types separately')
    x = np.array([r['score'] for r in rows]); y = np.array([r['correct'] for r in rows])
    groups = np.array([r['document_group'] for r in rows])
    train, test = next(GroupShuffleSplit(n_splits=1, test_size=.25, random_state=42).split(x, y, groups))
    if len(set(y[train])) < 2 or len(set(y[test])) < 2:
        raise ValueError('Both correctness outcomes are required in calibration and test partitions')
    if method == 'platt':
        model = LogisticRegression().fit(x[train].reshape(-1, 1), y[train])
        probabilities = model.predict_proba(x[test].reshape(-1, 1))[:, 1]
        artifact = {'method': method, 'coefficient': float(model.coef_[0, 0]), 'intercept': float(model.intercept_[0])}
    elif method == 'isotonic':
        model = IsotonicRegression(out_of_bounds='clip').fit(x[train], y[train])
        probabilities = model.predict(x[test])
        artifact = {'method': method, 'x': model.X_thresholds_.tolist(), 'y': model.y_thresholds_.tolist()}
    else:
        raise ValueError('Unsupported calibration method')
    bins = []
    assignments = np.minimum((probabilities*10).astype(int), 9)
    for index in range(10):
        mask = assignments == index
        if mask.any():
            bins.append({'count': int(mask.sum()), 'mean_probability': float(probabilities[mask].mean()),
                         'accuracy': float(y[test][mask].mean())})
    metrics = {'calibration_count': len(train), 'test_count': len(test),
               'calibration_groups': sorted(set(groups[train])), 'test_groups': sorted(set(groups[test])),
               'predictive_accuracy': float(y[test].mean()),
               'brier_score': float(np.mean((probabilities-y[test])**2)),
               'expected_calibration_error': sum(b['count']/len(test)*abs(b['mean_probability']-b['accuracy']) for b in bins),
               'scope': 'ML candidate correctness; not refined or LLM decision confidence',
               'limitations': 'A held-out metric is not certification. Independently verify label provenance and duplicate grouping.'}
    return artifact, metrics, bins

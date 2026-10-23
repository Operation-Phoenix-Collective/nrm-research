"""
Role: Train all models on the same data and store their results.
Description: Fits DeepSurv, the Faraggi-Simon network, the Cox proportional
hazards model, logistic regression, an SVM and a random forest on the
prepared train set. Scores the train, validation and test patients with each
model and writes three tables in the same layout for all models, each with a
column model: predictions.csv (one row per patient and model), metrics.csv
(one row per model and set) and history.csv (one row per epoch, for the
models trained in epochs). Also writes models.json with the settings.
Author: Bor
"""
import json
import logging
import time
from pathlib import Path

import numpy as np
import pandas as pd

from nrm_research import (classifier_models, cox_networks, model_data,
                          model_metrics)

log = logging.getLogger(__name__)

# name: (fit function, default settings). A fit function takes the data, the
# settings and the horizon and returns (predict, history or None, info).
MODEL_REGISTRY = {
    name: (cox_networks.fit_cox_network, params)
    for name, params in cox_networks.DEFAULT_PARAMS.items()
}
MODEL_REGISTRY.update({
    'Logistic regression': (
        classifier_models.fit_logistic_regression,
        classifier_models.DEFAULT_PARAMS['Logistic regression']),
    'SVM': (classifier_models.fit_svm,
            classifier_models.DEFAULT_PARAMS['SVM']),
    'Random forest': (
        classifier_models.fit_random_forest,
        classifier_models.DEFAULT_PARAMS['Random forest']),
})


def risk_groups(scores, train_scores, n_groups):
    """Group 1 (lowest risk) to n_groups (highest). The limits are the
    quantiles of the train scores, the same for every set."""
    limits = np.quantile(train_scores, np.linspace(0, 1, n_groups + 1)[1:-1])
    return np.searchsorted(limits, scores, side='right') + 1


def _score_sets(predict, data, ids, horizon, n_groups, model_name):
    """Return the prediction rows and the metric rows of one model."""
    scores = {name: np.asarray(predict(data[name][0]), dtype=np.float64)
              for name in model_data.SETS}
    prediction_rows, metric_rows = [], []
    for name in model_data.SETS:
        _, t, e = data[name]
        table = ids[name].copy()
        table.insert(0, 'set', name)
        table.insert(0, 'model', model_name)
        table['time'] = t
        table['event'] = e.astype(int)
        table['risk_score'] = scores[name]
        table['risk_group'] = risk_groups(
            scores[name], scores['train'], n_groups)
        prediction_rows.append(table)
        auc, n_known = model_metrics.auc_at_horizon(
            scores[name], t, e, horizon)
        metric_rows.append({
            'model': model_name, 'set': name, 'n_patients': len(t),
            'n_events': int(e.sum()),
            'c_index': model_metrics.concordance_index(scores[name], t, e),
            'horizon_months': horizon, 'n_known_at_horizon': n_known,
            'auc_at_horizon': auc})
    return prediction_rows, metric_rows


def run_models(data_folder, output_folder, horizon=12, n_groups=4,
               model_names=None, overrides=None):
    """Fit and score the models, write the result tables, return metrics.

    model_names picks models from MODEL_REGISTRY, all by default.
    overrides is {model name: {setting: value}} for changed settings.
    """
    output_folder = Path(output_folder)
    output_folder.mkdir(parents=True, exist_ok=True)
    data = model_data.load_all(data_folder)
    ids = {name: model_data.load_ids(data_folder, name)
           for name in model_data.SETS}
    predictions, metrics, history, settings = [], [], [], {}
    for model_name in model_names or list(MODEL_REGISTRY):
        fit, defaults = MODEL_REGISTRY[model_name]
        params = dict(defaults, **(overrides or {}).get(model_name, {}))
        log.info('=== %s ===', model_name)
        started = time.time()
        predict, model_history, info = fit(data, params, horizon)
        info['fit_seconds'] = round(time.time() - started, 1)
        settings[model_name] = info
        prediction_rows, metric_rows = _score_sets(
            predict, data, ids, horizon, n_groups, model_name)
        predictions += prediction_rows
        metrics += metric_rows
        for row in model_history or []:
            history.append(dict(model=model_name, **row))
        log.info('%s: ' + ', '.join('%s C-index %.3f' % (m['set'],
                                                         m['c_index'])
                                    for m in metric_rows), model_name)
    pd.concat(predictions, ignore_index=True).to_csv(
        output_folder / 'predictions.csv', index=False)
    metrics = pd.DataFrame(metrics)
    metrics.to_csv(output_folder / 'metrics.csv', index=False)
    pd.DataFrame(history).to_csv(output_folder / 'history.csv', index=False)
    with open(output_folder / 'models.json', 'w') as handle:
        json.dump(settings, handle, indent=2, default=str)
    return metrics

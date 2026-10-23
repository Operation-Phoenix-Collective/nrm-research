"""
Role: The three classification models: logistic regression, SVM, forest.
Description: These models predict a yes/no outcome, death within a number of
months (the horizon), not a survival time. They are trained on the train
patients whose outcome at the horizon is known, so a patient censored before
the horizon is left out of the fit. The risk score of a patient is the
predicted probability of death by the horizon, or for the SVM the distance
to the decision boundary. Every patient can be scored, so the models can be
compared with the Cox models on the C-index of all patients.
Author: Bor
"""
import logging

import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.svm import SVC

from nrm_research import model_data

log = logging.getLogger(__name__)

DEFAULT_PARAMS = {
    'Logistic regression': {'C': 1.0, 'max_iter': 2000, 'seed': 42},
    'SVM': {'C': 1.0, 'kernel': 'rbf', 'gamma': 'scale', 'seed': 42},
    'Random forest': {'n_estimators': 500, 'min_samples_leaf': 5,
                      'max_features': 'sqrt', 'seed': 42},
}


def _known_train_patients(data, horizon):
    """Features and died-by-horizon labels of the train patients that are
    known at the horizon."""
    x, t, e = data['train']
    known, died = model_data.horizon_labels(t, e, horizon)
    log.info('Fitting on %s of %s train patients with a known outcome at '
             '%s months, %.1f%% died', known.sum(), len(t), horizon,
             100 * died[known].mean())
    return x[known], died[known].astype(int)


def fit_logistic_regression(data, params, horizon):
    """Logistic regression with an l2 penalty."""
    x, y = _known_train_patients(data, horizon)
    model = LogisticRegression(C=params['C'], max_iter=params['max_iter'],
                               random_state=params['seed']).fit(x, y)
    info = {'params': params, 'n_fit': int(len(y))}
    return (lambda z: model.predict_proba(z)[:, 1]), None, info


def fit_svm(data, params, horizon):
    """Support vector machine, scored by its decision function."""
    x, y = _known_train_patients(data, horizon)
    model = SVC(C=params['C'], kernel=params['kernel'],
                gamma=params['gamma'], random_state=params['seed']
                ).fit(x, y)
    info = {'params': params, 'n_fit': int(len(y))}
    return (lambda z: model.decision_function(z)), None, info


def fit_random_forest(data, params, horizon):
    """Random forest classifier."""
    x, y = _known_train_patients(data, horizon)
    model = RandomForestClassifier(
        n_estimators=params['n_estimators'],
        min_samples_leaf=params['min_samples_leaf'],
        max_features=params['max_features'], n_jobs=-1,
        random_state=params['seed']).fit(x, y)
    info = {'params': params, 'n_fit': int(len(y))}
    return (lambda z: model.predict_proba(z)[:, 1]), None, info

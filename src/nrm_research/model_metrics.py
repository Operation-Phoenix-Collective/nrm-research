"""
Role: Metrics to compare survival and classification models.
Description: The concordance index (Harrell) works on the risk score of any
model and on all patients, censored or not, so it is the common metric. The
AUC at a time horizon uses only the patients whose outcome at the horizon is
known, and compares the models on the same yes/no question.
Author: Bor
"""
import numpy as np
from sklearn.metrics import roc_auc_score

from nrm_research import model_data

CHUNK = 1000


def concordance_index(risk, times, events):
    """Harrell's C-index. A pair is usable when the earlier time is an
    event. Higher risk for the earlier failure counts 1, equal risk 0.5.
    Works in chunks of rows so large sets need little memory."""
    risk = np.asarray(risk, dtype=np.float64)
    times = np.asarray(times)
    events = np.asarray(events)
    concordant, usable_total = 0.0, 0
    for start in range(0, len(risk), CHUNK):
        rows = slice(start, start + CHUNK)
        usable = ((times[rows, None] < times[None, :])
                  & (events[rows, None] == 1))
        higher = risk[rows, None] > risk[None, :]
        equal = risk[rows, None] == risk[None, :]
        usable_total += usable.sum()
        concordant += (usable & higher).sum() + 0.5 * (usable & equal).sum()
    if usable_total == 0:
        return float('nan')
    return float(concordant / usable_total)


def auc_at_horizon(risk, times, events, horizon):
    """AUC for death within horizon months, on the patients with a known
    outcome. Returns (auc, number of patients used)."""
    known, died = model_data.horizon_labels(times, events, horizon)
    n_known = int(known.sum())
    if n_known == 0 or len(np.unique(died[known])) < 2:
        return float('nan'), n_known
    return float(roc_auc_score(died[known], np.asarray(risk)[known])), n_known

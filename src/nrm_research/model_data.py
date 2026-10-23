"""
Role: Read the prepared survival sets for the model scripts.
Description: Loads train.csv, validation.csv and test.csv written by
nrm_research.survival_data, with the study and patient ids of each row. Also
turns the survival outcome into the yes/no outcome "died within a number of
months" that the classification models need. A patient censored before that
time has an unknown outcome and is marked as not known.
Author: Bor
"""
from pathlib import Path

import numpy as np
import pandas as pd

SETS = ('train', 'validation', 'test')


def load_split(folder, name):
    """Return the features, times and events of one prepared set."""
    table = pd.read_csv(Path(folder) / (name + '.csv'))
    x = table.drop(columns=['time', 'event']).to_numpy(dtype=np.float32)
    return (x, table['time'].to_numpy(np.float32),
            table['event'].to_numpy(np.float32))


def load_all(folder):
    """Return {set name: (x, time, event)} for the three sets."""
    return {name: load_split(folder, name) for name in SETS}


def load_ids(folder, name):
    """Return the study and patient id of each row, empty if not written."""
    ids_file = Path(folder) / (name + '_ids.csv')
    if ids_file.exists():
        return pd.read_csv(ids_file)
    return pd.DataFrame(index=range(len(load_split(folder, name)[1])))


def horizon_labels(times, events, horizon):
    """Return (known, died) for death within horizon months.

    died is true for a death at or before the horizon. known is false for
    a patient censored before the horizon, whose outcome is not known.
    """
    died = (events == 1) & (times <= horizon)
    known = died | (times > horizon)
    return known, died

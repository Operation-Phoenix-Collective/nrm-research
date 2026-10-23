"""
Role: Plot the training curves and compare the models.
Description: Reads history.csv, metrics.csv and predictions.csv from
results/models, written by scripts/run_train_models.py, and saves four
figures to vis/figures: the training curves of the models trained in epochs
(loss and validation C-index), the C-index and the AUC at the horizon of
every model on the three sets, and the Kaplan-Meier curves of the test
patients by predicted risk group for every model. The best model is the one
with the highest validation C-index, so the test set plays no part in the
choice. Run it from anywhere with: python vis/plot_model_comparison.py
Author: Bor
"""
import logging
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

log = logging.getLogger(__name__)

VIS_FOLDER = Path(__file__).resolve().parent
ROOT = VIS_FOLDER.parent
RESULTS = ROOT / 'results' / 'models'
FIGURES = VIS_FOLDER / 'figures'

DPI = 150
SET_COLORS = {'train': '#4c72b0', 'validation': '#55a868', 'test': '#c44e52'}


def best_model(metrics):
    """Name of the model with the highest validation C-index."""
    validation = metrics[metrics['set'] == 'validation']
    return validation.loc[validation['c_index'].idxmax(), 'model']


def plot_training_curves(history, metrics, output_png):
    """Train loss, validation loss and validation C-index of each model
    trained in epochs. Losses use the left axis, C-index the right axis."""
    models = list(history['model'].unique())
    fig, axes = plt.subplots(1, len(models), figsize=(5.5 * len(models), 4.5),
                             squeeze=False)
    for ax, model in zip(axes[0], models):
        h = history[history['model'] == model]
        best_epoch = h.loc[h['val_c_index'].idxmax(), 'epoch']
        handles = ax.plot(h['epoch'], h['train_cox_loss'], color='#4c72b0',
                          label='Train loss (Cox)')
        handles += ax.plot(h['epoch'], h['val_loss'], color='#c44e52',
                           label='Validation loss (Cox)')
        ax.set_xlabel('Epoch')
        ax.set_ylabel('Loss')
        ax.grid(alpha=0.3)
        ax_c = ax.twinx()
        handles += ax_c.plot(h['epoch'], h['val_c_index'], color='#55a868',
                             label='Validation C-index')
        ax_c.set_ylabel('C-index')
        handles.append(ax.axvline(best_epoch, color='grey', linestyle='--',
                                  label='best epoch %s' % best_epoch))
        ax.set_title(model)
        ax.legend(handles=handles, loc='center right', fontsize=8)
    fig.tight_layout()
    fig.savefig(output_png, dpi=DPI)
    plt.close(fig)


def plot_metric_comparison(metrics, column, title, baseline, output_png):
    """Grouped bars of a metric, one group per model, one bar per set,
    models ordered by validation value. The best model is marked."""
    pivot = metrics.pivot(index='model', columns='set', values=column)
    order = pivot['validation'].sort_values(ascending=False).index
    pivot = pivot.loc[order, ['train', 'validation', 'test']]
    best = best_model(metrics)
    fig, ax = plt.subplots(figsize=(1.8 * len(pivot) + 3, 4.8))
    width = 0.26
    for i, name in enumerate(pivot.columns):
        bars = ax.bar(np.arange(len(pivot)) + (i - 1) * width, pivot[name],
                      width, label=name, color=SET_COLORS[name])
        for bar, value in zip(bars, pivot[name]):
            ax.text(bar.get_x() + bar.get_width() / 2, value + 0.004,
                    '%.2f' % value, ha='center', fontsize=7)
    ax.axhline(baseline, color='grey', linestyle='--', label='random (0.5)')
    ax.set_xticks(np.arange(len(pivot)))
    ax.set_xticklabels([n + (' *' if n == best else '') for n in pivot.index])
    ax.set_ylim(0.4, min(1.0, np.nanmax(pivot.to_numpy()) + 0.08))
    ax.set_ylabel(title)
    ax.set_title('%s (* best on validation C-index)' % title)
    ax.legend(loc='upper right', fontsize=8)
    fig.tight_layout()
    fig.savefig(output_png, dpi=DPI)
    plt.close(fig)


def kaplan_meier(times, events):
    """Return the step points of the Kaplan-Meier survival curve."""
    order = np.argsort(times, kind='stable')
    times, events = times[order], events[order]
    survival, curve_t, curve_s = 1.0, [0.0], [1.0]
    for t in np.unique(times[events == 1]):
        at_risk = (times >= t).sum()
        died = ((times == t) & (events == 1)).sum()
        survival *= 1 - died / at_risk
        curve_t.append(t)
        curve_s.append(survival)
    return np.array(curve_t), np.array(curve_s)


def plot_risk_groups(predictions, metrics, output_png):
    """Kaplan-Meier curves of the test set by predicted risk group, one
    panel per model. Curves that are far apart and in the order of the
    groups mean the model ranks patients well."""
    test = predictions[predictions['set'] == 'test']
    models = list(metrics['model'].unique())
    best = best_model(metrics)
    n_groups = int(predictions['risk_group'].max())
    n_cols = min(3, len(models))
    n_rows = int(np.ceil(len(models) / n_cols))
    fig, axes = plt.subplots(n_rows, n_cols, figsize=(5 * n_cols, 4 * n_rows),
                             sharex=True, sharey=True, squeeze=False)
    colors = plt.cm.viridis(np.linspace(0.9, 0.1, n_groups))
    for ax, model in zip(axes.ravel(), models):
        rows = test[test['model'] == model]
        for g in range(1, n_groups + 1):
            members = rows[rows['risk_group'] == g]
            if members.empty:
                continue
            curve_t, curve_s = kaplan_meier(
                members['time'].to_numpy(), members['event'].to_numpy())
            label = ('lowest risk' if g == 1 else
                     'highest risk' if g == n_groups else 'group %s' % g)
            ax.step(curve_t, curve_s, where='post', color=colors[g - 1],
                    label='%s (n=%s)' % (label, len(members)))
        test_c = metrics[(metrics['model'] == model)
                         & (metrics['set'] == 'test')]['c_index'].iloc[0]
        ax.set_title('%s%s, test C-index %.3f'
                     % (model, ' (best)' if model == best else '', test_c))
        ax.set_ylim(0, 1.02)
        ax.grid(alpha=0.3)
        ax.legend(fontsize=7)
    for ax in axes.ravel()[len(models):]:
        ax.axis('off')
    for ax in axes[-1]:
        ax.set_xlabel('Months after transplant')
    for ax in axes[:, 0]:
        ax.set_ylabel('Overall survival')
    fig.tight_layout()
    fig.savefig(output_png, dpi=DPI)
    plt.close(fig)


if __name__ == '__main__':
    logging.basicConfig(
        level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
    FIGURES.mkdir(parents=True, exist_ok=True)
    metrics = pd.read_csv(RESULTS / 'metrics.csv')
    history = pd.read_csv(RESULTS / 'history.csv')
    predictions = pd.read_csv(RESULTS / 'predictions.csv')
    plot_training_curves(history, metrics, FIGURES / 'training_curves.png')
    plot_metric_comparison(metrics, 'c_index', 'C-index', 0.5,
                           FIGURES / 'c_index_comparison.png')
    plot_metric_comparison(metrics, 'auc_at_horizon', 'AUC at horizon', 0.5,
                           FIGURES / 'auc_comparison.png')
    plot_risk_groups(predictions, metrics, FIGURES / 'risk_groups_km.png')
    print('Best model on validation C-index: %s' % best_model(metrics))
    print('Figures written to %s' % FIGURES)

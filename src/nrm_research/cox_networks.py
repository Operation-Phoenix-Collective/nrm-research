"""
Role: The three models trained with the Cox partial likelihood.
Description: One feed-forward network with a single linear output, the
log-risk, trained on the average negative Cox partial log-likelihood with an
l2 penalty (Eq. 4 of Katzman et al., 2018). The settings give three models:
DeepSurv (several SELU layers with dropout, Katzman et al.), the
Faraggi-Simon network (one hidden layer of three logistic nodes, Faraggi and
Simon, 1995) and the Cox proportional hazards model (no hidden layer, so the
log-risk is linear, fitted with an l2 penalty). Each step uses all train
patients so the risk sets are complete. The validation C-index picks the
best epoch. The learning rate decays as lr / (1 + epoch * decay) (Eq. 10).
Author: Bor
"""
import logging

import numpy as np
import torch
from torch import nn

from nrm_research import model_metrics

log = logging.getLogger(__name__)

COMMON = {
    'optimizer': 'adam',
    'momentum': 0.9,
    'lr_decay_rate': 1e-3,
    'seed': 42,
}

DEFAULT_PARAMS = {
    'DeepSurv': dict(COMMON, hidden_layers=[64, 64], activation='selu',
                     dropout=0.2, learning_rate=1e-3, l2_reg=1e-3,
                     epochs=300, patience=40),
    'Faraggi-Simon': dict(COMMON, hidden_layers=[3], activation='sigmoid',
                          dropout=0.0, learning_rate=1e-2, l2_reg=1e-3,
                          epochs=500, patience=50),
    'Cox PH': dict(COMMON, hidden_layers=[], activation='selu',
                   dropout=0.0, learning_rate=1e-2, l2_reg=1e-3,
                   epochs=500, patience=50),
}

ACTIVATIONS = {'selu': nn.SELU, 'relu': nn.ReLU, 'tanh': nn.Tanh,
               'sigmoid': nn.Sigmoid}


class CoxNet(nn.Module):
    """Fully connected layers with dropout and a single linear output."""

    def __init__(self, n_features, hidden_layers, dropout, activation):
        super().__init__()
        layers, size = [], n_features
        for width in hidden_layers:
            layers += [nn.Linear(size, width), ACTIVATIONS[activation](),
                       nn.Dropout(dropout)]
            size = width
        layers.append(nn.Linear(size, 1))
        self.net = nn.Sequential(*layers)
        if activation == 'selu':
            for module in self.net:
                if isinstance(module, nn.Linear):
                    nn.init.kaiming_normal_(module.weight,
                                            nonlinearity='linear')
                    nn.init.zeros_(module.bias)

    def forward(self, x):
        return self.net(x).squeeze(-1)


def _tie_index(times_desc):
    """For times sorted descending, the last position with the same time.
    The risk set of a patient is every position up to it."""
    last = np.empty(len(times_desc), dtype=np.int64)
    end = len(times_desc) - 1
    for i in range(len(times_desc) - 1, -1, -1):
        if i < len(times_desc) - 1 and times_desc[i] != times_desc[i + 1]:
            end = i
        last[i] = end
    return last


def cox_loss(log_risk, events, tie_last):
    """Average negative Cox partial log-likelihood (Eq. 4 without l2).
    The patients must be sorted by descending time."""
    log_denominator = torch.logcumsumexp(log_risk, dim=0)[tie_last]
    n_events = events.sum().clamp(min=1.0)
    return -((log_risk - log_denominator) * events).sum() / n_events


def _sorted_tensors(x, t, e):
    """Sort a set by descending time and return tensors and tie index."""
    order = np.argsort(-t, kind='stable')
    return (torch.from_numpy(x[order]), torch.from_numpy(e[order]),
            torch.from_numpy(_tie_index(t[order])))


def _score(model, x):
    model.eval()
    with torch.no_grad():
        return model(torch.from_numpy(x)).numpy()


def fit_cox_network(data, params, horizon=None):
    """Train a network on the train set and return (predict, history, info).

    data holds the sets as {name: (x, time, event)}. predict(x) gives the
    log-risk. horizon is not used, the argument is shared with the other
    models. history is a list of one dict per epoch.
    """
    p = params
    torch.manual_seed(p['seed'])
    np.random.seed(p['seed'])
    x_tr, t_tr, e_tr = data['train']
    x_va, t_va, e_va = data['validation']
    x_t, e_t, tie_t = _sorted_tensors(x_tr, t_tr, e_tr)
    x_v, e_v, tie_v = _sorted_tensors(x_va, t_va, e_va)

    model = CoxNet(x_tr.shape[1], p['hidden_layers'], p['dropout'],
                   p['activation'])
    if p['optimizer'] == 'adam':
        optimizer = torch.optim.Adam(
            model.parameters(), lr=p['learning_rate'])
    else:
        optimizer = torch.optim.SGD(
            model.parameters(), lr=p['learning_rate'],
            momentum=p['momentum'], nesterov=True)

    history, best = [], {'c_index': -1.0, 'epoch': 0, 'state': None}
    for epoch in range(1, p['epochs'] + 1):
        lr = p['learning_rate'] / (1 + epoch * p['lr_decay_rate'])
        for group in optimizer.param_groups:
            group['lr'] = lr
        model.train()
        optimizer.zero_grad()
        cox = cox_loss(model(x_t), e_t, tie_t)
        l2 = sum((w ** 2).sum() for n, w in model.named_parameters()
                 if n.endswith('weight'))
        loss = cox + p['l2_reg'] * l2
        loss.backward()
        optimizer.step()

        model.eval()
        with torch.no_grad():
            val_loss = float(cox_loss(model(x_v), e_v, tie_v))
        val_c = model_metrics.concordance_index(
            _score(model, x_va), t_va, e_va)
        history.append({'epoch': epoch, 'train_loss': float(loss),
                        'train_cox_loss': float(cox), 'val_loss': val_loss,
                        'val_c_index': val_c, 'lr': lr})
        if val_c > best['c_index']:
            best = {'c_index': val_c, 'epoch': epoch,
                    'state': {k: v.clone()
                              for k, v in model.state_dict().items()}}
        if epoch % 25 == 0:
            log.info('epoch %s loss %.4f val C-index %.4f', epoch,
                     float(loss), val_c)
        if epoch - best['epoch'] >= p['patience']:
            log.info('Stopped at epoch %s, best epoch %s', epoch,
                     best['epoch'])
            break
    model.load_state_dict(best['state'])
    info = {'best_epoch': best['epoch'], 'params': p}
    return (lambda x: _score(model, x)), history, info

# Standard Library
import copy
import math
import warnings
# Import from third library
import torch
from torch import nn
from up.utils.general.registry_factory import INITIALIZER_REGISTRY


__all__ = [
    'init_weights_constant',
    'init_weights_normal',
    'init_weights_xavier',
    'init_weights_msra',
    'init_bias_focal',
    'initialize',
    'initialize_from_cfg']


@INITIALIZER_REGISTRY.register("constant")
def init_weights_constant(module, val=0):
    for m in module.modules():
        if isinstance(m, nn.Conv2d) or isinstance(m, nn.Linear) or isinstance(
                m, nn.ConvTranspose2d):
            nn.init.constant_(m.weight.data, val)
            nn.init.constant_(m.bias.data, val)


@INITIALIZER_REGISTRY.register("normal")
def init_weights_normal(module, std=0.01):
    for m in module.modules():
        if isinstance(m, nn.Conv2d) or isinstance(m, nn.Linear) or isinstance(
                m, nn.ConvTranspose2d):
            nn.init.normal_(m.weight.data, std=std)
            if m.bias is not None:
                m.bias.data.zero_()


@INITIALIZER_REGISTRY.register("xavier")
def init_weights_xavier(module):
    for m in module.modules():
        if isinstance(m, nn.Conv2d) or isinstance(m, nn.Linear) or isinstance(
                m, nn.ConvTranspose2d):
            nn.init.xavier_normal_(m.weight.data)
            if m.bias is not None:
                m.bias.data.zero_()


@INITIALIZER_REGISTRY.register("msra")
def init_weights_msra(module):
    for m in module.modules():
        if isinstance(m, nn.Conv2d) or isinstance(m, nn.Linear) or isinstance(
                m, nn.ConvTranspose2d):
            nn.init.kaiming_normal_(m.weight.data, a=1)
            if m.bias is not None:
                m.bias.data.zero_()


@INITIALIZER_REGISTRY.register("focal")
def init_bias_focal(module, cls_loss_type, init_prior, num_classes):
    if cls_loss_type == 'sigmoid':
        for m in module.modules():
            if isinstance(m, nn.Conv2d) or isinstance(m, nn.Linear):
                # to keep the torch random state
                m.bias.data.normal_(-math.log(1.0 / init_prior - 1.0), init_prior)
                torch.nn.init.constant_(m.bias, -math.log(1.0 / init_prior - 1.0))

    elif cls_loss_type == 'softmax':
        for m in module.modules():
            if isinstance(m, nn.Conv2d) or isinstance(m, nn.Linear):
                m.bias.data.normal_(0, 0.01)
                for i in range(0, m.bias.data.shape[0], num_classes):
                    fg = m.bias.data[i + 1:i + 1 + num_classes - 1]
                    mu = torch.exp(fg).sum()
                    m.bias.data[i] = math.log(mu * (1.0 - init_prior) / init_prior)
    else:
        raise NotImplementedError(f'{cls_loss_type} is not supported')


def initialize(model, method, **kwargs):
    # initialize BN
    for m in model.modules():
        if isinstance(m, nn.BatchNorm2d):
            if m.weight is not None:
                m.weight.data.fill_(1)
            if m.bias is not None:
                m.bias.data.zero_()
    init_instance = INITIALIZER_REGISTRY.get(method)
    init_instance(model, **kwargs)


def initialize_from_cfg(model, cfg):
    if cfg is None:
        initialize(model, 'normal', std=0.01)
        return

    cfg = copy.deepcopy(cfg)
    method = cfg.pop('method')
    initialize(model, method, **cfg)


def _no_grad_trunc_normal_(tensor, mean, std, a, b):

    def norm_cdf(x):
        return (1. + math.erf(x / math.sqrt(2.))) / 2.

    if (mean < a - 2 * std) or (mean > b + 2 * std):
        warnings.warn("mean is more than 2 std from [a, b] in nn.init.trunc_normal_. "
                      "The distribution of values may be incorrect.",
                      stacklevel=2)

    with torch.no_grad():

        v = norm_cdf((a - mean) / std)
        u = norm_cdf((b - mean) / std)

        # [2v-1, 2u-1].
        tensor.uniform_(2 * v - 1, 2 * u - 1)

        # standard normal
        tensor.erfinv_()

        # Transform to proper mean, std
        tensor.mul_(std * math.sqrt(2.))
        tensor.add_(mean)

        # Clamp to ensure it's in the proper range
        tensor.clamp_(min=a, max=b)
        return tensor


def trunc_normal_(tensor, mean=0., std=1., a=-2., b=2.):
    return _no_grad_trunc_normal_(tensor, mean, std, a, b)

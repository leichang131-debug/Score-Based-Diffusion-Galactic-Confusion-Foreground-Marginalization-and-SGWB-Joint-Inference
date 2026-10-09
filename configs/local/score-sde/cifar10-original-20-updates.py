"""Original DDPM++ continuous VP-SDE: exactly 20 updates on one CPU device."""
from configs.vp.cifar10_ddpmpp_continuous import get_config as original_config


def get_config():
    config = original_config()
    config.training.batch_size = 1
    config.eval.batch_size = 1
    config.training.n_jitted_steps = 1
    # Upstream loop includes both endpoints: range(0, n_iters + 1).
    config.training.n_iters = 19
    config.training.log_freq = 1
    config.training.eval_freq = 5
    config.training.snapshot_freq = 19
    config.training.snapshot_freq_for_preemption = 19
    # Sampling is a separate follow-up; do not change the SDE or sampler.
    config.training.snapshot_sampling = False
    return config

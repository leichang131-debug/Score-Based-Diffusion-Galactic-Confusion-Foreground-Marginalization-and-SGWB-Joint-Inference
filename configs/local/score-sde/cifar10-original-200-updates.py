"""Continue original DDPM++ VP-SDE to 200 total updates on one CPU device."""
from configs.vp.cifar10_ddpmpp_continuous import get_config as original_config


def get_config():
    config = original_config()
    config.training.batch_size = 1
    config.eval.batch_size = 1
    config.training.n_jitted_steps = 1
    config.training.n_iters = 199  # inclusive loop; final state.step is 200
    config.training.log_freq = 1
    config.training.eval_freq = 20
    config.training.snapshot_freq = 50
    config.training.snapshot_freq_for_preemption = 50
    config.training.snapshot_sampling = False
    return config

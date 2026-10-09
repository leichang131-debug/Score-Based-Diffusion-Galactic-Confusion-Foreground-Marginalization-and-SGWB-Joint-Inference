"""Resume original-network state at update 20 and execute exactly two updates."""
from configs.vp.cifar10_ddpmpp_continuous import get_config as original_config


def get_config():
    config = original_config()
    config.training.batch_size = 1
    config.eval.batch_size = 1
    config.training.n_jitted_steps = 1
    config.training.n_iters = 21  # inclusive loop labels 20 and 21 -> state.step 22
    config.training.log_freq = 1
    config.training.eval_freq = 1
    config.training.snapshot_freq = 1
    config.training.snapshot_freq_for_preemption = 1
    config.training.snapshot_sampling = False
    return config

"""Disable TF-GAN legacy Estimator imports; preserve its real evaluation APIs.

Score-SDE uses tensorflow_gan.eval, not TF-GAN Estimator training. TensorFlow
2.21 removed Estimator. This mirrors the upstream guide's optional-import
workaround without editing upstream source or installed third-party files.
"""
def prepare():
    import sys
    import types
    name = 'tensorflow_gan.python.estimator'
    if name not in sys.modules:
        module = types.ModuleType(name)
        module.__all__ = []
        module.__doc__ = 'Legacy TF-GAN Estimator is unavailable in this environment.'
        sys.modules[name] = module

if __name__ == '__main__':
    import runpy
    import sys
    from pathlib import Path
    root = Path(__file__).resolve().parents[2]
    upstream = root / 'external/score-sde-reproduction'
    sys.path.insert(0, str(upstream))
    prepare()
    runpy.run_path(str(upstream / 'run_train.py'), run_name='__main__')

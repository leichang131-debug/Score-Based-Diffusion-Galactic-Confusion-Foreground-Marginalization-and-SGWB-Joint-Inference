# Reconstruct stochastic GW background in TDC II datasets

This repository contains my personal pipeline for SGWB identification in the Taiji Data Challenge 2 dataset.
I have packaged it for ease of use and communication.
You can install the package directly  from the repository:
```shell
pip install .
```

By default, the installation does not include any MCMC sampler. 
I work with `Eryn` at present. You can obtain it from <https://github.com/mikekatz04/Eryn>.
Alternatively, install this package with the `[sampler]` option to include this sampler:
```shell
pip install '.[sampler]'
```
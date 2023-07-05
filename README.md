# SpeakerVerSim [![Python application](https://github.com/wq2012/SpeakerVerSim/actions/workflows/python-app.yml/badge.svg)](https://github.com/wq2012/SpeakerVerSim/actions/workflows/python-app.yml)


## Overview
SpeakerVerSim is an easily-extensible Python-based simulation framework for different version control strategies of speaker recognition systems under different network configurations.

These simulations are used in the paper [Version Control of Speaker Recognition Systems](https://arxiv.org/abs/2007.12069).

## How to use

### Run one simulation

You can easily start a simulation by running:

```
python run_simulator.py
```

This simulation will use the configurations in the `example_config.yml` file.

To use a different configuration file, you can use the `-c` or `--config` flag. For example:

```
python run_simulator.py --config my_config.yml
```

You can also override the strategy to be simulated from the config file using the `-s` or `--strategy` flag. For example:

```
python run_simulator.py -c my_config.yml -s SSO-sync
```

### Reproduce experiments

You can easily reproduce the experiments in our [paper](https://arxiv.org/abs/2007.12069) by running:

```
python run_exp.py
```

After running this script, simulation results will be stored in the `result_stats` directory.

Then you can visualize the metrics by running:

```
python visualize_results.py
```

The visualization graphics will be stored in the `figures` directory.

## List of implemented strategies

| Script                          | Strategy    | Description |
| ------------------------------- | ----------- | ----------- |
| `server_single_simple.py`       | SSO         | Basic server-side single version online updating strategy.
| `server_single_sync.py`         | SSO-sync    | Server-side single version online updating strategy with frontend-worker version sync.
| `server_single_hash.py`         | SSO-hash    | Server-side single version online updating strategy with user-ID hashing.
| `server_single_multiprofile.py` | SSO-mul     | Server-side single version online updating strategy with multi-profile database.
| `server_single_sync.py`         | SD          | Server-side double version updating strategy.

## Citation

```
@article{wang2020version,
  title={Version control of speaker recognition systems},
  author={Wang, Quan and Moreno, Ignacio Lopez},
  journal={arXiv preprint arXiv:2007.12069},
  year={2020}
}
```

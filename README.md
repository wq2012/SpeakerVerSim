# SpeakerVerSim [![Python application](https://github.com/wq2012/SpeakerVerSim/actions/workflows/python-app.yml/badge.svg)](https://github.com/wq2012/SpeakerVerSim/actions/workflows/python-app.yml) [![PyPI Version](https://img.shields.io/pypi/v/SpeakerVerSim.svg)](https://pypi.python.org/pypi/SpeakerVerSim) [![Python Versions](https://img.shields.io/pypi/pyversions/SpeakerVerSim.svg)](https://pypi.org/project/SpeakerVerSim) [![Downloads](https://pepy.tech/badge/SpeakerVerSim)](https://pepy.tech/project/SpeakerVerSim)


## Overview
SpeakerVerSim is an easily-extensible Python-based simulation framework for different version control strategies of speaker recognition systems under different network configurations.

These simulations are used in the paper [Version Control of Speaker Recognition Systems](https://arxiv.org/abs/2007.12069).

## How to use

### Install

The `SpeakerVerSim` library can be installed with:

```
pip install SpeakerVerSim
```

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

### Call the API

The highest level API is the `SpeakerVerSim.simulate` function.
It takes either the path to the config file or an object of the configurations as its input, and outputs the simulation stats.

Example usage:

```
import SpeakerVerSim

stats = SpeakerVerSim.simulate("example_config.yml")
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

## Design

The design of this library is summarized as below:

* This library is built on top of [SimPy](https://simpy.readthedocs.io), a process-based discrete-event simulation (DES) framework based on standard Python.
* All configurations of the simulation are represented in a single YAML file. `example_config.yml` has explanations for all the configuration fields.
* Each machine in the network inherits from the `Actor` class, including the client, the frontend server, the cloud worker, and the database.
* All clients inherit from the `BaseClient` class; all frontend servers inherit from the `BaseFrontend` class; all cloud workers inherit from the `BaseWorker` class; and all databases inherit from the `BaseDatabase` class.
* The communication between two machines happens like this: the sender creates a `Message` object, and adds it to the receiver's message pool, which is a `simpy.Store` object.
* During the simulation, metrics are logged in an object of the `GlobalStats` class.
* The entire network system is represented by the `NetworkSystem` class or its subclass.

Each version control strategy is implemented by creating a set of client, frontend server, cloud workers, database, and defining how they interact with each other.

## Citation

```
@article{wang2020version,
  title={Version control of speaker recognition systems},
  author={Wang, Quan and Moreno, Ignacio Lopez},
  journal={arXiv preprint arXiv:2007.12069},
  year={2020}
}
```

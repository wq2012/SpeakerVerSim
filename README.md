# SpeakerVersionSim [![Python application](https://github.com/wq2012/SpeakerVersionSim/actions/workflows/python-app.yml/badge.svg)](https://github.com/wq2012/SpeakerVersionSim/actions/workflows/python-app.yml)

Simulation experiments of version control strategies for speaker recognition systems.

These simulations are used in this [paper](https://arxiv.org/abs/2007.12069).

Cite the paper as:

```
@article{wang2020version,
  title={Version control of speaker recognition systems},
  author={Wang, Quan and Moreno, Ignacio Lopez},
  journal={arXiv preprint arXiv:2007.12069},
  year={2020}
}
```

Scripts:

* `server_single_simple.py`: Basic server-side single version online updating strategy.
* `server_single_sync.py`: Server-side single version online updating strategy with frontend-worker version sync.
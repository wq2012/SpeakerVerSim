# SpeakerVerSim [![Python application](https://github.com/wq2012/SpeakerVerSim/actions/workflows/python-app.yml/badge.svg)](https://github.com/wq2012/SpeakerVerSim/actions/workflows/python-app.yml)

SpeakerVerSim is an easily-extensible Python-based simulation framework for different version control strategies of speaker recognition systems under different network configurations.

These simulations are used in the paper [Version Control of Speaker Recognition Systems](https://arxiv.org/abs/2007.12069).

## List of implemented strategies

| Script                          | Strategy    | Description |
| ------------------------------- | ----------- | ----------- |
| `server_single_simple.py`       | SSO         | Basic server-side single version online updating strategy.
| `server_single_sync.py`         | SSO-sync    | Server-side single version online updating strategy with frontend-worker version sync.
| `server_single_hash.py`         | SSO-hash    | Server-side single version online updating strategy with user-ID hashing.
| `server_single_multiprofile.py` | SSO-mul     | Server-side single version online updating strategy with multi-profile database.
| `server_single_sync.py`         | SDO         | Server-side double version updating strategy.

## Citation

```
@article{wang2020version,
  title={Version control of speaker recognition systems},
  author={Wang, Quan and Moreno, Ignacio Lopez},
  journal={arXiv preprint arXiv:2007.12069},
  year={2020}
}
```

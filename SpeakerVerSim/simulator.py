"""The simulator API to simplify calling different strategies."""
from SpeakerVerSim.common import GlobalStats
from SpeakerVerSim import server_single_simple
from SpeakerVerSim import server_single_sync
from SpeakerVerSim import server_single_hash
from SpeakerVerSim import server_single_multiprofile
from SpeakerVerSim import server_double

from typing import Any


def simulate(config: dict[str, Any]) -> GlobalStats:
    """Main simulation function of this module."""
    strategy = config["strategy"]
    if strategy == "SSO":
        return server_single_simple.simulate(config)
    elif strategy == "SSO-sync":
        return server_single_sync.simulate(config)
    elif strategy == "SSO-hash":
        return server_single_hash.simulate(config)
    elif strategy == "SSO-mul":
        return server_single_multiprofile.simulate(config)
    elif strategy == "SD":
        return server_double.simulate(config)
    else:
        raise ValueError(f"Strategy not supported: {strategy}")

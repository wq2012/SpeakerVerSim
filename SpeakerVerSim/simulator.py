"""The simulator API to simplify calling different strategies."""
from SpeakerVerSim.common import GlobalStats
from SpeakerVerSim import server_single_simple
from SpeakerVerSim import server_single_sync
from SpeakerVerSim import server_single_hash
from SpeakerVerSim import server_single_multiprofile
from SpeakerVerSim import server_double

from typing import Union
import yaml
import munch


def simulate(config: Union[str, munch.Munch]) -> GlobalStats:
    """Main simulation function of this module.

    Args:
        config: either the path to a YAML file, or a Munch

    Returns:
        stats from the simulation

    Raises:
        ValueError: if the strategy in the config is unsupported
    """

    if isinstance(config, str):
        config_file = config
        with open(config_file, "r") as f:
            config = munch.Munch.fromDict(yaml.safe_load(f))

    strategy = config.strategy
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

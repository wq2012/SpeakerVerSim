"""The simulator API to simplify calling different strategies."""
from SpeakerVerSim.common import Strategy, GlobalStats
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
    match strategy:
        case Strategy.SSO:
            return server_single_simple.simulate(config)
        case Strategy.SSO_SYNC:
            return server_single_sync.simulate(config)
        case Strategy.SSO_HASH:
            return server_single_hash.simulate(config)
        case Strategy.SSO_MUL:
            return server_single_multiprofile.simulate(config)
        case Strategy.SD:
            return server_double.simulate(config)
        case _:
            raise ValueError(f"Strategy not supported: {strategy}")

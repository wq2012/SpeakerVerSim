"""Basic server-side double version online strategy."""
import simpy
# import random
import yaml
# from typing import Generator
import sys

from common import (BaseFrontend,
                    BaseWorker, NetworkSystem, MultiVersionDatabase,
                    GlobalStats, print_results)
import server_single_simple


class BackgroundReenrollFrontend(BaseFrontend):
    """A frontend for double version strategy.

    Re-enrollment happens as non-blocking background process.
    """

    def setup(self) -> None:
        pass


class DoubleVersionWorker(BaseWorker):
    """A backend worker serving two versions of models."""

    def setup(self) -> None:
        pass


def main(config_file: str = "example_config.yml") -> GlobalStats:

    with open(config_file, "r") as f:
        config = yaml.safe_load(f)

    env = simpy.Environment()
    stats = GlobalStats(config=config)
    client = server_single_simple.SimpleClient(env, "client", config, stats)
    frontend = BackgroundReenrollFrontend(env, "frontend", config, stats)
    workers = [
        DoubleVersionWorker(env, f"worker-{i}", config, stats)
        for i in range(config["num_cloud_workers"])]
    database = MultiVersionDatabase(env, "database", config, stats)
    database.create({0: [1, 2]})
    netsys = NetworkSystem(
        env,
        client,
        frontend,
        workers,
        database)

    env.run(until=config["time_to_run"])
    print_results(netsys)
    return netsys.client.stats


if __name__ == "__main__":
    if len(sys.argv) == 1:
        config_file = "example_config.yml"
    elif len(sys.argv) == 2:
        config_file = len(sys.argv[1])
    else:
        raise ValueError("Expecting at most one config file.")

    main(config_file)

"""Server-side single version online strategy with user hash.

The frontend server implements a load balancing algorithm based
on the hash value of the user’s ID, such that requests for each
user are always dispatched to the same cloud computing server.
"""
import simpy
import sys
import yaml

from common import (Message, BaseWorker, NetworkSystem, SingleVersionDatabase,
                    GlobalStats, print_results)
import server_single_simple


class UserHashFrontend(server_single_simple.SimpleFrontend):
    """A frontend that selects worker based on user hash."""

    def select_worker(self, msg: Message) -> BaseWorker:
        """Decide which worker to send the request to."""
        # Request from same user always goes to the same worker.
        user_hash = msg.user_id % len(self.workers)
        return self.workers[user_hash]


def main(config_file: str = "example_config.yml") -> GlobalStats:

    with open(config_file, "r") as f:
        config = yaml.safe_load(f)

    env = simpy.Environment()
    stats = GlobalStats(config=config)
    client = server_single_simple.SimpleClient(env, "client", config, stats)
    frontend = UserHashFrontend(env, "frontend", config, stats)
    workers = [
        server_single_simple.SimpleCloudWorker(
            env, f"worker-{i}", config, stats)
        for i in range(config["num_cloud_workers"])]
    database = SingleVersionDatabase(env, "database", config, stats)
    database.create({0: 1})
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

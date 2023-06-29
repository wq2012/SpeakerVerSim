"""Server-side single version online strategy with multi-profile database.

We store multiple versions of profiles for each user in the database.
Once the re-enrollment for a user has completed, we will store both
the old version and the new version of this user's profile.
"""


import server_single_simple

import simpy
import sys
import yaml
from typing import Generator

from common import (Message, NetworkSystem, MultiVersionDatabase,
                    GlobalStats, print_results)


class MultiProfileFrontend(server_single_simple.SimpleFrontend):
    """A frontend that uses a MultiVersionDatabase."""

    def send_worker_request(self, msg: Message) -> Generator:
        """Fetch profiles from database and send request to worker."""
        # Part 1: Fetch database.
        if len(msg.profile_versions) == 0:
            print(f"{self.name} fetch database at time {self.env.now}")
            yield from self.database.fetch_profile(msg)
            if len(msg.profile_versions) == 0:
                raise ValueError("fetch_profile failed.")
        else:
            raise ValueError("Frontend profile_versions must be empty.")

        # Part 2: Re-enroll if necessary.
        worker = self.select_worker(msg)
        if worker.version not in msg.profile_versions:
            if worker.version > max(msg.profile_versions):
                self.stats.forward_bounce_count += 1
            else:
                self.stats.backward_bounce_count += 1
            # Mark the request as an enrollment request.
            msg.is_enroll = True

        # Part 3: Send request to worker.
        yield from self.send_to_worker(worker, msg)

    def resend_worker_request(self, msg: Message) -> Generator:
        """After re-enroll, send worker request again."""
        # Part 1: Update database with re-enrolled profile.
        print(f"{self.name} update database at time {self.env.now}")
        yield from self.database.update_profile(msg)

        # Part 2: Re-send request to worker.
        worker = self.select_worker(msg)
        yield from self.send_to_worker(worker, msg)


def main(config_file: str = "example_config.yml") -> GlobalStats:

    with open(config_file, "r") as f:
        config = yaml.safe_load(f)

    env = simpy.Environment()
    stats = GlobalStats(config=config)
    client = server_single_simple.SimpleClient(env, "client", config, stats)
    frontend = MultiProfileFrontend(env, "frontend", config, stats)
    workers = [
        server_single_simple.SimpleCloudWorker(
            env, f"worker-{i}", config, stats)
        for i in range(config["num_cloud_workers"])]
    database = MultiVersionDatabase(env, "database", config, stats)
    database.create({0: [1]})
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

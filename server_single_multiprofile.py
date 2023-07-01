"""Server-side single version online strategy with multi-profile
database (SSO-mul).

We store multiple versions of profiles for each user in the database.
Once the re-enrollment for a user has completed, we will store both
the old version and the new version of this user's profile.
"""
import simpy
import sys
import yaml
from typing import Generator, Any

from common import (Message, NetworkSystem, MultiVersionDatabase,
                    GlobalStats)
import server_single_simple


class MultiProfileFrontend(server_single_simple.ForegroundReenrollFrontend):
    """A frontend that uses a MultiVersionDatabase."""

    def send_worker_request(self, msg: Message) -> Generator:
        """Fetch profiles from database and send request to worker."""
        # Part 1: Fetch database.
        if len(msg.profile_versions) == 0:
            self.log("fetch database")
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
        self.log("update database")
        yield from self.database.update_profile(msg)

        # Part 2: Re-send request to worker.
        worker = self.select_worker(msg)
        yield from self.send_to_worker(worker, msg)


def simulate(config: dict[str, Any]) -> GlobalStats:
    """Run simulation."""
    env = simpy.Environment()
    stats = GlobalStats(config=config)
    client = server_single_simple.SimpleClient(env, "client", config, stats)
    frontend = MultiProfileFrontend(env, "frontend", config, stats)
    workers = [
        server_single_simple.SingleVersionWorker(
            env, f"worker-{i}", config, stats)
        for i in range(config["num_cloud_workers"])]
    database = MultiVersionDatabase(env, "database", config, stats)
    database.create(init_versions=[1])
    netsys = NetworkSystem(
        env,
        client,
        frontend,
        workers,
        database)

    env.run(until=config["time_to_run"])
    return netsys.aggregate_metrics()


if __name__ == "__main__":
    if len(sys.argv) == 1:
        # Default config file.
        config_file = "example_config.yml"
    elif len(sys.argv) == 2:
        config_file = len(sys.argv[1])
    else:
        raise ValueError("Expecting at most one config file.")

    with open(config_file, "r") as f:
        config = yaml.safe_load(f)

    simulate(config)

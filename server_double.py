"""Basic server-side double version online strategy."""
import simpy
import yaml
from typing import Generator
import sys
import copy

from common import (Message, BaseFrontend,
                    BaseWorker, NetworkSystem, MultiVersionDatabase,
                    GlobalStats, print_results)
import server_single_simple


class BackgroundReenrollFrontend(BaseFrontend):
    """A frontend for double version strategy.

    Re-enrollment happens as non-blocking background process.
    """

    def setup(self) -> None:
        self.env.process(self.handle_messages())

    def handle_messages(self) -> Generator:
        while True:
            msg = yield self.message_pool.get()
            if msg.is_request:
                self.env.process(self.send_worker_request(msg))
            elif msg.is_enroll:
                # Enrollment response.
                # Enrollment happens in the background.
                # Just need to udpate database.
                # No need to resend request to worker.
                self.env.process(self.update_database(msg))
            else:
                # Send response back to client.
                self.env.process(self.send_client_response(msg))

    def send_worker_request(self, msg: Message) -> Generator:
        """Fetch profile from database and send request to worker."""
        # Part 1: Fetch database.
        if len(msg.profile_versions) == 0:
            print(f"{self.name} fetch database at time {self.env.now}")
            yield from self.database.fetch_profile(msg)
            if len(msg.profile_versions) == 0:
                raise ValueError("fetch_profile failed.")
        else:
            raise ValueError("Frontend profile_versions must be empty.")

        # Part 2: Send request to worker.
        worker = self.select_worker(msg)
        yield from self.send_to_worker(worker, msg)

        # Part 3: Decide whether need to trigger background re-enrollment.
        if max(worker.version) not in msg.profile_version:
            enroll_msg = copy.deepcopy(msg)
            enroll_msg.is_enroll = True
            self.env.process(self.send_to_worker(worker, enroll_msg))

    def update_database(self, msg: Message) -> Generator:
        """After background re-enroll, update database."""
        # Part 1: Update database with re-enrolled profile.
        print(f"{self.name} update database at time {self.env.now}")
        yield from self.database.update_profile(msg)

    def send_client_response(self, msg: Message) -> Generator:
        """Send response back to client."""
        yield from self.send_to_client(msg)


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

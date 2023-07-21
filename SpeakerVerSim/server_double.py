"""Basic server-side double version strategy (SD)."""
import simpy
import random
from typing import Generator
import copy
import munch

from SpeakerVerSim.common import (
    Message, BaseFrontend, BaseWorker, NetworkSystem,
    MultiVersionDatabase, GlobalStats)
from SpeakerVerSim import server_single_simple


class BackgroundReenrollFrontend(BaseFrontend):
    """A frontend for double version strategy.

    Re-enrollment happens as non-blocking background process.
    """
    # A helper mapping for summing flops.
    # Only needed for stats.
    id_to_msg: dict[int, Message]

    def setup(self) -> None:
        self.id_to_msg = dict()
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
                msg.is_enroll = False
                msg.is_request = True
                self.id_to_msg[msg.msg_id].total_flops += msg.total_flops
                self.env.process(self.update_database(msg))
            else:
                # Send response back to client.
                self.env.process(self.send_client_response(msg))

    def send_worker_request(self, msg: Message) -> Generator:
        """Fetch profile from database and send request to worker."""
        # Part 1: Fetch database.
        if len(msg.profile_versions) == 0:
            self.log("fetch database")
            yield from self.database.fetch_profile(msg)
            if len(msg.profile_versions) == 0:
                raise ValueError("fetch_profile failed.")
        else:
            raise ValueError("Frontend profile_versions must be empty.")

        # Part 2: Send request to worker.
        worker = self.select_worker(msg)
        yield from self.send_to_worker(worker, msg)

        # Part 3: Decide whether need to trigger background re-enrollment.
        if max(worker.versions) not in msg.profile_versions:
            enroll_msg = copy.deepcopy(msg)
            enroll_msg.is_enroll = True
            enroll_msg.total_flops = 0
            self.env.process(self.send_to_worker(worker, enroll_msg))
            # Note: Since enrollment is in a different background process,
            # its flops are not included in the original msg.
            # Thus we need to manually add them later.
            self.id_to_msg[msg.msg_id] = msg

    def update_database(self, msg: Message) -> Generator:
        """After background re-enroll, update database."""
        self.log("update database")
        yield from self.database.update_profile(msg)

    def send_client_response(self, msg: Message) -> Generator:
        """Send response back to client."""
        yield from self.send_to_client(msg)


class DoubleVersionWorker(BaseWorker):
    """A backend worker serving two versions of models."""
    versions: list[int]

    def setup(self) -> None:
        self.env.process(self.update_version())
        self.env.process(self.handle_requests())

    def handle_requests(self) -> Generator:
        """Handle all requests from frontend."""
        while True:
            msg = yield self.message_pool.get()
            if msg.is_request:
                self.env.process(self.handle_one_request(msg))
            else:
                raise ValueError("Not expecting responses to worker.")

    def handle_one_request(self, msg: Message) -> Generator:
        """Handle a single request and convert it to a reponse."""
        self.log("handle request")
        msg.worker_receive_time = self.env.now
        msg.worker_name = self.name

        # If this is enrollment request, update profile_version.
        if msg.is_enroll:
            # Find the version that needs to be enrolled
            for version in self.versions:
                if version not in msg.profile_versions:
                    msg.profile_version = version
                    break
            if msg.profile_version is None:
                raise ValueError("No version to enroll.")

        # Run inference.
        yield from self.run_inference(msg)
        self.log("complete request")

        # Send response back to frontend.
        msg.is_request = False
        yield from self.send_to_frontend(msg)

    def update_version(self) -> Generator:
        """Replace the oldest version (v1) by a new version (v3)."""
        update_time = random.expovariate(
            1.0 / self.config.worker_update_mean_time)
        yield self.env.timeout(update_time)
        # Delete oldest version.
        del self.versions[0]
        # Add newest version.
        self.versions.append(self.versions[-1] + 1)
        self.log("update model version")


class DoubleVersionNetworkSystem(NetworkSystem):
    """Class for the entire network system.

    But each worker has two model versions.
    """

    def set_worker_model_version(self):
        for worker in self.workers:
            worker.set_model_versions([1, 2])


def simulate(config: munch.Munch) -> GlobalStats:
    """Run simulation."""
    if config.strategy != "SD":
        raise ValueError("Incorrect strategy being used.")
    env = simpy.Environment()
    stats = GlobalStats(config=config)
    client = server_single_simple.SimpleClient(env, "client", config, stats)
    frontend = BackgroundReenrollFrontend(env, "frontend", config, stats)
    workers = [
        DoubleVersionWorker(env, f"worker-{i}", config, stats)
        for i in range(config["num_cloud_workers"])]
    database = MultiVersionDatabase(env, "database", config, stats)
    database.create(init_versions=[1, 2])
    netsys = DoubleVersionNetworkSystem(
        env,
        client,
        frontend,
        workers,
        database)
    return netsys.simulate()

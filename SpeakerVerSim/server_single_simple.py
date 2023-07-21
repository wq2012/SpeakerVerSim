"""Basic server-side single version online strategy (SSO)."""
import simpy
import random
from typing import Generator
import sys
import munch

from SpeakerVerSim.common import (
    Message, BaseClient, BaseFrontend, BaseWorker,
    NetworkSystem, SingleVersionDatabase, GlobalStats)


class SimpleClient(BaseClient):
    """A client that does not store user profiles."""

    def setup(self) -> None:
        self.env.process(self.send_frontend_requests())
        self.env.process(self.receive_frontend_responses())

    def create_init_request(self) -> Message:
        """Create the initial request with random msg_id."""
        return Message(
            msg_id=random.randint(0, sys.maxsize),
            user_id=self.get_user_id(),
            is_request=True,
            is_enroll=False,
        )

    def get_user_id(self) -> int:
        """Get the user_id of the initial request.

        Total number of users is self.config.num_users.

        Different users send requests with different frequency, depending
        on self.config.user_distribution.
        """
        user_ids = list(range(self.config.num_users))
        if self.config.user_distribution == "uniform":
            user_weights = [1 for _ in user_ids]
        elif self.config.user_distribution == "linear":
            user_weights = [x + 1 for x in user_ids]
        elif self.config.user_distribution == "exponential":
            user_weights = [0.8**x for x in user_ids]
        else:
            raise ValueError(
                "Unsupported user_distribution: {}".format(
                    self.config.user_distribution))
        return random.choices(user_ids, weights=user_weights, k=1)[0]

    def send_frontend_requests(self) -> Generator:
        """Keep sending requests to frontend with intervals."""
        while True:
            self.env.process(self.send_one_frontend_request())
            yield self.env.timeout(self.config.client_request_interval)

    def send_one_frontend_request(self) -> Generator:
        """Send one request to frontend."""
        msg = self.create_init_request()
        yield from self.send_to_frontend(msg)

    def receive_frontend_responses(self) -> Generator:
        """Receive the final responses."""
        while True:
            msg = yield self.message_pool.get()
            self.log("receive response")
            msg.client_return_time = self.env.now
            self.stats.final_messages.append(msg)


class ForegroundReenrollFrontend(BaseFrontend):
    """A basic frontend that runs re-enrollment on-the-fly.

    Re-enrollment is a foreground process that is blocking.
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
                # We need to send it again to a random worker.
                # First, mark it as a non-enrollment request.
                msg.is_enroll = False
                msg.is_request = True
                self.env.process(self.resend_worker_request(msg))
            else:
                # Send response back to client.
                self.env.process(self.send_client_response(msg))

    def send_worker_request(self, msg: Message) -> Generator:
        """Fetch profile from database and send request to worker."""
        # Part 1: Fetch database.
        if msg.profile_version is None:
            self.log("fetch database")
            yield from self.database.fetch_profile(msg)
            if msg.profile_version is None:
                raise ValueError("fetch_profile failed.")
        else:
            raise ValueError("Frontend profile_version must be None.")

        # Part 2: Re-enroll if necessary.
        worker = self.select_worker(msg)
        if worker.version != msg.profile_version:
            if worker.version < msg.profile_version:
                self.stats.backward_bounce_count += 1
            else:
                self.stats.forward_bounce_count += 1
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

    def send_client_response(self, msg: Message) -> Generator:
        """Send response back to client."""
        yield from self.send_to_client(msg)


class SingleVersionWorker(BaseWorker):
    """A basic cloud worker serving a single version of model."""

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
            msg.profile_version = self.version

        # Run inference.
        yield from self.run_inference(msg)
        self.log("complete request")

        # Send response back to frontend.
        msg.is_request = False
        yield from self.send_to_frontend(msg)

    def update_version(self) -> Generator:
        """Update the model to a new version."""
        update_time = random.expovariate(
            1.0 / self.config.worker_update_mean_time)
        yield self.env.timeout(update_time)
        self.version += 1
        self.log("update model version")


def simulate(config: munch.Munch) -> GlobalStats:
    """Run simulation."""
    if config.strategy != "SSO":
        raise ValueError("Incorrect strategy being used.")
    env = simpy.Environment()
    stats = GlobalStats(config=config)
    client = SimpleClient(env, "client", config, stats)
    frontend = ForegroundReenrollFrontend(env, "frontend", config, stats)
    workers = [
        SingleVersionWorker(env, f"worker-{i}", config, stats)
        for i in range(config.num_cloud_workers)]
    database = SingleVersionDatabase(env, "database", config, stats)
    database.create(init_version=1)
    netsys = NetworkSystem(
        env,
        client,
        frontend,
        workers,
        database)
    return netsys.simulate()

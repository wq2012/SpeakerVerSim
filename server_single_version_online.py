"""Server-side single version online strategy.
"""

import simpy
import random
from typing import Generator

import configs
from common import (Message, BaseClient, BaseFrontend,
                    BaseWorker, NetworkSystem, SingleVersionDatabase,
                    GlobalStats, print_results)


class SimpleClient(BaseClient):
    """A client that does not store user profiles."""

    def setup(self) -> None:
        self.env.process(self.send_frontend_requests())
        self.env.process(self.receive_frontend_responses())

    def send_frontend_requests(self) -> Generator:
        """Keep sending requests to frontend with intervals."""
        while True:
            self.env.process(self.send_one_frontend_request())
            yield self.env.timeout(configs.CLIENT_REQUEST_INTERVAL)

    def send_one_frontend_request(self) -> Generator:
        """Send one request to frontend."""
        print(f"{self.name} send request at time {self.env.now}")
        msg = Message(
            user_id=0,
            is_request=True,
            is_enroll=False,
        )
        yield from self.send_to_frontend(msg)

    def receive_frontend_responses(self) -> Generator:
        """Receive the final responses."""
        while True:
            msg = yield self.message_pool.get()
            print(f"{self.name} receive response at time {self.env.now}")
            msg.client_return_time = self.env.now
            self.stats.final_messages.append(msg)


class Frontend(BaseFrontend):

    def setup(self) -> None:
        self.env.process(self.handle_messages())

    def handle_messages(self) -> Generator:
        while True:
            msg = yield self.message_pool.get()
            if msg.is_request:
                # Send request to a random worker.
                worker = random.choice(self.workers)
                self.env.process(self.send_worker_request(worker, msg))
            elif msg.is_enroll:
                # Enrollment response.
                msg.is_enroll = False
                worker = random.choice(self.workers)
                self.env.process(self.resend_worker_request(worker, msg))
            else:
                # Send response back to client.
                self.env.process(self.send_client_response(msg))

    def send_worker_request(self, worker: BaseWorker, msg: Message
                            ) -> Generator:
        """Fetch profile from database and send request to worker."""
        # Part 1: Fetch database.
        if msg.profile_version is None:
            print(f"{self.name} fetch database at time {self.env.now}")
            msg.fetch_database_time = self.env.now
            yield from self.database.fetch_profile(msg)

        # Part 2: Re-enroll if necessary.
        if worker.version != msg.profile_version:
            if worker.version < msg.profile_version:
                self.stats.backward_bounce_count += 1
            else:
                self.stats.forward_bounce_count += 1
            msg.is_enroll = True

        # Part 3: Send request to worker.
        yield from self.send_to_worker(worker, msg)

    def resend_worker_request(self, worker: BaseWorker, msg: Message
                              ) -> Generator:
        """After re-enroll, send worker request again."""
        # Part 1: Update database.
        print(f"{self.name} update database at time {self.env.now}")
        msg.udpate_database_time = self.env.now
        yield from self.database.update_profile(msg)

        # Part 2: Re-send request to worker.
        yield from self.send_to_worker(worker, msg)

    def send_client_response(self, msg: Message) -> Generator:
        """Send response back to client."""
        yield from self.send_to_client(msg)


class CloudWorker(BaseWorker):

    def setup(self) -> None:
        self.env.process(self.update_version())
        self.env.process(self.handle_requests())

    def handle_requests(self) -> Generator:
        """Handle all requests from frontend."""
        while True:
            msg = yield self.message_pool.get()
            if msg.is_request:
                self.env.process(self.handle_one_request(msg))

    def handle_one_request(self, msg: Message) -> Generator:
        """Handle a single request and convert it to a reponse."""
        print(f"{self.name} handle request at time {self.env.now}")
        msg.worker_receive_time = self.env.now
        msg.worker_name = self.name

        # If enrollment request, update profile_version.
        if msg.is_enroll:
            msg.profile_version = self.version

        # Run inference.
        self.run_inference(msg)
        print(f"{self.name} complete request at time {self.env.now}")

        # Send response back to frontend.
        msg.is_request = False
        yield from self.send_to_frontend(msg)

    def update_version(self) -> Generator:
        """Update the model to a new version."""
        update_time = random.expovariate(1.0 / configs.WORKER_UPDATE_MEAN_TIME)
        yield self.env.timeout(update_time)
        self.version = 2
        print(f"{self.name} update model version")


def main():
    env = simpy.Environment()
    stats = GlobalStats()
    client = SimpleClient(env, "client", stats)
    frontend = Frontend(env, "frontend", stats)
    workers = [
        CloudWorker(env, f"worker-{i}", stats)
        for i in range(configs.NUM_CLOUD_WORKERS)]
    database = SingleVersionDatabase(env, "database", stats)
    database.create({0: 1})
    netsys = NetworkSystem(
        env,
        client,
        frontend,
        workers,
        database)

    env.run(until=2)
    print_results(netsys)


if __name__ == "__main__":
    main()

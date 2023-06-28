"""Server-side single version online strategy.
"""

import simpy
import random
from typing import Generator

from common import (Message, BaseClient, BaseFrontend,
                    BaseWorker, NetworkSystem, Database,
                    GlobalStats, print_results)

# How may cloud workers do we have in total.
NUM_CLOUD_WORKERS = 10

# Latency between client and frontend server.
CLIENT_FRONTEND_LATENCY = 0.1

# Latency between frontend server and cloud worker.
FRONTEND_WORKER_LATENCY = 0.002

# Latency for database IO.
DATABASE_IO_LATENCY = 0.005

# Latency to run speech inference engine.
WORKER_INFERENCE_LATENCY = 0.5

# Flops cost to run one inference.
FLOPS_PER_INFERENCE = 1000000

# How often do we send requests.
CLIENT_REQUEST_INTERVAL = 10

# Mean time of a model version update for each worker.
WORKER_UPDATE_MEAN_TIME = 3600


class Client(BaseClient):

    def run(self) -> Generator:
        self.env.process(self.receive_frontend_responses())
        while True:
            self.env.process(self.send_one_frontend_request())
            yield self.env.timeout(CLIENT_REQUEST_INTERVAL)

    def send_one_frontend_request(self) -> Generator:
        """Send one request to frontend."""
        print(f"{self.name} send request at time {self.env.now}")
        msg = Message(
            user_id=0,
            is_request=True,
            is_enroll=False,
            client_send_time=self.env.now,
        )
        # Simulate network latency.
        yield self.env.timeout(CLIENT_FRONTEND_LATENCY)
        self.frontend.message_pool.put(msg)

    def receive_frontend_responses(self) -> Generator:
        """Receive the final responses."""
        while True:
            msg = yield self.message_pool.get()
            print(f"{self.name} receive response at time {self.env.now}")
            msg.client_return_time = self.env.now
            self.stats.final_messages.append(msg)


class Frontend(BaseFrontend):

    def run(self) -> Generator:
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
            yield self.env.timeout(DATABASE_IO_LATENCY)
            msg.profile_version = self.database.fetch_profile(msg.user_id)

        # Part 2: Re-enroll if necessary.
        if worker.version != msg.profile_version:
            if worker.version < msg.profile_version:
                self.stats.backward_bounce_count += 1
            else:
                self.stats.forward_bounce_count += 1
            msg.is_enroll = True

        # Part 3: Send request to worker.
        print(f"{self.name} send request at time {self.env.now}")
        msg.frontend_send_worker_time = self.env.now
        # Simulate network latency.
        yield self.env.timeout(FRONTEND_WORKER_LATENCY)
        worker.message_pool.put(msg)

    def resend_worker_request(self, worker: BaseWorker, msg: Message
                              ) -> Generator:
        """After re-enroll, send worker request again."""
        # Part 1: Update database.
        print(f"{self.name} update database at time {self.env.now}")
        msg.database_udpate_time = self.env.now
        yield self.env.timeout(DATABASE_IO_LATENCY)
        self.database.update_profile(msg.user_id, msg.profile_version)

        # Part 2: Re-send request to worker.
        print(f"{self.name} send request at time {self.env.now}")
        msg.frontend_resend_worker_time = self.env.now
        # Simulate network latency.
        yield self.env.timeout(FRONTEND_WORKER_LATENCY)
        worker.message_pool.put(msg)

    def send_client_response(self, msg: Message) -> Generator:
        """Send response back to client."""
        print(f"{self.name} receive response at time {self.env.now}")
        msg.frontend_return_time = self.env.now
        # Simulate network latency.
        yield self.env.timeout(CLIENT_FRONTEND_LATENCY)
        self.client.message_pool.put(msg)


class CloudWorker(BaseWorker):

    def run(self) -> Generator:
        self.env.process(self.update_version())
        while True:
            msg = yield self.message_pool.get()
            if msg.is_request:
                self.env.process(self.handle_request(msg))

    def handle_request(self, msg: Message) -> Generator:
        """Handle a request and convert it to reponse."""
        print(f"{self.name} handle request at time {self.env.now}")
        msg.worker_receive_time = self.env.now
        msg.worker_name = self.name

        # If enrollment request, update profile_version.
        if msg.is_enroll:
            msg.profile_version = self.version

        # Simulate computation latency.
        yield self.env.timeout(WORKER_INFERENCE_LATENCY)
        msg.total_flops += FLOPS_PER_INFERENCE
        print(f"{self.name} complete request at time {self.env.now}")

        # Send response back to frontend.
        msg.worker_return_time = self.env.now
        msg.is_request = False
        # Simulate network latency.
        yield self.env.timeout(FRONTEND_WORKER_LATENCY)
        self.frontend.message_pool.put(msg)

    def update_version(self) -> Generator:
        """Update the model to a new version."""
        update_time = random.expovariate(1.0 / WORKER_UPDATE_MEAN_TIME)
        yield self.env.timeout(update_time)
        self.version = 2
        print(f"{self.name} update model version")


def main():
    env = simpy.Environment()
    stats = GlobalStats()
    client = Client(env, "client", stats)
    frontend = Frontend(env, "frontend", stats)
    workers = [
        CloudWorker(env, f"worker-{i}", stats)
        for i in range(NUM_CLOUD_WORKERS)]
    database = Database({0: 1})
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

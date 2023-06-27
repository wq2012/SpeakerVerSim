import simpy

import random
from typing import Generator

from common import (Message, BaseClient, BaseFrontend,
                    BaseCloudWorker, NetworkSystem)

NUM_CLOUD_WORKERS = 10
CLIENT_FRONTEND_LATENCY = 0.1
FRONTEND_WORKER_LATENCY = 0.002
WORKERL_LATENCY = 0.5


class Client(BaseClient):
    # How often do we send requests.
    REQUEST_INTERVAL = 10

    def run(self) -> Generator:
        while True:
            self.env.process(self.send_frontend_request())
            yield self.env.timeout(self.REQUEST_INTERVAL)

    def send_frontend_request(self):
        # Simulate network latency.
        print(f"Client put request at time {self.env.now}")
        msg = Message(
            user_id=0,
            is_request=True,
            is_enroll=False,
            client_send_time=self.env.now,
        )
        yield self.env.timeout(CLIENT_FRONTEND_LATENCY)
        self.frontend.request_pool.put(msg)


class Frontend(BaseFrontend):

    def run(self) -> Generator:
        while True:
            msg = yield self.request_pool.get()
            worker = random.choice(self.workers)
            self.env.process(self.send_worker_request(worker, msg))

    def send_worker_request(self, worker: BaseCloudWorker, msg: Message):
        # Simulate network latency.
        print(f"Frontend put request at time {self.env.now}")
        msg.frontend_send_time = self.env.now
        yield self.env.timeout(FRONTEND_WORKER_LATENCY)
        worker.request_pool.put(msg)


class CloudWorker(BaseCloudWorker):

    def run(self) -> Generator:
        while True:
            msg = yield self.request_pool.get()
            self.env.process(self.handle_request(msg))

    def handle_request(self, msg: Message):
        # Simulate computation latency.
        print(f"Worker handle request at time {self.env.now}")
        msg.worker_send_time = self.env.now
        yield self.env.timeout(WORKERL_LATENCY)
        print(f"Worker complete request at time {self.env.now}")
        msg.worker_return_time = self.env.now


def main():
    env = simpy.Environment()
    client = Client(env, "client")
    frontend = Frontend(env, "frontend")
    workers = [
        CloudWorker(env, f"worker-{i}") for i in range(NUM_CLOUD_WORKERS)]
    NetworkSystem(
        env,
        client,
        frontend,
        workers)

    env.run(until=100)


if __name__ == "__main__":
    main()

import simpy

from typing import Sequence
import random

from common import Message, Actor, NetworkSystem

NUM_CLOUD_WORKERS = 10
CLIENT_FRONTEND_LATENCY = 0.1
FRONTEND_WORKER_LATENCY = 0.002
WORKERL_LATENCY = 0.5


class Client(Actor):
    # How often do we send requests.
    REQUEST_INTERVAL = 10

    def set_frontend(self, frontend: Actor):
        self.frontend = frontend

    def run(self):
        while True:
            self.env.process(self.send_frontend_request())
            yield self.env.timeout(self.REQUEST_INTERVAL)

    def send_frontend_request(self):
        # Simulate network latency.
        print(f"Client put request at time {self.env.now}")
        yield self.env.timeout(CLIENT_FRONTEND_LATENCY)
        self.frontend.request_pool.put("req")


class Frontend(Actor):

    def set_client(self, client: Actor):
        self.client = client

    def set_workers(self, workers: Sequence[Actor]):
        self.workers = workers

    def run(self):
        while True:
            item = yield self.request_pool.get()
            worker = random.choice(self.workers)
            self.env.process(self.send_worker_request(worker, item))

    def send_worker_request(self, worker: Actor, item: str):
        # Simulate network latency.
        print(f"Frontend put request at time {self.env.now}")
        yield self.env.timeout(FRONTEND_WORKER_LATENCY)
        worker.request_pool.put(item)


class CloudWorker(Actor):

    def set_frontend(self, frontend: Actor):
        self.frontend = frontend

    def run(self):
        while True:
            item = yield self.request_pool.get()
            self.env.process(self.handle_request(item))

    def handle_request(self, item: str):
        # Simulate computation latency.
        print(f"Worker handle request at time {self.env.now}")
        yield self.env.timeout(WORKERL_LATENCY)
        print(f"Worker complete request at time {self.env.now}")


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

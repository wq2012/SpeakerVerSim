import simpy
from abc import ABC
from typing import Sequence
import random

NUM_CLOUD_WORKERS = 10
CLIENT_FRONTEND_LATENCY = 0.1
FRONTEND_WORKER_LATENCY = 0.002
WORKERL_LATENCY = 0.5


class Actor(ABC):
    def __init__(self, env: simpy.Environment):
        self.env = env


class Client(Actor):
    REQUEST_INTERVAL = 10

    def __init__(self, env: simpy.Environment):
        self.env = env

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
        self.frontend.task_pool.put("req")
            

class Frontend(Actor):
    def __init__(self, env: simpy.Environment):
        self.env = env
        self.task_pool = simpy.Store(env)

    def set_client(self, client: Actor):
        self.client = client

    def set_workers(self, workers: Sequence[Actor]):
        self.workers = workers

    def run(self):
        while True:
            item = yield self.task_pool.get()
            worker = random.choice(self.workers)
            self.env.process(self.send_worker_request(worker, item))

    def send_worker_request(self, worker: Actor, item: str):
        # Simulate network latency.
        print(f"Frontend put request at time {self.env.now}")
        yield self.env.timeout(FRONTEND_WORKER_LATENCY)
        worker.task_pool.put(item)


class CloudWorker(Actor):
    def __init__(self, env: simpy.Environment, name: str):
        self.env = env
        self.name = name
        self.task_pool = simpy.Store(env)

    def set_frontend(self, frontend: Actor):
        self.frontend = frontend

    def run(self):
        while True:
            item = yield self.task_pool.get()
            self.env.process(self.handle_request(item))

    def handle_request(self, item: str):
        # Simulate computation latency.
        print(f"Worker handle request at time {self.env.now}")
        yield self.env.timeout(WORKERL_LATENCY)
        print(f"Worker complete request at time {self.env.now}")


class NetworkSystem:
    def __init__(self, env: simpy.Environment):
        self.env = env

        # Create actors.
        self.client = Client(env)
        self.frontend = Frontend(env)
        self.workers = [CloudWorker(env, str(i)) for i in range(NUM_CLOUD_WORKERS)]

        # Build connections.
        self.client.set_frontend(self.frontend)
        self.frontend.set_client(self.client)
        self.frontend.set_workers(self.workers)
        for worker in self.workers:
            worker.set_frontend(self.frontend)

        # Add processes.
        env.process(self.client.run())
        env.process(self.frontend.run())
        for worker in self.workers:
            env.process(worker.run())


def main():
    env = simpy.Environment()
    NetworkSystem(env)
    env.run(until=100)


if __name__ == "__main__":
    main()

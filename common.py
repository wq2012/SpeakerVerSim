import simpy
from typing import Sequence, Optional
from dataclasses import dataclass
from abc import ABC


@dataclass
class Message:
    """A message being communicated between actors."""
    # Unique ID of the user.
    user_id: int = 0

    # Whether this is a request or response.
    is_request: bool = True

    # Timing information.
    client_send_time: Optional[float] = None
    frontend_send_time: Optional[float] = None
    worker_send_time: Optional[float] = None
    worker_return_time: Optional[float] = None
    frontend_return_time: Optional[float] = None
    client_return_time: Optional[float] = None


class Actor(ABC):
    """An actor machine which can be either client or server."""
    def __init__(self, env: simpy.Environment, name: str):
        self.env = env
        self.name = name

        # A pool of requests to be processed.
        self.request_pool = simpy.Store(env)
        

class NetworkSystem:
    def __init__(
            self,
            env: simpy.Environment,
            client: Actor,
            frontend: Actor,
            workers: Sequence[Actor]):
        self.env = env

        # Set actors.
        self.client = client
        self.frontend = frontend
        self.workers = workers

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

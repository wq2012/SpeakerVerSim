
"""Common components."""
import simpy
from typing import Sequence, Optional
import dataclasses
import abc


@dataclasses.dataclass
class Message:
    """A message being communicated between actors."""

    # Unique ID of the user.
    user_id: int = 0

    # Whether this is a request or response.
    is_request: bool = True

    # Whether this is an enrollment or runtime request/response.
    is_enroll: bool = False

    # Total flops used to process this request.
    total_flops: float = 0

    # Which worker handled this request.
    worker_name: str = ""

    # Timing information.
    client_send_time: Optional[float] = None
    frontend_send_time: Optional[float] = None
    worker_send_time: Optional[float] = None
    worker_return_time: Optional[float] = None
    frontend_return_time: Optional[float] = None
    client_return_time: Optional[float] = None


class Actor(abc.ABC):
    """An actor machine which can be either client or server."""

    def __init__(self, env: simpy.Environment, name: str):
        self.env = env
        self.name = name

        # A pool of messages to be processed.
        self.message_pool = simpy.Store(env)

        # Final messages for logging.
        self.final_messages = []

    @abc.abstractmethod
    def run() -> None:
        pass


class BaseClient(Actor):
    """Base class for a client."""

    def set_frontend(self, frontend: Actor) -> None:
        self.frontend = frontend


class BaseFrontend(Actor):
    """Base class for a frontend server."""

    def set_client(self, client: Actor) -> None:
        self.client = client

    def set_workers(self, workers: Sequence[Actor]) -> None:
        self.workers = workers


class BaseWorker(Actor):
    """Base class for a cloud worker."""

    def set_frontend(self, frontend: Actor) -> None:
        self.frontend = frontend


class NetworkSystem:
    """Class for the entire network system."""

    def __init__(
            self,
            env: simpy.Environment,
            client: BaseClient,
            frontend: BaseFrontend,
            workers: Sequence[BaseWorker]):
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

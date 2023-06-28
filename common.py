
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

    # Unique ID of the version of the profile.
    profile_version: Optional[int] = None

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
    fetch_database_time: Optional[float] = None
    frontend_send_worker_time: Optional[float] = None
    frontend_resend_worker_time: Optional[float] = None
    database_udpate_time: Optional[float] = None
    worker_receive_time: Optional[float] = None
    worker_return_time: Optional[float] = None
    frontend_return_time: Optional[float] = None
    client_return_time: Optional[float] = None


@dataclasses.dataclass
class GlobalStats:
    """Global statistics."""

    backward_bounce_count: int = 0

    forward_bounce_count: int = 0

    # Final messages for logging.
    final_messages: list[Message] = dataclasses.field(default_factory=list)


class Actor(abc.ABC):
    """An actor machine which can be either client or server."""

    def __init__(self, env: simpy.Environment, name: str, stats: GlobalStats):
        self.env = env
        self.name = name
        self.stats = stats

        # A pool of messages to be processed.
        self.message_pool = simpy.Store(env)

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

    def set_database(self, database: object) -> None:
        self.database = database


class BaseWorker(Actor):
    """Base class for a cloud worker."""

    def set_frontend(self, frontend: Actor) -> None:
        self.frontend = frontend

    def set_model_version(self, version: int) -> None:
        self.version = version


class Database:

    def __init__(self, data: dict[int, int] = {}):
        # A mapping from user_id to version_id.
        self.data = data

    def fetch_profile(self, user_id: int) -> int:
        if user_id not in self.data:
            raise ValueError(f"Missing profile for user {user_id}")

        return self.data[user_id]

    def update_profile(self, user_id: int, profile_version: int) -> None:
        self.data[user_id] = profile_version


class NetworkSystem:
    """Class for the entire network system."""

    def __init__(
            self,
            env: simpy.Environment,
            client: BaseClient,
            frontend: BaseFrontend,
            workers: Sequence[BaseWorker],
            database: object):
        self.env = env

        # Set actors.
        self.client = client
        self.frontend = frontend
        self.workers = workers

        # Set database.
        self.database = database

        # Set worker model version.
        for worker in self.workers:
            worker.set_model_version(1)

        # Build connections.
        self.client.set_frontend(self.frontend)
        self.frontend.set_client(self.client)
        self.frontend.set_workers(self.workers)
        self.frontend.set_database(self.database)
        for worker in self.workers:
            worker.set_frontend(self.frontend)

        # Add processes.
        env.process(self.client.run())
        env.process(self.frontend.run())
        for worker in self.workers:
            env.process(worker.run())


def print_results(netsys: NetworkSystem) -> None:
    print("========================================")
    print("Global stats:")
    print(netsys.client.stats)

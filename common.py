
"""Common components."""
import copy
import simpy
from typing import Sequence, Optional, Generator
import dataclasses
import abc

import configs


@dataclasses.dataclass
class Message:
    """A message being communicated between actors."""

    # Unique ID of the user.
    user_id: int = 0

    # Unique ID of the version of the profile.
    # Will be updated after fetching profile from database.
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
    frontend_send_worker_enroll_time: Optional[float] = None
    udpate_database_time: Optional[float] = None
    frontend_send_worker_time: Optional[float] = None
    worker_receive_time: Optional[float] = None
    worker_return_time: Optional[float] = None
    frontend_return_time: Optional[float] = None
    client_return_time: Optional[float] = None


@dataclasses.dataclass
class GlobalStats:
    """Global statistics."""

    # Count of version downgrades.
    backward_bounce_count: int = 0

    # Count of version upgrades.
    forward_bounce_count: int = 0

    # Average latency for fulfilling one request.
    average_e2e_latency: float = 0

    # Average flops for fulling one request.
    average_total_flops: float = 0

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
    def setup() -> None:
        """Function to add processes."""
        pass


class BaseClient(Actor):
    """Base class for a client."""
    frontend: Actor

    def set_frontend(self, frontend: Actor) -> None:
        self.frontend = frontend

    def send_to_frontend(self, msg: Message) -> Generator:
        """Send a message to frontend. Simulates latency."""
        print(f"{self.name} send request at time {self.env.now}")
        msg.client_send_time = self.env.now
        # Simulate network latency.
        yield self.env.timeout(configs.CLIENT_FRONTEND_LATENCY)
        self.frontend.message_pool.put(msg)


class BaseFrontend(Actor):
    """Base class for a frontend server."""
    client: Actor

    def set_client(self, client: Actor) -> None:
        self.client = client

    def set_workers(self, workers: Sequence[Actor]) -> None:
        self.workers = workers

    def set_database(self, database: object) -> None:
        self.database = database

    def send_to_worker(self, worker: Actor, msg: Message) -> Generator:
        """Send a message to worker. Simulates latency."""
        print(f"{self.name} send request at time {self.env.now}")
        if msg.is_enroll:
            msg.frontend_send_worker_enroll_time = self.env.now
        else:
            msg.frontend_send_worker_time = self.env.now
        # Simulate network latency.
        yield self.env.timeout(configs.FRONTEND_WORKER_LATENCY)
        worker.message_pool.put(msg)

    def send_to_client(self, msg: Message) -> Generator:
        """Send a message to client. Simulates latency."""
        print(f"{self.name} send response at time {self.env.now}")
        msg.frontend_return_time = self.env.now
        # Simulate network latency.
        yield self.env.timeout(configs.CLIENT_FRONTEND_LATENCY)
        self.client.message_pool.put(msg)


class BaseWorker(Actor):
    """Base class for a cloud worker."""
    frontend: Actor

    def set_frontend(self, frontend: Actor) -> None:
        self.frontend = frontend

    def set_model_version(self, version: int) -> None:
        self.version = version

    def send_to_frontend(self, msg: Message) -> Generator:
        """Send a message to frontend. Simulates latency."""
        print(f"{self.name} send response at time {self.env.now}")
        msg.worker_return_time = self.env.now
        # Simulate network latency.
        yield self.env.timeout(configs.FRONTEND_WORKER_LATENCY)
        self.frontend.message_pool.put(msg)

    def run_inference(self, msg: Message) -> Generator:
        """Run inference of speech engine. Simulates latency."""
        print(f"{self.name} run inference at time {self.env.now}")
        # Simulate computation latency.
        yield self.env.timeout(configs.WORKER_INFERENCE_LATENCY)
        msg.total_flops += configs.FLOPS_PER_INFERENCE


class SingleVersionDatabase(Actor):
    """Database storing a single version of profile for each user."""

    def setup(self):
        """No processes."""
        pass

    def create(self, data: dict[int, int] = {}):
        """Create a mapping from user_id to version_id."""
        self.data = data

    def fetch_profile(self, msg: Message) -> Generator:
        """Fetch profile from database. Simulates latency."""
        msg.fetch_database_time = self.env.now
        yield self.env.timeout(configs.DATABASE_IO_LATENCY)
        if msg.user_id not in self.data:
            raise ValueError(f"Missing profile for user {msg.user_id}")

        msg.profile_version = self.data[msg.user_id]

    def update_profile(self, msg: Message) -> Generator:
        """Update profile in database. Simulates latency."""
        msg.udpate_database_time = self.env.now
        yield self.env.timeout(configs.DATABASE_IO_LATENCY)
        self.data[msg.user_id] = msg.profile_version


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
        self.client.setup()
        self.frontend.setup()
        for worker in self.workers:
            worker.setup()


def print_results(netsys: NetworkSystem) -> None:
    # Aggregate metrics.
    stats = netsys.client.stats
    num_messages = len(stats.final_messages)
    for msg in stats.final_messages:
        stats.average_e2e_latency += (
            msg.client_return_time - msg.client_send_time)
        stats.average_total_flops += msg.total_flops
    stats.average_e2e_latency /= num_messages
    stats.average_total_flops /= num_messages

    print("========================================")
    print("Global stats:")
    stats_no_message = copy.deepcopy(stats)
    stats_no_message.final_messages = None
    print(stats_no_message)


"""Common components."""
import copy
import simpy
from typing import Optional, Generator, Any
import dataclasses
import abc


@dataclasses.dataclass
class Message:
    """A message being communicated between actors."""

    # Unique ID of the user.
    user_id: int = 0

    # Unique ID of the version of the profile.
    # Will be updated after fetching profile from database.
    profile_version: Optional[int] = None

    # Similar to profile_version, but contains multiple versions.
    profile_versions: list[int] = dataclasses.field(default_factory=list)

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

    # Configuration of the experiment.
    config: dict[str, Any] = dataclasses.field(default_factory=dict)

    # Workload of the workers, as a mapping from name to
    # (time, flops) pairs.
    workload: dict[str, list[tuple[float, float]]
                   ] = dataclasses.field(default_factory=dict)

    # Final messages for logging.
    final_messages: list[Message] = dataclasses.field(default_factory=list)


class Actor(abc.ABC):
    """An actor machine which can be either client or server."""

    def __init__(
            self,
            env: simpy.Environment,
            name: str,
            config: dict[str, Any],
            stats: GlobalStats):
        self.env = env
        self.name = name
        self.config = config
        self.stats = stats

        # A pool of messages to be processed.
        self.message_pool = simpy.Store(env)

    @abc.abstractmethod
    def setup() -> None:
        """Function to add processes."""
        pass


class BaseDatabase(Actor):
    """Base class for a database."""
    data: dict[int, Any]

    @abc.abstractmethod
    def fetch_profile(self, msg: Message) -> Generator:
        pass

    @abc.abstractmethod
    def update_profile(self, msg: Message) -> Generator:
        pass


class BaseClient(Actor):
    """Base class for a client."""
    frontend: "BaseFrontend"

    def set_frontend(self, frontend: "BaseFrontend") -> None:
        self.frontend = frontend

    def send_to_frontend(self, msg: Message) -> Generator:
        """Send a message to frontend. Simulates latency."""
        print(f"{self.name} send request at time {self.env.now}")
        msg.client_send_time = self.env.now
        # Simulate network latency.
        yield self.env.timeout(self.config["client_frontend_latency"])
        self.frontend.message_pool.put(msg)


class BaseFrontend(Actor):
    """Base class for a frontend server."""
    client: BaseClient

    def set_client(self, client: BaseClient) -> None:
        self.client = client

    def set_workers(self, workers: list["BaseWorker"]) -> None:
        self.workers = workers

    def set_database(self, database: BaseDatabase) -> None:
        self.database = database

    def send_to_worker(self, worker: Actor, msg: Message) -> Generator:
        """Send a message to worker. Simulates latency."""
        print(f"{self.name} send request at time {self.env.now}")
        if msg.is_enroll:
            msg.frontend_send_worker_enroll_time = self.env.now
        else:
            msg.frontend_send_worker_time = self.env.now
        # Simulate network latency.
        yield self.env.timeout(self.config["frontend_worker_latency"])
        worker.message_pool.put(msg)

    def send_to_client(self, msg: Message) -> Generator:
        """Send a message to client. Simulates latency."""
        print(f"{self.name} send response at time {self.env.now}")
        msg.frontend_return_time = self.env.now
        # Simulate network latency.
        yield self.env.timeout(self.config["client_frontend_latency"])
        self.client.message_pool.put(msg)


class BaseWorker(Actor):
    """Base class for a cloud worker."""
    frontend: BaseFrontend
    # TODO: add multi-version worker
    version: int

    def set_frontend(self, frontend: BaseFrontend) -> None:
        self.frontend = frontend

    def set_model_version(self, version: int) -> None:
        self.version = version

    def send_to_frontend(self, msg: Message) -> Generator:
        """Send a message to frontend. Simulates latency."""
        print(f"{self.name} send response at time {self.env.now}")
        msg.worker_return_time = self.env.now
        # Simulate network latency.
        yield self.env.timeout(self.config["frontend_worker_latency"])
        self.frontend.message_pool.put(msg)

    def run_inference(self, msg: Message) -> Generator:
        """Run inference of speech engine. Simulates latency."""
        print(f"{self.name} run inference at time {self.env.now}")
        # Simulate computation latency.
        yield self.env.timeout(self.config["worker_inference_latency"])
        msg.total_flops += self.config["flops_per_inference"]

        # Add to stats.
        if self.name not in self.stats.workload:
            self.stats.workload[self.name] = []
        self.stats.workload[self.name].append(
            (self.env.now, self.config["flops_per_inference"]))


class SingleVersionDatabase(BaseDatabase):
    """Database storing a single version of profile for each user."""

    def setup(self):
        """No processes."""
        pass

    def create(self, data: dict[int, int] = {}):
        """Create a mapping from user_id to version_id(s)."""
        self.data = data

    def fetch_profile(self, msg: Message) -> Generator:
        """Fetch profile from database. Simulates latency."""
        msg.fetch_database_time = self.env.now
        yield self.env.timeout(self.config["database_io_latency"])
        if msg.user_id not in self.data:
            raise ValueError(f"Missing profile for user {msg.user_id}")

        msg.profile_version = self.data[msg.user_id]

    def update_profile(self, msg: Message) -> Generator:
        """Update profile in database. Simulates latency."""
        msg.udpate_database_time = self.env.now
        yield self.env.timeout(self.config["database_io_latency"])
        self.data[msg.user_id] = msg.profile_version


class MultiVersionDatabase(BaseDatabase):
    """Database storing multiple versions of profile for each user."""

    def setup(self):
        """No processes."""
        pass

    def create(self, data: dict[int, list[int]] = {}):
        """Create a mapping from user_id to version_id(s)."""
        self.data = data

    def fetch_profile(self, msg: Message) -> Generator:
        """Fetch profiles from database. Simulates latency."""
        msg.fetch_database_time = self.env.now
        yield self.env.timeout(self.config["database_io_latency"])
        if msg.user_id not in self.data:
            raise ValueError(f"Missing profile for user {msg.user_id}")

        msg.profile_versions = self.data[msg.user_id]

    def update_profile(self, msg: Message) -> Generator:
        """Update profiles in database. Simulates latency."""
        msg.udpate_database_time = self.env.now
        yield self.env.timeout(self.config["database_io_latency"])
        if msg.profile_version is not None:
            # From single version worker.
            if msg.profile_version not in self.data[msg.user_id]:
                self.data[msg.user_id].append(msg.profile_version)
        else:
            # From multi version worker.
            if len(msg.profile_versions) == 0:
                raise ValueError("Expecting non-empty profile_versions.")
            for version in msg.profile_versions:
                if version not in self.data[msg.user_id]:
                    self.data[msg.user_id].append(version)


class NetworkSystem:
    """Class for the entire network system."""

    def __init__(
            self,
            env: simpy.Environment,
            client: BaseClient,
            frontend: BaseFrontend,
            workers: list[BaseWorker],
            database: BaseDatabase):
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
    stats_short = copy.deepcopy(stats)
    stats_short.final_messages = None
    stats_short.workload = None
    print(stats_short)

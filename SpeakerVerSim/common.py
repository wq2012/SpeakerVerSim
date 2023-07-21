
"""Common components."""
import copy
import simpy
from typing import Optional, Generator, Any
import dataclasses
import abc
import random
import munch


EPS = 1e-10
STRATEGIES = ["SSO", "SSO-sync", "SSO-hash", "SSO-mul", "SD"]


@dataclasses.dataclass
class Message:
    """A message being communicated between actors."""

    # Unique ID of this message.
    msg_id: int = 0

    # Unique ID of the user.
    user_id: int = 0

    # Unique ID of the version of the profile.
    # Will be updated after fetching profile from database.
    # For enrollment responses, the enrollment version will always
    # be stored in this field, and never in profile_versions.
    profile_version: Optional[int] = None

    # Similar to profile_version, but contains multiple versions.
    # TODO: Consider using Union.
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

    # Max latency for fulfilling one request.
    max_e2e_latency: float = 0

    # Average flops for fulfilling one request.
    average_total_flops: float = 0

    # Max flops for fulfilling one request.
    max_total_flops: float = 0

    # Configuration of the experiment.
    config: munch.Munch = dataclasses.field(default_factory=munch.Munch)

    # Length of final_messages.
    total_num_messages: int = 0

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
            config: munch.Munch,
            stats: GlobalStats):
        self.env = env
        self.name = name
        self.config = config
        self.stats = stats

        # A pool of messages to be processed.
        self.message_pool = simpy.Store(env)

    @abc.abstractmethod
    def setup() -> None:
        """Function to add processes and other initializations."""
        pass

    def log(self, text: str, verbosity: int = 2) -> None:
        """A replacement of print function with verbosity level support.

        Use this conversion:
            0: fatal / error
            1: warning
            2: info
        """
        if verbosity <= self.config.log_verbosity:
            timestamp = f"[{self.env.now:.5f}]"
            name = f"[{self.name}]"
            print(timestamp, name, text)

    def get_latency(self, mu: float) -> simpy.events.Timeout:
        """Simulate latency, which has a Gaussian distribution."""
        sigma = mu / 10.0
        latency = max(random.gauss(mu, sigma), EPS)
        return self.env.timeout(latency)


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
        self.log("send request")
        msg.client_send_time = self.env.now
        # Simulate network latency.
        yield self.get_latency(self.config.client_frontend_latency)
        self.frontend.message_pool.put(msg)


class BaseFrontend(Actor):
    """Base class for a frontend server."""
    client: BaseClient
    workers: list["BaseWorker"]

    def set_client(self, client: BaseClient) -> None:
        self.client = client

    def set_workers(self, workers: list["BaseWorker"]) -> None:
        self.workers = workers

    def set_database(self, database: BaseDatabase) -> None:
        self.database = database

    def select_worker(self, msg: Message) -> "BaseWorker":
        """Decide which worker to send the request to."""
        # By default, simply send request to a random worker.
        return random.choice(self.workers)

    def send_to_worker(self, worker: Actor, msg: Message) -> Generator:
        """Send a message to worker. Simulates latency."""
        self.log("send request")
        if msg.is_enroll:
            msg.frontend_send_worker_enroll_time = self.env.now
        else:
            msg.frontend_send_worker_time = self.env.now
        # Simulate network latency.
        yield self.get_latency(self.config.frontend_worker_latency)
        worker.message_pool.put(msg)

    def send_to_client(self, msg: Message) -> Generator:
        """Send a message to client. Simulates latency."""
        self.log("send response")
        msg.frontend_return_time = self.env.now
        # Simulate network latency.
        yield self.get_latency(self.config.client_frontend_latency)
        self.client.message_pool.put(msg)


class BaseWorker(Actor):
    """Base class for a cloud worker."""
    frontend: BaseFrontend

    # For single version worker.
    version: int

    # For multi version worker.
    versions: list[int]

    def set_frontend(self, frontend: BaseFrontend) -> None:
        self.frontend = frontend

    def set_model_version(self, version: int) -> None:
        self.version = version

    def set_model_versions(self, versions: list[int]) -> None:
        self.versions = versions

    def send_to_frontend(self, msg: Message) -> Generator:
        """Send a message to frontend. Simulates latency."""
        self.log("send response")
        msg.worker_return_time = self.env.now
        # Simulate network latency.
        yield self.get_latency(self.config.frontend_worker_latency)
        self.frontend.message_pool.put(msg)

    def run_inference(self, msg: Message) -> Generator:
        """Run inference of speech engine. Simulates latency."""
        self.log("run inference")
        # Simulate computation latency.
        yield self.get_latency(self.config.worker_inference_latency)
        msg.total_flops += self.config.flops_per_inference

        # Add to stats.
        if self.name not in self.stats.workload:
            self.stats.workload[self.name] = []
        self.stats.workload[self.name].append(
            (self.env.now, self.config.flops_per_inference))


class SingleVersionDatabase(BaseDatabase):
    """Database storing a single version of profile for each user."""

    def setup(self):
        """No processes."""
        pass

    def create(self, init_version: int) -> None:
        """Add initial version for all users."""
        self.data = {}
        for user_id in range(self.config.num_users):
            self.data[user_id] = init_version

    def fetch_profile(self, msg: Message) -> Generator:
        """Fetch profile from database. Simulates latency."""
        if not msg.is_request:
            raise ValueError("Must fetch profile with a request.")
        if msg.is_enroll:
            raise ValueError("Cannot fetch profile with enrollment request.")
        msg.fetch_database_time = self.env.now
        yield self.get_latency(self.config.database_read_latency)
        if msg.user_id not in self.data:
            raise ValueError(f"Missing profile for user {msg.user_id}")

        msg.profile_version = self.data[msg.user_id]

    def update_profile(self, msg: Message) -> Generator:
        """Update profile in database. Simulates latency."""
        if not msg.is_request:
            raise ValueError("Must update profile with a request.")
        if msg.is_enroll:
            raise ValueError("Cannot update profile with enrollment request.")
        msg.udpate_database_time = self.env.now
        yield self.get_latency(self.config.database_write_latency)
        self.data[msg.user_id] = msg.profile_version


class MultiVersionDatabase(BaseDatabase):
    """Database storing multiple versions of profile for each user."""

    def setup(self):
        """No processes."""
        pass

    def create(self, init_versions: list[int]) -> None:
        """Add initial versions for all users."""
        self.data = {}
        for user_id in range(self.config.num_users):
            self.data[user_id] = init_versions

    def fetch_profile(self, msg: Message) -> Generator:
        """Fetch profiles from database. Simulates latency."""
        if not msg.is_request:
            raise ValueError("Must fetch profile with a request.")
        if msg.is_enroll:
            raise ValueError("Cannot fetch profile with enrollment request.")
        msg.fetch_database_time = self.env.now
        yield self.get_latency(self.config.database_read_latency)
        if msg.user_id not in self.data:
            raise ValueError(f"Missing profile for user {msg.user_id}")

        msg.profile_versions = self.data[msg.user_id]

    def update_profile(self, msg: Message) -> Generator:
        """Update profiles in database. Simulates latency."""
        if not msg.is_request:
            raise ValueError("Must update profile with a request.")
        if msg.is_enroll:
            raise ValueError("Cannot update profile with enrollment request.")
        msg.udpate_database_time = self.env.now
        yield self.get_latency(self.config.database_write_latency)
        if msg.profile_version is not None:
            # From single version worker.
            if msg.profile_version not in self.data[msg.user_id]:
                self.data[msg.user_id].append(msg.profile_version)
        else:
            raise ValueError("profile_version should not be empty.")
            # TODO: remove
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

        # Config.
        self.config = self.client.config

        # Set worker model version.
        self.set_worker_model_version()

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

    def set_worker_model_version(self):
        for worker in self.workers:
            worker.set_model_version(1)

    def aggregate_metrics(self) -> GlobalStats:
        """Aggregate metrics, and maybe print."""
        stats = self.client.stats
        stats.total_num_messages = len(stats.final_messages)
        for msg in stats.final_messages:
            stats.average_e2e_latency += (
                msg.client_return_time - msg.client_send_time)
            stats.max_e2e_latency = max(
                stats.max_e2e_latency,
                msg.client_return_time - msg.client_send_time)
            stats.average_total_flops += msg.total_flops
            stats.max_total_flops = max(
                stats.max_total_flops, msg.total_flops)
        stats.average_e2e_latency /= stats.total_num_messages
        stats.average_total_flops /= stats.total_num_messages

        if self.config.print_stats:
            print("========================================")
            print("Global stats:")
            stats_short = copy.deepcopy(stats)
            stats_short.final_messages = None
            stats_short.workload = None
            print(stats_short)

        return stats

    def simulate(self) -> GlobalStats:
        """Run simulation."""
        self.env.run(until=self.config.time_to_run)
        return self.aggregate_metrics()

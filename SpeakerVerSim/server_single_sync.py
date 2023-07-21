"""Server-side single version online strategy with sync (SSO-sync).

The frontend server can periodically send synchronization requests
to all cloud computing servers, and maintain a table to record the
current model version of each cloud computing server.
"""
import simpy
import random
import dataclasses
from typing import Generator, Optional
import munch

from SpeakerVerSim.common import (
    Message, BaseWorker, NetworkSystem, SingleVersionDatabase,
    GlobalStats)
from SpeakerVerSim import server_single_simple


@dataclasses.dataclass
class VersionQuery:
    """A query to ask each worker which version it has."""

    # Whether this is a request or response.
    is_request: bool = True

    # Which worker handled this request.
    worker_name: str = ""

    # The version of the model served by the worker.
    version: Optional[int] = None


class VersionSyncFrontend(server_single_simple.ForegroundReenrollFrontend):
    """A frontend that keeps a model version table."""
    worker_version_table: dict
    query_pool: simpy.Store

    def setup(self) -> None:
        super().setup()
        # Create a table recording each worker's model version.
        self.worker_version_table = dict()
        for worker in self.workers:
            self.worker_version_table[worker.name] = worker.version

        # A pool for version query responses.
        self.query_pool = simpy.Store(self.env)

        # New processes.
        self.env.process(self.send_version_queries())
        self.env.process(self.handle_version_responses())

    def select_worker(self, msg: Message) -> BaseWorker:
        """Decide which worker to send the request to."""
        # Avoid backward version bouncing.
        if msg.profile_version is None:
            raise ValueError("Message version is unset.")
        worker = random.choice(self.workers)
        if self.worker_version_table[worker.name] < msg.profile_version:
            # Retry to find a worker with newer version.
            updated_workers = []
            for worker in self.workers:
                if (self.worker_version_table[worker.name]
                        == msg.profile_version):
                    updated_workers.append(worker)
            # Note: updated_workers can be empty, if the worker has updated,
            # but has not sync'ed with frontend yet.
            if len(updated_workers) > 0:
                return random.choice(updated_workers)
        return worker

    def send_version_queries(self) -> Generator:
        """Send version queries to all workers at intervals."""
        while True:
            yield self.env.timeout(self.config.version_query_interval)
            for worker in self.workers:
                self.env.process(self.send_one_version_query(worker))

    def send_one_version_query(self, worker: BaseWorker) -> Generator:
        """Send one query to one worker."""
        query = VersionQuery()
        # Simulate network latency.
        yield self.get_latency(self.config.frontend_worker_latency)
        worker.query_pool.put(query)  # pytype: disable=attribute-error

    def handle_version_responses(self) -> Generator:
        """Update table based on responses."""
        while True:
            query = yield self.query_pool.get()
            if (query.is_request) or (
                    query.version is None) or (not query.worker_name):
                raise ValueError("Invalid query.")
            self.worker_version_table[query.worker_name] = query.version


class VersionSyncWorker(server_single_simple.SingleVersionWorker):
    """A cloud worker that responds to version queries from frontend."""
    query_pool: simpy.Store

    def setup(self) -> None:
        super().setup()

        # A pool for version query responses.
        self.query_pool = simpy.Store(self.env)

        # New processes.
        self.env.process(self.handle_version_queries())

    def handle_version_queries(self) -> Generator:
        """Handle all version queries."""
        while True:
            query = yield self.query_pool.get()
            self.env.process(self.handle_one_query(query))

    def handle_one_query(self, query: VersionQuery) -> Generator:
        """Handle one version query request and create a response."""
        # Update query.
        if query.is_request:
            query.is_request = False
            query.worker_name = self.name
            query.version = self.version
        else:
            raise ValueError("Query received by worker must be request.")

        # Simulate network latency.
        yield self.get_latency(self.config.frontend_worker_latency)
        self.frontend.query_pool.put(query)  # pytype: disable=attribute-error


def simulate(config: munch.Munch) -> GlobalStats:
    """Run simulation."""
    if config.strategy != "SSO-sync":
        raise ValueError("Incorrect strategy being used.")
    env = simpy.Environment()
    stats = GlobalStats(config=config)
    client = server_single_simple.SimpleClient(env, "client", config, stats)
    frontend = VersionSyncFrontend(env, "frontend", config, stats)
    workers = [
        VersionSyncWorker(env, f"worker-{i}", config, stats)
        for i in range(config.num_cloud_workers)]
    database = SingleVersionDatabase(env, "database", config, stats)
    database.create(init_version=1)
    netsys = NetworkSystem(
        env,
        client,
        frontend,
        workers,
        database)
    return netsys.simulate()

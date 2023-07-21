"""Server-side single version online strategy with user hash (SSO-hash).

The frontend server implements a load balancing algorithm based
on the hash value of the user’s ID, such that requests for each
user are always dispatched to the same cloud computing server.
"""
import simpy
import munch

from SpeakerVerSim.common import (
    Message, BaseWorker, NetworkSystem, SingleVersionDatabase,
    GlobalStats)
from SpeakerVerSim import server_single_simple


class UserHashFrontend(server_single_simple.ForegroundReenrollFrontend):
    """A frontend that selects worker based on user hash."""

    def select_worker(self, msg: Message) -> BaseWorker:
        """Decide which worker to send the request to."""
        # Request from same user always goes to the same worker.
        user_hash = msg.user_id % len(self.workers)
        return self.workers[user_hash]


def simulate(config: munch.Munch) -> GlobalStats:
    """Run simulation."""
    if config.strategy != "SSO-hash":
        raise ValueError("Incorrect strategy being used.")
    env = simpy.Environment()
    stats = GlobalStats(config=config)
    client = server_single_simple.SimpleClient(env, "client", config, stats)
    frontend = UserHashFrontend(env, "frontend", config, stats)
    workers = [
        server_single_simple.SingleVersionWorker(
            env, f"worker-{i}", config, stats)
        for i in range(config["num_cloud_workers"])]
    database = SingleVersionDatabase(env, "database", config, stats)
    database.create(init_version=1)
    netsys = NetworkSystem(
        env,
        client,
        frontend,
        workers,
        database)
    return netsys.simulate()

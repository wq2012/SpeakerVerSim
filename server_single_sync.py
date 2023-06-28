"""Server-side single version online strategy with sync.

The frontend server can periodically send synchronization requests
to all cloud computing servers, and maintain a table to record the
current model version of each cloud computing server。
"""

import server_single_simple

import simpy
import random
import dataclasses
from typing import Generator, Optional

from common import (Message, BaseClient, BaseFrontend,
                    BaseWorker, NetworkSystem, SingleVersionDatabase,
                    GlobalStats, print_results)


@dataclasses.dataclass
class VersionQuery:
    """A query to ask each worker which version it has."""

    # Whether this is a request or response.
    is_request: bool = True

    # Which worker handled this request.
    worker_name: str = ""

    # The version of the model served by the worker.
    version: Optional[int] = None


class VersionSyncFrontend(server_single_simple.SimpleFrontend):
    """A frontend that keeps a model version table."""

    def setup(self) -> None:
        self.worker_version_table = dict()
        self.env.process(self.handle_messages())
        self.env.process(self.send_version_queries())
        self.env.process(self.handle_version_responses())

    def handle_messages(self) -> Generator:
        while True:
            msg = yield self.message_pool.get()
            if msg.is_request:
                # Send request to a random worker.
                worker = random.choice(self.workers)
                self.env.process(self.send_worker_request(worker, msg))
            elif msg.is_enroll:
                # Enrollment response.
                # We need to send it again to a random worker.
                # First, mark it as a non-enrollment request.
                msg.is_enroll = False
                msg.is_request = True
                worker = random.choice(self.workers)
                self.env.process(self.resend_worker_request(worker, msg))
            else:
                # Send response back to client.
                self.env.process(self.send_client_response(msg))

    def send_version_queries(self) -> Generator:
        yield None

    def handle_version_responses(self) -> Generator:
        yield None

from dataclasses import dataclass
import os
from queue import Queue

from splunk_sender import SplunkSender

DISPATCH_MIN_BATCH_SIZE = int(os.getenv("DISPATCH_MIN_BATCH_SIZE"))


@dataclass
class TelemetryDispacherConfig:
    sender: SplunkSender
    dispatch_min_batch_size: str


@dataclass
class TelemetryDispacher():
    config: TelemetryDispacherConfig

    def dispatch_telemetery(self, queue: Queue, force: bool):
        while ((not queue.empty()) and (force or queue.qsize() >= DISPATCH_MIN_BATCH_SIZE)):
            print("[telementry_dispatcher] Dispatch telemetry data")
            batch = queue.get_nowait()
            self.config.sender.send_data_batch(batch)

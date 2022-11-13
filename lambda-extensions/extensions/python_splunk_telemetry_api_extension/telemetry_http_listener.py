from dataclasses import dataclass
from queue import Queue
import sys
import json
from http.server import BaseHTTPRequestHandler, HTTPServer
from threading import Event, Thread


@dataclass
class TelemetryListenerConfig:
    listener_address: str
    listener_port: int


class TelemetryListener():
    def __init__(self, config: TelemetryListenerConfig) -> None:
        self.config = config
        self.listener_url = "http://{0}:{1}".format(
            self.config.listener_address, self.config.listener_port)
        self.queue = Queue()

    def start_extension_http_listener(self):
        def request_handler(*args):
            TelemetryRequestHandler(self.queue, *args)

        print("[telemetery_http_listener.start_http_listener] Starting http listener on {0}:{1}".format(
            self.config.listener_address, self.config.listener_port))
        http_server = HTTPServer(
            (self.config.listener_address, self.config.listener_port), request_handler)

        started_event = Event()
        server_thread = Thread(target=self.run_server, daemon=True,
                               args=(started_event, http_server, ))
        server_thread.start()
        is_event_started = started_event.wait(timeout=9)
        if not is_event_started:
            print(
                "[telemetery_http_listener.start_http_listener] server_thread has timedout before starting")
            raise Exception("server_thread has timedout before starting")

        print("[telemetery_http_listener.start_http_listener] Started http listener")
        return self.listener_url

    # Server thread

    def run_server(self, started_event: Event, http_server: HTTPServer):
        # Notify that this thread is up and running
        started_event.set()
        try:
            http_server.serve_forever()
        except Exception as e:
            print("Error in HTTP server {0}".format(
                sys.exc_info()[0]), flush=True)
            raise Exception("Error in HTTP server", e)
        finally:
            if http_server:
                http_server.shutdown()


class TelemetryRequestHandler(BaseHTTPRequestHandler):
    def __init__(self, queue: Queue, *args):
        self.queue = queue
        BaseHTTPRequestHandler.__init__(self, *args)

    def do_POST(self):
        try:
            cl = self.headers.get("Content-Length")
            if cl:
                data_len = int(cl)
            else:
                data_len = 0
            content = self.rfile.read(data_len)
            self.send_response(200)
            self.end_headers()
            batch = json.loads(content.decode("utf-8"))
            # for filtering only function events view types in https://docs.aws.amazon.com/lambda/latest/dg/telemetry-api.html
            for e in batch:
                if e["record"] and self.is_json(e["record"]):
                    e["record"] = json.loads(e["record"])
            self.queue.put(batch)

        except Exception as e:
            raise Exception("Error processing message", e)

    def is_json(self, myjson):
        try:
            json.loads(myjson)
        except Exception as e:
            return False
        return True

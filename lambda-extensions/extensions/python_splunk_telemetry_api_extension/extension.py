import os
import sys
import time

from pathlib import Path

from splunk_sender import SplunkSender, SplunkSenderConfig
from extensions_api_client import ExtensionApiClient, ExtensionApiClientConfig
from telemetry_http_listener import TelemetryListener, TelemetryListenerConfig
from telemetry_api_client import TelemetryApiClient, TelemetryApiClientConfig
from telemetry_dispatcher import TelemetryDispacher, TelemetryDispacherConfig


def subscribe_extension_http_listener_to_telemetry_api(extension_id, listener_url):
    print("Extension Main: Subscribing the listener to TelemetryAPI", flush=True)
    telemetry_api_config = TelemetryApiClientConfig(
        telemetry_api_url="http://{0}/2022-07-01/telemetry".format(
            os.getenv("AWS_LAMBDA_RUNTIME_API")),
        lambda_extension_identifier_header_key="Lambda-Extension-Identifier",
        timeout_ms=1000,
        max_bytes=256*1024,
        max_items=10000,
    )
    telemetry_api_client = TelemetryApiClient(telemetry_api_config)
    telemetry_api_client.subscribe_listener(extension_id, listener_url)


def configure_extension_api_client():
    extension_api_client_config = ExtensionApiClientConfig(
        lambda_extension_name_header_key="Lambda-Extension-Name",
        lambda_extension_identifier_header_key="Lambda-Extension-Identifier",
        registration_request_base_url="http://{0}/2020-01-01/extension".format(
            os.getenv("AWS_LAMBDA_RUNTIME_API"))
    )
    return ExtensionApiClient(extension_api_client_config)


def configure_handler_telemetry_events(extension_api_client: ExtensionApiClient, extension_id, telemetry_listener: TelemetryListener):
    splunk_sender_config = SplunkSenderConfig(
        host=os.environ["SPLUNK_HOST"],
        hec_token=os.environ['SPLUNK_HEC_TOKEN'],
        index=os.environ["SPLUNK_INDEX"]
    )
    splunk_sender = SplunkSender(splunk_sender_config)
    telemetry_dispatcher_config = TelemetryDispacherConfig(
        sender=splunk_sender,
        dispatch_min_batch_size=int(os.getenv("DISPATCH_MIN_BATCH_SIZE"))
    )
    telemetry_dispatcher = TelemetryDispacher(telemetry_dispatcher_config)
    while True:
        event_data = extension_api_client.next(extension_id)
        telemetry_dispatcher.dispatch_telemetery(
            telemetry_listener.queue, False)
        if event_data["eventType"] == "SHUTDOWN":
            time.sleep(1)
            print("Extension Main: Handle Shutdown Event", flush=True)
            telemetry_dispatcher.dispatch_telemetery(
                telemetry_listener.queue, True)
            sys.exit(0)


def generate_telemetry_listener() -> TelemetryListener:
    telemetry_listener_config = TelemetryListenerConfig(
        listener_address="0.0.0.0" if os.getenv(
            "AWS_SAM_LOCAL") else "sandbox.localdomain",
        listener_port=4243
    )
    return TelemetryListener(telemetry_listener_config)


def generate_extension_name_with_same_name_main_script():
    return f'{Path(__file__).parent.name}.sh'


def main():
    extension_api_client = configure_extension_api_client()
    extension_name = generate_extension_name_with_same_name_main_script()
    extension_id = extension_api_client.register_extension(extension_name)

    telemetry_listener: TelemetryListener = generate_telemetry_listener()
    listener_url = telemetry_listener.start_extension_http_listener()

    subscribe_extension_http_listener_to_telemetry_api(
        extension_id, listener_url)

    configure_handler_telemetry_events(
        extension_api_client, extension_id, telemetry_listener)


if __name__ == "__main__":

    main()

from dataclasses import dataclass
import requests
import json


@dataclass
class TelemetryApiClientConfig:
    telemetry_api_url: str
    lambda_extension_identifier_header_key: str
    timeout_ms: int
    max_bytes: int
    max_items: int


@dataclass
class TelemetryApiClient():
    config: TelemetryApiClientConfig

    def subscribe_listener(self, extension_id, listener_url):
        print("[telemetry_api_client.subscribe_listener] Subscribing Extension to receive telemetry data. ExtenionsId: {0}, listener url: {1}, telemetry api url: {2}".format(
            extension_id, listener_url, self.config.telemetry_api_url))

        # See more about the payload body in https://docs.aws.amazon.com/lambda/latest/dg/telemetry-api.html
        types_without_extension = ["platform", "function"]
        try:
            subscription_request_body = {
                "schemaVersion": "2022-07-01",
                "destination": {
                    "protocol": "HTTP",
                    "URI": listener_url,
                },
                "types": types_without_extension,
                "buffering": {
                    "timeoutMs": self.config.timeout_ms,
                    "maxBytes": self.config.max_bytes,
                    "maxItems": self.config.max_items
                }
            }

            subscription_request_headers = {
                "Content-Type": "application/json",
                self.config.lambda_extension_identifier_header_key: extension_id,
            }

            response = requests.put(
                self.config.telemetry_api_url,
                data=json.dumps(subscription_request_body),
                headers=subscription_request_headers
            )

            if response.status_code == 200:
                print("[telemetry_api_client.subscibe_listener] Extension successfully subscribed to telemetry api",
                      response.text, flush=True)
            elif response.status_code == 202:
                print("[telemetry_api_client.subscibe_listener] Telemetry API not supported. Are you running the extension locally?", flush=True)
            else:
                print("[telemetry_api_client.subscibe_listener] Subscription to telmetry API failed. ",
                      "status code: ", response.status_code, "response text: ", response.text, flush=True)
            return extension_id

        except Exception as e:
            print("Error registering extension.", e, flush=True)
            raise Exception("Error setting AWS_LAMBDA_RUNTIME_API", e)

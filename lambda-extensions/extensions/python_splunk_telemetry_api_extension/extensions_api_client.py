from dataclasses import dataclass
import sys
import requests
import json


@dataclass
class ExtensionApiClientConfig:
    lambda_extension_name_header_key: str
    lambda_extension_identifier_header_key: str
    registration_request_base_url: str


@dataclass
class ExtensionApiClient():
    config: ExtensionApiClientConfig

    def register_extension(self, extension_name):
        print("[extension_api_client.register_extension] Registering Extension using {0}".format(
            self.config.registration_request_base_url))

        try:
            registration_request_body = {
                "events":
                [
                    "INVOKE", "SHUTDOWN"
                ]
            }
            registration_request_header = {
                "Content-Type": "application/json",
                self.config.lambda_extension_name_header_key: extension_name,
            }

            response = requests.post(
                "{0}/register".format(self.config.registration_request_base_url),
                data=json.dumps(registration_request_body),
                headers=registration_request_header
            )

            if response.ok:
                extension_id = response.headers[self.config.lambda_extension_identifier_header_key]
                print("[extension_api_client.register_extension] Registration success with extensionId {0}".format(
                    extension_id), flush=True)
            else:
                print("[extension_api_client.register_extension] Error Registering extension: ",
                      response.text, flush=True)
                # Fail the extension
                sys.exit(1)

            return extension_id

        except Exception as e:
            print(
                "[extension_api_client.register_extension] Error registering extension: ", e, flush=True)
            raise Exception("Error setting AWS_LAMBDA_RUNTIME_API", e)

    def next(self, extension_id):
        try:
            next_event_request_header = {
                "Content-Type": "application/json",
                self.config.lambda_extension_identifier_header_key: extension_id,
            }

            response = requests.get(
                "{0}/event/next".format(self.config.registration_request_base_url),
                headers=next_event_request_header
            )

            if not response.ok:
                print("[extension_api_client.next] Failed receiving next event ",
                      response.status_code, response.text, flush=True)
                # Fail extension with non-zero exit code
                sys.exit(1)

            event_data = response.json()
            return event_data

        except Exception as e:
            print(
                "[extension_api_client.next] Error registering extension.", e, flush=True)
            raise Exception("Error setting AWS_LAMBDA_RUNTIME_API", e)

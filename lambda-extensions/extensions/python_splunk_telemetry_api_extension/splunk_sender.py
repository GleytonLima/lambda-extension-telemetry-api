from dataclasses import dataclass
from urllib.error import HTTPError
import requests
import json
from typing import List


@dataclass
class SplunkSenderConfig():
    host: str
    index: str
    hec_token: str


class SplunkSender():
    def __init__(self,
                 config: SplunkSenderConfig):
        self.config = config
        self.splunk_endpoint = f"{self.config.host}/services/collector/event"

    def send_data_batch(self, event_data: List[dict]):
        data_to_send = []
        for item in event_data:
            data_to_send.append({"index": self.config.index, "event": item})
        data = json.dumps(data_to_send).encode("utf-8")

        headers = {'Authorization': f'Splunk {self.config.hec_token}'}

        # TODO: Change verify to True and point to your cert
        try:
            response = requests.post(
                self.splunk_endpoint,
                data=data,
                headers=headers,
                verify=False)
            if not response.ok:
                print(
                    f"Could not send logs to splunk: {response.status_code} {response.json()}")
        except HTTPError as e:
            print(
                f"Could not send logs to splunk: {str(e)}")

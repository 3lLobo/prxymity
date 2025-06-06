#!/usr/bin/env python3

import os
import json
import requests
import logging
import time
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class License:
    """
    Class for the ES license.
    Get initiated with a json file path.
    Submits the license to an ES server in periodic intervals.
    """

    def __init__(self, license_file: str):
        """
        Initialize the License class.
        :param license_file: Path to the license file.
        """
        self.license_file = license_file
        self.license = None
        self.es = None
        self.es_license = None
        self.es_license_status = None
        self.es_license_status_code = None
        self.es_license_status_message = None
        self.insecure = True
        self.username = None
        self.password = None

    def set_es_url(self, es_url: str, insecure: bool = True):
        """
        Set the ES URL.
        :param es_url: ES URL.
        :param insecure: If True, ignore SSL certificate verification.
        """
        self.es = es_url
        self.insecure = insecure

    def ser_credential(self, username: str, password: str):
        """
        Set the credentials for the ES server.
        :param username: Username for ES server.
        :param password: Password for ES server.
        """
        self.username = username
        self.password = password

    def post_license_file(self):
        """
        Send thew license file as a POST request to the ES server.
        :return: Response from the ES server.
        """
        if not os.path.exists(self.license_file):
            raise FileNotFoundError(
                f"License file {self.license_file} does not exist.",
            )

        with open(self.license_file, "rb") as f:
            self.license = json.load(f)

        headers = {"Content-Type": "application/json"}
        response = requests.post(
            f"{self.es}/_license",
            headers=headers,
            data=json.dumps(self.license),
            verify=not self.insecure,
            auth=(
                (self.username, self.password)
                if self.username and self.password
                else None
            ),
            timeout=10,
        )
        self.es_license_status = response.json()
        self.es_license_status_code = response.status_code

        return response

    def activate(self, interval: int = 60):
        """
        Activate the license.
        :param interval: Interval in seconds to check the license status.
        """
        if not self.es:
            raise ValueError("ES URL is not set.")

        while True:
            response = self.post_license_file()
            if response.status_code == 200:
                logging.info("License activated successfully.")
            else:
                logging.error(
                    "Failed to activate license: {} - {}".format(
                        response.status_code,
                        self.es_license_status.get("error", {}).get(
                            "reason",
                            None,
                        ),
                    )
                )
            time.sleep(interval)


if __name__ == "__main__":

    import argparse

    parser = argparse.ArgumentParser(description="Activate ES license.")
    parser.add_argument(
        "--license_file",
        type=str,
        required=True,
        help="Path to the license file.",
    )
    parser.add_argument("--es_url", type=str, required=True, help="ES URL.")
    parser.add_argument("--username", type=str, help="Username for ES server.")
    parser.add_argument("--password", type=str, help="Password for ES server.")
    parser.add_argument(
        "--interval",
        type=int,
        default=60,
        help="Interval in seconds to check the license status.",
    )
    parser.add_argument(
        "--insecure",
        action="store_true",
        help="Ignore SSL certificate verification.",
    )

    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO)

    es_license = License(args.license_file)
    es_license.set_es_url(args.es_url, args.insecure)
    if args.username and args.password:
        es_license.ser_credential(args.username, args.password)

    es_license.activate(args.interval)

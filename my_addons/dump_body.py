import json
import logging
import pathlib
from mitmproxy.http import HTTPFlow
from datetime import datetime
from addict import Dict

DUMP_PATH = pathlib.Path("data/")
DUMP_PATH.mkdir(exist_ok=True)


class DumpBody(object):
    """Mitmproxy addon to dump the body
    from requests and responses to the OpenAI API.
    """

    def __init__(self):
        self.dump_path = DUMP_PATH
        self.flow_data = Dict()
        pass

    def handle_flow(self, flow: HTTPFlow, type: str) -> None:
        """If the request is a POST request, dump the body.

        Args:
            flow (HTTPFlow): The request flow.
            type (str): The type of flow, either request or response.
        """
        if flow.request.method == "POST":
            stream_id = flow.id
            if type == "response":
                frame = flow.response
            else:
                frame = flow.request
            try:
                self.dump_body(frame.json(), stream_id)
            except Exception as e:
                logging.error(e)
                self.dump_raw(frame.content, stream_id)

    def requestheaders(self, flow: HTTPFlow) -> None:
        """If the response is streamed, buffer it and dump the complete.

        Args:
            flow (HTTPFlow): The flow.
        """
        flow.request.stream = False

    def responseheaders(self, flow: HTTPFlow) -> None:
        """If the response is streamed, buffer it and dump the complete.

        Args:
            flow (HTTPFlow): The flow.
        """
        flow.response.stream = False

    def response(self, flow: HTTPFlow) -> None:
        """Grep the response body for the corresponding stream_id.
        If the response is streamed, buffer it and dump the complete
        response body.

        Args:
            flow (HTTPFlow): The response flow.
        """
        self.handle_flow(flow, type="response")

    def request(self, flow: HTTPFlow) -> None:
        """Grep the request body for the corresponding stream_id.
        If the request is streamed, buffer it and dump the complete
        request body.

        Args:
            flow (HTTPFlow): The request flow.
        """
        self.handle_flow(flow, type="request")

    def dump_raw(self, data: bytes, stream_id: str) -> None:
        """Dump the raw data to a file.

        Args:
            data (bytes): The raw data.
            stream_id (str): Flow id.
        """
        compact_time_str = datetime.now().strftime("%Y%m%d%H%M%S")
        dump_file: pathlib.Path = self.dump_path.joinpath(f"raw/{compact_time_str}.txt")
        dump_file.parent.mkdir(exist_ok=True)
        dump_file.write_bytes(data)
        logging.info(f"Dumping raw {stream_id} to {dump_file}")
        self.flow_data[stream_id].raw = str(dump_file)

    def dump_body(self, body: json.loads, stream_id: str) -> None:
        """Dump the body to a file. If it is a request body,
          store the data in memory. For responses, dump the data
          to a file and clear memory.

        Args:
            body (json.loads): The body to dump.
            stream_id (str): The stream id.
        """
        time_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        if body is None:
            logging.info(f"{time_str} {stream_id} None")
            body = {}
        if self.flow_data.get(stream_id) is None:
            self.flow_data[stream_id] = Dict()
            self.flow_data[stream_id].request = body
        else:
            self.flow_data[stream_id].response = body
            compact_time_str = datetime.now().strftime("%Y%m%d%H%M%S")
            dump_file: pathlib.Path = self.dump_path.joinpath(
                f"{compact_time_str}.json"
            )
            logging.info(f"Dumping {stream_id} to {pathlib.Path(dump_file).absolute()}")
            logging.info(self.flow_data[stream_id])
            dump_file.write_text(
                json.dumps(self.flow_data[stream_id].to_dict()),
            )
            del self.flow_data[stream_id]

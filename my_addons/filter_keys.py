import json
import logging
from mitmproxy.http import HTTPFlow


class FilterKeys(object):
    """Mitmproxy addon to filter the keys
    from the request body to the OpenAI API.
    """

    def __init__(self, keys=[]):
        self.keys = keys

    def request(self, flow: HTTPFlow) -> None:
        """Grep the request body for the corresponding stream_id.
        If the request is streamed, buffer it and dump the complete
        request body.

        Args:
            flow (HTTPFlow): The request flow.
        """
        # get content field
        try:

            data = json.loads(flow.request.content.decode("utf-8"))
            # if not in keys, delete the attribute
            for key in list(data.keys()):
                if key not in self.keys:
                    del data[key]

            flow.request.content = json.dumps(data).encode("utf-8")
        except Exception as e:
            logging.error(e)
            # if the request is not a json, just pass

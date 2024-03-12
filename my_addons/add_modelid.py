import json
import logging

MODEL_NAME = "TheBloke/Llama-2-13B-chat-AWQ"


class AddModelId(object):
    def __init__(self, model_name=MODEL_NAME):
        self.model_name = model_name

    def request(self, flow):
        # Add the field "model": self.model_name to the request body
        if flow.request.method == "POST":
            # Save headers
            headers = flow.request.headers
            logging.info(headers)
            with open("headers.txt", "w") as f:
                f.write(str(headers))
            try:
                data = json.loads(flow.request.content.decode("utf-8"))
                if "model" not in data:
                    data["model"] = self.model_name
                # logging.info(data)
                flow.request.content = json.dumps(data).encode("utf-8")
            except Exception as e:
                logging.error(e)


addons = [AddModelId()]

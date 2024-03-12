from my_addons.dump_body import DumpBody
from my_addons.add_modelid import AddModelId

MODEL_NAME = "gpt-4-0125-preview"
MODEL_NAME = "TheBloke/Llama-2-13B-chat-AWQ"

addons = [DumpBody(), AddModelId(MODEL_NAME)]

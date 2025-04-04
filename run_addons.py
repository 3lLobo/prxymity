from my_addons.dump_body import DumpBody
from my_addons.add_modelid import AddModelId
from my_addons.filter_keys import FilterKeys

MODEL_NAME = "gemini-2.0-flash"
FILTER_KEYS = ["model", "messages"]

addons = [
    FilterKeys(keys=FILTER_KEYS),
    AddModelId(MODEL_NAME),
    DumpBody(),
]

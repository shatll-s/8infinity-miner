import json
import os

dirname = os.path.dirname(__file__)


POW_ADDRESS = "0x8888FF459Da48e5c9883f893fc8653c8E55F8888"
with open(os.path.join(dirname, "./abi/pow.json")) as f:
    POW_ABI = json.load(f)

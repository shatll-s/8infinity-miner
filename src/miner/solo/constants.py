import json
import os

dirname = os.path.dirname(__file__)


POW_ADDRESS = "0x8888FF459Da48e5c9883f893fc8653c8E55F8888"
with open(os.path.join(dirname, "./abi/pow.json")) as f:
    POW_ABI = json.load(f)

INFINITY_ADDRESS = "0x888852d1c63c7b333efEb1c4C5C79E36ce918888"
with open(os.path.join(dirname, "./abi/erc20.json")) as f:
    ERC20_ABI = json.load(f)

import os
import logging

from eth_account import Account
from eth_utils import is_same_address
from web3 import Web3


logging.basicConfig(
    level=os.getenv("LOGLEVEL", "INFO"),
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

# Node Config
RPC = os.getenv("INFINITY_RPC", "https://rpc.soniclabs.com")
WS = os.getenv("INFINITY_WS", "wss://rpc.soniclabs.com")

# Common miner config
MINER_PRIVATE_KEY = os.getenv("INFINITY_MINER_PRIVATE_KEY")
REWARDS_RECIPIENT_ADDRESS = os.getenv("REWARDS_RECIPIENT_ADDRESS")


# ============ Config validation ============

if MINER_PRIVATE_KEY is None:
    print(
        "[ERROR]: INFINITY_MINER_PRIVATE_KEY is missing. Please set it in your .env file."
    )
    exit(0)

try:
    miner_account = Account.from_key(MINER_PRIVATE_KEY)
except Exception:
    pk = (
        MINER_PRIVATE_KEY[:4]
        + "*" * (len(MINER_PRIVATE_KEY) - 8)
        + MINER_PRIVATE_KEY[-4:]
    )
    print(
        f"[ERROR]: The value provided for INFINITY_MINER_PRIVATE_KEY ({pk}) is not a valid private key."
    )
    exit(0)

if REWARDS_RECIPIENT_ADDRESS is None:
    REWARDS_RECIPIENT_ADDRESS = miner_account.address


if not is_same_address(miner_account.address, REWARDS_RECIPIENT_ADDRESS):
    print(
        f"[WARNING]: Make sure you have access to the REWARDS_RECIPIENT_ADDRESS ({REWARDS_RECIPIENT_ADDRESS})."
    )

try:
    w3 = Web3(Web3.HTTPProvider(RPC))
    miner_balance = w3.eth.get_balance(miner_account.address)
except Exception:
    print(f"[ERROR]: Unable to establish a connection with INFINITY_RPC ({RPC}).")
    exit(0)

if miner_balance < 10e18:
    print(
        f"[WARNING]: Current master balance is {miner_balance/1e18:.2f} $S. Consider topping it up."
    )

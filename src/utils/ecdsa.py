from eth_keys.constants import SECPK1_N
from eth_account import Account
from eth_account.signers.local import LocalAccount
from eth_keys.backends.native.ecdsa import G, fast_multiply


def add_private_key(private_key_a: int, private_key_b: int) -> int:
    return (private_key_a + private_key_b) % SECPK1_N


def get_account_ab(private_key_a: int, private_key_b: int) -> LocalAccount:
    return Account.from_key(add_private_key(private_key_a, private_key_b).to_bytes(32))


def private_key_to_ec_point(private_key: int) -> tuple[int, int]:
    return fast_multiply(G, private_key)

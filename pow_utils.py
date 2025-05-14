from eth_keys.constants import SECPK1_N
from eth_account import Account
from eth_account.signers.local import LocalAccount
from eth_keys.backends.native.ecdsa import G, fast_multiply


MAGIC_NUMBER = 0x8888888888888888888888888888888888888888


def get_account_ab(private_key_a: int, private_key_b: int) -> LocalAccount:
    private_key_ab = (private_key_a + private_key_b) % SECPK1_N
    return Account.from_key(private_key_ab.to_bytes(32))


def private_key_to_ec_point(private_key: int) -> tuple[int, int]:
    return fast_multiply(G, private_key)

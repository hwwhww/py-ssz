import time

from ssz import (
    hash_tree_root,
)
from ssz.hash import (
    hash_eth2,
)
from ssz.sedes import (
    boolean,
    List,
    Serializable,
    bytes32,
    bytes48,
    uint64,
)

from minimal_ssz import (
    SSZType,
    hash_tree_root as mini_hash_tree_root
)


class ValidatorRecord(Serializable):
    fields = [
        ('pubkey', bytes48),
        ('withdrawal_credentials', bytes32),
        ('activation_epoch', uint64),
        ('exit_epoch', uint64),
        ('withdrawable_epoch', uint64),
        ('initiated_exit', boolean),
        ('slashed', boolean),
        ('high_balance', uint64),
    ]


def create_validator(seed, ssz_container) -> ValidatorRecord:
    seed_bytes32 = seed.to_bytes(32, 'little')
    return ssz_container(
        pubkey=(
            hash_eth2(seed_bytes32 + b'pubkey_1')[0:24] +
            hash_eth2(seed_bytes32 + b'pubkey_2')[0:24]
        ),
        withdrawal_credentials=hash_eth2(seed_bytes32 + b'withdrawal_credentials'),
        activation_epoch=seed + 1,
        exit_epoch=seed + 2,
        withdrawable_epoch=seed + 3,
        initiated_exit=False,
        slashed=False,
        high_balance=seed + 10000,
    )


class State(Serializable):
    fields = [
        ('validator_registry', List(ValidatorRecord)),
    ]


def make_state(num_validators):
    state = State(
        validator_registry=tuple(
            create_validator(i, ValidatorRecord)
            for i in range(num_validators)
        ),
    )
    return state


#
# Minimal spec
#
Validator = SSZType({
    # BLS public key
    'pubkey': 'bytes48',
    # Withdrawal credentials
    'withdrawal_credentials': 'bytes32',
    # Epoch when validator activated
    'activation_epoch': 'uint64',
    # Epoch when validator exited
    'exit_epoch': 'uint64',
    # Epoch when validator is eligible to withdraw
    'withdrawable_epoch': 'uint64',
    # Did the validator initiate an exit
    'initiated_exit': 'bool',
    # Was the validator slashed
    'slashed': 'bool',
    # Rounded balance
    'high_balance': 'uint64'
})

BeaconState = SSZType({
    # Validator registry
    'validator_registry': [Validator],
})


def make_minimal_ssz_state(num_validators):
    minimal_ssz_state = BeaconState(
        validator_registry=[
            create_validator(i, Validator)
            for i in range(num_validators)
        ]
    )
    return minimal_ssz_state


def run():
    num_validators = 2**18

    state = make_state(num_validators)
    start_time = time.time()
    tree_root_result = hash_tree_root(state)
    actual_performance = time.time() - start_time
    print("Performance of hash_tree_root", actual_performance)

    # minimal SSZ
    state = make_minimal_ssz_state(num_validators)
    start_time = time.time()
    mini_hash_tree_root_result = mini_hash_tree_root(state)
    actual_performance = time.time() - start_time
    print("Performance of mini_hash_tree_root", actual_performance)

    assert mini_hash_tree_root_result == tree_root_result


if __name__ == '__main__':
    run()

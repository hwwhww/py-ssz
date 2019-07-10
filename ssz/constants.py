from eth_typing import (
    Hash32,
)
from eth_utils.toolz import (
    iterate,
    take,
)

from ssz.hash import (
    hash_eth2,
)

CHUNK_SIZE = 32  # named BYTES_PER_CHUNK in the spec
EMPTY_CHUNK = Hash32(b"\x00" * CHUNK_SIZE)

SIGNATURE_FIELD_NAME = "signature"

# number of bytes for a serialized offset
OFFSET_SIZE = 4

FIELDS_META_ATTR = "fields"

ZERO_BYTES32 = b'\x00' * 32
ZERO_HASHES = tuple(take(100, iterate(lambda child: hash_eth2(child + child), ZERO_BYTES32)))

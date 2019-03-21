from eth_typing import (
    Hash32,
)

CHUNK_SIZE = 32
EMPTY_CHUNK = Hash32(b"\x00" * CHUNK_SIZE)

SIZE_PREFIX_SIZE = 4
MAX_CONTENT_SIZE = 2 ** (SIZE_PREFIX_SIZE * 8) - 1

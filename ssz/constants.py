CHUNK_SIZE = 32
EMPTY_CHUNK = b"\x00" * CHUNK_SIZE

SIZE_PREFIX_SIZE = 4
MAX_CONTENT_SIZE = 2 ** (SIZE_PREFIX_SIZE * 8) - 1

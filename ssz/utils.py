from ssz.exceptions import (
    SerializationError,
)
from ssz.sedes import (
    boolean,
)


def is_sedes(obj):
    """
    Check if `obj` is a sedes object.
    A sedes object is characterized by having the methods
    `serialize(obj)` and `deserialize(serial)`.
    """
    return hasattr(obj, 'serialize') and hasattr(obj, 'deserialize')


def infer_sedes(obj):
    """
    Try to find a sedes objects suitable for a given Python object.
    """
    if isinstance(obj, bool):
        return boolean
    elif isinstance(obj, int):
        raise SerializationError(
            'uint sedes object or uint string needs to be specified for ints',
            obj
        )

    msg = 'Did not find sedes handling type {}'.format(type(obj).__name__)
    raise TypeError(msg)

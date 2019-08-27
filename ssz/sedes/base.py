from abc import (
    ABC,
    abstractmethod,
)
import collections
from typing import (
    Any,
    Generic,
    Optional,
    Sequence,
    Tuple,
)

from eth_typing import (
    Hash32,
)

from ssz.typing import (
    CacheObj,
    TDeserialized,
    TSerializable,
)


class BaseSedes(ABC, Generic[TSerializable, TDeserialized]):
    #
    # Size
    #
    @property
    @abstractmethod
    def is_fixed_sized(self) -> bool:
        ...

    @abstractmethod
    def get_fixed_size(self) -> int:
        ...

    #
    # Serialization
    #
    @abstractmethod
    def serialize(self, value: TSerializable) -> bytes:
        ...

    #
    # Deserialization
    #
    @abstractmethod
    def deserialize(self, data: bytes) -> TDeserialized:
        ...

    #
    # Tree hashing
    #
    @abstractmethod
    def get_hash_tree_root(self, value: TSerializable) -> Hash32:
        ...

    @abstractmethod
    def get_hash_tree_root_and_leaves(self,
                                      value: TSerializable,
                                      cache: CacheObj) -> Tuple[Hash32, CacheObj]:
        ...

    @abstractmethod
    def chunk_count(self) -> int:
        ...

    @abstractmethod
    def get_key(self, value: Any) -> bytes:
        ...


TSedes = BaseSedes[Any, Any]


class BaseCompositeSedes(BaseSedes[TSerializable, TDeserialized]):
    @abstractmethod
    def get_fixed_size_section_length(
            self,
            value: Sequence[TSerializable],
            pairs: Optional[Tuple[Tuple[TSerializable, TSedes], ...]]=None) -> int:
        ...

class BaseSerializable(collections.Sequence):
    ...

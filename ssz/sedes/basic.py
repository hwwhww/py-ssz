from abc import (
    abstractmethod,
)
import io
import operator
from typing import (
    IO,
    Any,
    Iterable,
    Optional,
    Sequence,
    Tuple,
    Union,
)

from eth_typing import (
    Hash32,
)
from eth_utils import (
    to_tuple,
)
from eth_utils.toolz import (
    accumulate,
    concatv,
)

from ssz import (
    constants,
)
from ssz.cache.utils import (
    _get_key,
    get_key,
)
from ssz.exceptions import (
    DeserializationError,
)
from ssz.sedes.base import (
    BaseCompositeSedes,
    BaseSedes,
    BaseSerializable,
    TSedes,
)
from ssz.typing import (
    CacheObj,
    TDeserialized,
    TSerializable,
)
from ssz.utils import (
    encode_offset,
    merkleize,
    merkleize_with_cache,
    pack,
)


class BasicSedes(BaseSedes[TSerializable, TDeserialized]):
    def __init__(self, size: int):
        if size <= 0:
            raise ValueError("Length must be greater than 0")

        self.size = size

    #
    # Size
    #
    is_fixed_sized = True

    def get_fixed_size(self):
        return self.size

    #
    # Tree hashing
    #
    def get_hash_tree_root(self, value: TSerializable) -> bytes:
        serialized_value = self.serialize(value)
        return merkleize(pack((serialized_value,)))

    def get_hash_tree_root_and_leaves(self,
                                      value: TSerializable,
                                      cache: CacheObj) -> Tuple[Hash32, CacheObj]:
        serialized_value = self.serialize(value)
        return merkleize_with_cache(
            pack((serialized_value,)),
            cache=cache,
        )

    def chunk_count(self) -> int:
        return 1

    def get_key(self, value: Any) -> bytes:
        return get_key(self, value)


def _compute_fixed_size_section_length(element_sedes: Iterable[TSedes]) -> int:
    return sum(
        sedes.get_fixed_size()
        if sedes.is_fixed_sized else constants.OFFSET_SIZE
        for sedes in element_sedes
    )


class BasicBytesSedes(BaseSedes[TSerializable, TDeserialized]):
    def get_key(self, value: Any) -> bytes:
        return get_key(self, value)


class CompositeSedes(BaseCompositeSedes[TSerializable, TDeserialized]):
    @abstractmethod
    def _get_item_sedes_pairs(self,
                              value: Sequence[TSerializable],
                              ) -> Tuple[Tuple[TSerializable, TSedes], ...]:
        ...

    def get_fixed_size_section_length(
            self,
            value: Sequence[TSerializable],
            pairs: Optional[Tuple[Tuple[TSerializable, TSedes], ...]]=None) -> int:
        if pairs is None:
            pairs = self._get_item_sedes_pairs(value)
        element_sedes = tuple(sedes for element, sedes in pairs)
        return _compute_fixed_size_section_length(element_sedes)

    def _validate_serializable(self, value: Any) -> None:
        ...

    def serialize(self, value: TSerializable, fixed_size_section_length=None) -> bytes:
        self._validate_serializable(value)

        if not len(value):
            return b''

        pairs = self._get_item_sedes_pairs(value)
        if fixed_size_section_length is None:
            fixed_size_section_length = self.get_fixed_size_section_length(value, pairs=pairs)

        variable_size_section_parts = tuple(
            sedes.serialize(item)  # slow
            for item, sedes
            in pairs
            if not sedes.is_fixed_sized
        )

        if variable_size_section_parts:
            offsets = tuple(accumulate(
                operator.add,
                map(len, variable_size_section_parts[:-1]),
                fixed_size_section_length,
            ))
        else:
            offsets = ()

        offsets_iter = iter(offsets)

        fixed_size_section_parts = tuple(
            sedes.serialize(item)  # slow
            if sedes.is_fixed_sized
            else encode_offset(next(offsets_iter))
            for item, sedes in pairs
        )

        try:
            next(offsets_iter)
        except StopIteration:
            pass
        else:
            raise DeserializationError("Did not consume all offsets while decoding value")

        return b"".join(concatv(
            fixed_size_section_parts,
            variable_size_section_parts,
        ))

    def deserialize(self, data: bytes) -> TDeserialized:
        stream = io.BytesIO(data)
        value = self._deserialize_stream(stream)
        extra_data = stream.read()
        if extra_data:
            raise DeserializationError(f"Got {len(extra_data)} superfluous bytes")
        return value

    @abstractmethod
    def _deserialize_stream(self, stream: IO[bytes]) -> TDeserialized:
        ...

    def get_key(self, value: Any) -> bytes:
        return get_key(self, value)


class HomogeneousCompositeSedes(CompositeSedes[TSerializable, TDeserialized]):
    def get_key(self, value: Any) -> str:
        key = _get_key(self, value).hex()
        sedes_name = type(self).__name__
        if len(key) > 0:
            return sedes_name + key
        else:
            return sedes_name + str(self.max_length)

    def get_merkle_leaves(self, value: Any, cache: CacheObj) -> Tuple[Tuple[Hash32], CacheObj]:
        merkle_leaves = ()
        if isinstance(self.element_sedes, BasicSedes):
            serialized_elements = tuple(
                self.element_sedes.serialize(element)
                for element in value
            )
            merkle_leaves = pack(serialized_elements)
        else:
            has_get_hash_tree_root_and_leaves = hasattr(
                self.element_sedes,
                'get_hash_tree_root_and_leaves',
            )
            if has_get_hash_tree_root_and_leaves:
                merkle_leaves, cache = self.get_merkle_leaves_with_cache(
                    value,
                    cache,
                )
            else:
                merkle_leaves = self.get_merkle_leaves_without_cache(value)

            # merkle_leaves = self.get_merkle_leaves_without_cache(value)
            # merkle_leaves = self._get_merkle_leaves_no_query(value, cache)
            # if isinstance(self.element_sedes, BasicBytesSedes):
            #     # It's low overhead, no need to cache
            #     # merkle_leaves = self.get_merkle_leaves_without_cache(value)
            #     merkle_leaves = self._get_merkle_leaves_no_query(value, cache)
            # else:
            #     merkle_leaves, cache = self.get_merkle_leaves_with_cache(value, cache)
        return merkle_leaves, cache

    def get_merkle_leaves_with_cache(self,
                                     value: Any,
                                     cache: CacheObj) -> Tuple[Tuple[Hash32], CacheObj]:
        result = self._get_merkle_leaves_with_cache(value, cache)
        return result, cache

    @to_tuple
    def _get_merkle_leaves_with_cache(self,
                                     value: Any,
                                     cache: CacheObj) -> Iterable[Hash32]:
        """
        NOTE: cache is mutable
        """
        for element in value:
            key = self.element_sedes.get_key(element)
            if key not in cache:
                root, cache = (
                    self.element_sedes.get_hash_tree_root_and_leaves(element, cache)
                )
                cache[key] = root
            yield cache[key]

    @to_tuple
    def get_merkle_leaves_without_cache(self, value: Any) -> Iterable[Hash32]:
        for element in value:
            yield self.element_sedes.get_hash_tree_root(element)

    @to_tuple
    def _get_merkle_leaves_no_query(self, value: Any, cache) -> Iterable[Hash32]:
        for element in value:
            root, cache = (
                self.element_sedes.get_hash_tree_root_and_leaves(element, cache)
            )
            yield root


class NonhomogeneousCompositeSedes(CompositeSedes[TSerializable, TDeserialized]):
    ...

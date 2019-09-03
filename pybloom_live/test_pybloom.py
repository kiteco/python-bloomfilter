from __future__ import absolute_import
from pybloom_live.pybloom import (BloomFilter, ScalableBloomFilter,
                                  make_hashfuncs)
from pybloom_live.storage import BitArrayStorage, Storage
from pybloom_live.utils import running_python_3, range_fn

try:
    import StringIO
    import cStringIO
except ImportError:
    pass

import io

import unittest
import random
import tempfile

import pytest


class CustomStorage(Storage):
    """Custom storage class that keeps bits in a list of booleans"""

    def __init__(self, num_bits):
        super(CustomStorage, self).__init__(num_bits)
        self.bits = []
        self.clear()

    def clear(self):
        self.bits = [False] * self.num_bits

    def get(self, index):
        return self.bits[index]

    def set(self, index):
        self.bits[index] = True

    def copy(self):
        new_storage = CustomStorage(self.num_bits)
        new_storage.bits = self.bits[:]
        return new_storage

    def union(self, other):
        assert isinstance(other, CustomStorage)
        new_storage = self.copy()
        for i, bit in enumerate(other.bits):
            if bit:
                new_storage.bits[i] = True
        return new_storage

    def intersection(self, other):
        assert isinstance(other, CustomStorage)
        new_storage = self.copy()
        for i, bit in enumerate(other.bits):
            if not bit:
                new_storage.bits[i] = False
        return new_storage

    def tobytes(self):
        return ''.join('1' if bit else '0' for bit in self.bits).encode('latin1')

    @classmethod
    def frombytes(cls, data):
        self = cls(len(data))
        self.bits = [True if bit == '1' else False for bit in data.decode('latin1')]
        return self


class TestMakeHashFuncs(unittest.TestCase):
    def test_make_hashfuncs_returns_hashfn(self):
        make_hashes, hashfn = make_hashfuncs(100, 20)
        self.assertEquals('openssl_sha512', hashfn.__name__)
        make_hashes, hashfn = make_hashfuncs(20, 3)
        self.assertEquals('openssl_sha384', hashfn.__name__)
        make_hashes, hashfn = make_hashfuncs(15, 2)
        self.assertEquals('openssl_sha256', hashfn.__name__)
        make_hashes, hashfn = make_hashfuncs(10, 2)
        self.assertEquals('openssl_sha1', hashfn.__name__)
        make_hashes, hashfn = make_hashfuncs(5, 1)
        self.assertEquals('openssl_md5', hashfn.__name__)


class TestUnionIntersection(object):

    @pytest.fixture(name='storage', params=[None, BitArrayStorage, CustomStorage])
    def storage_fixture(self, request):
        return request.param

    def test_union(self, storage):
        if storage is None:
            bloom_one = BloomFilter(100, 0.001)
            bloom_two = BloomFilter(100, 0.001)
        else:
            bloom_one = BloomFilter(100, 0.001, storage=storage)
            bloom_two = BloomFilter(100, 0.001, storage=storage)
            assert isinstance(bloom_one.storage, storage)
        chars = [chr(i) for i in range_fn(97, 123)]
        for char in chars[int(len(chars)/2):]:
            bloom_one.add(char)
        for char in chars[:int(len(chars)/2)]:
            bloom_two.add(char)
        new_bloom = bloom_one.union(bloom_two)
        for char in chars:
            assert char in new_bloom

    def test_intersection(self, storage):
        if storage is None:
            bloom_one = BloomFilter(100, 0.001)
            bloom_two = BloomFilter(100, 0.001)
        else:
            bloom_one = BloomFilter(100, 0.001, storage=storage)
            bloom_two = BloomFilter(100, 0.001, storage=storage)
            assert isinstance(bloom_one.storage, storage)
        chars = [chr(i) for i in range_fn(97, 123)]
        for char in chars:
            bloom_one.add(char)
        for char in chars[:int(len(chars)/2)]:
            bloom_two.add(char)
        new_bloom = bloom_one.intersection(bloom_two)
        for char in chars[:int(len(chars)/2)]:
            assert char in new_bloom
        for char in chars[int(len(chars)/2):]:
            assert char not in new_bloom

    def test_intersection_capacity_fail(self, storage):
        if storage is None:
            bloom_one = BloomFilter(1000, 0.001)
            bloom_two = BloomFilter(100, 0.001)
        else:
            bloom_one = BloomFilter(1000, 0.001, storage=storage)
            bloom_two = BloomFilter(100, 0.001, storage=storage)
            assert isinstance(bloom_one.storage, storage)
        with pytest.raises(ValueError):
            bloom_one.intersection(bloom_two)

    def test_union_capacity_fail(self, storage):
        if storage is None:
            bloom_one = BloomFilter(1000, 0.001)
            bloom_two = BloomFilter(100, 0.001)
        else:
            bloom_one = BloomFilter(1000, 0.001, storage=storage)
            bloom_two = BloomFilter(100, 0.001, storage=storage)
            assert isinstance(bloom_one.storage, storage)
        with pytest.raises(ValueError):
            bloom_one.union(bloom_two)

    def test_intersection_k_fail(self, storage):
        if storage is None:
            bloom_one = BloomFilter(100, 0.001)
            bloom_two = BloomFilter(100, 0.01)
        else:
            bloom_one = BloomFilter(100, 0.001, storage=storage)
            bloom_two = BloomFilter(100, 0.01, storage=storage)
            assert isinstance(bloom_one.storage, storage)
        with pytest.raises(ValueError):
            bloom_one.intersection(bloom_two)

    def test_union_k_fail(self, storage):
        if storage is None:
            bloom_one = BloomFilter(100, 0.01)
            bloom_two = BloomFilter(100, 0.001)
        else:
            bloom_one = BloomFilter(100, 0.01, storage=storage)
            bloom_two = BloomFilter(100, 0.001, storage=storage)
            assert isinstance(bloom_one.storage, storage)
        with pytest.raises(ValueError):
            bloom_one.union(bloom_two)

    def test_union_storage_fail(self):
        bloom_one = BloomFilter(100, 0.001)
        bloom_two = BloomFilter(100, 0.001, storage=CustomStorage)
        assert not isinstance(bloom_two.storage, type(bloom_one.storage))
        with pytest.raises(ValueError):
            bloom_one.union(bloom_two)

    def test_intersection_storage_fail(self):
        bloom_one = BloomFilter(100, 0.001)
        bloom_two = BloomFilter(100, 0.001, storage=CustomStorage)
        assert not isinstance(bloom_two.storage, type(bloom_one.storage))
        with pytest.raises(ValueError):
            bloom_one.intersection(bloom_two)


class TestScalableBloomFilterUnionIntersection(object):

    def test_union_scalable_bloom_filter(self):
        bloom_one = ScalableBloomFilter(mode=ScalableBloomFilter.SMALL_SET_GROWTH)
        bloom_two = ScalableBloomFilter(mode=ScalableBloomFilter.SMALL_SET_GROWTH)
        numbers = [i for i in range_fn(1, 10000)]
        middle = int(len(numbers) / 2)
        for number in numbers[middle:]:
            bloom_one.add(number)
        for number in numbers[:middle]:
            bloom_two.add(number)
        new_bloom = bloom_one.union(bloom_two)
        for number in numbers:
            assert number in new_bloom


class TestSerialization(object):
    SIZE = 12345
    EXPECTED = set([random.randint(0, 10000100) for _ in range_fn(0, SIZE)])

    @pytest.mark.parametrize("cls,args,storage", [
        (BloomFilter, (SIZE,), None),
        (BloomFilter, (SIZE,), BitArrayStorage),
        (BloomFilter, (SIZE,), CustomStorage),
        (ScalableBloomFilter, (), None),
    ])
    @pytest.mark.parametrize("stream_factory", [
        lambda: tempfile.TemporaryFile,
        lambda: io.BytesIO,
        pytest.param(
            lambda: cStringIO.StringIO,
            marks=pytest.mark.skipif(running_python_3, reason="Python 2 only")),
        pytest.param(
            lambda: StringIO.StringIO,
            marks=pytest.mark.skipif(running_python_3, reason="Python 2 only")),
    ])
    def test_serialization(self, cls, args, stream_factory, storage):
        if storage is None:
            filter = cls(*args)
        else:
            filter = cls(*args, storage=storage)
        for item in self.EXPECTED:
            filter.add(item)

        f = stream_factory()()
        filter.tofile(f)
        del filter

        f.seek(0)
        if storage is None:
            filter = cls.fromfile(f)
        else:
            filter = cls.fromfile(f, storage=storage)
        for item in self.EXPECTED:
            assert item in filter


if __name__ == '__main__':
    unittest.main()

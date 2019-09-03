import pytest

from pybloom_live.storage import BitArrayStorage, Storage


class TestBitArrayStorage(object):

    def test_init_zero_size(self):
        storage = BitArrayStorage(0)
        assert storage.num_bits == 0
        assert storage.bitarray.to01() == ''

    def test_init_nonzero_size(self):
        storage = BitArrayStorage(5)
        assert storage.num_bits == 5
        assert storage.bitarray.to01() == '00000'

    def test_set(self):
        storage = BitArrayStorage(5)
        storage.set(2)
        storage.set(4)
        assert storage.bitarray.to01() == '00101'

    def test_get(self):
        storage = BitArrayStorage(5)
        storage.set(2)
        storage.set(4)
        assert storage.get(0) is False
        assert storage.get(1) is False
        assert storage.get(2) is True
        assert storage.get(3) is False
        assert storage.get(4) is True

    def test_clear(self):
        storage = BitArrayStorage(5)
        storage.set(2)
        storage.set(4)
        storage.clear()
        assert storage.bitarray.to01() == '00000'

    def test_copy(self):
        storage = BitArrayStorage(5)
        storage.set(2)
        storage.set(4)
        copy = storage.copy()
        assert storage.bitarray is not copy.bitarray
        assert storage.num_bits == copy.num_bits
        assert storage.bitarray.to01() == copy.bitarray.to01()

    def test_union(self):
        storage_a = BitArrayStorage(5)
        storage_a.set(2)
        storage_b = BitArrayStorage(5)
        storage_b.set(4)
        union = storage_a.union(storage_b)
        assert union.bitarray.to01() == '00101'
        assert storage_b.union(storage_a).bitarray.to01() == union.bitarray.to01()

    def test_intersection(self):
        storage_a = BitArrayStorage(5)
        storage_a.set(0)
        storage_a.set(2)
        storage_b = BitArrayStorage(5)
        storage_b.set(2)
        storage_b.set(4)
        intersection = storage_a.intersection(storage_b)
        assert intersection.bitarray.to01() == '00100'
        assert storage_b.intersection(storage_a).bitarray.to01() == intersection.bitarray.to01()

    def test_union_type_mismatch(self):
        storage_a = BitArrayStorage(5)
        storage_b = Storage(5)
        with pytest.raises(ValueError):
            storage_a.union(storage_b)

    def test_intersection_type_mismatch(self):
        storage_a = BitArrayStorage(5)
        storage_b = Storage(5)
        with pytest.raises(ValueError):
            storage_a.intersection(storage_b)

    def test_tobytes(self):
        storage = BitArrayStorage(5)
        storage.set(2)
        storage.set(4)
        data = storage.tobytes()
        assert data == b'\x14'

    def test_frombytes(self):
        storage = BitArrayStorage.frombytes(b'\x14')
        assert storage.bitarray.to01() == '00101000'
        assert storage.num_bits == 8

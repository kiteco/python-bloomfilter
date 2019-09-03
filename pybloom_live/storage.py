from bitarray import bitarray


class Storage(object):

    def __init__(self, num_bits):
        self.num_bits = num_bits

    def clear(self):
        raise NotImplementedError

    def get(self, index):
        raise NotImplementedError

    def set(self, index):
        raise NotImplementedError

    def copy(self):
        raise NotImplementedError

    def union(self, other):
        raise NotImplementedError

    def intersection(self, other):
        raise NotImplementedError

    def tobytes(self):
        raise NotImplementedError

    @classmethod
    def frombytes(cls, data):
        raise NotImplementedError


class BitArrayStorage(Storage):

    def __init__(self, num_bits, _bitarray=None):
        super(BitArrayStorage, self).__init__(num_bits)
        if _bitarray is None:
            self.bitarray = bitarray(self.num_bits, endian='little')
            self.clear()
        else:
            assert num_bits == _bitarray.length()
            self.bitarray = _bitarray

    def clear(self):
        self.bitarray.setall(False)

    def get(self, index):
        return self.bitarray[index]

    def set(self, index):
        self.bitarray[index] = True

    def copy(self):
        new_storage = BitArrayStorage(self.num_bits, _bitarray=self.bitarray.copy())
        return new_storage

    def union(self, other):
        if not isinstance(other, BitArrayStorage):
            raise ValueError('Storage type mismatch: <self> | <other>'.format(
                self=type(self).__name__, other=type(other).__name__))
        new_storage = BitArrayStorage(self.num_bits, _bitarray=self.bitarray | other.bitarray)
        return new_storage

    def intersection(self, other):
        if not isinstance(other, BitArrayStorage):
            raise ValueError('Storage type mismatch: <self> & <other>'.format(
                self=type(self).__name__, other=type(other).__name__))
        new_storage = BitArrayStorage(self.num_bits, _bitarray=self.bitarray & other.bitarray)
        return new_storage

    def tobytes(self):
        return self.bitarray.tobytes()

    @classmethod
    def frombytes(cls, bytes):
        data = bitarray(0, endian='little')
        data.frombytes(bytes)
        return cls(data.length(), data)

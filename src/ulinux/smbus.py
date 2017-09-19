"""MicroPython implementation of I2C SMBus on Linux.

Essentially, this provides the same functionality that the ``i2c_smbus_*``
functions from ``linux/i2c-dev.h`` do in C.
"""

from fcntl import ioctl

from micropython import const
from uctypes import addressof
from uctypes import sizeof
from uctypes import struct
from uctypes import ARRAY
from uctypes import PTR
from uctypes import UINT8
from uctypes import UINT16
from uctypes import UINT32

# from linux/i2c.h

_I2C_M_TEN = const(0x0010)
_I2C_M_RD = const(0x0001)
_I2C_M_STOP = const(0x8000)
_I2C_M_NOSTART = const(0x4000)
_I2C_M_REV_DIR_ADDR = const(0x2000)
_I2C_M_IGNORE_NAK = const(0x1000)
_I2C_M_NO_RD_ACK = const(0x0800)
_I2C_M_RECV_LEN = const(0x0400)

_I2C_FUNC_I2C = const(0x00000001)
_I2C_FUNC_10BIT_ADDR = const(0x00000002)
_I2C_FUNC_PROTOCOL_MANGLING = const(0x00000004)
_I2C_FUNC_SMBUS_PEC = const(0x00000008)
_I2C_FUNC_NOSTART = const(0x00000010)
_I2C_FUNC_SLAVE = const(0x00000020)
_I2C_FUNC_SMBUS_BLOCK_PROC_CALL = const(0x00008000)
_I2C_FUNC_SMBUS_QUICK = const(0x00010000)
_I2C_FUNC_SMBUS_READ_BYTE = const(0x00020000)
_I2C_FUNC_SMBUS_WRITE_BYTE = const(0x00040000)
_I2C_FUNC_SMBUS_READ_BYTE_DATA = const(0x00080000)
_I2C_FUNC_SMBUS_WRITE_BYTE_DATA = const(0x00100000)
_I2C_FUNC_SMBUS_READ_WORD_DATA = const(0x00200000)
_I2C_FUNC_SMBUS_WRITE_WORD_DATA = const(0x00400000)
_I2C_FUNC_SMBUS_PROC_CALL = const(0x00800000)
_I2C_FUNC_SMBUS_READ_BLOCK_DATA = const(0x01000000)
_I2C_FUNC_SMBUS_WRITE_BLOCK_DATA = const(0x02000000)
_I2C_FUNC_SMBUS_READ_I2C_BLOCK = const(0x04000000)
_I2C_FUNC_SMBUS_WRITE_I2C_BLOCK = const(0x08000000)

_I2C_SMBUS_BLOCK_MAX = const(32)

_i2c_smbus_data = {
    'byte': UINT8 | 0,
    'word': UINT16 | 0,
    'block': (ARRAY | 0, UINT8 | (_I2C_SMBUS_BLOCK_MAX + 2))
}

_size_of_i2c_smbus_data = sizeof(_i2c_smbus_data)

_I2C_SMBUS_READ = const(1)
_I2C_SMBUS_WRITE = const(0)

_I2C_SMBUS_QUICK = const(0)
_I2C_SMBUS_BYTE = const(1)
_I2C_SMBUS_BYTE_DATA = const(2)
_I2C_SMBUS_WORD_DATA = const(3)
_I2C_SMBUS_PROC_CALL = const(4)
_I2C_SMBUS_BLOCK_DATA = const(5)
_I2C_SMBUS_I2C_BLOCK_BROKEN = const(6)
_I2C_SMBUS_BLOCK_PROC_CALL = const(7)
_I2C_SMBUS_I2C_BLOCK_DATA = const(8)

# from linux/i2c-dev.h

_I2C_RETRIES = const(0x0701)
_I2C_TIMEOUT = const(0x0702)
_I2C_SLAVE = const(0x0703)
_I2C_SLAVE_FORCE = const(0x0706)
_I2C_TENBIT = const(0x0704)
_I2C_FUNCS = const(0x0705)
_I2C_RDWR = const(0x0707)
_I2C_PEC = const(0x0708)
_I2C_SMBUS = const(0x0720)

_i2c_smbus_ioctl_data = {
    'read_write': UINT8 | 0,
    'command': UINT8 | 1,
    'size': UINT32 | 4,
    'data': PTR | 8
}

_size_of_i2c_smbus_ioctl_data = sizeof(_i2c_smbus_ioctl_data)


class SMBus():
    """Object that represents a single I2C adapter

    Args:
        path (str): The path to the I2C device node, e.g. ``/dev/i2c-0``
    """

    def __init__(self, path):
        self._devnode = open(path, 'w+')
        self._fd = self._devnode.fileno()
        flags = bytearray(4)
        ioctl(self._fd, _I2C_FUNCS, flags, mut=True)
        flags = struct(addressof(flags), {
            'flags': UINT32  # unsigned long
        }).flags
        self._func = {
            'i2c': bool(flags & _I2C_FUNC_I2C),
            'ten_bit_addr': bool(flags & _I2C_FUNC_10BIT_ADDR),
            'protocol_mangling': bool(flags & _I2C_FUNC_PROTOCOL_MANGLING),
            'smbus_pec': bool(flags & _I2C_FUNC_SMBUS_PEC),
            'no_start': bool(flags & _I2C_FUNC_NOSTART),
            'slave': bool(flags & _I2C_FUNC_SLAVE),
            'smbus_block_proc_call': bool(flags & _I2C_FUNC_SMBUS_BLOCK_PROC_CALL),
            'smbus_quick': bool(flags & _I2C_FUNC_SMBUS_QUICK),
            'smbus_read_byte': bool(flags & _I2C_FUNC_SMBUS_READ_BYTE),
            'smbus_write_byte': bool(flags & _I2C_FUNC_SMBUS_WRITE_BYTE),
            'smbus_read_byte_data': bool(flags & _I2C_FUNC_SMBUS_READ_BYTE_DATA),
            'smbus_write_byte_data': bool(flags & _I2C_FUNC_SMBUS_WRITE_BYTE_DATA),
            'smbus_read_word_data': bool(flags & _I2C_FUNC_SMBUS_READ_WORD_DATA),
            'smbus_write_word_data': bool(flags & _I2C_FUNC_SMBUS_WRITE_WORD_DATA),
            'smbus_proc_call': bool(flags & _I2C_FUNC_SMBUS_PROC_CALL),
            'smbus_read_block_data': bool(flags & _I2C_FUNC_SMBUS_READ_BLOCK_DATA),
            'smbus_write_block_data': bool(flags & _I2C_FUNC_SMBUS_WRITE_BLOCK_DATA),
            'smbus_read_i2c_block': bool(flags & _I2C_FUNC_SMBUS_READ_I2C_BLOCK),
            'smbus_write_i2c_block': bool(flags & _I2C_FUNC_SMBUS_WRITE_I2C_BLOCK),
        }

    def _access(self, address, read_write, command, size, data):
        ioctl(self._fd, _I2C_SLAVE, address)
        b = bytearray(_size_of_i2c_smbus_ioctl_data)
        args = struct(addressof(b), _i2c_smbus_ioctl_data)
        args.read_write = read_write
        args.command = command
        args.size = size
        args.data = addressof(data)
        ioctl(self._fd, _I2C_SMBUS, args, mut=True)

    def write_quick(self, address, value):
        """Performs a `Quick Command`

        Args:
            address (7-bit): The I2C address
            value (8-bit): The value to write

        Raises:
            OSError: There was an I/O error
            RuntimeError: The I2C adapter does not support this function
        """
        if not self._func['smbus_quick']:
            raise RuntimeError('Function is not supported by the hardware')
        self._access(address, value, 0, _I2C_SMBUS_QUICK, None)

    def read_byte(self, address):
        """Performs a `Receive Byte`

        Args:
            address (7-bit): The I2C address

        Returns:
            The byte read (8-bit).

        Raises:
            OSError: There was an I/O error
            RuntimeError: The I2C adapter does not support this function
        """
        if not self._func['smbus_read_byte']:
            raise RuntimeError('Function is not supported by the hardware')
        b = bytearray(_size_of_i2c_smbus_data)
        data = struct(addressof(b), _i2c_smbus_data)
        self._access(address, _I2C_SMBUS_READ, 0, _I2C_SMBUS_BYTE,
                     data)
        return data.byte

    def write_byte(self, address, value):
        """Performs a `Send Byte`

        Args:
            address (7-bit): The I2C address
            value (8-bit): The value to write

        Raises:
            OSError: There was an I/O error
            RuntimeError: The I2C adapter does not support this function
        """
        if not self._func['smbus_write_byte']:
            raise RuntimeError('Function is not supported by the hardware')
        self._access(address, _I2C_SMBUS_WRITE, value,
                     _I2C_SMBUS_BYTE, None)

    def read_byte_data(self, address, command):
        """Performs a `Read Byte`

        Args:
            address (7-bit): The I2C address
            command (8-bit): The I2C register

        Returns:
            The value read (8-bit)

        Raises:
            OSError: There was an I/O error
            RuntimeError: The I2C adapter does not support this function
        """
        if not self._func['smbus_read_byte_data']:
            raise RuntimeError('Function is not supported by the hardware')
        b = bytearray(_size_of_i2c_smbus_data)
        data = struct(addressof(b), _i2c_smbus_data)
        self._access(address, _I2C_SMBUS_READ, command,
                     _I2C_SMBUS_BYTE_DATA, data)
        return data.byte

    def write_byte_data(self, address, command, value):
        """Performs a `Write Byte`

        Args:
            address (7-bit): The I2C address
            command (8-bit): The I2C register
            value (8-bit): The value to write

        Raises:
            OSError: There was an I/O error
            RuntimeError: The I2C adapter does not support this function
        """
        if not self._func['smbus_write_byte_data']:
            raise RuntimeError('Function is not supported by the hardware')
        b = bytearray(_size_of_i2c_smbus_data)
        data = struct(addressof(b), _i2c_smbus_data)
        data.byte = value
        self._access(address, _I2C_SMBUS_WRITE, command,
                     _I2C_SMBUS_BYTE_DATA, data)

    def read_word_data(self, address, command):
        """Performs a `Read Word`

        Args:
            address (7-bit): The I2C address
            command (8-bit): The I2C register

        Returns:
            The value read (16-bit)

        Raises:
            OSError: There was an I/O error
            RuntimeError: The I2C adapter does not support this function
        """
        if not self._func['smbus_read_word_data']:
            raise RuntimeError('Function is not supported by the hardware')
        b = bytearray(_size_of_i2c_smbus_data)
        data = struct(addressof(b), _i2c_smbus_data)
        self._access(address, _I2C_SMBUS_READ, command,
                     _I2C_SMBUS_WORD_DATA, data)
        return data.word

    def write_word_data(self, address, command, value):
        """Performs a `Write Word`

        Args:
            address (7-bit): The I2C address
            command (8-bit): The I2C register
            value (16-bit): The value to write

        Raises:
            OSError: There was an I/O error
            RuntimeError: The I2C adapter does not support this function
        """
        if not self._func['smbus_write_word_data']:
            raise RuntimeError('Function is not supported by the hardware')
        b = bytearray(_size_of_i2c_smbus_data)
        data = struct(addressof(b), _i2c_smbus_data)
        data.word = value
        self._access(address, _I2C_SMBUS_WRITE, command,
                     _I2C_SMBUS_WORD_DATA, data)

    def process_call(self, address, command, value):
        """Performs a `Process Call`

        Args:
            address (7-bit): The I2C address
            command (8-bit): The I2C register
            value (16-bit): The value to write

        Returns:
            The value read (16-bit)

        Raises:
            OSError: There was an I/O error
            RuntimeError: The I2C adapter does not support this function
        """
        if not self._func['smbus_proc_call']:
            raise RuntimeError('Function is not supported by the hardware')
        b = bytearray(_size_of_i2c_smbus_data)
        data = struct(addressof(b), _i2c_smbus_data)
        data.word = value
        self._access(address, _I2C_SMBUS_WRITE, command,
                     _I2C_SMBUS_PROC_CALL, data)
        return data.word

    def read_block_data(self, address, command):
        """Performs a `Block Read`

        Args:
            address (7-bit): The I2C address
            command (8-bit): The I2C register

        Returns:
            A list of up to 32 8-bit values that were read

        Raises:
            OSError: There was an I/O error
            RuntimeError: The I2C adapter does not support this function
        """
        if not self._func['smbus_read_block_data']:
            raise RuntimeError('Function is not supported by the hardware')
        b = bytearray(_size_of_i2c_smbus_data)
        data = struct(addressof(b), _i2c_smbus_data)
        self._access(address, _I2C_SMBUS_READ, command,
                     _I2C_SMBUS_BLOCK_DATA, data)
        return data.block[1:][:data.block[0]]

    def write_block_data(self, address, command, values):
        """Performs a `Block Write`

        Args:
            address (7-bit): The I2C address
            command (8-bit): The I2C register
            values: A list of up to 32 8-bit values to write

        Raises:
            OSError: There was an I/O error
            RuntimeError: The I2C adapter does not support this function
        """
        if not self._func['smbus_write_block_data']:
            raise RuntimeError('Function is not supported by the hardware')
        b = bytearray(_size_of_i2c_smbus_data)
        data = struct(addressof(b), _i2c_smbus_data)
        values = values[:32]
        data.block = [len(values)] + values
        self._access(address, _I2C_SMBUS_WRITE, command,
                     _I2C_SMBUS_BLOCK_DATA, data)

    def read_i2c_block_data(self, address, command, length):
        """Performs a read of arbitrary size

        Args:
            address (7-bit): The I2C address
            command (8-bit): The I2C register
            length: The number of bytes to read (max 32)

        Returns:
            A list of ``length`` values that were read

        Raises:
            OSError: There was an I/O error
            RuntimeError: The I2C adapter does not support this function
        """
        if not self._func['smbus_read_i2c_block']:
            raise RuntimeError('Function is not supported by the hardware')
        b = bytearray(_size_of_i2c_smbus_data)
        data = struct(addressof(b), _i2c_smbus_data)
        length = min(length, 32)
        data.block[0] = length
        if length == 32:
            size = _I2C_SMBUS_I2C_BLOCK_BROKEN
        else:
            size = _I2C_SMBUS_I2C_BLOCK_DATA
        self._access(address, _I2C_SMBUS_READ, command, size, data)
        return data.block[1:][:data.block[0]]

    def write_i2c_block_data(self, address, command, values):
        """Performs a write of arbitrary size

        Args:
            address (7-bit): The I2C address
            command (8-bit): The I2C register
            values: A list of up to 32 8-bit values to write

        Raises:
            OSError: There was an I/O error
            RuntimeError: The I2C adapter does not support this function
        """
        if not self._func['smbus_write_i2c_block']:
            raise RuntimeError('Function is not supported by the hardware')
        b = bytearray(_size_of_i2c_smbus_data)
        data = struct(addressof(b), _i2c_smbus_data)
        values = values[:32]
        data.block = [len(values)] + values
        self._access(address, _I2C_SMBUS_WRITE, command,
                     _I2C_SMBUS_I2C_BLOCK_BROKEN, data)

    def block_process_call(self, address, command, values):
        """Performs a `Block Process Call`

        Args:
            address (7-bit): The I2C address
            command (8-bit): The I2C register
            values: A list of up to 32 8-bit values to write

        Returns:
            A list the same size as values containing the values that were read

        Raises:
            OSError: There was an I/O error
            RuntimeError: The I2C adapter does not support this function
        """
        if not self._func['smbus_block_proc_call']:
            raise RuntimeError('Function is not supported by the hardware')
        b = bytearray(_size_of_i2c_smbus_data)
        data = struct(addressof(b), _i2c_smbus_data)
        values = values[:32]
        data.block = [len(values)] + values
        self._access(address, _I2C_SMBUS_WRITE, command,
                     _I2C_SMBUS_BLOCK_PROC_CALL, data)
        return data.block[1:][:data.block[0]]

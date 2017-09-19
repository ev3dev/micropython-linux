"""The Linux frame buffer device"""

from fcntl import ioctl

from framebuf import FrameBuffer
from framebuf import MONO_HMSB
from micropython import const
from uctypes import addressof
from uctypes import sizeof
from uctypes import struct
from uctypes import ARRAY
from uctypes import PTR
from uctypes import UINT8
from uctypes import UINT16
from uctypes import UINT32

# from linux/fb.h

_FBIOGET_VSCREENINFO = const(0x4600)
_FBIOGET_FSCREENINFO = const(0x4602)

_FB_VISUAL_MONO01 = const(0)
_FB_VISUAL_MONO10 = const(1)

_fb_fix_screeninfo = {
    'id_name': (ARRAY | 0, UINT8 | 16),
    'smem_start': UINT32 | 16,  # long
    'smem_len': UINT32 | 20,
    'type': UINT32 | 24,
    'type_aux': UINT32 | 28,
    'visual': UINT32 | 32,
    'xpanstep': UINT16 | 36,
    'ypanstep': UINT16 | 38,
    'ywrapstep': UINT16 | 40,
    'line_length': UINT32 | 44,
    'mmio_start': UINT32 | 48,  # long
    'mmio_len': UINT32 | 52,
    'accel': UINT32 | 56,
    'capabilities': UINT16 | 60,
    'reserved0': UINT16 | 62,
    'reserved1': UINT16 | 64,
}

_fb_bitfield = {
    'offset': UINT32 | 0,
    'length': UINT32 | 4,
    'msb_right': UINT32 | 8,
}

_fb_var_screeninfo = {
    'xres': UINT32 | 0,
    'yres': UINT32 | 4,
    'xres_virtual': UINT32 | 8,
    'yres_virtual': UINT32 | 12,
    'xoffset': UINT32 | 16,
    'yoffset': UINT32 | 20,
    'bits_per_pixel': UINT32 | 24,
    'grayscale': UINT32 | 28,
    'red': (32, _fb_bitfield),
    'green': (44, _fb_bitfield),
    'blue': (56, _fb_bitfield),
    'transp': (68, _fb_bitfield),
    'nonstd': UINT32 | 80,
    'activate': UINT32 | 84,
    'height': UINT32 | 88,
    'width': UINT32 | 92,
    'accel_flags': UINT32 | 96,
    'pixclock': UINT32 | 100,
    'left_margin': UINT32 | 104,
    'right_margin': UINT32 | 108,
    'upper_margin': UINT32 | 112,
    'lower_margin': UINT32 | 116,
    'hsync_len': UINT32 | 120,
    'vsync_len': UINT32 | 124,
    'sync': UINT32 | 128,
    'vmode': UINT32 | 132,
    'rotate': UINT32 | 136,
    'colorspace': UINT32 | 140,
    'reserved0': UINT32 | 144,
    'reserved1': UINT32 | 148,
    'reserved2': UINT32 | 152,
    'reserved3': UINT32 | 156,
}


class Fbdev():
    """Object that represents a framebuffer device

    Parameters:
        path (str): The path to the fbdev device node, e.g. ``/dev/fb0``
    """

    def __init__(self, path):
        self._fbdev = open(path, 'w+')
        self._fix_info_data = bytearray(sizeof(_fb_fix_screeninfo))
        fd = self._fbdev.fileno()
        ioctl(fd, _FBIOGET_FSCREENINFO, self._fix_info_data, mut=True)
        self._fix_info = struct(addressof(self._fix_info_data),
                                _fb_fix_screeninfo)
        self._var_info_data = bytearray(sizeof(_fb_var_screeninfo))
        ioctl(fd, _FBIOGET_VSCREENINFO, self._var_info_data, mut=True)
        self._var_info = struct(addressof(self._var_info_data),
                                _fb_var_screeninfo)
        self._fb_data = {}

    @property
    def width(self):
        """Gets the width of the display in pixels"""
        return self._var_info.xres_virtual

    @property
    def height(self):
        """Gets the height of the display in pixels"""
        return self._var_info.yres_virtual

    @property
    def bpp(self):
        """Gets the color depth of the screen in bits per pixel"""
        return self._var_info.bits_per_pixel

    def update(self, data):
        """Updates the display with the framebuffer data.

        Parameters:
            data: Must be bytearray returned by :py:meth:`framebuffer`.
        """
        self._fbdev.seek(0)
        self._fbdev.write(data)

    def framebuffer(self):
        """Creates a new frame buffer for the display

        Returns:
            A ``framebuf.FrameBuffer`` object used for drawing and a bytearray
            object to be passed to :py:meth:`update`
        """
        data = bytearray(self._fix_info.line_length * self.height)
        if self._fix_info.visual in (_FB_VISUAL_MONO01,
                                     _FB_VISUAL_MONO10):
            fmt = MONO_HMSB
        fbuf = FrameBuffer(data, self.width, self.height, fmt,
                           self._fix_info.line_length // self.bpp * 8)
        return fbuf, data

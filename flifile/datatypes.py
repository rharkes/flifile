from enum import Enum

import numpy as np


class Format(Enum):
    Mono8 = 1
    Mono10 = 2
    Mono10p = 3
    Mono10pmsb = 4
    Mono12 = 5
    Mono12p = 6
    Mono12pmsb = 7
    Mono12Packed = 8  # GigE 12 packing
    Mono14 = 9
    Mono14p = 10
    Mono16 = 11
    BGR8 = 12
    BGR8Packed = 13  # GigE name for BGR8
    RGB8 = 14
    RGB8Packed = 15  # GigE name for RGB8
    BayerBG8 = 16
    BayerBG12 = 17
    BayerBG12p = 18
    BayerBG12pmsb = 19
    BayerBG16 = 20
    BayerGB8 = 21
    BayerGB12 = 22
    BayerGB12p = 23
    BayerGB12pmsb = 24
    BayerGB16 = 25
    BayerGR8 = 26
    BayerGR10 = 27
    BayerGR12 = 28
    BayerGR12p = 29
    BayerGR12pmsb = 30
    BayerGR16 = 31
    BayerRG8 = 32
    BayerRG10 = 33
    BayerRG12 = 34
    BayerRG12p = 35
    BayerRG12pmsb = 36
    BayerRG12Packed = 37
    BayerRG16 = 38
    YUV411Packed = 39
    YUV411_8_UYYVYY = 40
    YCbCr422_8 = 41
    YUV422Packed = 42
    YUV444Packed = 43


class PixelFormat:
    def __init__(self, pixelFormat: str):
        self.pixelFormat = self.setFormat(pixelFormat)
        self.bitdepth = self.setBitDepth(self.pixelFormat)
        self.channels = self.setChannels(self.pixelFormat)
        self.numpytype = self.setNumpyType(self.pixelFormat)
        self.packing = self.setPacking(self.pixelFormat)
        self.pixelsizebits = self.setSizeBits(self.pixelFormat)

    def setFormat(self, pixelFormat: str) -> Format:
        if pixelFormat == "Mono8":
            return Format.Mono8
        elif pixelFormat == "Mono10":
            return Format.Mono10
        elif pixelFormat == "Mono10p":
            return Format.Mono10p
        elif pixelFormat == "Mono10pmsb":
            return Format.Mono10pmsb
        elif pixelFormat == "Mono12":
            return Format.Mono12
        elif pixelFormat == "Mono12p":
            return Format.Mono12p
        elif pixelFormat == "Mono12pmsb":
            return Format.Mono12pmsb
        elif pixelFormat == "Mono12Packed":
            return Format.Mono12Packed
        elif pixelFormat == "Mono14":
            return Format.Mono14
        elif pixelFormat == "Mono14p":
            return Format.Mono14p
        elif pixelFormat == "Mono16":
            return Format.Mono16
        elif pixelFormat == "BGR8":
            return Format.BGR8
        elif pixelFormat == "BGR8Packed":
            return Format.BGR8Packed
        elif pixelFormat == "RGB8":
            return Format.RGB8
        elif pixelFormat == "RGB8Packed":
            return Format.RGB8Packed
        elif pixelFormat == "BayerBG8":
            return Format.BayerBG8
        elif pixelFormat == "BayerBG12":
            return Format.BayerBG12
        elif pixelFormat == "BayerBG12p":
            return Format.BayerBG12p
        elif pixelFormat == "BayerBG12pmsb":
            return Format.BayerBG12pmsb
        elif pixelFormat == "BayerBG16":
            return Format.BayerBG16
        elif pixelFormat == "BayerGB8":
            return Format.BayerGB8
        elif pixelFormat == "BayerGB12":
            return Format.BayerGB12
        elif pixelFormat == "BayerGB12p":
            return Format.BayerGB12p
        elif pixelFormat == "BayerGB12pmsb":
            return Format.BayerGB12pmsb
        elif pixelFormat == "BayerGB16":
            return Format.BayerGB16
        elif pixelFormat == "BayerGR8":
            return Format.BayerGR8
        elif pixelFormat == "BayerGR10":
            return Format.BayerGR10
        elif pixelFormat == "BayerGR12":
            return Format.BayerGR12
        elif pixelFormat == "BayerGR12p":
            return Format.BayerGR12p
        elif pixelFormat == "BayerGR12pmsb":
            return Format.BayerGR12pmsb
        elif pixelFormat == "BayerGR16":
            return Format.BayerGR16
        elif pixelFormat == "BayerRG8":
            return Format.BayerRG8
        elif pixelFormat == "BayerRG10":
            return Format.BayerRG10
        elif pixelFormat == "BayerRG12":
            return Format.BayerRG12
        elif pixelFormat == "BayerRG12p":
            return Format.BayerRG12p
        elif pixelFormat == "BayerRG12pmsb":
            return Format.BayerRG12pmsb
        elif pixelFormat == "BayerRG12Packed":
            return Format.BayerRG12Packed
        elif pixelFormat == "BayerRG16":
            return Format.BayerRG16
        elif pixelFormat == "YUV411Packed":
            return Format.YUV411Packed
        elif pixelFormat == "YUV411_8_UYYVYY":
            return Format.YUV411_8_UYYVYY
        elif pixelFormat == "YCbCr422_8":
            return Format.YCbCr422_8
        elif pixelFormat == "YUV422Packed":
            return Format.YUV422Packed
        elif pixelFormat == "YUV444Packed":
            return Format.YUV444Packed

    def setBitDepth(self, format: Format):
        if format in [
            Format.Mono8,
            Format.BGR8,
            Format.RGB8,
            Format.BayerGB8,
            Format.BayerRG8,
            Format.BayerGR8,
            Format.BayerBG8,
            Format.YUV411Packed,
            Format.YUV422Packed,
            Format.YUV411_8_UYYVYY,
            Format.YUV444Packed,
            Format.YCbCr422_8,
            Format.BGR8Packed,
            Format.RGB8Packed,
        ]:
            return 8
        if format in [
            Format.Mono10,
            Format.Mono10p,
            Format.BayerGR10,
            Format.Mono10pmsb,
            Format.BayerRG10,
        ]:
            return 10
        if format in [
            Format.Mono12,
            Format.Mono12p,
            Format.Mono12Packed,
            Format.Mono12pmsb,
            Format.BayerBG12,
            Format.BayerBG12p,
            Format.BayerBG12pmsb,
            Format.BayerGB12,
            Format.BayerGB12p,
            Format.BayerGB12pmsb,
            Format.BayerGR12,
            Format.BayerGR12p,
            Format.BayerGR12pmsb,
            Format.BayerRG12,
            Format.BayerRG12p,
            Format.BayerRG12pmsb,
            Format.BayerRG12Packed,
        ]:
            return 12
        if format in [Format.Mono14, Format.Mono14p]:
            return 14
        if format in [
            Format.BayerBG16,
            Format.BayerGB16,
            Format.BayerGR16,
            Format.BayerRG16,
            Format.Mono16,
        ]:
            return 16

    def setChannels(self, format: Format):
        if format in [
            Format.Mono8,
            Format.BayerGB8,
            Format.BayerRG8,
            Format.BayerGR8,
            Format.BayerBG8,
            Format.Mono10,
            Format.Mono10p,
            Format.BayerGR10,
            Format.Mono10pmsb,
            Format.BayerRG10,
            Format.Mono12,
            Format.Mono12p,
            Format.Mono12Packed,
            Format.Mono12pmsb,
            Format.BayerBG12,
            Format.BayerBG12p,
            Format.BayerBG12pmsb,
            Format.BayerGB12,
            Format.BayerGB12p,
            Format.BayerGB12pmsb,
            Format.BayerGR12,
            Format.BayerGR12p,
            Format.BayerGR12pmsb,
            Format.BayerRG12,
            Format.BayerRG12p,
            Format.BayerRG12pmsb,
            Format.BayerRG12Packed,
            Format.Mono14,
            Format.Mono14p,
            Format.BayerBG16,
            Format.BayerGB16,
            Format.BayerGR16,
            Format.BayerRG16,
            Format.Mono16,
        ]:
            return 1
        if format in [
            Format.BGR8,
            Format.RGB8,
            Format.YUV411Packed,
            Format.YUV422Packed,
            Format.YUV411_8_UYYVYY,
            Format.YUV444Packed,
            Format.YCbCr422_8,
            Format.BGR8Packed,
            Format.RGB8Packed,
        ]:
            return 3

    def setNumpyType(self, format: Format):
        if format in [
            Format.BayerBG16,
            Format.BayerGB16,
            Format.BayerRG10,
            Format.BayerRG12,
            Format.BayerRG16,
            Format.Mono10,
            Format.Mono12,
            Format.Mono14,
            Format.Mono16,
            Format.BayerBG12,
            Format.BayerGB12,
        ]:
            return (np.uint16, 16)
        if format in [Format.Mono10p, Format.Mono10pmsb]:
            return (np.uint16, 10)
        if format in [
            Format.BayerBG12p,
            Format.BayerBG12pmsb,
            Format.BayerGB12p,
            Format.BayerGB12pmsb,
            Format.BayerRG12p,
            Format.BayerRG12pmsb,
            Format.BayerRG12Packed,
            Format.Mono12p,
            Format.Mono12pmsb,
            Format.Mono12Packed,
        ]:
            return (np.uint16, 12)
        if format in [
            Format.Mono8,
            Format.BayerBG8,
            Format.BayerGB8,
            Format.BGR8,
            Format.BGR8Packed,
            Format.RGB8,
            Format.RGB8Packed,
            Format.YUV422Packed,
            Format.YUV411_8_UYYVYY,
            Format.YUV411Packed,
            Format.YUV444Packed,
            Format.YCbCr422_8,
        ]:
            return (np.uint8, 8)
        if format in [Format.Mono14p]:
            return (np.uint16, 14)

    def setPacking(self, format: Format):
        if format in [
            Format.Mono10p,
            Format.Mono12p,
            Format.Mono14p,
            Format.BayerBG12p,
            Format.BayerGB12p,
            Format.BayerRG12p,
        ]:
            return "lsb"
        elif format in [
            Format.BayerRG12pmsb,
            Format.BayerBG12pmsb,
            Format.BayerGB12pmsb,
            Format.Mono10pmsb,
            Format.Mono12pmsb,
        ]:
            return "msb"
        elif format in [Format.YUV411Packed, Format.YUV411_8_UYYVYY]:
            return "YUV411"
        elif format in [Format.YUV422Packed, Format.YCbCr422_8]:
            return "YUV422"
        else:
            return "none"

    def setSizeBits(self, format: Format):
        if format in [
            Format.BGR8,
            Format.BGR8Packed,
            Format.RGB8,
            Format.RGB8Packed,
            Format.YUV444Packed,
        ]:
            return 24
        if format in [
            Format.BayerBG12,
            Format.BayerBG16,
            Format.BayerGB16,
            Format.BayerGB12,
            Format.BayerGR10,
            Format.BayerRG10,
            Format.BayerGR12,
            Format.BayerRG12,
            Format.Mono10,
            Format.Mono12,
            Format.Mono12,
            Format.Mono14,
            Format.Mono16,
            Format.BayerGR16,
            Format.BayerRG16,
            Format.YCbCr422_8,
            Format.YUV422Packed,
        ]:
            return 16
        if format in [Format.Mono14p]:
            return 14
        if format in [
            Format.BayerBG12p,
            Format.BayerBG12pmsb,
            Format.BayerGB12p,
            Format.BayerGB12pmsb,
            Format.BayerGR12p,
            Format.BayerGR12pmsb,
            Format.BayerRG12p,
            Format.BayerRG12pmsb,
            Format.BayerRG12Packed,
            Format.Mono12p,
            Format.Mono12pmsb,
            Format.Mono12Packed,
            Format.YUV411Packed,
            Format.YUV411_8_UYYVYY,
        ]:
            return 12
        if format in [Format.Mono10p, Format.Mono10pmsb]:
            return 10
        if format in [
            Format.BayerBG8,
            Format.BayerGB8,
            Format.BayerGR8,
            Format.BayerRG8,
            Format.Mono8,
        ]:
            return 8

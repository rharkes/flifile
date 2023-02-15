"""
Python support for the Lambert Instruments .fli file

(c) R.Harkes NKI

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""
import os
from pathlib import Path
from collections import deque
import numpy as np
import zlib
import logging
from .datatypes import *


class FliFile:
    """
    Lambert Instruments .fli file
    Contains:
    - header: dictionary with all header entries
    - path: pathlib.Path to the file
    Hidden:
    - _bg: to store the background
    - _datastart: pointer to the start of the data
    - _di: dictionary with data information based on the header
    """

    def __init__(self, filepath) -> None:
        # open file
        if isinstance(filepath, str):
            self.path = Path(filepath)
        elif isinstance(filepath, Path):
            self.path = filepath
        else:
            raise ValueError("not a valid filename")
        if self.path.suffix != ".fli":
            raise ValueError("Not a valid extension")
        fid = self.path.open(mode="rb")
        self.log = logging.getLogger("flifile")
        self.header = {}
        self._bg = np.array([])  # type:np.ndarray
        self.pixelFormat = PixelFormat("Mono8")  # type:Datatypes
        path = Path(filepath)
        self.version = 1.0
        self.header = self.readheader(path)
        if self.version == 2.0:
            self._di = self._get_data_info2()
        else:
            self._di = self._get_data_info()

    def readheadersize(self, f) -> int:
        queue = deque(b"     ", maxlen=5)
        stop = deque([b"{", b"E", b"N", b"D", b"}"], maxlen=5)
        while True:
            byte = f.read(1)
            queue.append(byte)
            if queue == stop:
                return f.tell()

    def readheader(self, file) -> dict:
        with file.open(mode="rb") as f:
            s = self.readheadersize(f)
            f.seek(0)
            h = self.parseheader(f.read(s))
            h["datastart"] = s
            return h

    def parseheader(self, headerstring) -> dict:
        chapter = "DEFAULT"
        section = "DEFAULT"
        header = {}
        if b"version = 2.0" in headerstring[:32]:
            self.version = 2.0
        for line in headerstring.split(b"\n"):
            if line.startswith(b"{"):
                chapter = line[1:-1].decode("utf-8")
            if line.startswith(b"["):
                section = line[1:-1].decode("utf-8")
            else:
                kvp = line.split(b"=")
                if len(kvp) != 2:
                    continue
                if chapter not in header.keys():
                    header[chapter] = {}
                if section not in header[chapter]:
                    header[chapter][section] = {}
                header[chapter][section][kvp[0].decode("utf-8").strip()] = (
                    kvp[1].decode("utf-8").strip()
                )
        return header

    def getdata(
        self, subtractbackground: bool = True, squeeze: bool = True
    ) -> np.array:
        """
        Returns the data from the .fli file. If squeeze is False the data is retured with these dimensions:
        frequency,time,phase,z,y,x,channel
        :param subtractbackground: Subtract the background from the image data
        :param squeeze: Return data without singleton dimensions in x,y,ph,t,z,fr,c order
        :return: numpy.ndarray
        """
        if not self._di["BG_present"]:
            subtractbackground = False
        datasize = np.prod(self._di["IMSize"], dtype=np.uint64)
        if self._di["Compression"] > 0:
            fid = self.path.open(mode="rb")
            fid.seek(self._datastart)
            dcmp = zlib.decompressobj(32 + zlib.MAX_WBITS)  # skip the GZIP header
            data = np.frombuffer(
                dcmp.decompress(fid.read()), dtype=self._di["IMType"][0]
            )
            bg = data[datasize:]
            self._bg = bg.reshape(self._di["BGSize"][::-1])
            data = data[:datasize]
        else:
            data = self._get_data_from_file(
                offset=self.header["datastart"],
                datatype=self._di["IMType"],
                datasize=datasize,
            )

        if self._di["IMType"][1] == 12:  # 12 bit per pixel packed per 2 in 3 bytes
            data = self._convert_12_bit(
                data, datatype=self._di["IMType"], packingtype=self._di["IMPacking"]
            )
        data = data.reshape(self._di["IMSize"][::-1])
        if subtractbackground:
            self._bg = self.getbackground(squeeze=False)
            mask = np.where(data < self._bg)
            data = data - self._bg
            data[mask] = 0
        if squeeze:
            data = np.squeeze(data.transpose((5, 4, 2, 1, 3, 0, 6)))  # x,y,ph,t,z,fr,c

        return data

    def getbackground(self, squeeze: bool = True) -> np.ndarray:
        """
        Returns the background data from the .fli file. If squeeze is False the data is retured with these dimensions:
        frequency,time,phase,z,y,x,channel
        :param squeeze: Return data without singleton dimensions in x,y,ph,t,z,fr,c order
        :return: numpy.ndarray
        """
        if not self._di["BG_present"]:
            self.log.warning("WARNING: No background present in file")
            return np.array([])
        if self._bg is not None:
            data = self._bg
        else:
            if self._di["Compression"] > 0:
                self.log.warning(
                    "WARNING: Getting background before getting data is inefficient in compressed files."
                )
                self.getdata(subtractbackground=True, squeeze=False)
                data = self._bg
            else:
                offset = np.uint64(self._datastart)
                offset = (
                    offset
                    + (
                        np.uint64(self._di["IMType"][1])
                        * np.prod(self._di["IMSize"], dtype=np.uint64)
                    )
                    / 8
                )
                datasize = np.prod(self._di["BGSize"], dtype=np.uint64)
                data = self._get_data_from_file(
                    offset=int(offset), datatype=self._di["BGType"], datasize=datasize
                )
                if (
                    self._di["BGType"][1] == 12
                ):  # 12 bit per pixel packed per 2 in 3 bytes
                    data = self._convert_12_bit(
                        data,
                        datatype=self._di["BGType"],
                        packingtype=self._di["BGPacking"],
                    )
                data = data.reshape(self._di["BGSize"][::-1])
        if squeeze:
            return np.squeeze(data.transpose((5, 4, 2, 1, 3, 0, 6)))  # x,y,ph,t,z,fr,c
        else:
            return data

    def getframe(
        self,
        channel: int = 0,
        z: int = 0,
        phase: int = 0,
        timestamp: int = 0,
        frequency: int = 0,
        subtractbackground: bool = True,
        squeeze: bool = True,
    ) -> np.ndarray:
        """
        -NOT IMPLEMENTED-
        Get a single frame from the .fli file
        :param squeeze:
        :param subtractbackground:
        :param timestamp:
        :param channel:
        :param z:
        :param phase:
        :param frequency:
        :return:
        """
        # check input
        if channel > (self._di["IMSize"][0] - 1):
            self.log.warning("WARNING: Channel out of range")
            return np.array([])
        if z > (self._di["IMSize"][3] - 1):
            self.log.warning("WARNING: Z out of range")
            return np.array([])
        if phase > (self._di["IMSize"][4] - 1):
            self.log.warning("WARNING: Phase out of range")
            return np.array([])
        if timestamp > (self._di["IMSize"][5] - 1):
            self.log.warning("WARNING: Timestamp out of range")
            return np.array([])
        if frequency > (self._di["IMSize"][6] - 1):
            self.log.warning("WARNING: Frequency out of range")
            return np.array([])
        # get pointer
        return np.array([])
        # get data

    @staticmethod
    def _convert_12_bit(data, datatype, packingtype="lsb"):
        datasize = int((data.size / 3) * 2)
        byte1 = data[0::3]  # contains the 8 least-significant bits of the even pixels
        byte2 = data[
            1::3
        ]  # contains the 4 most-significant bits of the even pixels and 4 least-significant of the odd pixels
        byte3 = data[2::3]  # contains the 8 least-significant bits of the odd pixels
        data = np.zeros(datasize, dtype=datatype[0])
        if packingtype == "lsb":
            data[0::2] = byte1.astype(np.uint16) + np.left_shift(
                np.left_shift(byte2, 4).astype(np.uint8).astype(np.uint16), 4
            )
            data[1::2] = np.left_shift(byte3.astype(np.uint16), 4) + np.right_shift(
                byte2, 4
            ).astype(np.uint8)
        elif packingtype == "msb":
            data[0::2] = np.left_shift(byte1.astype(np.uint16), 4) + np.right_shift(
                byte2, 4
            ).astype(np.uint8)
            data[1::2] = np.left_shift(
                np.left_shift(byte2, 4).astype(np.uint8).astype(np.uint16), 4
            ) + byte3.astype(np.uint16)
        else:
            raise ValueError("Data has no valid packing type")
        return data

    def _get_data_from_file(self, offset, datatype, datasize):
        if datatype[1] == 12:  # 12 bit per pixel packed per 2 in 3 bytes
            count = int(3 * (datasize / 2))
            dtype = np.uint8
        else:
            count = int(datasize)
            dtype = datatype[0]
        return np.fromfile(self.path, offset=offset, dtype=dtype, count=count)

    def _get_data_info(self):
        type_dict = {
            "UINT8": (np.uint8, 8),
            "UINT16": (np.uint16, 16),
            "UINT12": (np.uint16, 12),
            "UINT32": (np.uint32, 32),
            "INT8": (np.int8, 8),
            "INT16": (np.int16, 16),
            "INT32": (np.int32, 32),
            "REAL32": (np.float32, 32),
            "REAL64": (np.float64, 64),
        }
        if "FLIMIMAGE" not in self.header:
            raise KeyError(f"FLIMIMAGE not found in header of {self}")
        if "LAYOUT" not in self.header["FLIMIMAGE"]:
            raise KeyError(f"LAYOUT not found in header of {self}")
        self.datatype = type_dict[
            self.header["FLIMIMAGE"]["LAYOUT"].get("datatype", "UINT8")
        ]
        # read data layout. Default for each dimension is 1. Default datatype is UINT8. Default packing is lsb.
        data_info = {
            "IMSize": (
                int(self.header["FLIMIMAGE"]["LAYOUT"].get("channels", 1)),
                int(self.header["FLIMIMAGE"]["LAYOUT"].get("x", 1)),
                int(self.header["FLIMIMAGE"]["LAYOUT"].get("y", 1)),
                int(self.header["FLIMIMAGE"]["LAYOUT"].get("z", 1)),
                int(self.header["FLIMIMAGE"]["LAYOUT"].get("phases", 1)),
                int(self.header["FLIMIMAGE"]["LAYOUT"].get("timestamps", 1)),
                int(self.header["FLIMIMAGE"]["LAYOUT"].get("frequencies", 1)),
            ),
            "IMType": type_dict[
                self.header["FLIMIMAGE"]["LAYOUT"].get("datatype", "UINT8")
            ],
            "IMPacking": self.header["FLIMIMAGE"]["LAYOUT"].get("packing", "lsb"),
        }

        if "hasDarkImage" in self.header["FLIMIMAGE"]["LAYOUT"]:
            data_info["BG_present"] = bool(
                int(self.header["FLIMIMAGE"]["LAYOUT"].get("hasDarkImage", 0))
            )
            data_info["BGSize"] = list(data_info["IMSize"])
            d = [0, 3, 4, 5]
            for dim in d:
                data_info["BGSize"][dim] = 1
            data_info["BGSize"] = tuple(data_info["BGSize"])
            data_info["BGType"] = data_info["IMType"]
            data_info["BGPacking"] = data_info["IMPacking"]

        if "BACKGROUND" in self.header["FLIMIMAGE"]:
            data_info["BG_present"] = True
            data_info["BGSize"] = (
                int(self.header["FLIMIMAGE"]["BACKGROUND"].get("channels", 1)),
                int(self.header["FLIMIMAGE"]["BACKGROUND"].get("x", 1)),
                int(self.header["FLIMIMAGE"]["BACKGROUND"].get("y", 1)),
                int(self.header["FLIMIMAGE"]["BACKGROUND"].get("z", 1)),
                int(self.header["FLIMIMAGE"]["BACKGROUND"].get("phases", 1)),
                int(self.header["FLIMIMAGE"]["BACKGROUND"].get("timestamps", 1)),
                int(self.header["FLIMIMAGE"]["BACKGROUND"].get("frequencies", 1)),
            )
            data_info["BGType"] = type_dict[
                self.header["FLIMIMAGE"]["BACKGROUND"].get("datatype", "UINT8")
            ]

        if "INFO" not in self.header["FLIMIMAGE"]:
            self.log.warning("WARNING: INFO not found in Header")
            data_info["Compression"] = 0
            return data_info
        data_info["Compression"] = int(
            self.header["FLIMIMAGE"]["INFO"].get("compression", 0)
        )
        return data_info

    def _get_data_info2(self):
        if "FLIMIMAGE" not in self.header:
            raise KeyError(f"FLIMIMAGE not found in header of {self}")
        data_info = {}
        data_info["IMSize"] = [1, 1, 1, 1, 1, 1, 1]
        data_info["IMSize"][0] = len(
            self.header["FLIMIMAGE"]["DEFAULT"].get("channels", "{}").split(",")
        )
        data_info["IMSize"][1] = int(self.header["FLIMIMAGE"]["DEFAULT"].get("x", 1))
        data_info["IMSize"][2] = int(self.header["FLIMIMAGE"]["DEFAULT"].get("y", 1))
        data_info["IMSize"][3] = int(self.header["FLIMIMAGE"]["DEFAULT"].get("z", 1))
        data_info["IMSize"][4] = len(
            self.header["FLIMIMAGE"]["DEFAULT"].get("phases", "[]").split(",")
        )
        data_info["IMSize"][5] = int(
            self.header["FLIMIMAGE"]["DEFAULT"].get("numberOfFrames", 1)
        )
        data_info["IMSize"][6] = len(
            self.header["FLIMIMAGE"]["DEFAULT"].get("frequencies", "[]").split(",")
        )
        self.pixelFormat = PixelFormat(
            self.header["FLIMIMAGE"]["DEFAULT"].get("pixelFormat", "Mono8")
        )
        data_info["IMType"] = self.pixelFormat.numpytype
        data_info["IMPacking"] = self.pixelFormat.packing
        nrOfDarkImages = int(
            self.header["FLIMIMAGE"]["DEFAULT"].get("numberOfDarkImages", 0)
        )
        data_info["BG_present"] = nrOfDarkImages > 0
        data_info["BGSize"] = list(data_info["IMSize"])
        data_info["BGType"] = data_info["IMType"]
        data_info["BGPacking"] = data_info["IMPacking"]
        data_info["Compression"] = 0
        return data_info

    def __str__(self):
        return self.path.name

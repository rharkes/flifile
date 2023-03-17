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
from typing import Any, Union
import numpy as np
import zlib
import logging
from .datatypes import Packing, Datatypes, np_dtypes
from .readheader import readheader, telldatainfo


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

    def __init__(self, filepath: Union[str, os.PathLike[Any]]) -> None:
        # open file
        if isinstance(filepath, str):
            self.path = Path(filepath)
        elif isinstance(filepath, Path):
            self.path = filepath
        else:
            raise ValueError("not a valid filename")
        if self.path.suffix != ".fli":
            raise ValueError("Not a valid extension")
        self.log = logging.getLogger("flifile")
        self.header, self._datastart = readheader(self.path)
        self.datainfo = telldatainfo(self.header)
        self._bg = np.array([], dtype=self.datainfo.BGType.nptype)

    def getdata(
        self, subtractbackground: bool = True, squeeze: bool = True
    ) -> np.ndarray[Any, np.dtype[np_dtypes]]:
        """
        Returns the data from the .fli file. If squeeze is False the data is retured with these dimensions:
        frequency,time,phase,z,y,x,channel
        :param subtractbackground: Subtract the background from the image data
        :param squeeze: Return data without singleton dimensions in x,y,ph,t,z,fr,c order
        :return: numpy.ndarray
        """
        if not self.datainfo.BG_present:
            subtractbackground = False
        datasize = int(np.prod(self.datainfo.IMSize, dtype=np.uint64))
        if self.datainfo.Compression > 0:
            fid = self.path.open(mode="rb")
            fid.seek(self._datastart)
            dcmp = zlib.decompressobj(32 + zlib.MAX_WBITS)  # skip the GZIP header
            data = np.frombuffer(
                dcmp.decompress(fid.read()), dtype=self.datainfo.IMType.nptype
            )
            bg = data[datasize:]
            self._bg = bg.reshape(self.datainfo.BGSize[::-1])
            data = data[:datasize]
        else:
            data = self._get_data_from_file(
                offset=self._datastart,
                datatype=self.datainfo.IMType,
                datasize=datasize,
            )

        if self.datainfo.IMType.bits == 12:  # 12 bit per pixel packed per 2 in 3 bytes
            data = self._convert_12_bit(data, datatype=self.datainfo.IMType)
        data = data.reshape(self.datainfo.IMSize[::-1])
        if subtractbackground:
            self._bg = self.getbackground(squeeze=False)
            mask = np.where(data < self._bg)
            data = data - self._bg
            data[mask] = 0
        if squeeze:
            data = np.squeeze(data.transpose((5, 4, 2, 1, 3, 0, 6)))  # x,y,ph,t,z,fr,c

        return data

    def getbackground(
        self, squeeze: bool = True
    ) -> np.ndarray[Any, np.dtype[np_dtypes]]:
        """
        Returns the background data from the .fli file. If squeeze is False the data is retured with these dimensions:
        frequency,time,phase,z,y,x,channel
        :param squeeze: Return data without singleton dimensions in x,y,ph,t,z,fr,c order
        :return: numpy.ndarray
        """
        if not self.datainfo.BG_present:
            self.log.warning("WARNING: No background present in file")
            return np.array([])
        if self._bg.size == 0:
            data = self._bg
        else:
            if self.datainfo.Compression > 0:
                self.log.warning(
                    "WARNING: Getting background before getting data is inefficient in compressed files."
                )
                self.getdata(subtractbackground=True, squeeze=False)
                data = self._bg
            else:
                offset = (
                    self._datastart
                    + (
                        self.datainfo.IMType.bits
                        * int(np.prod(self.datainfo.IMSize, dtype=np.uint64))
                    )
                    / 8
                )
                datasize = int(np.prod(self.datainfo.BGSize, dtype=np.uint64))
                data = self._get_data_from_file(
                    offset=int(offset), datatype=self.datainfo.BGType, datasize=datasize
                )
                if (
                    self.datainfo.BGType.bits == 12
                ):  # 12 bit per pixel packed per 2 in 3 bytes
                    data = self._convert_12_bit(
                        data,
                        datatype=self.datainfo.BGType,
                    )
                data = data.reshape(self.datainfo.BGSize[::-1])
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
    ) -> np.ndarray[Any, np.dtype[np_dtypes]]:
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
        if channel > (self.datainfo.IMSize[0] - 1):
            self.log.warning("WARNING: Channel out of range")
            return np.array([])
        if z > (self.datainfo.IMSize[3] - 1):
            self.log.warning("WARNING: Z out of range")
            return np.array([])
        if phase > (self.datainfo.IMSize[4] - 1):
            self.log.warning("WARNING: Phase out of range")
            return np.array([])
        if timestamp > (self.datainfo.IMSize[5] - 1):
            self.log.warning("WARNING: Timestamp out of range")
            return np.array([])
        if frequency > (self.datainfo.IMSize[6] - 1):
            self.log.warning("WARNING: Frequency out of range")
            return np.array([])
        # get pointer
        return np.array([])
        # get data

    @staticmethod
    def _convert_12_bit(
        data: np.ndarray[Any, np.dtype[np_dtypes]], datatype: Datatypes
    ) -> np.ndarray[Any, np.dtype[np_dtypes]]:
        datasize = int((data.size / 3) * 2)
        byte1 = data[0::3]  # contains the 8 least-significant bits of the even pixels
        byte2 = data[
            1::3
        ]  # contains the 4 most-significant bits of the even pixels and 4 least-significant of the odd pixels
        byte3 = data[2::3]  # contains the 8 least-significant bits of the odd pixels
        data = np.zeros(datasize, dtype=datatype.nptype)
        if datatype.packing == Packing.LSB:
            data[0::2] = byte1.astype(np.uint16) + np.left_shift(
                np.left_shift(byte2, 4).astype(np.uint8).astype(np.uint16), 4
            )
            data[1::2] = np.left_shift(byte3.astype(np.uint16), 4) + np.right_shift(
                byte2, 4
            ).astype(np.uint8)
        elif datatype.packing == Packing.MSB:
            data[0::2] = np.left_shift(byte1.astype(np.uint16), 4) + np.right_shift(
                byte2, 4
            ).astype(np.uint8)
            data[1::2] = np.left_shift(
                np.left_shift(byte2, 4).astype(np.uint8).astype(np.uint16), 4
            ) + byte3.astype(np.uint16)
        else:
            raise ValueError("Data has no valid packing type")
        return data

    def _get_data_from_file(
        self, offset: int, datatype: Datatypes, datasize: int
    ) -> np.ndarray[Any, np.dtype[np_dtypes]]:
        if datatype.bits == 12:  # 12 bit per pixel packed per 2 in 3 bytes
            count = int(3 * (datasize / 2))
        else:
            count = datasize
        return np.fromfile(self.path, offset=offset, dtype=datatype.nptype, count=count)

    def __str__(self) -> str:
        return self.path.name

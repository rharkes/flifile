"""
Python support for the the Lambert Instruments .fli file
Version 1.2.0

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
from pathlib import Path
import numpy as np
import zlib


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

    def __init__(self, filepath):
        # open file
        if isinstance(filepath, str):
            self.path = Path(filepath)
        elif isinstance(filepath, Path):
            self.path = filepath
        else:
            raise ValueError('not a valid filename')
        if self.path.suffix != '.fli':
            raise ValueError('Not a valid extension')
        fid = self.path.open(mode='rb')
        self.header = {}
        self._bg = None
        # get header information
        # Lines in the header are {Chapter} or [section] or parameter = value
        mode = 0  # default mode, reading parameter
        chapter = []
        current_chapter = ''
        section = []
        current_section = ''
        parameter = []
        current_parameter = ''
        value = []
        pv_pairs = {}
        sections = {}
        while True:
            byte = fid.read(1)
            if byte == b'{':
                if current_chapter:  # there is a chapter finished
                    sections[current_section] = pv_pairs  # add last pv_pairs to the sections
                    pv_pairs = {}
                    current_parameter = ''
                    self.header[current_chapter] = sections  # add sections to the header
                    sections = {}
                    current_section = ''
                mode = 1  # reading chapter
                chapter = []
                continue
            if byte == b'}':
                mode = 0  # end of chapter/section
                current_chapter = ''.join(chapter).strip()
                chapter = []
                if current_chapter == 'END':
                    self._datastart = fid.tell()
                    break
                continue
            if byte == b']':
                mode = 0  # end of chapter/section
                current_section = ''.join(section).strip()
                section = []
                continue
            if byte == b'[':
                mode = 2  # reading section
                if current_section:
                    sections[current_section] = pv_pairs
                    pv_pairs = {}
                continue
            if byte == b'=':
                current_parameter = ''.join(parameter).strip()
                parameter = []
                mode = 3  # reading value
                continue
            if byte == b'\n' or byte == b'\r':
                if mode == 3:  # finished reading value. Must put with the parameter
                    pv_pairs[current_parameter] = ''.join(value).strip()
                    value = []
                mode = 0
                continue
            # a valid character to read
            if mode == 0:
                parameter.append(byte.decode("utf-8"))
            if mode == 1:
                chapter.append(byte.decode("utf-8"))
            if mode == 2:
                section.append(byte.decode("utf-8"))
            if mode == 3:
                value.append(byte.decode("utf-8"))
        fid.close()
        self._di = self._get_data_info()

    def getdata(self, subtractbackground=True, squeeze=True):
        """
        Returns the data from the .fli file. If squeeze is False the data is retured with these dimensions:
        frequency,time,phase,z,y,x,channel
        :param subtractbackground: Subtract the background from the image data
        :param squeeze: Return data without singleton dimensions in x,y,ph,t,z,fr,c order
        :return: numpy.ndarray
        """
        if not self._di['BG_present']:
            subtractbackground = False
        datasize = np.prod(self._di['IMSize'], dtype=np.uint64)
        if self._di['Compression'] > 0:
            fid = self.path.open(mode='rb')
            fid.seek(self._datastart)
            dcmp = zlib.decompressobj(32 + zlib.MAX_WBITS)  # skip the GZIP header
            data = np.frombuffer(dcmp.decompress(fid.read()), dtype=self._di['IMType'][0])
            bg = data[datasize:]
            self._bg = bg.reshape(self._di['BGSize'][::-1])
            data = data[:datasize]
        else:
            data = self._get_data_from_file(offset=self._datastart, datatype=self._di['IMType'], datasize=datasize)

        if self._di['IMType'][1] == 12:  # 12 bit per pixel packed per 2 in 3 bytes
            data = self._convert_12_bit(data, datatype=self._di['IMType'], packingtype=self._di['IMPacking'])
        data = data.reshape(self._di['IMSize'][::-1])
        if subtractbackground:
            self._bg = self.getbackground(squeeze=False)
            mask = np.where(data < self._bg)
            data = data - self._bg
            data[mask] = 0
        if squeeze:
            data = np.squeeze(data.transpose((5, 4, 2, 1, 3, 0, 6)))  # x,y,ph,t,z,fr,c

        return data

    def getbackground(self, squeeze=True):
        """
        Returns the background data from the .fli file. If squeeze is False the data is retured with these dimensions:
        frequency,time,phase,z,y,x,channel
        :param squeeze: Return data without singleton dimensions in x,y,ph,t,z,fr,c order
        :return: numpy.ndarray
        """
        if not self._di['BG_present']:
            print('WARNING: No background present in file')
            return 0
        if self._bg is not None:
            data = self._bg
        else:
            if self._di['Compression'] > 0:
                print('WARNING: Getting background before getting data is inefficient in compressed files.')
                self.getdata(subtractbackground=True, squeeze=False)
                data = self._bg
            else:
                offset = np.uint64(self._datastart)
                offset = offset + (np.uint64(self._di['IMType'][1]) * np.prod(self._di['IMSize'], dtype=np.uint64)) / 8
                datasize = np.prod(self._di['BGSize'], dtype=np.uint64)
                data = self._get_data_from_file(offset=int(offset), datatype=self._di['BGType'], datasize=datasize)
                if self._di['BGType'][1] == 12:  # 12 bit per pixel packed per 2 in 3 bytes
                    data = self._convert_12_bit(data, datatype=self._di['BGType'], packingtype=self._di['BGPacking'])
                data = data.reshape(self._di['BGSize'][::-1])
        if squeeze:
            return np.squeeze(data.transpose((5, 4, 2, 1, 3, 0, 6)))  # x,y,ph,t,z,fr,c
        else:
            return data

    def getframe(self, channel=0, z=0, phase=0, timestamp=0, frequency=0, subtractbackground=True, squeeze=True):
        """
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
        if channel > (self._di['IMSize'][0] - 1):
            print('WARNING: Channel out of range')
            return 0
        if z > (self._di['IMSize'][3] - 1):
            print('WARNING: Z out of range')
            return 0
        if phase > (self._di['IMSize'][4] - 1):
            print('WARNING: Phase out of range')
            return 0
        if timestamp > (self._di['IMSize'][5] - 1):
            print('WARNING: Timestamp out of range')
            return 0
        if frequency > (self._di['IMSize'][6] - 1):
            print('WARNING: Frequency out of range')
            return 0
        # get pointer
        return 0
        # get data

    @staticmethod
    def _convert_12_bit(data, datatype, packingtype='lsb'):
        datasize = int((data.size / 3) * 2)
        byte1 = data[0::3]  # contains the 8 least-significant bits of the even pixels
        byte2 = data[
                1::3]  # contains the 4 most-significant bits of the even pixels and 4 least-significant of the odd pixels
        byte3 = data[2::3]  # contains the 8 least-significant bits of the odd pixels
        data = np.zeros(datasize, dtype=datatype[0])
        if packingtype == 'lsb':
            data[0::2] = byte1.astype(np.uint16) + np.left_shift(
                np.left_shift(byte2, 4).astype(np.uint8).astype(np.uint16), 4)
            data[1::2] = np.left_shift(byte3.astype(np.uint16), 4) + np.right_shift(byte2, 4).astype(np.uint8)
        elif packingtype == 'msb':
            data[0::2] = np.left_shift(byte1.astype(np.uint16), 4) + np.right_shift(byte2, 4).astype(np.uint8)
            data[1::2] = np.left_shift(np.left_shift(byte2, 4).astype(np.uint8).astype(np.uint16), 4) + byte3.astype(
                np.uint16)
        else:
            raise ValueError('Data has no valid packing type')
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
        type_dict = {'UINT8': (np.uint8, 8),
                     'UINT16': (np.uint16, 16),
                     'UINT12': (np.uint16, 12),
                     'UINT32': (np.uint32, 32),
                     'INT8': (np.int8, 8),
                     'INT16': (np.int16, 16),
                     'INT32': (np.int32, 32),
                     'REAL32': (np.float32, 32),
                     'REAL64': (np.float64, 64)}
        if 'FLIMIMAGE' not in self.header:
            print('WARNING: FLIMIMAGE not found in header')
            return {}
        if 'LAYOUT' not in self.header['FLIMIMAGE']:
            print('WARNING: LAYOUT not found in header')
            return {}

        # read data layout. Default for each dimension is 1. Default datatype is UINT8. Default packing is lsb.
        data_info = {'IMSize': (int(self.header['FLIMIMAGE']['LAYOUT'].get('channels', 1)),
                                int(self.header['FLIMIMAGE']['LAYOUT'].get('x', 1)),
                                int(self.header['FLIMIMAGE']['LAYOUT'].get('y', 1)),
                                int(self.header['FLIMIMAGE']['LAYOUT'].get('z', 1)),
                                int(self.header['FLIMIMAGE']['LAYOUT'].get('phases', 1)),
                                int(self.header['FLIMIMAGE']['LAYOUT'].get('timestamps', 1)),
                                int(self.header['FLIMIMAGE']['LAYOUT'].get('frequencies', 1))),
                     'IMType': type_dict[self.header['FLIMIMAGE']['LAYOUT'].get('datatype', 'UINT8')],
                     'IMPacking': self.header['FLIMIMAGE']['LAYOUT'].get('packing', 'lsb')}

        if 'hasDarkImage' in self.header['FLIMIMAGE']['LAYOUT']:
            data_info['BG_present'] = bool(int(self.header['FLIMIMAGE']['LAYOUT'].get('hasDarkImage', 0)))
            data_info['BGSize'] = list(data_info['IMSize'])
            d = [0, 3, 4, 5]
            for dim in d:
                data_info['BGSize'][dim] = 1
            data_info['BGSize'] = tuple(data_info['BGSize'])
            data_info['BGType'] = data_info['IMType']
            data_info['BGPacking'] = data_info['IMPacking']

        if 'BACKGROUND' in self.header['FLIMIMAGE']:
            data_info['BG_present'] = True
            data_info['BGSize'] = (int(self.header['FLIMIMAGE']['BACKGROUND'].get('channels', 1)),
                                   int(self.header['FLIMIMAGE']['BACKGROUND'].get('x', 1)),
                                   int(self.header['FLIMIMAGE']['BACKGROUND'].get('y', 1)),
                                   int(self.header['FLIMIMAGE']['BACKGROUND'].get('z', 1)),
                                   int(self.header['FLIMIMAGE']['BACKGROUND'].get('phases', 1)),
                                   int(self.header['FLIMIMAGE']['BACKGROUND'].get('timestamps', 1)),
                                   int(self.header['FLIMIMAGE']['BACKGROUND'].get('frequencies', 1)))
            data_info['BGType'] = type_dict[self.header['FLIMIMAGE']['BACKGROUND'].get('datatype', 'UINT8')]

        if 'INFO' not in self.header['FLIMIMAGE']:
            print('WARNING: INFO not found in Header')
            data_info['Compression'] = 0
            return data_info
        data_info['Compression'] = int(self.header['FLIMIMAGE']['INFO'].get('compression', 0))
        return data_info

    def __str__(self):
        return self.path.name

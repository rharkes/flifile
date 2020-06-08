"""
Python support for the the Lambert Instruments .fli file
Version 1.0

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
        while byte := fid.read(1):
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

    def getdata(self, subtractbackground=True, squeeze=True):
        """
        Returns the data from the .fli file. If squeeze is False the data is retured with these dimensions:
        frequency,time,phase,z,y,x,channel
        :param subtractbackground: Subtract the background from the image data
        :param squeeze: Return data without singleton dimensions in x,y,ph,t,z,fr,c order
        :return: numpy.ndarray
        """
        data_info = self._get_data_info()
        data_size = np.prod(data_info['IMSize'], dtype=np.uint64)
        if data_info['Compression'] > 0:
            fid = self.path.open(mode='rb')
            fid.seek(self._datastart)
            dcmp = zlib.decompressobj(32 + zlib.MAX_WBITS)  # skip the GZIP header
            data = np.frombuffer(dcmp.decompress(fid.read()), dtype=data_info['IMType'])
            bg = data[data_size:]
            self._bg = bg.reshape(data_info['BGSize'][::-1])
            data = data[:data_size]
            data = data.reshape(data_info['IMSize'][::-1])
        else:
            data = np.fromfile(self.path, offset=self._datastart,
                               dtype=data_info['IMType'], count=data_size)
            data = data.reshape(data_info['IMSize'][::-1])
        if subtractbackground:
            self._bg = self.getbackground(squeeze=False)
            data = data - self._bg
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
        if self._bg is not None:
            data = self._bg
        else:
            data_info = self._get_data_info()
            if data_info['Compression'] > 0:
                print('WARNING: Getting background before getting data is inefficient in compressed files.')
                self.getdata(subtractbackground=True, squeeze=False)
                data = self._bg
            else:
                bgstart = np.uint64(self._datastart)
                bgstart = bgstart + np.uint64(np.dtype(data_info['IMType']).itemsize) * np.prod(data_info['IMSize'],
                                                                                                dtype=np.uint64)
                print(type(bgstart))
                data = np.fromfile(self.path, offset=bgstart,
                                   dtype=data_info['BGType'], count=np.prod(data_info['BGSize'], dtype=np.uint64))
                data = data.reshape(data_info['BGSize'][::-1])
        if squeeze:
            return np.squeeze(data.transpose((5, 4, 2, 1, 3, 0, 6)))  # x,y,ph,t,z,fr,c
        else:
            return data

    def _get_data_info(self):
        type_dict = {'UINT16': np.uint16}
        data_info = {'IMSize': (int(self.header['FLIMIMAGE']['LAYOUT']['channels']),
                                int(self.header['FLIMIMAGE']['LAYOUT']['x']),
                                int(self.header['FLIMIMAGE']['LAYOUT']['y']),
                                int(self.header['FLIMIMAGE']['LAYOUT']['z']),
                                int(self.header['FLIMIMAGE']['LAYOUT']['phases']),
                                int(self.header['FLIMIMAGE']['LAYOUT']['timestamps']),
                                int(self.header['FLIMIMAGE']['LAYOUT']['frequencies'])),
                     'BGSize': (int(self.header['FLIMIMAGE']['BACKGROUND']['channels']),
                                int(self.header['FLIMIMAGE']['BACKGROUND']['x']),
                                int(self.header['FLIMIMAGE']['BACKGROUND']['y']),
                                int(self.header['FLIMIMAGE']['BACKGROUND']['z']),
                                int(self.header['FLIMIMAGE']['BACKGROUND']['phases']),
                                int(self.header['FLIMIMAGE']['BACKGROUND']['timestamps']),
                                int(self.header['FLIMIMAGE']['BACKGROUND']['frequencies'])),
                     'IMType': type_dict[self.header['FLIMIMAGE']['LAYOUT']['datatype']],
                     'BGType': type_dict[self.header['FLIMIMAGE']['BACKGROUND']['datatype']],
                     'Compression': int(self.header['FLIMIMAGE']['INFO']['compression'])}
        return data_info

    def __str__(self):
        return self.path.name

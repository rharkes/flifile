import os
from collections import deque
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Union, Any, BinaryIO, Tuple

from flifile.datatypes import Datatypes, getdatatype


def readheadersize(f: BinaryIO) -> int:
    queue = deque([b" ", b" ", b" ", b" ", b" "], maxlen=5)
    stop = deque([b"{", b"E", b"N", b"D", b"}"], maxlen=5)
    while True:
        byte = f.read(1)
        queue.append(byte)
        if queue == stop:
            return f.tell()


def readheader(
    file: Union[str, os.PathLike[Any]]
) -> Tuple[dict[str, Dict[str, Dict[str, str]]], int]:
    file = Path(file)
    with file.open(mode="rb") as f:
        s = readheadersize(f)
        f.seek(0)
        h = parseheader(f.read(s))
        return h, s


def parseheader(headerstring: bytes) -> Dict[str, Dict[str, Dict[str, str]]]:
    chapter = "DEFAULT"
    section = "DEFAULT"
    header: Dict[str, Dict[str, Dict[str, str]]] = {}
    for line in headerstring.split(b"\n"):
        if line.startswith(b"{"):
            chapter = line.decode("utf-8").strip()[1:-1]
        if line.startswith(b"["):
            section = line.decode("utf-8").strip()[1:-1]
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


def tellversion(header: Dict[str, Dict[str, Dict[str, str]]]) -> str:
    version = ""
    if "FLIMIMAGE" in header:  # for version 1
        if "INFO" in header["FLIMIMAGE"]:
            version = header["FLIMIMAGE"]["INFO"].get("version", "")
            if version:
                return version

    if "FLIMIMAGE" in header:  # for version 2
        if "DEFAULT" in header["FLIMIMAGE"]:
            version = header["FLIMIMAGE"]["DEFAULT"].get("version", "")
            if version:
                return version
    if "DEFAULT" in header:  # for version 2 if the chapter is gone.
        if "DEFAULT" in header["DEFAULT"]:
            version = header["DEFAULT"]["DEFAULT"].get("version", "")
            if version:
                return version
    return version


@dataclass
class DataInfo:
    version: str
    IMSize: tuple[int, int, int, int, int, int, int]  # ch, x, y, z, ph, t, freq
    IMType: Datatypes
    Compression: int
    BG_present: bool
    BGSize: tuple[int, int, int, int, int, int, int]  # ch, x, y, z, ph, t, freq
    BGType: Datatypes
    valid: bool

    def __bool__(self) -> bool:
        return self.valid


def telldatainfo(header: Dict[str, Dict[str, Dict[str, str]]]) -> DataInfo:
    version = tellversion(header)
    imsize = (0, 0, 0, 0, 0, 0, 0)
    imtype = Datatypes.UINT8
    compression = 0
    bgpresent = False
    bgsize = (0, 0, 0, 0, 0, 0, 0)
    bgtype = Datatypes.UINT8
    valid = False
    if version == "1.0":
        imsize = (
            int(header["FLIMIMAGE"]["LAYOUT"]["Channel"]),
            int(header["FLIMIMAGE"]["LAYOUT"]["x"]),
            int(header["FLIMIMAGE"]["LAYOUT"]["y"]),
            int(header["FLIMIMAGE"]["LAYOUT"]["z"]),
            int(header["FLIMIMAGE"]["LAYOUT"]["phases"]),
            int(header["FLIMIMAGE"]["LAYOUT"]["timestamps"]),
            int(header["FLIMIMAGE"]["LAYOUT"]["frequencies"]),
        )
        imtype = getdatatype(
            header["FLIMIMAGE"]["LAYOUT"]["datatype"],
            header["FLIMIMAGE"]["LAYOUT"]["pixelFormat"],
        )
        compression = int(header["FLIMIMAGE"]["INFO"]["compression"])
        bgpresent = bool(header["FLIMIMAGE"]["LAYOUT"].get("hasDarkImage", "0") == "1")
        bgsize = (
            1,
            int(header["FLIMIMAGE"]["LAYOUT"]["x"]),
            int(header["FLIMIMAGE"]["LAYOUT"]["y"]),
            1,
            1,
            1,
            1,
        )
        bgtype = getdatatype(
            header["FLIMIMAGE"]["LAYOUT"]["datatype"],
            header["FLIMIMAGE"]["LAYOUT"]["pixelFormat"],
        )
        if "BACKGROUND" in header["FLIMIMAGE"]:
            bgpresent = True
            bgsize = (
                int(header["FLIMIMAGE"]["BACKGROUND"]["Channel"]),
                int(header["FLIMIMAGE"]["BACKGROUND"]["x"]),
                int(header["FLIMIMAGE"]["BACKGROUND"]["y"]),
                int(header["FLIMIMAGE"]["BACKGROUND"]["z"]),
                int(header["FLIMIMAGE"]["BACKGROUND"]["phases"]),
                int(header["FLIMIMAGE"]["BACKGROUND"]["timestamps"]),
                int(header["FLIMIMAGE"]["BACKGROUND"]["frequencies"]),
            )
            bgtype = getdatatype(
                header["FLIMIMAGE"]["BACKGROUND"]["datatype"],
                header["FLIMIMAGE"]["BACKGROUND"]["pixelFormat"],
            )
        valid = True

    return DataInfo(
        version=version,
        IMSize=imsize,
        IMType=imtype,
        Compression=compression,
        BG_present=bgpresent,
        BGSize=bgsize,
        BGType=bgtype,
        valid=valid,
    )

import os
from collections import deque
from dataclasses import dataclass
from pathlib import Path
from typing import Any, BinaryIO

from flifile.datatypes import Datatypes, getdatatype


def readheadersize(f: BinaryIO) -> int:
    """
    Bit convoluted, since you can probably just aswell read a 4kb page,
    check if it already contains {END} and trim to get the header, or expand with another 4kb.
    But using deque is fun.
    """
    queue = deque([b" ", b" ", b" ", b" ", b" "], maxlen=5)
    stop = deque([b"{", b"E", b"N", b"D", b"}"], maxlen=5)
    while True:
        byte = f.read(1)
        queue.append(byte)
        if queue == stop:
            return f.tell()


def readheader(
    file: str | os.PathLike[Any],
) -> tuple[dict[str, dict[str, dict[str, str]]], int]:
    file = Path(file)
    with file.open(mode="rb") as f:
        s = readheadersize(f)
        f.seek(0)
        h = parseheader(f.read(s))
        return h, s


def parseheader(headerstring: bytes) -> dict[str, dict[str, dict[str, str]]]:
    chapter = "DEFAULT"
    section = "DEFAULT"
    header: dict[str, dict[str, dict[str, str]]] = {}
    for line in headerstring.split(b"\n"):
        if line.startswith(b"{"):
            chapter = line.decode("utf-8").strip()[1:-1]
        if line.startswith(b"["):
            section = line.decode("utf-8").strip()[1:-1]
        else:
            kvp = line.split(b"=")
            if len(kvp) != 2:
                continue
            if chapter not in header:
                header[chapter] = {}
            if section not in header[chapter]:
                header[chapter][section] = {}
            header[chapter][section][kvp[0].decode("utf-8").strip()] = (
                kvp[1].decode("utf-8").strip()
            )
    return header


def tellversion(header: dict[str, dict[str, dict[str, str]]]) -> str:
    version = ""
    if ("FLIMIMAGE" in header) & ("INFO" in header["FLIMIMAGE"]):  # for version 1
        version = header["FLIMIMAGE"]["INFO"].get("version", "")
        if version:
            return version

    if ("FLIMIMAGE" in header) & ("DEFAULT" in header["FLIMIMAGE"]):  # for version 2
        version = header["FLIMIMAGE"]["DEFAULT"].get("version", "")
        if version:
            return version
    if ("DEFAULT" in header) & ("DEFAULT" in header["DEFAULT"]):  # for version 2 if the chapter is gone.
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


def telldatainfo(header: dict[str, dict[str, dict[str, str]]]) -> DataInfo:
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
            int(header["FLIMIMAGE"]["LAYOUT"]["channels"]),
            int(header["FLIMIMAGE"]["LAYOUT"]["x"]),
            int(header["FLIMIMAGE"]["LAYOUT"]["y"]),
            int(header["FLIMIMAGE"]["LAYOUT"]["z"]),
            int(header["FLIMIMAGE"]["LAYOUT"]["phases"]),
            int(header["FLIMIMAGE"]["LAYOUT"]["timestamps"]),
            int(header["FLIMIMAGE"]["LAYOUT"]["frequencies"]),
        )
        imtype = getdatatype(
            header["FLIMIMAGE"]["LAYOUT"].get("datatype", ""),
            header["FLIMIMAGE"]["LAYOUT"].get("pixelFormat", ""),
        )
        compression = int(header["FLIMIMAGE"]["INFO"]["compression"])
        bgpresent = bool(header["FLIMIMAGE"]["LAYOUT"].get("hasDarkImage", "0") == "1")
        bgsize = (
            1,
            imsize[1],
            imsize[2],
            1,
            1,
            1,
            1,
        )
        bgtype = imtype
        if "BACKGROUND" in header["FLIMIMAGE"]:
            bgpresent = True
            bgsize = (
                int(header["FLIMIMAGE"]["BACKGROUND"]["channels"]),
                int(header["FLIMIMAGE"]["BACKGROUND"]["x"]),
                int(header["FLIMIMAGE"]["BACKGROUND"]["y"]),
                int(header["FLIMIMAGE"]["BACKGROUND"]["z"]),
                int(header["FLIMIMAGE"]["BACKGROUND"]["phases"]),
                int(header["FLIMIMAGE"]["BACKGROUND"]["timestamps"]),
                int(header["FLIMIMAGE"]["BACKGROUND"]["frequencies"]),
            )
            bgtype = getdatatype(
                header["FLIMIMAGE"]["LAYOUT"].get("datatype", ""),
                header["FLIMIMAGE"]["LAYOUT"].get("pixelFormat", ""),
            )
        valid = True
    elif version == "2.0":
        ch = len(header["FLIMIMAGE"]["DEFAULT"]["channels"].strip("{}[]").split(","))
        ph = len(header["FLIMIMAGE"]["DEFAULT"]["phases"].strip("{}[]").split(","))
        _ = len(
            header["FLIMIMAGE"]["DEFAULT"]["timestamps"].strip("{}[]").split(",")
        )  # seems unused
        fr = len(header["FLIMIMAGE"]["DEFAULT"]["frequencies"].strip("{}[]").split(","))
        imsize = (
            ch,
            int(header["FLIMIMAGE"]["DEFAULT"]["x"]),
            int(header["FLIMIMAGE"]["DEFAULT"]["y"]),
            int(header["FLIMIMAGE"]["DEFAULT"]["z"]),
            ph,
            int(header["FLIMIMAGE"]["DEFAULT"]["numberOfFrames"]),
            fr,
        )
        imtype = getdatatype(
            "",
            header["FLIMIMAGE"]["DEFAULT"]["pixelFormat"],
        )
        compression = 0
        bgpresent = False
        bgsize = (
            1,
            imsize[1],
            imsize[2],
            1,
            1,
            1,
            1,
        )
        bgtype = imtype
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

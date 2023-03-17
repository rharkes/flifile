import os
from collections import deque
from pathlib import Path
from typing import Dict, Union, Any, BinaryIO, Tuple


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

from collections import deque


def readheadersize(f) -> int:
    """
    Bit convoluted, since you can probably just aswell read a 4kb page,
    check if it already contains {END} and trim to get the header, or expand with another 4kb.
    But using deque is fun.
    """
    queue = deque(b"     ", maxlen=5)
    stop = deque([b"{", b"E", b"N", b"D", b"}"], maxlen=5)
    while True:
        byte = f.read(1)
        queue.append(byte)
        if queue == stop:
            return f.tell()


def readheader(file) -> dict:
    with file.open(mode="rb") as f:
        s = readheadersize(f)
        f.seek(0)
        h = parseheader(f.read(s))
        h["datastart"] = s
        return h


def parseheader(headerstring) -> dict:
    chapter = "DEFAULT"
    section = "DEFAULT"
    header = {}
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


def tellversion(header: dict) -> str:
    version = None
    if "FLIMIMAGE" in header:  # for version 1
        if "INFO" in header["FLIMIMAGE"]:
            version = header["FLIMIMAGE"]["INFO"].get("version", None)
            if version:
                return version

    if "FLIMIMAGE" in header:  # for version 2
        if "DEFAULT" in header["FLIMIMAGE"]:
            version = header["FLIMIMAGE"]["DEFAULT"].get("version", None)
            if version:
                return version
    if "DEFAULT" in header:  # for version 2 if the chapter is gone.
        if "DEFAULT" in header["DEFAULT"]:
            version = header["DEFAULT"]["DEFAULT"].get("version", None)
            if version:
                return version
    return version

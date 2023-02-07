from collections import deque


def readheadersize(f) -> int:
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
            header[chapter][section][kvp[0].decode("utf-8").strip()] = kvp[1].decode("utf-8").strip()
    return header

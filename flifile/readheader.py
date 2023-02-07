from collections import deque


def readheadersize(f) -> int:
    queue = deque(b'     ', maxlen=5)
    stop = deque([b'{', b'E', b'N', b'D', b'}'], maxlen=5)
    while True:
        byte = f.read(1)
        queue.append(byte)
        if queue == stop:
            return f.tell()


def readheader(file) -> dict:
    with file.open(mode="rb") as f:
        s = readheadersize(f)
        f.seek(0)
        return {'headerstring': f.read(s), 'datastart': s}

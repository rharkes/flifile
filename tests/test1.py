import pytest as pytest
from pathlib import Path

from flifile.readheader import readheader


@pytest.fixture
def file():
    return Path(Path.cwd(), 'testdata', 'header.txt')


@pytest.fixture
def headerstring():
    return b'{FLIMDATA}\n[image]\nx=1\ny=2\n[background]\nx=123\ny=32\n{CAMERADATA}\n[something]\nwhy=because\n{END}'


@pytest.fixture
def datastart():
    return 93


def testheader(file, headerstring, datastart):
    h = readheader(file)
    assert (h['headerstring'] == headerstring)
    assert (h['datastart'] == datastart)

import pytest as pytest
from pathlib import Path

from flifile.readheader import readheader


@pytest.fixture
def file():
    return Path(Path.cwd(), 'testdata', 'header.txt')


@pytest.fixture
def header():
    return {'CAMERADATA': {'something': {'why': 'because'}},
            'FLIMDATA': {'background': {'x': '123', 'y': '32'},
                         'image': {'x': '1', 'y': '2'}},
            'datastart': 93}


def testheader(file, header):
    assert (readheader(file) == header)

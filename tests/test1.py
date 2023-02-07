import pytest as pytest
from pathlib import Path

from flifile.readheader import readheader
from tests.testdata.header1 import result as result1


@pytest.fixture
def file1():
    return Path(Path.cwd(), "testdata", "header1.txt")


def testheader(file1):
    assert readheader(file1) == result1

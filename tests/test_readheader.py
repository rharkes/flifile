import pytest as pytest
from pathlib import Path

from flifile.readheader import readheader
from tests.testdata.headers import returnheaders


@pytest.fixture
def files():
    return [
        Path(Path.cwd(), "testdata", "FliFile1.0(1)_DEV_1AB22C01C4FA_DS_0x0_02HH6.fli"),
        Path(Path.cwd(), "testdata", "FliFile2.0(1)_DEV_1AB22C01C4FA_DS_0x0_02HH6.fli"),
        Path(Path.cwd(), "testdata", "FliFile1.0_DEV_1AB22C01C4FA_DS_0x0_02HH6.fli"),
        Path(Path.cwd(), "testdata", "FliFile2.0_DEV_1AB22C01C4FA_DS_0x0_02HH6.fli"),
    ]


def testheaders(files):
    headers = returnheaders()
    for file in files:
        assert readheader(file) == headers[file.name]

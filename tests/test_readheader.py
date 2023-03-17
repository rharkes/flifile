import pytest as pytest
from pathlib import Path

from flifile.readheader import readheader, tellversion
from tests.testdata.headers import returnheaders, returnversions, returndatastarts


@pytest.fixture
def files():
    return [
        Path(
            Path.cwd(),
            "tests",
            "testdata",
            "FliFile1.0(1)_DEV_1AB22C01C4FA_DS_0x0_02HH6.fli",
        ),
        Path(
            Path.cwd(),
            "tests",
            "testdata",
            "FliFile2.0(1)_DEV_1AB22C01C4FA_DS_0x0_02HH6.fli",
        ),
        Path(
            Path.cwd(),
            "tests",
            "testdata",
            "FliFile1.0_DEV_1AB22C01C4FA_DS_0x0_02HH6.fli",
        ),
        Path(
            Path.cwd(),
            "tests",
            "testdata",
            "FliFile2.0_DEV_1AB22C01C4FA_DS_0x0_02HH6.fli",
        ),
    ]


def testheaders(files):
    headers = returnheaders()
    versions = returnversions()
    datastarts = returndatastarts()
    for file in files:
        header, ds = readheader(file)
        assert header == headers[file.name]
        assert tellversion(header) == versions[file.name]
        assert ds == datastarts[file.name]

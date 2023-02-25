# flifile
Python code for opening a lambert instruments .fli file

## Requirements
* Numpy

## Examples
Open a local .fli file
```
>>> from flifile import FliFile
>>> myflifile = FliFile('sample_file.fli')
>>> data = myflifile.getdata()
>>> data.shape
(348, 256, 12)
>>> data.mean()
26342.449652777777
```

## Install
`pip install flifile`

https://pypi.org/project/flifile/

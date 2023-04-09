import pytest
import pywebify
import os
from pathlib import Path
ph = pywebify.html
CUR_DIR = Path(os.path.dirname(__file__))


def test_convert_rst():
    rst_file = Path('tests/Example/Data Files/Summary.rst')
    ph.convert_rst(rst_file)
    with open(str(rst_file).replace('.rst', '.html'), 'r') as input:
        rst = input.read()
    assert 'figure::' not in rst
    assert 'alt=' in rst


def test_dir2html():
    # non-list ext
    d2h = ph.Dir2HTML(CUR_DIR / 'Example', ext='jpg')
    assert d2h.ext == ['jpg']

    # no files found
    with pytest.raises(ph.EmptyReportError):
        ph.Dir2HTML(CUR_DIR / 'Example', ext='boom')


def test_dir2html_from_file_list():
    # from file list
    d2h = ph.Dir2HTML(CUR_DIR / 'file_list.csv', ext='jpg', from_file=True)
    assert len(d2h.files) == 1

    d2h = ph.Dir2HTML(CUR_DIR / 'file_list.csv', ext=['jpg', 'png'], from_file=True)
    assert len(d2h.files) == 4

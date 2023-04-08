import pytest
import numpy as np
import pywebify
from pathlib import Path
pc = pywebify.config


@pytest.fixture(scope='session')
def path():
    return Path('tests/config_with_index.ini')


def test_str_2_dtype():
    # special
    pc.str_2_dtype('\\t')

    # None
    assert not pc.str_2_dtype('None')

    # bool
    assert pc.str_2_dtype('True')

    # str
    assert pc.str_2_dtype('"3,4,5"') == '3,4,5'

    # dict
    assert pc.str_2_dtype('{karma: police}') == {'karma': 'police'}

    # tuple
    assert pc.str_2_dtype('(3, 4, "5")') == (3, 4, '5')

    # list
    assert pc.str_2_dtype('[3, 4, "5"]') == [3, 4, '5']
    assert pc.str_2_dtype('3=="4",4,5') == ['3=="4"', 4, 5]

    # float
    np.testing.assert_almost_equal(pc.str_2_dtype('3.14'), 3.14)

    # int
    assert pc.str_2_dtype('666') == 666


def test_config_ini(path):
    cc = pc.ConfigFile(str(path), header=True)

    # header
    assert 'Default Configuration File' in cc.header

    # body
    keys = ['BODY', 'EMAIL', 'FILES', 'ICONS', 'JAVASCRIPT', 'LABELS', 'MAINDIV', 'NAVBAR', 'OPTIONS', 'RST',
            'RST_INDEX', 'SIDEBAR', 'TEMPLATES', 'TOGGLE', 'VIEWER']
    for kk in keys:
        assert kk in cc.config_dict.keys()

    # bad config
    with pytest.raises(FileNotFoundError):
        pc.ConfigFile('paranoid_android.ini')


def test_config_str():
    cc = pc.ConfigFile(raw="[topsecret.server.example]\nPort=48484")
    assert 'topsecret.server.example' in cc.config_dict.keys()


def test_config_write(path, tmp_path):
    cc = pc.ConfigFile(path, header=True)
    header = cc.header
    keys = cc.config_dict.keys()
    dest = tmp_path / 'temp_config'
    cc.write(dest)

    cc2 = pc.ConfigFile(dest, header=True)
    assert cc2.header == header
    assert cc2.config_dict.keys() == keys

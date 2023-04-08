import pytest
import os
import pywebify
import importlib
from pathlib import Path


CUR_DIR = Path(os.path.dirname(__file__))


def test_copy_configs(tmp_path):
    path = tmp_path / 'temp_config'
    pywebify.copy_configs(path)
    files = os.listdir(path)

    assert 'config.ini' in files
    assert 'templates' in files
    assert 'boom' not in files


def test_fix_sep():
    assert pywebify.fix_sep(None) is None

    path = pywebify.fix_sep('hi\\friend')
    assert len(str(path).split(os.sep)) == 2


def test_get_config():
    path = pywebify.get_config()
    assert path.suffix == '.ini'


def test_kwget():
    dict1 = {'test': 3}
    dict2 = {'test': 4}
    nope = {'no_test': 0}
    val = 'test'
    default = 5

    assert pywebify.kwget(dict1, nope, val, default) == 3
    assert pywebify.kwget(nope, dict2, val, default) == 4
    assert pywebify.kwget(nope, nope, val, default) == 5


def test_reset_config():
    pywebify.set_config('hi.ini')
    pywebify.reset_config()
    path = pywebify.get_config()
    assert 'config.ini' in str(path)


def test_pywebify_config_cases():
    # Use setup.txt config
    pw = pywebify.PyWebify('tests/Example', make=False)
    assert pw.config_path == pywebify.get_config()

    # User specified config
    pw = pywebify.PyWebify('tests/Example', make=False, config='tests/config_with_logo.ini')
    assert pw.config_path == Path('tests') / Path('config_with_logo.ini')

    # Level up
    pw = pywebify.PyWebify('tests/Example', make=False, config='config.ini')
    assert pw.config_path.name == 'config.ini'

    # No setup.txt [could have some issues here with setup.boom living on?]
    setup = (pywebify.get_config().parent / 'setup.txt')
    revert = Path(str(setup).replace('.txt', '.boom'))
    setup.rename(setup.with_suffix('.boom'))
    pw = pywebify.PyWebify('tests/Example', make=False)
    assert pw.config_path.name == 'config.ini'
    revert.rename(revert.with_suffix('.txt'))

    # Bad config
    with pytest.raises(FileNotFoundError):
        pywebify.PyWebify('tests/Example', make=False, config='paranoid_android.ini')


def test_rst():
    # Case of build_rst=True but not listed in config['FILES']['ext']
    pw = pywebify.PyWebify('tests/Example', make=False, config='tests/config_with_logo.ini')
    assert 'rst' in pw.config['FILES']['ext']

    # Case of build_rst=False but rst listed in config['FILES']['ext']
    pw = pywebify.PyWebify('tests/Example', make=False, build_rst=False, config='tests/config_with_index.ini')
    assert 'rst' not in pw.config['FILES']['ext']


def test_other_class_attributes():
    # Case of build_rst=True but not listed in config['FILES']['ext']
    pw = pywebify.PyWebify('tests/Example', make=False, config='tests/config_with_logo.ini', report_subdir='potato')
    assert pw.report_subdir == Path('potato')

    # Random kwargs
    pw = pywebify.PyWebify('tests/Example', make=False, config='tests/config_with_logo.ini', rock='roll')
    assert pw.rock == 'roll'


def test_full_report():
    pw = pywebify.PyWebify('tests/Example', config='tests/config_with_logo.ini', open=False)
    with open(str(pw.report_path / pw.report_filename) + '.html', 'r') as input:
        report = input.read()
    assert '<button id="toggle"></button> <img id="img0" src="." alt="" />' in report

    pw = pywebify.PyWebify('tests/Example', config='tests/config_with_index.ini', open=False)
    with open(str(pw.report_path / pw.report_filename) + '.html', 'r') as input:
        report = input.read()
    assert '<button id="toggle"></button> <object id="html0" data="index.html" width=100% height=100% />' in report

    with open(str(pw.report_path / 'index.html'), 'r') as input:
        index = input.read()
    assert f"{pw.config['RST_INDEX']['rst_h1_font_color']} !important;" in index


def test_init_make_setup():
    setup = (pywebify.get_config().parent / 'setup.txt')
    os.remove(setup)
    assert not setup.exists()

    importlib.reload(pywebify)
    assert setup.exists()

    os.remove(setup)
    assert not setup.exists()
    pywebify.get_config()
    assert setup.exists()

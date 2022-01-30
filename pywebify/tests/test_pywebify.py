import pytest
from pywebify import *
import os
import sys
import pdb
import shutil
from pathlib import Path
sys.path.append('..\..')
cur_dir = Path(os.path.dirname(__file__))
osjoin = os.path.join
db = pdb.set_trace
BASE_PATH = cur_dir.joinpath('Example')


def strip_txt(txt, key):
    """
    For comparison of current results with a txt file standard, strip any
    "Compiled" data fields that are specific to build

    Args:
        txt (str): generated file section
        key (str): search string [ex: "Compiled", etc]

    Returns:
        txt with tags containing the offending key removed

    """

    txt = txt.split('<')
    txt = [f for f in txt if key not in f]

    return '<'.join(txt)


@pytest.fixture
def pyweb_index():
    return PyWebify(osjoin(cur_dir, 'tests', 'Example'), config=osjoin(
        cur_dir, 'tests', 'config_with_index.ini'))


@pytest.fixture
def pyweb_logo():
    return PyWebify(osjoin(cur_dir, 'tests', 'Example'), config=osjoin(
        cur_dir, 'tests', 'config_with_logo.ini'))


def test_basic():
    pyw = PyWebify(BASE_PATH, make=False)

    assert list(pyw.config.keys()) == \
        ['BODY', 'BROWSER', 'EMAIL', 'FILES', 'ICONS', 'JAVASCRIPT',
         'LABELS', 'MAINDIV', 'NAVBAR', 'OPTIONS', 'SIDEBAR', 'TEMPLATES',
         'TOGGLE', 'VIEWER']
    assert pyw.config['SIDEBAR']['onmouseover'] == 'div_switch'


def test_make_index():
    """
    Test with an rst index build
    """

    pyw = PyWebify(BASE_PATH,
                   config=cur_dir.joinpath('config_with_index.ini'),
                   open=False)
    filepath = Path('test_txt_files').joinpath('make_index')

    # Check the navbar
    with open(filepath.joinpath('navbar.txt'), 'r') as input:
        txt = input.read()
    assert txt == strip_txt(pyw.html_dict['NAVBAR'], 'Compiled')

    # Build the html file
    with open(filepath.joinpath('html.txt'), 'r') as input:
        txt = input.read()
    html = strip_txt(pyw.html.raw, 'Compiled')
    html = html.replace(str(BASE_PATH).replace('\\', '/'), '')
    assert txt == html

    # Build the css file
    with open(filepath.joinpath('css.txt'), 'r') as input:
        txt = input.read()
    assert txt == pyw.css.raw

    # Move (then remove) any static files
    if pyw.setup_path.joinpath('test_txt_files', 'css.txt').exists():
        os.remove(pyw.setup_path.joinpath('test_txt_files', 'css.txt'))
    if pyw.setup_path.joinpath('test_txt_files').exists():
        os.rmdir(pyw.setup_path.joinpath('test_txt_files'))
    pyw.move_files(filepath.joinpath('css.txt'),
                   new_dir=Path('test_txt_files'))
    assert pyw.setup_path.joinpath('test_txt_files', 'css.txt').exists()
    os.remove(pyw.setup_path.joinpath('test_txt_files', 'css.txt'))
    os.rmdir(pyw.setup_path.joinpath('test_txt_files'))


def test_make_logo():
    """
    Test with a custom logo
    """

    pyw = PyWebify(BASE_PATH,
                   config=cur_dir.joinpath('config_with_logo.ini'),
                   open=False)
    filepath = Path('test_txt_files').joinpath('make_logo')

    # # Check the navbar [skip b/c same as navbar.txt test_make_index]
    # with open(filepath.joinpath('navbar.txt'), 'r') as input:
    #     txt = input.read()
    # assert txt == strip_txt(pyw.html_dict['NAVBAR'], 'Compiled')

    # Build the html file
    with open(filepath.joinpath('html.txt'), 'r') as input:
        txt = input.read()
    html = strip_txt(pyw.html.raw, 'Compiled')
    html = html.replace(str(BASE_PATH).replace('\\', '/'), '')
    assert txt == html

    # # Build the css file [skip b/c same as navbar.txt test_make_index]
    # with open(filepath.joinpath('css.txt'), 'r') as input:
    #     txt = input.read()
    # assert txt == pyw.css.raw


def test_config_not_found():
    try:
        pyw = PyWebify(BASE_PATH,
                       config=cur_dir.joinpath('boom_x8930a.ini'),
                       open=False)
        assert 0 == 1
    except OSError:
        assert 1 == 1


def test_build_navabar():
    assert 1 == 1


def test_check_path():
    assert 1 == 1


def test_get_files():
    assert 1 == 1


def test_get_javascript():
    assert 1 == 1


def test_set_output_paths():
    assert 1 == 1


def test_make_report_index():
    assert 1 == 1


def test_make_report_logo():
    assert 1 == 1


def test_copy_configs():
    path = cur_dir.joinpath('copy')
    if path.exists():
        shutil.rmtree(str(path))
    os.mkdir('copy')
    copy_configs(str(path), False)
    copied = os.listdir(str(path))

    assert len(copied) == 2
    assert 'config.ini' in copied
    assert 'templates' in copied

    if path.exists():
        shutil.rmtree(str(path))


def test_get_config():
    config = get_config()
    assert config == 'config.ini'


def test_kwget():
    kwargs = {'make': True}
    config = {'OPTIONS': {'make': False, 'explode': True}}
    # kwargs example
    assert kwget(kwargs, config['OPTIONS'], 'make', 'hi') == True

    # no kwargs example
    assert kwget(kwargs, config['OPTIONS'], 'explode', 'hi') == True

    # default
    assert kwget(kwargs, config['OPTIONS'], 'wut', 'hi') == 'hi'


def test_reset_config():
    reset_config()
    config = get_config()
    assert config == 'config.ini'


def test_set_config():
    reset_config()
    set_config('hi.ini')
    config = get_config()
    assert config == 'hi.ini'
    reset_config()


# # # Remove old transferred files
# # dirs = ['templates', 'config.ini']
# # for d in dirs:
# #     if os.path.exists(osjoin(cur_dir, 'tests', d)):
# #         if os.path.isdir(osjoin(cur_dir, 'tests', d)):
# #             shutil.rmtree(osjoin(cur_dir, 'tests', d))
# #         else:
# #             os.remove(osjoin(cur_dir, 'tests', d))
# #
# # # Copy config files
# # copy_configs(osjoin(cur_dir, 'tests'))


# # Make a dummy report with start page
# p = PyWebify(osjoin(cur_dir, 'tests', 'Example'), config=osjoin(
#     cur_dir, 'tests', 'config_with_index.ini'))

# # Make a dummy report with logo
# p = PyWebify(osjoin(cur_dir, 'tests', 'Example'), config=osjoin(
#     cur_dir, 'tests', 'config_with_logo.ini'))

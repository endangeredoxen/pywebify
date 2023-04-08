import os

__author__ = 'Steve Nicholes'
__copyright__ = 'Copyright (C) 2015 Steve Nicholes'
__license__ = 'GPLv3'
with open(os.path.join(os.path.dirname(__file__), r'version.txt'), 'r') as input:
    __version__ = input.readlines()[0]
__url__ = 'https://github.com/endangeredoxen/pywebify'

from pywebify.template import *  # noqa
from pywebify.pywebify import *  # noqa
from pywebify.config import *  # noqa
from pathlib import Path


# install default setup.txt based on current install directory
setup_path = Path(os.path.dirname(__file__)) / 'setup.txt'
if not os.path.exists(setup_path):
    with open(setup_path, 'w') as output:
        output.write(str(Path(os.path.dirname(__file__)) / 'config.ini'))

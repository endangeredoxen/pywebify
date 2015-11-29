import sys
import os
import shutil
sys.path.append('..\..')
cur_dir = os.path.dirname(__file__)
osjoin = os.path.join
from pywebify import *

# # Remove old transferred files
# dirs = ['templates', 'config.ini']
# for d in dirs:
#     if os.path.exists(osjoin(cur_dir, 'tests', d)):
#         if os.path.isdir(osjoin(cur_dir, 'tests', d)):
#             shutil.rmtree(osjoin(cur_dir, 'tests', d))
#         else:
#             os.remove(osjoin(cur_dir, 'tests', d))
#
# # Copy config files
# copy_configs(osjoin(cur_dir, 'tests'))

# Make a dummy report with start page
p = PyWebify(osjoin(cur_dir, 'tests', 'Example'), config=osjoin(cur_dir, 'tests', 'config_with_index.ini'))

# Make a dummy report with logo
p = PyWebify(osjoin(cur_dir, 'tests', 'Example'), config=osjoin(cur_dir, 'tests', 'config_with_logo.ini'))
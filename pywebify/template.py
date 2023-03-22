############################################################################
# template.py
#   Template maker utility: populates a template with special keyword values
#   to generate an HTML page or section of a page
############################################################################
__author__ = 'Steve Nicholes'
__copyright__ = 'Copyright (C) 2015 Steve Nicholes'
__license__ = 'GPLv3'
__version__ = '0.2'
__url__ = 'https://github.com/endangeredoxen/pywebify'

import os
import string
import pdb
from pathlib import Path
from typing import Union
db = pdb.set_trace


class Template():
    def __init__(self, template, subs):
        """ Template maker

        Replaces strings within a specified template in order to make a
        functional HTML page or section of a page

        Args:
            template (str):  path to template file
            subs (dict|list):  replacement strings dict or list of dicts

        """

        # Set the path
        self.templatePath = template

        # Init the raw html output varialbe
        self.raw = ''

        # Process multiple replacement dictionaries
        if len(subs) > 1:
            self.subs = self.merge_dicts(subs)
        else:
            self.subs = subs[0]

    def merge_dicts(self, subs):
        """ Combine multiple dictionaries in to one

        Args:
            subs (list): list of dicts

        Returns:
            merged dict
        """

        merged = subs[0]
        for i in range(1, len(subs)):
            merged.update(subs[i])
        return merged

    def substitute(self, caps=None):
        """ String substitution

        Args:
            caps (bool):  force uppercase on all dict keys

        Returns:
            none:  self.raw updated
        """

        if caps:
            self.subs = dict((k.upper(), v) for k, v in self.subs.items())
        self.raw = self.raw.safe_substitute(self.subs)

    def write(self, dest: Union[Path, None] = None, caps: bool = True, bonus: str = ''):
        """Write the updated template to file.

        Args:
            dest:  output filepath for template; if None, self.raw returned
            caps: force uppercase on all dict keys
            bonus: additional text to add to self.raw

        Returns:
            if dest==None, return self.raw
        """

        self.raw = string.Template(open(self.templatePath).read())
        self.substitute(caps)
        self.raw = self.raw + '\n' + bonus
        if dest:
            if not os.path.exists(dest.parent):
                os.makedirs(dest.parent)
            with open(dest, 'w') as temp:
                temp.write(self.raw)
        else:
            return self.raw

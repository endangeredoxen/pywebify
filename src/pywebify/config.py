############################################################################
# config.py
#
#   ini-style config file reader
#
############################################################################
__author__ = 'Steve Nicholes'
__copyright__ = 'Copyright (C) 2017 Steve Nicholes'
__license__ = 'GPLv3'
__url__ = 'https://github.com/endangeredoxen/pywebify'


try:
    import configparser
except:  # noqa
    import ConfigParser as configparser
import os
import re
import ast
import pdb
from typing import Union
from pathlib import Path
oswalk = os.walk
osjoin = os.path.join
db = pdb.set_trace


def str_2_dtype(val: str, ignore_list: bool = False) -> Union[str, int, float, list]:
    """Convert a string to the most appropriate data type.

    Args:
        val: string value to convert
        ignore_list:  ignore option to convert to list

    Returns:
        val with the interpreted data type
    """
    if len(val) == 0:
        return ''

    # Special chars
    chars = {'\\t': '\t', '\\n': '\n', '\\r': '\r'}

    # Remove comments
    v = re.split("#(?=([^\"]*\"[^\"]*\")*[^\"]*$)", val)
    if len(v) > 1:  # handle comments
        v = [f for f in v if f is not None]
        if v[0] == '':
            val = '#' + v[1].rstrip().lstrip()
        else:
            val = v[0].rstrip().lstrip()

    # Special
    if val in chars.keys():
        val = chars[val]
    # None
    if val == 'None':
        return None
    # bool
    if val == 'True':
        return True
    if val == 'False':
        return False
    # dict
    if ':' in val and '{' in val:
        val = val.replace('{', '').replace('}', '')
        val = re.split(''',(?=(?:[^'"]|'[^']*'|"[^"]*")*$)''', val)
        k = []
        v = []
        for t in val:
            tt = re.split(''':(?=(?:[^'"]|'[^']*'|"[^"]*")*$)''', t)
            k += [str_2_dtype(tt[0], ignore_list=True)]
            v += [str_2_dtype(':'.join(tt[1:]))]
        return dict(zip(k, v))
    # tuple
    if val[0] == '(' and val[-1] == ')' and ',' in val:
        return ast.literal_eval(val)
    # list
    if (',' in val or val.lstrip(' ')[0] == '[') and not ignore_list \
            and val != ',':
        if val[0] == '"' and val[-1] == '"' and ', ' not in val:
            return str(val.replace('"', ''))
        if val.lstrip(' ')[0] == '[':
            val = val.lstrip('[').rstrip(']')
        val = val.replace(', ', ',')
        new = []
        val = re.split(',(?=(?:"[^"]*?(?: [^"]*)*))|,(?=[^",]+(?:,|$))', val)
        for v in val:
            if '=="' in v:
                new += [v.rstrip().lstrip()]
            elif '"' in v:
                double_quoted = [f for f in re.findall(r'"([^"]*)"', v) if f != '']
                v = str(v.replace('"', ''))
                for dq in double_quoted:
                    v = v.replace(dq, '"%s"' % dq)
                try:
                    if isinstance(ast.literal_eval(v.lstrip()), str):
                        v = ast.literal_eval(v.lstrip())
                    new += [v]
                except:  # noqa
                    new += [v.replace('"', '').rstrip().lstrip()]
            else:
                try:
                    new += [str_2_dtype(v.replace('"', '').rstrip().lstrip())]
                except RecursionError:
                    pass
        if len(new) == 1:
            return new[0]
        return new
    # float and int

    try:
        int(val)
        return int(val)
    except:  # noqa
        try:
            float(val)
            return float(val)
        except:  # noqa
            v = val.split('#')
            if len(v) > 1:  # handle comments
                if v[0] == '':
                    return '#' + v[1].rstrip().lstrip()
                else:
                    return v[0].rstrip().lstrip()
            elif val in chars.values():
                return val
            else:
                val = val.rstrip().lstrip()
                if val[0] in ['"', "'"] and val[-1] in ['"', "'"]:
                    return val.strip('\'"')
                else:
                    return val


class ConfigFile():
    def __init__(self, path: Union[str, Path] = None, raw: str = False, header: bool = False):
        """Config file reader.

        Reads and parses a config file of the .ini format.  Data types are interpreted using str_2_dtype and all
        parameters are stored in both a ConfigParser class and a multi-dimensional dictionary.  "#" is the
        comment character.

        Args:
            path: location of the ini file (default=None)
            raw: raw text to avoid directly reading the config file
            header: optionally read comment lines above the first section and call them a header

        """

        self.config_path = path
        if isinstance(self.config_path, str):
            self.config_path = Path(self.config_path)
        self.config = configparser.RawConfigParser()
        self.config_dict = {}
        self.header = None
        self.is_valid = False
        self.raw = raw
        self.rel_path = Path(os.path.dirname(__file__))

        if self.config_path:
            self.validate_file_path()
        if self.is_valid:
            self.read_file()
        elif self.raw is not False:
            self.read_raw()
        else:
            raise FileNotFoundError('Could not find a config.ini file at the following location: %s' % self.config_path)

        self.make_dict()

        if header:
            self.get_header()

    def get_header(self):
        """Read any comment lines above the first section and call them a header."""
        header = []
        with open(self.config_path, 'r') as input:
            line = input.readline()
            while line:
                if line.lstrip(' ')[0] in ['#', ';', '\n']:
                    header += [line]
                    line = input.readline()
                else:
                    break

        if len(header) > 0:
            self.header = ''.join(header)

    def make_dict(self):
        """Convert the configparser object into a dictionary for easier handling."""
        self.config_dict = {s: {k: str_2_dtype(v)
                            for k, v in self.config.items(s)}
                            for s in self.config.sections()}

    def read_file(self):
        """Read the config file as using the parser option."""
        self.config.read(self.config_path)

    def read_raw(self):
        """Read from a raw string."""
        self.config.read_string(self.raw)

    def validate_file_path(self):
        """Make sure there is a valid config file at the location specified by self.config_path."""
        if self.config_path.exists():
            self.is_valid = True
        elif (self.rel_path / self.config_path).exists():
            self.config_path = self.rel_path / self.config_path
            self.is_valid = True
        else:
            self.is_valid = False

    def write(self, filename):
        """Write self.dict back to a config file."""
        with open(filename, 'w') as output:
            if self.header:
                output.write(self.header)
            for i, (k, v) in enumerate(self.config_dict.items()):
                if i > 0:
                    output.write('\n')
                output.write('[{}]\n'.format(k.upper()))
                for kk, vv in v.items():
                    output.write('{} = {}\n'.format(kk, vv))

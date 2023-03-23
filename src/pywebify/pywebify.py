############################################################################
# pywebify.py
#   PyWebify is a utility to create browser-based reports of images and html
#   files for easy data analysis.
############################################################################
__author__ = 'Steve Nicholes'
__copyright__ = 'Copyright (C) 2015 Steve Nicholes'
__license__ = 'GPLv3'
__url__ = 'https://github.com/endangeredoxen/pywebify'

from pywebify.config import ConfigFile
from pywebify.html import Dir2HTML
from pywebify.template import Template
from pathlib import Path
from typing import Union
import pdb
import getpass
import os
import shutil
import datetime
import sys
import subprocess
CUR_DIR = Path(os.path.dirname(__file__))
sys.path.append(CUR_DIR)
db = pdb.set_trace
osjoin = os.path.join


def copy_configs(path: Path):
    """Copy the default config file and the templates to a user directory for manipulation.

    Args:
        path: directory of the new file

    """
    print('Transferring PyWebify files:')
    # Create directory if needed
    if not path.exists():
        os.makedirs(path)

    # Copy the config file
    print('   config.ini...', end='')
    shutil.copyfile(CUR_DIR / 'config.ini', path / 'config.ini')
    print('done!')

    # Copy the templates folder
    print('   templates....', end='')
    shutil.copytree(CUR_DIR / 'templates', path / 'templates')
    print('done!')


def fix_sep(path: Union[Path, None]) -> Path:
    """Fix slashes in the path separator due to an artificat in ConfigParser."""
    if not path:
        return None

    return Path(str(path).replace('\\', os.path.sep))


def get_config():
    """Read the default config path from the setup.txt file."""
    with open(osjoin(CUR_DIR, 'setup.txt'), 'r') as input:
        return input.readlines()[0]


def kwget(dict1: dict, dict2: dict, val: str, default: Union[str, int, float]) -> Union[str, int, float]:
    """Augmented kwargs.get function.

    Args:
        dict1: first dictionary to check for the value
        dict2: second dictionary to check for the value
        val: value to look for
        default: default value if not found in dict1 or dict2 keys

    Returns:
        new value to use

    """
    if val in dict1.keys():
        return dict1[val]
    elif val in dict2.keys():
        return dict2[val]
    else:
        return default


def reset_config():
    """Reset the default config path in setup.txt."""
    set_config('config.ini')


def set_config(path: Path):
    """Set the config path.

    To avoid having to always add a custom config path to an instantiation of PyWebify update a setup.txt file with
    the path to the user-defined config path.

    Args:
        path:  full path to user config.ini

    """
    with open(CUR_DIR / 'setup.txt', 'w') as output:
        output.write(path)


class PyWebify():

    def __init__(self, base_path: Union[str, Path], **kwargs):
        """PyWebify report builder.

        This utility was designed to simplify visualization of data and plots using a convenient HTML-based report.
        The user provides either a directory path or the location of a text file containing paths and filenames.  The
        locations are scanned for image files (plots, pictures, drawings, whatever) and other html files (summary text,
        interactive data tables, whatever) and links are created for easy viewing in a web browser.

        Args:
            base_path: top-level directory containing files to add the report or the path to a text file containing
                paths and filenames

        Keyword Args:
            config (str): path to config ini file (note: most options are controlled using this file)
            exclude (list): file names to exclude from the sidebar list of files
            make (bool): make the report upon initialization of the class
            natsort (bool): use natural (human) sorting on the file list
            open (bool): pop open the report
            report_filename (str):  name of output html report file
            report_subdir (str): name of folder to dump report file
            setup_subdir (str): name of folder to dump report setup files
            show_ext (bool): show/hide file extension in the file list
            subtitle (str): report subtitle (location depends on template)
            title (str): report title (location depends on template)

        """
        # Get configuration file
        self.config_path = kwargs.get('config', get_config())
        if isinstance(self.config_path, str):
            self.config_path = Path(self.config_path)
        if not self.config_path.exists():
            if (CUR_DIR / self.config_path).exists():
                self.config_path = CUR_DIR / self.config_path
            else:
                raise OSError('Config file "%s" not found.  Please try again.' % self.config_path)
        self.config = getattr(ConfigFile(self.config_path), 'config_dict')
        sections = ['BODY', 'BROWSER', 'EMAIL', 'FILES', 'ICONS', 'JAVASCRIPT', 'LABELS', 'MAINDIV', 'NAVBAR',
                    'OPTIONS', 'RST', 'SIDEBAR', 'TEMPLATES', 'TOGGLE', 'VIEWER']
        for sec in sections:
            if sec not in self.config.keys():
                self.config[sec] = {}

        # Set class attributes
        if isinstance(base_path, str):
            base_path = Path(base_path)
        self.base_path = base_path.resolve()
        self.css = None
        self.css_path = ''
        self.css_replaces = self.get_replacements('css')
        if 'exclude' in self.config['OPTIONS']:
            self.exclude = kwargs.get('exclude', self.config['OPTIONS']['exclude'])
            if type(self.exclude) is str:
                self.exclude = [self.exclude]
        else:
            self.exclude = []
        self.files = None
        self.from_file = False
        self.html = None
        self.html_dict = {}
        self.html_path = ''
        self.img_path = ''
        self.js_css = ''
        self.js_files = []
        self.make = kwget(kwargs, self.config['OPTIONS'], 'make', True)
        self.merge_html = kwargs.get('merge_html', True)
        self.natsort = kwget(kwargs, self.config['OPTIONS'], 'natsort', True)
        self.navbar_path = ''
        self.open = kwget(kwargs, self.config['OPTIONS'], 'open', True)
        self.report_filename = kwget(kwargs, self.config['OPTIONS'], 'report_filepath', 'report')
        self.report_path = None
        self.report_subdir = kwget(kwargs, self.config['OPTIONS'], 'report_subdir', None)
        if self.report_subdir:
            self.report_subdir = Path(self.report_subdir)
        self.setup_path = None
        self.setup_subdir = Path(kwget(kwargs, self.config['OPTIONS'], 'setup_subdir', 'pywebify'))
        if 'rst_css' in self.config['TEMPLATES'].keys():
            self.rst_css = self.config['TEMPLATES']['rst_css']
            self.check_path('rst_css')
        else:
            self.rst_css = None
        self.show_ext = kwargs.get('show_ext', self.config['OPTIONS']['show_ext'])
        self.special = {}
        self.subtitle = kwget(kwargs, self.config['OPTIONS'], 'subtitle', self.base_path.name)
        self.temp_path = ''
        self.title = kwget(kwargs, self.config['OPTIONS'], 'title', self.base_path.name)
        self.use_relative = kwget(kwargs, self.config['OPTIONS'], 'use_relative', True)
        for key, value in kwargs.items():
            if not hasattr(self, key):
                setattr(self, key, value)

        # Set the output path
        self.set_output_paths()
        self.exclude += [str(self.report_path / self.report_filename), str(self.setup_path), 'index.html']
        self.exclude = [f for f in self.exclude if f != '']  # this would remove everything from the sidebar

        # Get the files at base_path
        self.get_files()

        # Update rst css
        self.update_rst_css()

        # Get top-level string replacements
        self.get_special()
        if self.make:
            self.run()

    def build_css(self):
        """Build the report css file."""
        # Get main css file
        self.css_path = self.config['TEMPLATES']['css']
        self.check_path('css_path')
        css_paths = [self.css_path]

        # Read any javascript css files
        for ff in self.config['JAVASCRIPT']['files']:
            self.temp_path = Path('templates') / Path('css') / (ff.split('.')[0] + '.css')
            self.check_path('temp_path')
            if self.temp_path.exists():
                css_paths += [self.temp_path]

        # Write the css file
        self.css = Template(css_paths, self.css_replaces + [self.special])
        dest = self.setup_path / 'css' / f'{self.report_filename}.css'
        self.css.write(dest=dest, bonus=self.js_css)

        # Clean the css from any template parameters that weren't populated by the config file
        with open(dest, 'r') as input:
            css = input.readlines()
        css_new = []
        for line in css:
            if '$' not in line:
                css_new += [line]
        with open(dest, 'w') as output:
            output.write(''.join(css_new))

    def build_html(self):
        """Build the html report file."""
        # Populate the html replacement dictionary
        self.html_dict['SIDEBAR'] = self.files.ul.replace('  ', '    ').replace('\n', '\n            ')
        self.html_dict['JS_FILES'], self.js_files, self.js_css = self.get_javascript(self.config['JAVASCRIPT']['files'])

        # Load the html template and build
        self.html_path = Path(self.config['TEMPLATES']['html'])
        self.check_path('html_path')
        self.html = Template(self.html_path, [self.html_dict, self.special])
        self.html.write(dest=self.report_path / f'{self.report_filename}.html')

    def build_navbar(self):
        """Build the top level navbar menu for the report."""
        self.html_dict['NAVBAR'] = ''
        if 'navbar' in self.config.get('TEMPLATES').keys():
            self.navbar_path = Path(self.config['TEMPLATES']['navbar'])
            self.check_path('navbar_path')
            if self.navbar_path.exists():
                nav_replaces = self.get_replacements('navbar')
                self.navbar = Template(self.navbar_path, nav_replaces+[self.special])
                self.html_dict['NAVBAR'] = self.navbar.write()

    def update_rst_css(self):
        """Convert rst files into built html."""
        pass

    def check_path(self, path: str):
        """Handle relative paths for filees in current directory.

        Args:
            path: name of a class attribute holding a path

        """
        ffile = fix_sep(getattr(self, path))
        if not ffile.exists():
            if (CUR_DIR / ffile).exists():
                setattr(self, path, CUR_DIR / ffile)

    def get_files(self):
        """Build a Files object that contains information about the files used in the report."""
        if 'rst' in [f.lower() for f in self.config['FILES']['ext']]:
            build_rst = True

            # Get the rst css file and do substitutions
            rst = Template(self.rst_css, self.config['RST'])
            rst.write(dest='rst_css_temp.css')
        else:
            build_rst = False
        self.files = Dir2HTML(str(self.base_path), self.config['FILES']['ext'],
                              onmouseover=self.config['SIDEBAR']['onmouseover'], from_file=self.from_file,
                              onclick=self.config['SIDEBAR']['onclick'], exclude=self.exclude,
                              merge_html=self.merge_html, use_relative=self.use_relative, show_ext=self.show_ext,
                              build_rst=build_rst, rst_css='rst_css_temp.css', natsort=self.natsort)
        if build_rst:
            os.remove('rst_css_temp.css')

    def get_javascript(self, files: list) -> [str, list, str]:
        """Adds javascript files to the report.

        Args:
            files: list of js filenames from the config file

        Returns:
            javascript <script> tag
            list of javascript files
            javascript css
        """
        js = []
        jsfiles = []
        jscss = ''
        if self.setup_subdir is not None:
            subdir = self.setup_subdir
        else:
            subdir = ''

        for f in files:
            # Define the script call for the html file
            js += [f'<script type="text/javascript" src="{subdir}/js/{f}"></script>\n']

            # Add the filename to the js file list
            jsfiles += [Path('js') / Path(f)]

        return '    '.join(js), jsfiles, jscss

    def get_replacements(self, template: str) -> dict:
        """ Find parameters in the config file that will be replaced in the given template file.

        Args:
            template: template name

        Returns:
            dict of replacement strings

        """
        replaces = []
        for sec in self.config.keys():
            if 'replace_in' in self.config[sec].keys() and \
                            self.config[sec]['replace_in'] == template:
                self.config[sec].pop('replace_in')
                replaces += [self.config[sec]]
        return replaces

    def get_special(self):
        """Populate "special" replacement strings."""
        self.special['BASEPATH'] = '.'
        self.special['CSS_FILE'] = self.setup_subdir / 'css' / (f"{self.report_filename}.css").replace('\\', '/')
        self.special['NOW'] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.special['COMPILEDBY'] = getpass.getuser()
        self.special['FAVICON'] = fix_sep(self.config['ICONS']['favicon'])
        logo = fix_sep(self.config['ICONS']['logo'])
        if logo is not None:
            self.move_files([logo], new_dir='img')
        self.special['QUANTITY'] = '%s' % len(self.files.files)
        self.special['REPORTNAME'] = self.report_filename
        if self.config['OPTIONS']['start_screen'] == 'logo' and logo:
            self.special['START_SCREEN'] = f'<img id="img0" src="{logo.parent}" alt="" />'
        elif 'html' in self.config['OPTIONS']['start_screen']:
            self.special['START_SCREEN'] = \
                '<object id="html0" data="' + self.config['OPTIONS']['start_screen'] + '" width=100% height=100% />'
        self.special['SUBTITLE'] = self.subtitle
        self.special['SUMMARY'] = ''
        self.special['TITLE'] = self.title

    def launch(self):
        """Open the report in the browser."""
        filename = self.report_path / f'{self.report_filename}.html'
        if sys.platform == "win32":
            os.startfile(filename)
        else:
            opener = "open" if sys.platform == "darwin" else "xdg-open"
            subprocess.call([opener, str(filename)])

    def move_files(self, files: list, new_dir: Union[None, bool, Path] = None):
        """Transfer files to the report directory.

        Args:
            files: filepaths to transfer
            new_dir:  make a new directory flag or a Path

        """
        for f in files:
            f = Path(f)
            self.temp_path = Path(f)
            self.check_path('temp_path')
            if self.temp_path.exists():
                if new_dir is not None:
                    path = self.setup_path / new_dir
                else:
                    path = self.setup_path / f.parent
                if not path.exists():
                    os.makedirs(path)
                shutil.copy(self.temp_path, path / f.name)

    def run(self):
        """Build, move, and open the report files."""
        # Build the navbar
        self.build_navbar()

        # Build the html file
        self.build_html()

        # Build the css file
        self.build_css()

        # Move any static files
        self.move_files(self.js_files)

        self.img_path = self.config['FILES']['img_dir']
        self.check_path('img_path')
        self.move_files([osjoin('img', f) for f in os.listdir(self.img_path)])

        # Open web report
        if self.open:
            self.launch()

    def set_output_paths(self):
        """Update the report path for the actual html file and all supplementary files."""
        # Update the base path if reading from file
        if self.from_file:
            self.base_path = os.sep.join(self.base_path.split(os.sep)[0:-1])

        # Set the actual html file path
        if self.report_subdir is not None:
            self.report_path = self.base_path / self.report_folder
        else:
            self.report_path = self.base_path

        # Set the supplemental files path
        if self.setup_subdir is not None:
            self.setup_path = self.base_path / Path(self.setup_subdir)
        else:
            self.setup_path = self.base_path


if __name__ == "__main__":
    pass

############################################################################
# pywebify.py
#   PyWebify is a utility to create browser-based reports of images and html
#   files for easy data analysis.
############################################################################
import sys
import datetime
import shutil
import os
import getpass
from pywebify.template import Template
from fivecentfileio import Dir2HTML
from fivecentfileio import ConfigFile
import subprocess
import pdb
from pathlib import Path
__author__ = 'Steve Nicholes'
__copyright__ = 'Copyright (C) 2015 Steve Nicholes'
__license__ = 'GPLv3'
__url__ = 'https://github.com/endangeredoxen/pywebify'

db = pdb.set_trace
osjoin = os.path.join
wsep = '\\'
lsep = '/'
sep = [wsep, lsep] if lsep in str(os.path.dirname(__file__)) else [lsep, wsep]


def copy_configs(path, verbose=True):
    """
    Copy the default config file and the templates to a user directory for
    manipulation

    Args:
        path (str): directory of the new file

    """

    cur_dir = Path(os.path.dirname(__file__))
    path = Path(path.replace(*sep))

    if verbose:
        print('Transferring PyWebify files:')

    # Create directory if needed
    if not os.path.exists(path):
        os.makedirs(path)

    # Copy the config file
    if verbose:
        print('   config.ini...', end='')
    shutil.copyfile(cur_dir.joinpath('config.ini'),
                    path.joinpath('config.ini'))
    if verbose:
        print('done!')

    # Copy the templates folder
    if verbose:
        print('   templates....', end='')
    shutil.copytree(osjoin(cur_dir, 'templates'), osjoin(path, 'templates'))
    if verbose:
        print('done!')


def get_config():
    """
    Read the default config path from the setup.txt file
    """

    cur_dir = Path(os.path.dirname(__file__))
    with open(cur_dir.joinpath('setup.txt'), 'r') as input:
        return input.readlines()[0]


def kwget(dict1, dict2, val, default):
    """
    Augmented kwargs.get function

    Args:
        dict1 (dict): first dictionary to check for the value
        dict2 (dict): second dictionary to check for the value
        val (str): value to look for
        default (multiple): default value if not found in
            dict1 or dict2 keys

    Returns:
        value to use
    """

    if val in dict1.keys():
        return dict1[val]
    elif val in dict2.keys():
        return dict2[val]
    else:
        return default


def reset_config():
    """
    Reset the default config path in setup.txt
    """

    set_config('config.ini')


def set_config(path):
    """
    To avoid having to always add a custom config path to an instantiation of
    PyWebify update a setup.txt file with the path to the user-defined config
    path

    Args:
        path (str):  full path to user config.ini

    """

    cur_dir = Path(os.path.dirname(__file__))
    with open(cur_dir.joinpath('setup.txt'), 'w') as output:
        output.write(path)


class PyWebify():

    def __init__(self, base_path, **kwargs):
        """
        PyWebify report builder

        This utility was designed to simplify visualization of data and
        plots using a convenient HTML-based report.  The user provides either
        a directory path or the location of a text file containing paths and
        filenames.  The locations are scanned for image files (plots,
        pictures, drawings, whatever) and other html files (summary text,
        interactive data tables, whatever) and links are created for easy
        viewing in a web browser.

        Args:
            base_path (str): top-level directory containing files to add the
                             report or the path to a text file containing
                             paths and filenames

        Keyword Args:
            config (str): path to config ini file (note: most options are
                          controlled using this file)
            exclude (list): file names to exclude from the sidebar
                            list of files
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
        cur_dir = Path(os.path.dirname(__file__))
        self.config_path = \
            Path(str(kwargs.get('config', get_config())).replace(*sep))
        if not os.path.exists(self.config_path):
            if cur_dir.joinpath(self.config_path).exists():
                self.config_path = cur_dir.joinpath(self.config_path)
            else:
                raise OSError('Config file "%s" not found.  '
                              'Please try again.' % self.config_path)
        self.config = getattr(ConfigFile(self.config_path), 'config_dict')
        sections = ['BODY', 'BROWSER', 'EMAIL', 'FILES', 'ICONS', 'JAVASCRIPT',
                    'LABELS', 'MAINDIV', 'NAVBAR', 'OPTIONS', 'SIDEBAR',
                    'TEMPLATES', 'TOGGLE', 'VIEWER']
        for sec in sections:
            if sec not in self.config.keys():
                self.config[sec] = {}

        # Set class attributes
        self.base_path = Path(base_path).absolute()
        self.css = None
        self.css_path = Path()
        if 'exclude' in self.config['OPTIONS']:
            self.exclude = kwargs.get('exclude',
                                      self.config['OPTIONS']['exclude'])
            if type(self.exclude) is str:
                self.exclude = [self.exclude]
        else:
            self.exclude = []
        self.files = None
        self.from_file = False
        self.html = None
        self.html_dict = {}
        self.html_path = Path()
        self.img_path = Path()
        self.js_css = ''
        self.js_files = []
        self.make = kwget(kwargs, self.config['OPTIONS'], 'make', True)
        self.merge_html = kwargs.get('merge_html', True)
        self.natsort = kwget(kwargs, self.config['OPTIONS'], 'natsort', True)
        self.navbar_path = ''
        self.open = kwget(kwargs, self.config['OPTIONS'], 'open', True)
        self.report_filename = kwget(kwargs, self.config['OPTIONS'],
                                     'report_filepath', 'report')
        self.report_path = Path()
        self.report_subdir = kwget(kwargs, self.config['OPTIONS'],
                                   'report_subdir', None)
        self.setup_path = Path()
        self.setup_subdir = Path(kwget(kwargs, self.config['OPTIONS'],
                                       'setup_subdir', 'pywebify'))
        if 'rst_css' in self.config['TEMPLATES'].keys():
            self.rst_css = Path(f"{self.config['TEMPLATES']['rst_css'].replace(*sep)}")
            self.check_path('rst_css')
        else:
            self.rst_css = None
        self.show_ext = kwargs.get('show_ext',
                                   self.config['OPTIONS']['show_ext'])
        self.special = {}
        self.subtitle = kwget(kwargs, self.config['OPTIONS'], 'subtitle',
                              self.base_path.stem)
        self.temp_path = Path()
        self.title = kwget(kwargs, self.config['OPTIONS'], 'title',
                           self.base_path.stem)
        self.use_relative = kwget(kwargs, self.config['OPTIONS'],
                                  'use_relative', True)
        for key, value in kwargs.items():
            if not hasattr(self, key):
                setattr(self, key, value)

        # Set the output path
        self.set_output_paths()
        self.exclude += [str(self.report_path.joinpath(self.report_filename)),
                         str(self.setup_path), 'index.html']

        # Get the files at base_path
        self.get_files()

        # Get top-level string replacements
        self.get_special()

        if self.make:
            self.run()

    def build_css(self):
        """ Build the report css file """

        css_replaces = self.get_replacements('css')

        self.css_path = Path(
            f"{self.config['TEMPLATES']['css'].replace(*sep)}")
        self.check_path('css_path')
        self.css = Template(self.css_path, css_replaces+[self.special])
        self.css.write(dest=self.setup_path.joinpath('css',
                                                     f'{self.report_filename}.css'),
                       bonus=self.js_css)

    def build_html(self):
        """ Build the html report file """

        # Populate the html replacement dictionary
        self.html_dict['SIDEBAR'] = self.files.ul
        self.html_dict['JS_FILES'], self.js_files, self.js_css = \
            self.get_javascript(self.config['JAVASCRIPT']['files'])

        # Load the html template and build
        self.html_path = Path(
            f"{self.config['TEMPLATES']['html'].replace(*sep)}")
        self.check_path('html_path')
        self.html = Template(self.html_path, [self.html_dict, self.special])
        self.html.write(dest=self.report_path.joinpath(
            f'{self.report_filename.replace(*sep)}.html'))

    def build_navbar(self):
        """ Build the top level navbar menu for the report """

        self.html_dict['NAVBAR'] = ''
        if 'navbar' in self.config.get('TEMPLATES').keys():
            self.navbar_path = Path(
                self.config['TEMPLATES']['navbar'].replace(*sep))
            self.check_path('navbar_path')
            if os.path.exists(self.navbar_path):
                nav_replaces = self.get_replacements('navbar')
                self.navbar = Template(self.navbar_path,
                                       nav_replaces+[self.special])
                self.html_dict['NAVBAR'] = self.navbar.write()

    def check_path(self, path):
        """ Handle relative paths for files in current directory """

        cur_dir = Path(os.path.dirname(__file__))
        file = getattr(self, path)
        if not os.path.exists(file):
            if os.path.exists(cur_dir.joinpath(file)):
                setattr(self, path, cur_dir.joinpath(file))

    def get_files(self):
        """
        Build a Files object that contains information about the files used
        in the report
        """

        if 'rst' in [f.lower() for f in self.config['FILES']['ext']]:
            build_rst = True
        else:
            build_rst = False

        self.files = Dir2HTML(str(self.base_path), self.config['FILES']['ext'],
                              onmouseover=self.config['SIDEBAR']
                                                     ['onmouseover'],
                              from_file=self.from_file,
                              onclick=self.config['SIDEBAR']['onclick'],
                              exclude=self.exclude, merge_html=self.merge_html,
                              use_relative=self.use_relative,
                              show_ext=self.show_ext, build_rst=build_rst,
                              rst_css=self.rst_css, natsort=self.natsort)

    def get_javascript(self, files):
        """
        Adds javascript files to the report

        Args:
            files (list): list of js filenames from the config file

        """

        js = ''
        jsfiles = []
        jscss = ''
        if self.setup_subdir is not None:
            subdir = str(self.setup_subdir) + '/'
        else:
            subdir = ''

        for f in files:
            f = Path(f)

            # Define the script call for the html file
            js += '<script type="text/javascript" src="%sjs/%s"></script>\n' \
                  % (subdir, str(f))

            # Add the filename to the js file list
            jsfiles += [str(Path('js').joinpath(f))]

            # Get any additional css related to the js addition
            self.temp_path = Path('templates', 'css', f.stem + '.css')
            self.check_path('temp_path')
            if os.path.exists(self.temp_path):
                with open(self.temp_path, 'r') as input:
                    jscss += input.read()

        return js, jsfiles, jscss

    def get_replacements(self, template):
        """
        Find parameters in the config file that will be replaced in the given
        template file

        Args:
            template (str): template name

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
        """ Populate "special" replacement strings """

        # self.special['BASEPATH'] = r'file:///' + \
        #                           self.base_path.replace('\\','/')
        self.special['BASEPATH'] = '.'
        self.special['CSS_FILE'] = self.setup_subdir.joinpath(
            'css', f'{self.report_filename}.css')
        self.special['NOW'] = \
            datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.special['COMPILEDBY'] = getpass.getuser()
        self.special['FAVICON'] = Path(f"{self.config['ICONS']['favicon'].replace(*sep)}")
        if not self.special['FAVICON'].exists() and \
                self.config_path.parent.joinpath(self.special['FAVICON']).exists():
            self.special['FAVICON'] = self.config_path.parent.joinpath(self.special['FAVICON'])
        if self.config['ICONS']['logo'] is not None:
            self.config['ICONS']['logo'] = \
                Path(f"{self.config['ICONS']['logo'].replace(*sep)}")
            if not self.config['ICONS']['logo'].exists() and \
                    self.config_path.parent.joinpath(self.config['ICONS']['logo']).exists():
                self.config['ICONS']['logo'] = \
                    self.config_path.parent.joinpath(self.config['ICONS']['logo'])
            self.move_files([self.config['ICONS']['logo']],
                            new_dir='img')
        self.special['QUANTITY'] = '%s' % len(self.files.files)
        self.special['REPORTNAME'] = self.report_filename
        if self.config['OPTIONS']['start_screen'] == 'logo':
            self.special['START_SCREEN'] = \
                '<img id="img0" src="%s" alt="" />' % self.config['ICONS']['logo'].name
        elif 'html' in self.config['OPTIONS']['start_screen']:
            self.special['START_SCREEN'] = \
                '<object id="html0" data="' + \
                self.config['OPTIONS']['start_screen'] + \
                '" width=100% height=100% />'
        self.special['SUBTITLE'] = self.subtitle
        self.special['SUMMARY'] = ''
        self.special['TITLE'] = self.title

    def launch(self):
        """ Open the report in the browser """

        filename = self.report_path.joinpath(f'{self.report_filename}.html')

        if sys.platform == "win32":
            os.startfile(filename)
        else:
            opener = "open" if sys.platform == "darwin" else "xdg-open"
            subprocess.call([opener, filename])

    def move_files(self, files, new_dir=None):
        """
        Transfer files to the report directory

        Args:
            files (list): filepaths to transfer
            new_dir (bool):  make a new directory

        """

        if not isinstance(files, list):
            files = [files]

        for f in files:
            if not isinstance(f, Path):
                f = Path(f.replace(*sep))
            self.temp_path = f
            self.check_path('temp_path')
            if os.path.exists(self.temp_path):
                if new_dir is not None:
                    path = self.setup_path.joinpath(new_dir)
                else:
                    path = self.setup_path.joinpath(f.parent)
                if not os.path.exists(path):
                    os.makedirs(path)
                try:
                    shutil.copy(self.temp_path, path.joinpath(f.name))
                except shutil.SameFileError:
                    pass

    def run(self):
        """ Build, move, and open the report files """

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
        """
        Update the report path for the actual html file and all
        supplementary files
        """

        # Update the base path if reading from file
        if self.from_file:
            self.base_path = self.base_path.parent

        # Set the actual html file path
        if self.report_subdir is not None:
            self.report_path = self.base_path.joinpath(self.report_folder)
        else:
            self.report_path = self.base_path

        # Set the supplemental files path
        if self.setup_subdir is not None:
            self.setup_path = self.base_path.joinpath(self.setup_subdir)
        else:
            self.setup_path = self.base_path


if __name__ == "__main__":
    pass

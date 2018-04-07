############################################################################
# pywebify.py
#   PyWebify is a utility to create browser-based reports of images and html
#   files for easy data analysis.
############################################################################
__author__    = 'Steve Nicholes'
__copyright__ = 'Copyright (C) 2015 Steve Nicholes'
__license__   = 'GPLv3'
__version__   = '0.2'
__url__       = 'https://github.com/endangeredoxen/pywebify'

import pdb
from fileio import ConfigFile
from fileio import Dir2HTML
from pywebify.template import Template
import getpass
import os
import shutil
import datetime
import sys
cur_dir = os.path.dirname(__file__)
sys.path.append(cur_dir)
st = pdb.set_trace
osjoin = os.path.join


def copy_configs(dir):
    """
    Copy the default config file and the templates to a user directory for
    manipulation

    Args:
        dir (str): directory of the new file

    """

    print('Transferring PyWebify files:')
    # Create directory if needed
    if not os.path.exists(dir):
        os.makedirs(dir)

    # Copy the config file
    print('   config.ini...', end='')
    shutil.copyfile(osjoin(cur_dir, 'config.ini'), osjoin(dir, 'config.ini'))
    print('done!')

    # Copy the templates folder
    print('   templates....', end='')
    shutil.copytree(osjoin(cur_dir, 'templates'), osjoin(dir, 'templates'))
    print('done!')


def get_config():
    """
    Read the default config path from the setup.txt file
    """

    with open(osjoin(cur_dir, 'setup.txt'), 'r') as input:
        return input.readlines()[0]


def kw_get(kwargs, attr, config, default=None, func=None, verbose=False):
    """
    Checks kwargs and/or a configuration file for keywords and if missing
    returns a default value

    Args:
        kwargs (dict): keyword arguments
        attr (str): value to find in the config file
        config (dict): config file section
        default (all types): default value if attr is not in config
        func (module):  reference to a module if kw is a function
        verbose (boolean): print warnings

    Returns:
        kw or default value
    """

    def kw_return(value, func=None):
        """ Return the keyword value or the default value

        Args:
            value (str): the value to return or the value associated with func
            func (module): str reference to a module
        """

        if func:
            return getattr(func, value)
        else:
            return value

    if attr in kwargs.keys():
        # attr provided by user in kwargs
        return kw_return(kwargs[attr], func)
    elif attr in config.keys():
        # attr found in config file
        return kw_return(config[attr], func)
    else:
        # return the default
        return kw_return(default, func)


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

    with open(osjoin(cur_dir, 'setup.txt'), 'w') as output:
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
            browser (str): name of browser with which to open the report
            exclude (list): file names to exclude from the sidebar
                            list of files
            make (bool): make the report upon initialization of the class
            natsort (bool): use natural (human) sorting on the file list
            open (bool): pop open the report
            output_name (str):  name of output html report file
            report_folder (str): name of folder to dump report setup files
            show_ext (bool): show/hide file extension in the file list
            subtitle (str): report subtitle (location depends on template)
            title (str): report title (location depends on template)

        """

        # Get configuration file
        self.config_path = kwargs.get('config', get_config())
        if not os.path.exists(self.config_path):
            if os.path.exists(osjoin(cur_dir, self.config_path)):
                self.config_path = osjoin(cur_dir, self.config_path)
            else:
                raise OSError('Config file "%s" not found.  '
                              'Please try again.' % self.config_path)
        self.config = getattr(ConfigFile(self.config_path), 'config_dict')

        # Set class attributes
        self.base_path = os.path.abspath(base_path)
        self.browser = kwargs.get('browser', self.config['OPTIONS']['browser'])
        self.css = None
        self.css_path = ''
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
        self.html_path = ''
        self.img_path = ''
        self.js_css = ''
        self.js_files = []
        self.make = kwargs.get('make', self.config['OPTIONS']['make'])
        self.natsort = kwargs.get('natsort',
                                  self.config['OPTIONS']['natsort'])
        self.navbar_path = ''
        self.open = kwargs.get('open', self.config['OPTIONS']['open'])
        self.report_filename = kw_get(kwargs, 'report_filepath',
                                      self.config['OPTIONS'], 'report')
        self.report_path = None
        self.report_subdir = kw_get(kwargs, 'report_subdir',
                                    self.config['OPTIONS'], None)
        self.setup_path = None
        self.setup_subdir = kw_get(kwargs, 'setup_subdir',
                                   self.config['OPTIONS'], 'pywebify')
        if 'rst_css' in self.config['TEMPLATES'].keys():
            self.rst_css = self.config['TEMPLATES']['rst_css']
            self.check_path('rst_css')
        else:
            self.rst_css = None
        self.show_ext = kwargs.get('show_ext',
                                   self.config['OPTIONS']['show_ext'])
        self.special = {}
        self.subtitle = kw_get(kwargs, 'subtitle', self.config['OPTIONS'],
                               self.base_path.split(os.sep)[-1])
        self.temp_path = ''
        self.title = kw_get(kwargs, 'title', self.config['OPTIONS'],
                            self.base_path.split(os.sep)[-1])
        self.use_relative = kw_get(kwargs, 'use_relative',
                                   self.config['OPTIONS'], True)
        for key, value in kwargs.items():
            if not hasattr(self, key):
                setattr(self,key,value)

        # Set the output path
        self.set_output_paths()
        self.exclude += [osjoin(self.report_path, self.report_filename),
                         self.setup_path, 'index.html']

        # Get the files at base_path
        self.get_files()

        # Get top-level string replacements
        self.get_special()

        if self.make:
            self.run()

    def build_css(self):
        """ Build the report css file """

        css_replaces = self.get_replacements('css')

        self.css_path = r'%s' % self.config['TEMPLATES']['css']
        self.check_path('css_path')
        self.css = Template(self.css_path, css_replaces+[self.special])
        self.css.write(dest=osjoin(self.setup_path, 'css',
                                   '%s.css' % self.report_filename),
                       bonus=self.js_css)

    def build_html(self):
        """ Build the html report file """

        # Populate the html replacement dictionary
        self.html_dict['SIDEBAR'] = self.files.ul
        self.html_dict['JS_FILES'], self.js_files, self.js_css = \
            self.get_javascript(self.config['JAVASCRIPT']['files'])

        # Load the html template and build
        self.html_path = r'%s' % self.config['TEMPLATES']['html']
        self.check_path('html_path')
        self.html = Template(self.html_path,[self.html_dict, self.special])
        self.html.write(dest=osjoin(self.report_path,
                                    '%s.html' % self.report_filename))

    def build_navbar(self):
        """ Build the top level navbar menu for the report """

        self.html_dict['NAVBAR'] = ''
        if 'navbar' in self.config.get('TEMPLATES').keys():
            self.navbar_path = self.config['TEMPLATES']['navbar']
            self.check_path('navbar_path')
            if os.path.exists(self.navbar_path):
                nav_replaces = self.get_replacements('navbar')
                self.navbar = Template(self.navbar_path,
                                       nav_replaces+[self.special])
                self.html_dict['NAVBAR'] = self.navbar.write()

    def check_path(self, path):
        """ Handle relative paths for filees in current directory """

        file = getattr(self, path)
        if not os.path.exists(file):
            if os.path.exists(osjoin(cur_dir, file)):
                setattr(self, path, osjoin(cur_dir, file))

    def get_files(self):
        """
        Build a Files object that contains information about the files used
        in the report
        """

        if 'rst' in [f.lower() for f in self.config['FILES']['ext']]:
            build_rst = True
        else:
            build_rst = False

        self.files = Dir2HTML(self.base_path, self.config['FILES']['ext'],
                              onmouseover=self.config['SIDEBAR']\
                                                     ['onmouseover'],
                              from_file=self.from_file,
                              onclick=self.config['SIDEBAR']['onclick'],
                              exclude=self.exclude,
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
            subdir = self.setup_subdir + '/'
        else:
            subdir = ''

        for f in files:
            # Define the script call for the html file
            js += '<script type="text/javascript" src="%sjs/%s"></script>\n' \
                  % (subdir, f)

            # Add the filename to the js file list
            jsfiles += [osjoin('js',f)]

            # Get any additional css related to the js addition
            self.temp_path = osjoin('templates\css', f.split('.')[0] + '.css')
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

        #self.special['BASEPATH'] = r'file:///' + \
        #                           self.base_path.replace('\\','/')
        self.special['BASEPATH'] = '.'
        self.special['CSS_FILE'] = osjoin(self.setup_subdir, 'css',
                                          '%s.css' % self.report_filename) \
                                   .replace('\\', '/')
        self.special['NOW'] = \
            datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.special['COMPILEDBY'] = getpass.getuser()
        self.special['FAVICON'] = self.config['ICONS']['favicon']
        if self.config['ICONS']['logo'] is not None:
            self.move_files([self.config['ICONS']['logo']],
                                new_dir='img')
        self.special['QUANTITY'] = '%s' % len(self.files.files)
        self.special['REPORTNAME'] = self.report_filename
        if self.config['OPTIONS']['start_screen'] == 'logo':
            self.special['START_SCREEN'] = \
                '<img id="img0" src="%s" alt="" />' \
                % self.config['ICONS']['logo'].split(os.path.sep)[-1]
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

        os.startfile(osjoin(self.report_path, '%s.html' % self.report_filename))

    def move_files(self, files, new_dir=None):
        """
        Transfer files to the report directory

        Args:
            files (list): filepaths to transfer
            new_dir (bool):  make a new directory

        """

        for f in files:
            self.temp_path = f
            self.check_path('temp_path')
            if os.path.exists(self.temp_path):
                if new_dir is not None:
                    path = osjoin(self.setup_path, new_dir)
                else:
                    path = osjoin(self.setup_path,
                                  os.path.sep.join(f.split(os.path.sep)[0:-1]))
                f = f.split(os.path.sep)[-1]
                if not os.path.exists(path):
                    os.makedirs(path)
                shutil.copy(self.temp_path, osjoin(path, f))

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
            self.base_path = os.sep.join(self.base_path.split(os.sep)[0:-1])

        # Set the actual html file path
        if self.report_subdir is not None:
            self.report_path = osjoin(self.base_path, self.report_folder)
        else:
            self.report_path = self.base_path

        # Set the supplemental files path
        if self.setup_subdir is not None:
            self.setup_path = osjoin(self.base_path, self.setup_subdir)
        else:
            self.setup_path = self.base_path


if __name__ == "__main__":
    pass

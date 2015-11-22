############################################################################
# pywebify.py
#   PyWebify is a utility to create browser-based reports of images and html
#   files for easy data analysis.
############################################################################
__author__    = 'Steve Nicholes'
__copyright__ = 'Copyright (C) 2015 Steve Nicholes'
__license__   = 'GPLv3'
__version__   = '.1'
__url__       = 'https://github.com/endangeredoxen/pywebify'

import pdb
from pywebify.files import ConfigFile
from pywebify.files import Dir2HTML
from pywebify.template import Template
import os
import shutil
import platform
import datetime
import sys
sys.path.append(os.path.dirname(__file__))
st = pdb.set_trace
osjoin = os.path.join


def copy_config(dir):
    '''
    Copy the default config file to a user directory for manipulation
    :param dir: directory of the new file
    :return: None
    '''
    filename = 'pywebify.ini'
    if not os.path.exists(dir):
        os.makedirs(dir)
    shutil.copyfile('config.ini', osjoin(dir, filename))


class PyWebify():

    def __init__(self, base_path, **kwargs):
        # Get configuration file
        self.config_path = kwargs.get('config', 'config.ini')
        self.config = getattr(ConfigFile(self.config_path), 'config_dict')

        # Set class attributes
        self.base_path = base_path
        self.browser = kwargs.get('browser', self.config['OPTIONS']['browser'])
        self.css = None
        self.css_path = ''
        self.excludes = []
        self.files = None
        self.from_file = False
        self.html = None
        self.html_dict = {}
        self.html_path = ''
        self.img_path = ''
        self.js_css = ''
        self.js_files = []
        self.make = kwargs.get('make', self.config['OPTIONS']['make'])
        self.navbar_path = ''
        self.open = kwargs.get('open', self.config['OPTIONS']['open'])
        self.output_name = kwargs.get('output_name', self.config['OPTIONS']['output_name'])
        self.output_path = None
        self.rel_path = os.path.dirname(__file__)
        self.report_folder = kwargs.get('report_folder', self.config['OPTIONS']['report_folder'])
        self.show_ext = kwargs.get('show_ext', self.config['OPTIONS']['show_ext'])
        self.special = {}
        self.subtitle = kwargs.get('subtitle', self.config['OPTIONS']['subtitle'])
        self.temp_path = ''
        self.title = kwargs.get('title', self.config['OPTIONS']['title'])

        for key, value in kwargs.items():
            if not hasattr(self, key):
                setattr(self,key,value)

        # Set the output path
        if not self.output_path:
            self.set_output_path()
        self.excludes += [self.output_path]

        # Get the files at base_path
        self.get_files()

        # Get top-level string replacements
        self.get_special()

        if self.make:
            self.run()

    def build_css(self):
        ''' Build the report css file '''

        css_replaces = self.get_replacements('css')

        self.css_path = r'%s' % self.config['TEMPLATES']['css']
        self.check_path('css_path', 'CSS TEMPLATE')
        self.css = Template(self.css_path, css_replaces+[self.special])
        self.css.write(dest=osjoin(self.output_path, 'css', '%s.css' % self.output_name), bonus=self.js_css)

    def build_html(self):
        ''' Build the html report file '''

        # Populate the html replacement dictionary
        self.html_dict['SIDEBAR'] = self.files.ul
        self.html_dict['JS_FILES'], self.js_files, self.js_css = \
            self.get_javascript(self.config['JAVASCRIPT']['files'])

        # Load the html template and build
        self.html_path = r'%s' % self.config['TEMPLATES']['html']
        self.check_path('html_path', 'HTML TEMPLATE')
        self.html = Template(self.html_path,[self.html_dict, self.special])
        self.html.write(dest=osjoin(self.output_path, '%s.html' % self.output_name))

    def build_navbar(self):
        ''' Build the top level navbar menu for the report '''

        self.html_dict['NAVBAR'] = ''
        if 'navbar' in self.config.get('TEMPLATES').keys():
            self.navbar_path = self.config['TEMPLATES']['navbar']
            self.check_path('navbar_path', 'NAVBAR')
            if os.path.exists(self.navbar_path):
                nav_replaces = self.get_replacements('navbar')
                self.navbar = Template(self.navbar_path, nav_replaces+[self.special])
                self.html_dict['NAVBAR'] = self.navbar.write()

    def check_path(self, path, filetype='CONFIG'):
        ''' Handle relative paths '''

        file = getattr(self, path)
        if not os.path.exists(file):
            if os.path.exists(osjoin(self.rel_path, file)):
                setattr(self, path, osjoin(self.rel_path, file))

    def get_files(self):
        ''' Build a Files object that contains information about the files used in the report '''

        self.files = Dir2HTML(self.base_path, self.config['FILES']['ext'],
                              onmouseover=self.config['SIDEBAR']['onmouseover'],
                              onclick=self.config['SIDEBAR']['onclick'],
                              from_file=self.from_file, excludes=self.excludes,
                              show_ext=self.show_ext)

    def get_javascript(self, files):
        '''
        Adds javascript files to the report
        :param files: list of js files from the config file
        '''

        js = ''
        jsfiles = []
        jscss = ''
        for f in files:
            # Define the script call for the html file
            js += '<script type="text/javascript" src="js\%s"></script>\n' % f

            # Add the filename to the js file list
            jsfiles += [osjoin('js',f)]

            # Get any additional css related to the js addition
            self.temp_path = osjoin('templates\css', f.split('.')[0] + '.css')
            self.check_path('temp_path','JS CSS')
            if os.path.exists(self.temp_path):
                with open(self.temp_path, 'r') as input:
                    jscss += input.read()

        return js, jsfiles, jscss

    def get_replacements(self, template):
        '''
        Find parameters in the config file that will be replaced in the given template file
        :param template: template name
        :return: None
        '''
        replaces = []
        for sec in self.config.keys():
            if 'replace_in' in self.config[sec].keys() and self.config[sec]['replace_in'] == template:
                self.config[sec].pop('replace_in')
                replaces += [self.config[sec]]
        return replaces

    def get_special(self):
        ''' Populate special replacement strings '''
        self.special['BASEPATH'] = self.base_path
        self.special['NOW'] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.special['COMPILEDBY'] = platform.node()
        self.special['FAVICON'] = self.config['ICONS']['favicon']
        if self.config['ICONS']['logo'] is None:
            self.special['LOGO'] = ''
        else:
            self.special['LOGO'] = '<img id="img0" src="%s" alt="" />' % self.config['ICONS']['logo']
        self.special['QUANTITY'] = '%s' % len(self.files.files)
        self.special['REPORTNAME'] = self.output_name
        self.special['SUBTITLE'] = self.subtitle
        self.special['SUMMARY'] = ''
        self.special['TITLE'] = self.title

    def launch(self):
        ''' Open the report in the browser '''
        os.startfile(osjoin(self.output_path, '%s.html' % self.output_name))

    def move_files(self, files):
        '''
        Transfer files to the report directory
        :param files: list of filepaths to transfer
        :return: None
        '''
        for f in files:
            self.temp_path = f
            self.check_path('temp_path', f)
            if os.path.exists(self.temp_path):
                path = os.path.sep.join(osjoin(self.output_path,f).split(os.path.sep)[0:-1])
                if not os.path.exists(path):
                    os.makedirs(path)
                shutil.copy(self.temp_path, osjoin(self.output_path,f))

    def run(self):
        ''' Build, move, and open the report files '''

        # Build the navbar
        self.build_navbar()

        # Build the html file
        self.build_html()

        # Build the css file
        self.build_css()

        # Move any static files
        self.move_files(self.js_files)

        self.img_path = self.config['FILES']['img_dir']
        self.check_path('img_path', 'IMAGE DIR')
        self.move_files([osjoin('img', f) for f in os.listdir(self.img_path)])

        # Open web report
        if self.open:
            self.launch()

    def set_output_path(self):
        if self.from_file:
            self.output_path = os.sep.join(self.base_path.split(os.sep)[0:-1])
        else:
            self.output_path = self.base_path
        self.output_path = osjoin(self.output_path,self.report_folder)


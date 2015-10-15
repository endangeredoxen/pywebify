import argparse
import configparser
from pywebify.files import Files
from pywebify.template import Template
import os
osjoin = os.path.join
import pdb
st = pdb.set_trace
import shutil
import platform
import datetime
import sys
sys.path.append(os.path.dirname(__file__))


class PyWebify():

    def __init__(self, base_path, **kwargs):
        # Set class attributes
        self.base_path = base_path
        self.browser = 'default'
        self.config = 'config.ini'
        self.config_path = ''
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
        self.make = False
        self.navbar_path = ''
        self.open = True
        self.output_name = 'webify'
        self.output_path = None
        self.rel_path = os.path.dirname(__file__)
        self.special = {}
        self.subtitle = ''
        self.temp_path = ''
        self.title = 'My Report'

        for key, value in kwargs.items():
            setattr(self,key,value)

        # Open and parse the config file
        self.get_config_file()

        # Get the files at base_path
        self.get_files()

        # Get top-level string replacements
        self.get_special()

        if self.make:
            self.run()

    def build_css(self):
        ''' Build the report css file '''

        css_replaces = self.get_replacements('css')

        self.css_path = r'%s' % self.config.get('TEMPLATES','css')
        self.check_path('css_path', 'CSS TEMPLATE')
        self.css = Template(self.css_path, css_replaces+[self.special])
        self.css.write(dest=osjoin(self.output_path, 'html', 'css', '%s.css' % self.output_name), bonus=self.js_css)

    def build_html(self):
        ''' Build the html report file '''

        # Populate the html replacement dictionary
        self.html_dict['SIDEBAR'] = self.files.ul
        self.html_dict['JS_FILES'], self.js_files, self.js_css = \
            self.get_javascript(self.config.get('JAVASCRIPT','files'))

        # Load the html template and build
        self.html_path = r'%s' % self.config.get('TEMPLATES','html')
        self.check_path('html_path', 'HTML TEMPLATE')
        self.html = Template(self.html_path,[self.html_dict, self.special])
        self.html.write(dest=osjoin(self.output_path, 'html', 'webify.html'))

    def build_navbar(self):
        ''' Build the top level navbar menu for the report '''

        self.html_dict['NAVBAR'] = ''
        if self.config.has_option('TEMPLATES','navbar'):
            self.navbar_path = self.config.get('TEMPLATES','navbar')
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

    def get_config_file(self):
        ''' Config file parsing '''

        self.check_path('config')
        self.config_path = '%s' % self.config
        self.config = configparser.RawConfigParser()
        self.config.read(self.config_path)

    def get_files(self):
        ''' Build a Files object that contains information about the files used in the report '''

        self.files = Files(self.base_path, self.config.get('FILES','ext'),
                           onmouseover=self.config.get('SIDEBAR','onmouseover'),
                           onclick=self.config.get('SIDEBAR','onclick'),
                           from_file=self.from_file, excludes=self.excludes)

    def get_javascript(self, files):
        '''
        Adds javascript files to the report
        :param files: list of js files from the config file
        '''

        files = files.split(',')
        files = [f.lstrip() for f in files]
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
        for sec in self.config.sections():
            d = dict(self.config.items(sec))
            if 'replace_in' in d.keys() and d['replace_in'] == template:
                d.pop('replace_in')
                replaces += [d]
        return replaces

    def get_special(self):
        ''' Populate special replacement strings '''
        self.special['BASEPATH'] = self.base_path
        self.special['NOW'] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.special['COMPILEDBY'] = platform.node()
        self.special['FAVICON'] = self.config.get('ICONS','favicon')
        self.special['QUANTITY'] = '%s' % len(self.files.files)
        self.special['SUBTITLE'] = self.subtitle
        self.special['SUMMARY'] = ''
        self.special['TITLE'] = self.title

    def launch(self):
        ''' Open the report in the browser '''
        os.startfile(osjoin(self.output_path, 'html', '%s.html' % self.output_name))

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
                path = os.path.sep.join(osjoin(self.output_path,'html',f).split(os.path.sep)[0:-1])
                if not os.path.exists(path):
                    os.makedirs(path)
                shutil.copy(self.temp_path, osjoin(self.output_path,'html',f))

    def run(self):
        ''' Build, move, and open the report files '''

        # Set the output path
        if not self.output_path:
            self.set_output_path()

        # Build the navbar
        self.build_navbar()

        # Build the html file
        self.build_html()

        # Build the css file
        self.build_css()

        # Move any static files
        self.move_files(self.js_files)

        self.img_path = self.config.get('FILES','img_dir')
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

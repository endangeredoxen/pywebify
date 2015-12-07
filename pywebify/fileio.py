############################################################################
# files.py
#   Contains classes for reading various types of files
############################################################################
__author__    = 'Steve Nicholes'
__copyright__ = 'Copyright (C) 2015 Steve Nicholes'
__license__   = 'GPLv3'
__version__   = '.1'
__url__       = 'https://github.com/endangeredoxen/pywebify'


try:
    import configparser
except:
    import ConfigParser as configparser
import os
try:
    import scandir
    oswalk = scandir.walk
except:
    oswalk = os.walk
    print('scandir module not found! Try installing for faster file reading performance ' +
          '(http://www.lfd.uci.edu/~gohlke/pythonlibs/#scandir).')
import pandas as pd
import pdb
import pathlib
from xml.dom import minidom
from xml.etree import ElementTree
import numpy as np
from docutils import core
from natsort import natsorted
osjoin = os.path.join
st = pdb.set_trace


def convert_rst(file_name, stylesheet=None):
    '''
    Converts single rst files to html
      Adapted from Andrew Pinion's solution @
      http://halfcooked.com/blog/2010/06/01/generating-html-versions-of-restructuredtext-files/
    :param file_name: Name of rst file to convert to html
    :param stylesheet: Optional path to a stylesheet
    :return: None
    '''
    settings_overrides=None
    if stylesheet is not None:
        if type(stylesheet) is not list:
            stylesheet = [stylesheet]
        settings_overrides = {'stylesheet_path':stylesheet}
    source = open(file_name, 'r')
    file_dest = os.path.splitext(file_name)[0] + '.html'
    destination = open(file_dest, 'w')
    core.publish_file(source=source, destination=destination, writer_name='html',
                      settings_overrides=settings_overrides)
    source.close()
    destination.close()


def read_csv(file_name, **kwargs):
    '''
    Wrapper for pandas.read_csv to deal with kwargs overload
    :param file_name: str; filename
    :param kwargs: keyword arguments
    :return: pandas.DataFrame
    '''

    kw_master = []

    delkw = [f for f in kwargs.keys() if f not in kw_master]
    for kw in delkw:
        kwargs.pop(kw)

    return pd.read_csv(file_name, **kwargs)


def str_2_dtype(val):
    '''
    Convert a string to the most appropriate data type
    :param val:
    :return:
    '''

    # Remove comments
    v = val.split('#')
    if len(v) > 1:  # handle comments
        if v[0] == '':
            val = '#' + v[1].rstrip().lstrip()
        else:
            val = v[0].rstrip().lstrip()

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
        k = val.split(':').rstrip().lstrip()[0]
        v = str_2_dtype(val.split(':').rstrip().lstrip()[1])
        return {k:v}
    # list
    if ',' in val or '[' in val:
        val = val.replace('[','').replace(']','')
        new = []
        for v in val.split(','):
            new += [str_2_dtype(v.rstrip().lstrip())]
        return new
    # float and int
    try:
        int(val)
        return int(val)
    except:
        try:
            float(val)
            return float(val)
        except:
            return val


class ConfigFile():
    def __init__(self, path):
        '''
        Read and parse a config.ini file
        :param path: location of the ini file
        :return: object containing config file attributes
        '''
        self.config_path = path
        self.config = None
        self.config_dict = {}
        self.is_valid = False
        self.rel_path = os.path.dirname(__file__)

        self.validate_file_path()

        if self.is_valid:
            self.read_file()
        else:
            raise ValueError('Could not find a config.ini file at the following location: %s' % self.config_path)

        self.make_dict()

    def make_dict(self):
        '''
        Convert the configparser object into a dictionary for easier handling
        '''
        self.config_dict = {s:{k:str_2_dtype(v) for k,v in self.config.items(s)} for s in self.config.sections()}

    def read_file(self):
        '''
        Read the config file
        '''
        self.config = configparser.RawConfigParser()
        self.config.read(self.config_path)

    def validate_file_path(self):
        '''
        Make sure there is a valid config file at the location specified by self.config_path
        '''

        if os.path.exists(self.config_path):
            self.is_valid = True
        else:
            if os.path.exists(osjoin(self.rel_path, file)):
                self.config_path = osjoin(self.rel_path, self.config_path )
                self.is_valid = True


class Dir2HTML():
    def __init__(self, base_path, ext=None, **kwargs):
        '''
        Converts a list of directories/files to an HTML unordered list (UL)
        :param base_path: str; top level directory or path to a list of files to use in the report
        :param ext: list; file types to include when building file list
        :param kwargs: see below
        :Keyword Arguments:
            * build_rst: boolean; convert rst files to html
            * excludes: list; names of files to exclude from the UL
            * from_file: boolean; make the report from a file containing a list of directories + files or just scan the
                         base_path directory
            * natsort: boolean; use natural (human) sorting on the file list
            * onclick: boolean; enable click to open for files listed in the UL
            * onmouseover: boolean; enable onmouseover viewing for files listed in the UL
            * rst_css: str; path to css file for rst files
            * show_ext: boolean; show/hide file extension in the file list
            
        '''
        
        self.base_path = base_path
        self.build_rst = kwargs.get('build_rst', False)
        self.excludes = kwargs.get('excludes',[])
        self.files = []
        self.from_file = kwargs.get('from_file', False)
        self.natsort = kwargs.get('natsort', True)
        self.onclick = kwargs.get('onclick', None)
        self.onmouseover = kwargs.get('onmouseover', None)
        self.rst = ''
        self.rst_css = kwargs.get('rst_css', None)
        self.show_ext = kwargs.get('show_ext', False)

        self.ext = ext
        if self.ext is not None and type(self.ext) is not list:
            self.ext = self.ext.replace(' ','').split(',')
            self.ext = [f.lower() for f in self.ext]

        self.get_files(self.from_file)
        if self.build_rst:
            self.make_html()
        self.filter()
        self.files = self.files.drop_duplicates().reset_index(drop=True)
        self.nan_to_str()
        self.make_links()
        self.make_ul()

    def df_to_xml(self, df, parent_node=None, parent_name=''):

        def node_for_value(name, value, parent_node, parent_name, dir=False):
            """
            creates the <li><input><label>...</label></input></li> elements.
            returns the <li> element.
            """
            node= ElementTree.SubElement(parent_node, 'li')
            child= ElementTree.SubElement(node, 'A')
            if self.onmouseover and not dir:
                child.set('onmouseover', self.onmouseover+"('"+value+"')")
            if self.onclick and not dir:
                child.set('onclick', self.onclick+"('"+value+"')")
                child.set('href', 'javascript:void(0)')
            elif self.onclick and dir:
                child.set('onclick', self.onclick+"('"+value+"')")
                child.set('href', 'javascript:void(0)')
            child.text= name
            return node

        subdirs = [f for f in df.columns if 'subdir' in f]

        if parent_node is None:
            node = ElementTree.Element('ul')
        else:
            node = ElementTree.SubElement(parent_node, 'ul')
        node.set('id', 'collapse')

        if len(subdirs) > 0:
            groups = df.groupby(subdirs[0])
            for i, (n, g) in enumerate(groups):
                del g[subdirs[0]]
                if n == 'nan':
                    for row in range(0,len(g)):
                        node_for_value(g.filename.iloc[row], g.html_path.iloc[row], node, parent_name)
                else:
                    current_path_list = g.full_path.iloc[0].split(os.path.sep)
                    path_idx = current_path_list.index(n)
                    folder_path = os.path.sep.join(current_path_list[0:path_idx+1])
                    try:
                        folder_path = pathlib.Path(folder_path).as_uri()
                    except:
                        st()
                    child = node_for_value(n, folder_path, node, parent_name, dir=True)
                    self.df_to_xml(g, child, n)

        else:
            for row in range(0,len(df)):
                node_for_value(df.filename.iloc[row], df.html_path.iloc[row], node, parent_name)

        return node

    def get_files(self, from_file):
        if from_file:
            with open(self.base_path,'r') as input:
                files = input.readlines()
            temp = pd.DataFrame()
            files = [f.strip('\n') for f in files if len(f) > 0]
            for f in files:
                self.base_path = f
                self.get_files(False)
                temp = pd.concat([temp,self.files])
            self.files = temp.reset_index(drop=True)

        else:
            self.files = []
            for dirName, subdirList, fileList in oswalk(self.base_path):
                if self.ext is not None:
                    fileList = [f for f in fileList if f.split('.')[-1].lower() in self.ext]
                for fname in fileList:
                    temp = {}
                    temp['full_path'] = os.path.abspath(osjoin(self.base_path,dirName,fname))
                    temp['html_path'] = pathlib.Path(temp['full_path']).as_uri().replace('file:', r'file:///')
                    temp['ext'] = fname.split('.')[-1]
                    if self.from_file:
                        top = self.base_path.split(os.sep)[-1]
                        subdirs = temp['full_path'].replace(self.base_path.replace(top,''),'').split(os.sep)
                    else:
                        subdirs = temp['full_path'].replace(self.base_path+os.sep,'').split(os.sep)
                    temp['base_path'] = self.base_path
                    for i,s in enumerate(subdirs[:-1]):
                        temp['subdir%s' % i] = s
                    temp['filename_ext'] = subdirs[-1]
                    temp['filename'] = os.path.splitext(subdirs[-1])[0]
                    self.files += [temp]

            if len(self.files) == 0 and os.path.exists(self.base_path) and self.base_path.split('.')[-1] in self.ext:
                temp = {}
                temp['full_path'] = os.path.abspath(self.base_path)
                temp['html_path'] = pathlib.Path(temp['full_path']).as_uri()
                subdirs = temp['full_path'].split(os.sep)
                temp['base_path'] = os.sep.join(subdirs[0:-1])
                temp['filename'] = subdirs[-1]
                self.files += [temp]

            self.files = pd.DataFrame(self.files)

            if self.natsort:
                temp = self.files.set_index('full_path')
                self.files = temp.reindex(index=natsorted(temp.index)).reset_index()

    def filter(self):
        for ex in self.excludes:
            self.files = self.files[~self.files.full_path.str.contains(ex, regex=False)].reset_index(drop=True)

    def make_html(self):
        ''' Build html files from rst files '''
        self.rst = self.files[self.files.ext=='rst']
        for i, f in self.rst.iterrows():
            convert_rst(f['full_path'], stylesheet=self.rst_css)
            self.files.iloc[i]['ext'] = 'html'
            self.files.iloc[i]['filename'] = self.files.iloc[i]['filename'].replace('rst','html')
            self.files.iloc[i]['filename_ext'] = self.files.iloc[i]['filename_ext'].replace('rst','html')
            self.files.iloc[i]['full_path'] = self.files.iloc[i]['full_path'].replace('rst','html')
            self.files.iloc[i]['html_path'] = self.files.iloc[i]['html_path'].replace('rst','html')

    def make_links(self):
        self.files['link'] = '''<A onmouseover="div_switch(' ''' + \
                             self.files.html_path.map(str) + \
                             '''')" onclick="HREF=window.open(' ''' + \
                             self.files.html_path.map(str) + \
                             '''')"href="javascript:void(0)">''' + \
                             self.files.filename.map(str) + \
                             '''</A><br>'''

    def make_ul(self):
        element= self.df_to_xml(self.files)
        xml = ElementTree.tostring(element)
        xml = minidom.parseString(xml)
        self.ul = xml.toprettyxml(indent='  ')
        self.ul = self.ul.replace('<?xml version="1.0" ?>\n', '')

    def nan_to_str(self):
        self.files = self.files.replace(np.nan, 'nan')


class FileReader():
    def __init__(self, path, **kwargs):
        '''
        Reads multiple raw data files into memory based on a partial path name or a list of files and populates them
        into a single pandas DataFrame or a list of DataFrames
        :param path: str|list; partial path name or a list of files
        :param kwargs: see below
        :Keyword Arguments:
            * contains: str; search string used to filter the file list (default='')
            * concat: boolean; True=concatenate all DataFrames into one | False=return a list of DataFrames
                      (default=True)
            * gui: boolean; True=use a PyQt4 gui prompt to select files | False=search directories automatically
            * labels: list|str; adds a special label column to the DataFrame for distinguishing between files
                      list=one entry per DataFrame added in order of self.file_list
                      str: single label added to all files (ex. today's date, username, etc.)
            * file_tags: list; values separated by self.tag_char in the filename that can be added as columns to the
                         file (ex. Filename='MyData_T=25C.txt' --> file_tags=['T'] and tag_char='=' to extract)
            * file_split: str; str by which to split the filename.  Can be used with split_fields to extract values from
                          a filename (ex. Filename='MyData_20151225_Wfr16.txt' --> file_split = '_' and
                          split_fields = [None, 'Date', 'Wafer'] (None are ignored)
            * read: boolean; read the DataFrames after compiling the file_list
            * scan: boolean; search subdirectories
            * split_fields: list; values to extract from the filename based on file_split (ex. Filename=
                            'MyData_20151225_Wfr16.txt' --> file_split = '_' and split_fields = [None, 'Date', 'Wafer']
                            (None are ignored)
            * tag_char: str; split character for file tag values (ex. Filename='MyData_T=25C.txt' --> file_tags=['T']
                             and tag_char='=' to extract)
            * verbose: boolean; print file read progress
        '''

        self.path = path
        self.contains = kwargs.get('contains', '')
        self.header = kwargs.get('header', True)
        self.concat = kwargs.get('concat', True)
        self.ext = kwargs.get('ext', '')
        self.gui = kwargs.get('gui', False)
        self.labels = kwargs.get('labels', [])
        self.scan = kwargs.get('scan', False)
        self.file_tags = kwargs.get('file_tags', [])
        self.file_tags_parsed = {}
        self.file_split = kwargs.get('file_split', '_')
        self.read = kwargs.get('read', True)
        self.split_fields = kwargs.get('split_fields', [])
        self.tag_char = kwargs.get('tag_char', '=')
        self.file_list = []
        self.verbose = kwargs.get('verbose', False)
        self.read_func = kwargs.get('read_func', read_csv)
        self.kwargs = kwargs

        # Format ext
        if self.ext != '':
            if type(self.ext) is not list:
                self.ext = [self.ext]
            for i, ext in enumerate(self.ext):
                if ext[0] != '.':
                    self.ext[i] = '.' + ext

        if self.concat:
            self.df = pd.DataFrame()
        else:
            self.df = []

        self.get_files()

        if self.read:
            self.read_files()

    def get_files(self):
        '''
        Search directories automatically or manually by gui for file paths to add to self.file_list
        '''

        # Gui option
        if self.gui:
            self.gui_search()

        # If list of files is passed to FileReader with no scan option
        elif type(self.path) is list and self.scan != False:
            self.file_list = self.path

        # If list of files is passed to FileReader with a scan option
        elif type(self.path) is list and self.scan == True:
            for p in self.path:
                self.walk_dir(p)

        # If single path is passed to FileReader
        elif self.scan:
            self.walk_dir(self.path)

        # No scanning - use provided path
        else:
            self.file_list = [self.path]

        # Filter based on self.contains search string
        self.file_list = [f for f in self.file_list if self.contains in f]

        # Filter based on self.ext
        try:
            if self.ext != '':
                self.file_list = [f for f in self.file_list if os.path.splitext(f)[-1] in self.ext]
        except:
            raise ValueError('File name list is malformatted: \n   %s\nIf you passed a path and ' % self.file_list + \
                             'meant to scan the directory, please set the "scan" parameter to True')

    def gui_search(self):
        '''
        Search for files using a PyQt4 gui
            Add new files to self.file_list
        '''

        from PyQt4 import QtGui

        done = False
        while done != QtGui.QMessageBox.Yes:
            # Open the file dialog
            self.file_list += QtGui.QFileDialog.getOpenFileNames(None, 'Pick files to open', self.path)

            # Check if all files have been selected
            done = QtGui.QMessageBox.question(None, 'File search', 'Finished adding files?',
                                               QtGui.QMessageBox.Yes | QtGui.QMessageBox.No, QtGui.QMessageBox.Yes)

    def parse_filename(self, filename, df):
        '''
        Parse the filename to retrieve attributes for each file
        :param: filename: str; name of the file
        :param: df: pandas.DataFrame; DataFrame containing the data found in filename
        :return: updated Dataframe
        '''

        filename = filename.split(os.path.sep)[-1]  # remove the directory
        filename = ''.join(filename.split('.')[0:-1]) # remove the extension

        # Handle file_splits
        file_splits = filename.split(self.file_split)
        for i, f in enumerate(self.split_fields):
            if f is not None:
                df[f] = str_2_dtype(file_splits[i])

        # Handle file tags
        for i, f in enumerate(self.file_tags):
            val = [k for k in file_splits if f in k]
            val_split = val[0].split(self.tag_char)
            if len(val_split) > 0:
                df[val_split[0]] = str_2_dtype(val_split[1])

        return df

    def read_files(self):
        '''
        Read the files in self.file_list (assumes all files can be cast into pandas DataFrames)
        '''

        if self.verbose:
            print('Reading files...')

        for i, f in enumerate(self.file_list):

            # Read the raw data file
            try:
                if self.verbos:
                    print('   %s' % f)
                temp = self.read_func(f, **self.kwargs)
            except:
                raise ValueError('Could not read "%s".  Is it a valid data file?' % f)

            # Add optional info to the table
            if type(self.labels) is list and len(self.labels) > i:
                temp['Label'] = self.labels[i]
            elif self.labels == '#':
                temp['Label'] = i
            elif type(self.labels) is str:
                temp['Label'] = self.labels

            # Optionally parse the filename to add new columns to the table
            if type(self.file_tags) is list and len(self.file_tags) > 0:
                temp = self.parse_filename(f, temp)

            # Add filename
            temp['Filename'] = f

            # Add to master
            if self.concat:
                self.df = pd.concat([self.df, temp])
            else:
                self.df += [temp]

        if self.concat:
            self.df = self.df.reset_index(drop=True)

    def walk_dir(self, path):
        '''
        Walk through a directory and its subfolders to find file names
        :param path: top level directory
        '''

        for dir_name, subdir_list, file_list in oswalk(path):
            self.file_list += [os.path.join(dir_name, f) for f in file_list]
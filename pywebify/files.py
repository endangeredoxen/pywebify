import os
osjoin = os.path.join
import scandir
import pandas as pd
import pdb
st = pdb.set_trace
import pathlib
from xml.dom import minidom
from xml.etree import ElementTree
import numpy as np
from docutils import core


class Files():
    def __init__(self, base_path, ext=None, **kwargs):
        self.base_path = base_path
        self.build_rst = kwargs.get('build_rst', False)
        self.excludes = kwargs.get('excludes',[])
        self.files = []
        self.from_file = kwargs.get('from_file', False)
        self.onclick = kwargs.get('onclick',None)
        self.onmouseover = kwargs.get('onmouseover',None)
        self.rst = ''
        self.rst_stylesheet = kwargs.get('rst_stylesheet',None)

        self.ext = ext
        if self.ext is not None and type(self.ext) is not list:
            self.ext = self.ext.replace(' ','').split(',')
            self.ext = [f.lower() for f in self.ext]

        self.get_files(self.from_file)
        self.filter()
        if self.build_rst:
            self.make_html()
        self.files = self.files.drop_duplicates().reset_index(drop=True)
        self.nan_to_str()
        self.make_links()
        self.make_ul()

    def convert_rst(self, file_name, stylesheet=None):
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
                    folder_path = pathlib.Path(folder_path).as_uri()
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
            for dirName, subdirList, fileList in scandir.walk(self.base_path):
                if self.ext is not None:
                    fileList = [f for f in fileList if f.split('.')[-1].lower() in self.ext]
                for fname in fileList:
                    temp = {}
                    temp['full_path'] = osjoin(self.base_path,dirName,fname)
                    temp['html_path'] = pathlib.Path(temp['full_path']).as_uri()
                    temp['ext'] = fname[-3:]
                    if self.from_file:
                        top = self.base_path.split(os.sep)[-1]
                        subdirs = temp['full_path'].replace(self.base_path.replace(top,''),'').split(os.sep)
                    else:
                        subdirs = temp['full_path'].replace(self.base_path+os.sep,'').split(os.sep)
                    temp['base_path'] = self.base_path
                    for i,s in enumerate(subdirs[:-1]):
                        temp['subdir%s' % i] = s
                    temp['filename'] = subdirs[-1]
                    self.files += [temp]

            if len(self.files) == 0 and os.path.exists(self.base_path) and self.base_path.split('.')[-1] in self.ext:
                temp = {}
                temp['full_path'] = self.base_path
                temp['html_path'] = pathlib.Path(temp['full_path']).as_uri()
                subdirs = temp['full_path'].split(os.sep)
                temp['base_path'] = os.sep.join(subdirs[0:-1])
                temp['filename'] = subdirs[-1]
                self.files += [temp]

            self.files = pd.DataFrame(self.files)

    def filter(self):
        for ex in self.excludes:
            self.files = self.files[~self.files.full_path.str.contains(ex)]

    def make_html(self):
        ''' Build html files from rst files '''
        self.rst = self.files[self.files.ext=='rst']
        for i, f in self.rst.iterrows():
            self.convert_rst(f['full_path'], stylesheet=self.rst_stylesheet)
            self.files.iloc[i]['ext'] = 'html'
            self.files.iloc[i]['filename'] = self.files.iloc[i]['filename'].replace('rst','html')
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

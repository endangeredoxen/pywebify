import os
osjoin = os.path.join
import scandir
import pandas as pd
import pdb
st = pdb.set_trace
import pathlib


class Files():
    def __init__(self, base_path, ext=None, **kwargs):
        self.base_path = base_path

        self.ext = ext
        if self.ext is not None:
            self.ext = self.ext.replace(' ','').split(',')
            self.ext = [f.lower() for f in self.ext]

        self.get_files()

    def get_files(self):
        subdir_list = []
        self.files = []
        for dirName, subdirList, fileList in scandir.walk(self.base_path):
            if self.ext is not None:
                fileList = [f for f in fileList if f.split('.')[-1].lower() in self.ext]
            for fname in fileList:
                temp = {}
                temp['full_path'] = osjoin(self.base_path,dirName,fname)
                temp['html_path'] = pathlib.Path(temp['full_path']).as_uri()
                subdirs = temp['full_path'].replace(self.base_path+os.sep,'').split(os.sep)
                temp['base_path'] = self.base_path
                for i,s in enumerate(subdirs[:-1]):
                    temp['subdir%s' % i] = s
                    if 'subdir%s' % i not in subdir_list:
                        subdir_list += ['subdir%s' % i]
                temp['filename'] = subdirs[-1]
                self.files += [temp]

        self.files = pd.DataFrame(self.files)
        self.make_links()

    def make_links(self):
        self.files['link'] = '\t'*1 + \
                             '''<li><A onmouseover="div_switch(' ''' + \
                             self.files.html_path.map(str) + \
                             '''')" onclick="HREF=window.open(' ''' + \
                             self.files.html_path.map(str) + \
                             '''')"href="javascript:void(0)">''' + \
                             self.files.filename.map(str) + \
                             '''</A><br></li>\n'''
#################################################################################
# html.py
#
#   Classes and functions for reading and outputting html-based files using pandas
#
##################################################################################
__author__ = 'Steve Nicholes'
__copyright__ = 'Copyright (C) 2017 Steve Nicholes'
__license__ = 'GPLv3'
__url__ = 'https://github.com/endangeredoxen/pywebify'

import os
import pandas as pd
import pdb
import re
from xml.dom import minidom
from xml.etree import ElementTree
import numpy as np
from docutils import core
from natsort import natsorted
from pathlib import Path
from typing import Union
osjoin = os.path.join
db = pdb.set_trace


def convert_rst(file_name: Union[str, Path], stylesheet: Union[str, None] = None):
    """Converts single rst files to html.

    Adapted from Andrew Pinion's solution @ http://halfcooked.com/blog/2010/06/01/generating-html-versions-of-
        restructuredtext-files/

    Args:
        file_name: name of rst file to convert to html
        stylesheet: optional path to a stylesheet
    """
    # Configure any css stylesheets
    if not stylesheet:
        settings_overrides = None
    else:
        if not isinstance(stylesheet, list):
            stylesheet = [stylesheet]
        settings_overrides = {'stylesheet_path': stylesheet}

    # Build the rst with docutils
    source = open(file_name, 'r')
    file_dest = os.path.splitext(file_name)[0] + '.html'
    destination = open(file_dest, 'w')
    core.publish_file(source=source, destination=destination, writer_name='html', settings_overrides=settings_overrides)
    source.close()
    destination.close()

    # Fix issue with spaces in figure path and links
    with open(file_name, 'r') as input:
        rst = input.readlines()

    with open(file_dest, 'r') as input:
        html = input.read()

    # Case of figures
    imgs = [f for f in rst if 'figure::' in f]
    for img in imgs:
        img = img.replace('.. figure:: ', '').replace('\n', '').lstrip()
        if ' ' in img:
            img_ns = img.replace(' ', '').replace('\\', '')
            idx = html.find(img_ns) - 5
            if idx < 0:
                continue
            old = 'alt="%s" src="%s"' % (img_ns, img_ns)
            new = 'alt="%s" src="%s"' % (img, img)
            html = html[0:idx] + new + html[idx+len(old):]

            with open(file_dest, 'w') as output:
                output.write(html)

    # Case of substituted images
    imgs = [f for f in rst if 'image::' in f]
    for img in imgs:
        img = img.replace('.. image:: ', '').replace('\n', '').lstrip()
        if ' ' in img:
            img_ns = img.replace(' ', '').replace('\\', '')
            idx = html.find(img_ns) - 5
            if idx < 0:
                continue
            old = 'alt="%s" src="%s"' % (img_ns, img_ns)
            new = 'alt="%s" src="%s"' % (img, img)
            html = html[0:idx] + new + html[idx+len(old):]

            with open(file_dest, 'w') as output:
                output.write(html)

    # Case of links
    links = [f for f in rst if ">`_" in f]
    for link in links:
        try:
            link = re.search("<(.*)>`_", link).group(1)
        except:  # noqa
            print('invalid rst link: "%s"' % link)
            continue
        if ' ' in link:
            link_ns = link.replace(' ', '')
            idx = html.find(link_ns)
            html = html[0:idx] + link + html[idx+len(link_ns):]
            with open(file_dest, 'w') as output:
                output.write(html)


class EmptyReportError(Exception):
    def __init__(self, *args, **kwargs):
        """Empty report error."""
        Exception.__init__(self, *args, **kwargs)


class Dir2HTML():
    def __init__(self, base_path: Union[str, Path], ext: Union[list, None] = None, **kwargs):
        """Directory to unordered html list (UL) conversion tool.

        Args:
            base_path: top level directory or path to a list of files to use in the UL
            ext: file extensions to include when building file list

        Keyword Args:
            build_rst (bool): convert rst files to html. Defaults to True.
            exclude (list): names of files to exclude from the UL
            from_file (bool): make the report from a text file containing a
                list of directories and files or just scan the
                base_path directory
            natsort (bool): use natural (human) sorting on the file list
            onclick (bool): enable click to open for files listed in the UL
            onmouseover (bool): enable onmouseover viewing for files listed in
                the UL
            rst_css (str): path to css file for rst files
            show_ext (bool): show/hide file extension in the file list
            use_relative (bool):  use relative paths.  Defaults to True.
        """
        self.base_path = base_path
        if isinstance(self.base_path, str):
            self.base_path = Path(self.base_path)
        self.build_rst = kwargs.get('build_rst', True)
        self.exclude = kwargs.get('exclude', [])
        self.files = []
        self.from_file = kwargs.get('from_file', False)
        self.merge_html = kwargs.get('merge_html', True)
        self.natsort = kwargs.get('natsort', True)
        self.onclick = kwargs.get('onclick', None)
        self.onmouseover = kwargs.get('onmouseover', None)
        self.rst_css = kwargs.get('rst_css', None)
        self.rst_files = []
        self.show_ext = kwargs.get('show_ext', False)
        self.ul = '<ul>'
        self.use_relative = kwargs.get('use_relative', True)

        self.ext = ext
        if self.ext is not None and not isinstance(self.ext, list):
            self.ext = self.ext.replace(' ', '').split(',')
            self.ext = [f.lower() for f in self.ext]
        elif not self.ext or len(self.ext) == 0:
            raise ValueError('list of file extensions is required')

        self.get_files(self.from_file)
        if len(self.files) == 0:
            raise EmptyReportError(f'No files found with extension(s): {", ".join(self.ext)}.  Report is empty!')

        if self.build_rst and 'rst' in self.files.ext.str.lower().values:
            self.make_rst()
        self.filter()
        self.drop_duplicates()
        self.nan_to_str()
        self.make_links()
        self.make_ul()

    def df_to_xml(self, df: pd.DataFrame, parent_node: Union[ElementTree.Element, None] = None, parent_name: str = ''):
        """Builds an xml structure from a DataFrame.

        Args:
            df:  directory structure
            parent_node:  parent node in the xml structure
            parent_name:  string name of the node

        Returns:
            node:  ElementTree xml representation of df
        """
        def node_for_value(name, value, parent_node, parent_name, dir=False, set_id=None):
            """creates the <li><input><label>...</label></input></li> elements.
            returns the <li> element.
            """

            node = ElementTree.SubElement(parent_node, 'li')
            child = ElementTree.SubElement(node, 'A')
            if set_id is not None:
                child.set('id', set_id)
            if self.onmouseover and not dir:
                child.set('onmouseover', self.onmouseover+"('"+value+"')")
            if self.onclick and not dir:
                child.set('onclick', self.onclick+"('"+value+"')")
                child.set('href', self.href(value))
            elif self.onclick and dir:
                child.set('onclick', self.onclick+"('"+value+"')")
                child.set('href', self.href(value))
            child.text = name
            return node

        subdirs = [f for f in df.columns if 'subdir' in f]

        if parent_node is None:
            node = ElementTree.Element('ul')
        else:
            node = ElementTree.SubElement(parent_node, 'ul')
        node.set('id', 'collapse')

        if len(subdirs) > 0:
            groups = df.groupby(subdirs[0], sort=False)
            for i, (n, g) in enumerate(groups):
                del g[subdirs[0]]
                if n == 'nan':
                    for row in range(0, len(g)):
                        node_for_value(g.filename.iloc[row], g.html_path.iloc[row], node,
                                       parent_name, set_id='image_link')
                else:
                    try:
                        idx = g.full_path.apply(lambda x: len(x.split(os.path.sep))).idxmin()
                    except:  # noqa
                        idx = g.full_path.apply(lambda x: len(x.split(os.path.sep))).argmin()
                    folder_path = os.sep.join(g.loc[idx, 'full_path'].split(os.sep)[0:-1])
                    if self.use_relative:
                        folder_path = folder_path.replace(str(self.base_path) + os.sep, '')
                        folder_path = folder_path.replace(os.sep, '/')
                    else:
                        folder_path = Path(folder_path).as_uri()
                    child = node_for_value(n, folder_path, node, parent_name, dir=True)
                    self.df_to_xml(g, child, n)

        else:
            for row in range(0, len(df)):
                node_for_value(df.filename.iloc[row], df.html_path.iloc[row], node, parent_name, set_id='image_link')

        return node

    def drop_duplicates(self):
        """Remove duplicate values and for image + html, reduce to one link."""
        # Drop complete duplicates
        self.files = self.files.drop_duplicates().reset_index(drop=True)

        # Condense html + image file pairs
        if self.merge_html:
            subdir_cols = [f for f in self.files.columns if 'subdir' in f]
            dups = self.files[subdir_cols + ['filename']].duplicated()
            dup_idx = list(dups[dups].index)
            for ii, idx in enumerate(dup_idx):
                if self.files.loc[idx, 'ext'] != 'html':
                    dup_idx[ii] = idx - 1
            self.files = self.files.drop(dup_idx).reset_index(drop=True)

    def get_files(self, from_file: bool):
        """Get the files for the report.

        Args:
            from_file:  use a text file to identify the directories and files to be used in the report
        """
        def paths_to_str(temp: dict) -> dict:
            """Convert pathlibs to str.

            Args:
                temp: dict of filename keys

            Returns:
                updated dict
            """
            keys = ['full_path', 'rel_path', 'html_path', 'base_path', 'filename']
            for k in keys:
                temp[k] = str(temp[k])
            return temp

        if from_file:
            # Build the list from a text file
            with open(self.base_path, 'r') as input:
                files = input.readlines()
            temp = pd.DataFrame()
            files = [f.strip('\n') for f in files if len(f) > 0]
            for f in files:
                self.base_path = Path(f).resolve()
                self.get_files(False)
                if len(self.files) > 0:
                    temp = pd.concat([temp, self.files])
            self.files = temp.reset_index(drop=True)

        else:
            # Walk the base_path to identify all the files for the report
            self.files = []
            for dir_name, subdir_list, file_list in os.walk(self.base_path):
                file_list = [f for f in file_list if f.split('.')[-1].lower() in self.ext]
                for fname in file_list:
                    fname = Path(fname)
                    temp = {}
                    temp['full_path'] = (self.base_path / dir_name / fname).resolve()
                    temp['rel_path'] = Path(str(temp['full_path']).replace(str(self.base_path) + os.sep, ''))
                    if self.use_relative:
                        temp['html_path'] = temp['rel_path']  # need to verify on Windows
                    else:
                        temp['html_path'] = Path(temp['full_path']).as_uri()
                    temp['ext'] = fname.suffix[1:]
                    if self.from_file:
                        top = str(self.base_path).split(os.sep)[-1]
                        subdirs = str(temp['full_path']).replace(str(self.base_path).replace(top, ''), '').split(os.sep)
                    else:
                        subdirs = str(temp['full_path']).replace(str(self.base_path)+os.sep, '').split(os.sep)
                    temp['base_path'] = self.base_path
                    for i, s in enumerate(subdirs[:-1]):
                        temp[f'subdir{i}'] = s
                    temp['filename_ext'] = temp['full_path'].suffix[1:]
                    temp['filename'] = os.path.splitext(subdirs[-1])[0]
                    temp = paths_to_str(temp)
                    self.files += [temp]

            # Discrete files will not get os.walked so add manually (only applies to file_list=True)
            if not self.base_path.is_dir() and self.base_path.exists():
                temp = {}
                temp['full_path'] = self.base_path.resolve()
                temp['rel_path'] = self.base_path
                if self.use_relative:
                    temp['html_path'] = temp['rel_path']  # need to verify on Windows
                else:
                    temp['html_path'] = Path(temp['full_path']).as_uri()
                temp['ext'] = self.base_path.suffix[1:]
                if temp['ext'] not in self.ext:
                    # if ext is not in the list of allowed, drop it
                    return
                temp['base_path'] = self.base_path
                for i, s in enumerate(self.base_path.parts[:-1]):
                    temp[f'subdir{i}'] = s
                temp['filename_ext'] = self.base_path.suffix[1:]
                temp['filename'] = os.path.splitext(self.base_path.name)[0]
                temp = paths_to_str(temp)
                self.files += [temp]

            # Exit if no files found
            if len(self.files) == 0:
                return

            # Make list into DataFrame
            self.files = pd.DataFrame(self.files)

            # Sort the files
            if self.natsort and len(self.files) > 0:
                temp = self.files.set_index('full_path')
                self.files = temp.reindex(index=natsorted(temp.index)).reset_index()

            # Add top level files below the folder list
            folders = self.files.loc[self.files.subdir0.map(str) != 'nan']
            top_level_files = self.files.loc[self.files.subdir0.map(str) == 'nan']
            self.files = pd.concat([folders, top_level_files]).reset_index(drop=True)

    def filter(self):
        """Filter out any files on the exclude list."""

        for ex in self.exclude:
            self.files = self.files[~self.files.full_path.str.contains(ex, regex=False)]

        self.files = self.files.reset_index(drop=True)

    def href(self, value):
        """Make the auto-open href."""
        return os.path.splitext('?id=%s' % value.replace(' ', '%20'))[0]

    def make_rst(self):
        """Build html files from rst files."""
        self.rst = self.files[self.files.ext == 'rst']
        idx_to_drop = []
        for i, f in self.rst.iterrows():
            # Convert the rst to html
            convert_rst(f['full_path'], stylesheet=self.rst_css)

            # Preserve a list of rst files that were compiled
            self.rst_files += [self.files.iloc[i]['full_path']]

            # Update the file list to reflect the new html file extension
            self.files.iloc[i]['ext'] = 'html'
            self.files.iloc[i]['filename'] = self.files.iloc[i]['filename'].replace('rst', 'html')
            self.files.iloc[i]['filename_ext'] = self.files.iloc[i]['filename_ext'].replace('rst', 'html')
            self.files.iloc[i]['full_path'] = self.files.iloc[i]['full_path'].replace('rst', 'html')
            self.files.iloc[i]['html_path'] = self.files.iloc[i]['html_path'].replace('rst', 'html')
            self.files.iloc[i]['rel_path'] = self.files.iloc[i]['rel_path'].replace('rst', 'html')

            # Check for same-named images
            for ext in [v for v in self.ext if v != 'html']:
                idx = self.files.query('full_path==r"%s"' % self.files.iloc[i]['full_path'].replace('html', ext)).index
                if len(idx) > 0:
                    idx_to_drop += list(idx)

        self.files = self.files.drop(idx_to_drop).reset_index(drop=True)

    def make_links(self):
        """Build the HTML links."""
        self.files['link'] = '''<A onmouseover="div_switch(' ''' + self.files.html_path.map(str) + \
                             '''')" onclick="HREF=window.open(' ''' + self.files.html_path.map(str) + \
                             '''')"href="javascript:void(0)">''' + self.files.filename.map(str) + \
                             '''</A><br>'''

    def make_ul(self):
        """Convert the DataFrame of paths and files to xml."""
        element = self.df_to_xml(self.files)
        xml = ElementTree.tostring(element)
        xml = minidom.parseString(xml)
        self.ul = xml.toprettyxml(indent='  ')
        self.ul = self.ul.replace('<?xml version="1.0" ?>\n', '')

    def nan_to_str(self):
        """Replace NaN with a string version."""
        self.files = self.files.replace(np.nan, 'nan')

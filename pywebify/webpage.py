import os
import sys
import pdb
import functools

from jinja2 import Environment, FileSystemLoader

st = pdb.set_trace
exists = os.path.exists
osjoin = os.path.join
osplit = os.path.split

FPATH = os.path.dirname(os.path.realpath(__file__))
TEMPLATE_ENVIRONMENT = Environment(
                                    autoescape=False,
                                    loader=FileSystemLoader(os.path.join(FPATH, 'templates')),
                                    trim_blocks=False
                                  )


def render_template(template_filename, context):
    return TEMPLATE_ENVIRONMENT.get_template(template_filename).render(context)


def valid_attribute(func):
    """
    checks if valid attribute of instantiating class
    """
    @functools.wraps(func)  # get __doc__ strings etc
    def wrapper(*args, **kwargs):
        for key in kwargs.keys():
            if not hasattr(args[0], key):
                raise AttributeError("'" + key + "'" + ' is not a valid  attribute of a {}'.format(type(args[0])))
        return func(*args, **kwargs)
    return wrapper


class Webpage(object):

    def __init__(self, **kwargs):

        self.basepath = r'c:\temp'
        self.context = None
        self.forbiddennew = ''
        self.logger = None
        self.print_ = False
        self.overwrite = True
        self.overwrite_static = False
        self.relpaths = []  # has to come before others with attribute error chekcin
        self.tabbed = False
        self.tabs = None  # update in tabsinit method
        self.tabtype = 'tab'  # tab|pill
        self.url = None

        self.figfileext = '.png'
        self.pagefileext = '.html'
        self._figfilename = 'figure'
        self._pagefilename = 'page'

        self.figname = 'figure.png'
        self.pagename = 'pagename.html'

        self._set_kwargs(**kwargs)

    @valid_attribute
    def _set_kwargs(self, **kwargs):
        """
        set kwargs as attributes if valid else raise attribute exception
        """
        for key, value in kwargs.items():
            setattr(self, key, value)

    def _setname(self, filename, fileext):
        """
        concatenate and return either the page or figure full file name (including path)
        """
        path = self.basepath
        for relpath in self.relpaths:
            path = osjoin(path, relpath)
        os.makedirs(path) if not os.path.isdir(path) else None
        name = osjoin(path, '{}{}'.format(filename, fileext))

        return name

    @property
    def pagefilename(self):
        return self._pagefilename

    @pagefilename.setter
    def pagefilename(self, filename):
        self._pagefilename = filename
        self.pagename = self._setname(filename, self.pagefileext)

    @property
    def figfilename(self):
        return self._figfilename

    @figfilename.setter
    def figfilename(self, filename):
        self._figfilename = filename
        self.figname = self._setname(filename, self.figfileext)

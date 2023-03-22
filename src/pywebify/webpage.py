import os
import sys
import pdb
import functools
import traceback

from jinja2 import Environment, FileSystemLoader

st = pdb.set_trace
exists = os.path.exists
osjoin = os.path.join
osplit = os.path.split

FPATH = os.path.dirname(os.path.realpath(__file__))
TEMPLATE_ENVIRONMENT = Environment(
                                    autoescape=False,
                                    loader=FileSystemLoader(osjoin(FPATH, 'templates', 'jinja')),
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
                raise AttributeError("'{}' is not a valid  attribute of a {}".format(
                                     key, type(args[0])))
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
        self.template = 'webpage.html'

        self._figfilename = 'figure'
        self._pagefilename = 'webpage'
        self.figfileext = '.png'
        self.pagefileext = '.html'
        self.figname = 'figure.png'
        self.pagename = None

        self._set_kwargs(**kwargs)

        self.pagefilename = self._pagefilename
        self.templatereset = self.template
        self.reset()

    @valid_attribute
    def _set_kwargs(self, **kwargs):
        """
        Set kwargs as attributes if valid else raise attribute exception
        """
        for key, value in kwargs.items():
            setattr(self, key, value)

    def _setname(self, filename, fileext):
        """
        Concatenate and return either the page or figure full file name (including path)

        Returns:
            name: concatenated full file name
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

    def content(self, html):
        """
        Add HTML content to render

        Args:
            html (str): html string

        Returns:
            self
        """
        if self.tabbed:
            self.tabs['content'] += [html]
        else:
            self.context['content'] += [html]

        return self

    def imglink(self, image=None, hr=True):
        """
        Add image link to add to page

        Args:
            image (str)
            hr (bool)

        Returns:
            self
        """
        image = image or self.figfilename
        imstr = """<a href="{0}"><img src="{1}" style="width:100%; max-width:1000px"></a>\n""".format(image, image)
        imstr += '<hr>' if hr else ''
        self.content(imstr)

        return self

    def log(self, level=None, *msgs):
        """
        Logging method

        Args:
            level (str): logging level
            msgs (list of str):
        """
        msg = ' '.join(msgs)
        if self.logger is None:
            if self.print:
                print(msg)
            if level == 'exception':
                exc = traceback.format_exception(*sys.exc_info())
                if self.printexceptions:
                    for elem in exc:
                        print('%s' % elem)

            return self

        level = level or 'info'
        getattr(self.logger, level)(msg + ' <br>')

        return self

    @staticmethod
    def replaceforbidden(name, forbidden=None, new=''):
        """
        Replace forbidden characters (typcially filesystem restricted) from string

        Args:
            name (str): name to replace characters
            forbidden (list of str): optional list of forbidden characters to search for
            new (str): replacement string

        Returns:
            replaced (str) input name with forbidden characters replaced
        """
        forbidden = forbidden or ['/', '#', '&', '{', '}', '<', '>', '*', '?', '$', '!', '"', "'", ':', '@', '+',
                                  '`', '|', '=']
        replaced = name
        for f in forbidden:
            if f in name:
                if f == '+':
                    rnew = new or 'plus'
                    replaced.replace(f, rnew)
                elif f == '&':
                    rnew = new or 'and'
                    replaced.replace(f, rnew)
                elif f == '#':
                    rnew = new or 'hash'
                    replaced.replace(f, rnew)
                elif f == ':':
                    if name.find(f) < 3:
                        continue
                    rnew = new or 'colon'
                    replaced.replace(f, rnew)
                else:
                    replaced = replaced.replace(f, new)

        return replaced

    def pagelink(self, alias='[page link]', pagefilename=None, nbr=1,
                 hr=False, h=None, favicon=False, height=2):
        """
        Link to self added to page

        Args:
         alias (str|'page link'): string to use in link
         pagefilename (str): set pagefilename attribute
         nbr (int|1): number of line breaks
         hr  (bool|False): if True add <hr>
         h (int): heading level
         favicon (bool|False): use favicon if True

        Returns:
            self

        """
        height = height  # or self.get_height().height # need to define get_height
        self.pagefilename = pagefilename or self._pagefilename

        url = 'file://///' + self.pagename
        html = """<a href="{0}">{1}</a>\n""".format(url, alias)

        if favicon:
            up1 = '../'
            up = ''
            for i in range(height):
                up += up1

            fv = '''<img src="{}static/img/favicon.ico" id="img" name="img"></img>'''.format(up)
            html = '<h{}>{} {}</h{}>'.format(h, fv, html, h) if h is not None else html
        else:
            html = '<h{}>{}</h{}>'.format(h, html, h) if h is not None else html

        br = ''
        for i in range(nbr):
            br += '<br>'
        html += br
        if hr:
            html += '<hr>'

        self.content(html)

        return self

    def render(self):
        """
        Add context to template and save resultant content to HTML file

        Returns:
            self
        """
        if self.pagename is None:
            raise ValueError('pagefilename has not been defined')

        # to check for cases updating basepath|relpaths|ext after figfilename
        self.figfilename = self._figfilename

        # to check for cases updating basepath|relpaths|ext after figfilename
        # could add a setter for each of these
        self.pagefilename = self._pagefilename

        with open(self.pagename, 'w') as fid:
            fid.write(render_template(self.template, context=self.context))

        self.url = self.pagename

        return self

    def reset(self):
        """
        Reset html contents, turns off tabbed, uses the reset template, and maybe other stuff later

        Returns:
            self
        """
        self.tabbed = False
        self.template = self.templatereset
        self.context = {
                            'page': 'webpage',
                            'subtitle': 'webpagesubtitle',
                            'relpath': '..',
                            'content': [],
                            'js': []
                        }

        return self

    def savefig(self, fig, filename=None, *args, **kwargs):
        """
        Save figure to reporterpage defined directory

        fig (matplotlib.figure.Figure): figure instance to write
        filename (str): filename string to write

        Keyword Args:
            passed directly to matplotlib.Figure.savefig

        Returns:
            self
        """
        self.figfilename = filename or self._figfilename

        # self.log('info', 'saving figure: ' + self.figname[self.baselen + 1:])
        if exists(self.figname):
            if not self.overwrite:
                self.log('info', 'exists and overwrite not enabled. save skipped')
                return self

        fig.savefig(self.figname, *args, **kwargs)

        return self

    def set_height(self, offset=1):
        """
        Set height attribute
        """
        self.height = len(self.relpaths) + offset

        return self

    def tabsinit(self, name='tab', template=None):
        """
        initialize tabs for content
        """

        self.template = 'tabs.html' if template is None else template

        # nav = ''' <ul class="nav nav-tabs">
        #             <li class="active"><a data-toggle="tab" href="#tab0">{name}</a></li>
        #       '''.format(name=name)

        nav = ''' <ul class="nav nav-{tabtype}s">
                    <li class="active"><a data-toggle="{tabtype}" href="#tab0">{name}</a></li>
              '''.format(name=name, tabtype=self.tabtype)

        content = ['''<div class="tab-content">
                    <div id="tab0" class="tab-pane fade in active">
                    ''']

        self.tabs = dict(nav=nav, content=content, tabno=0)
        self.tabbed = True

        return self

    def tabsnext(self, name='tab'):
        """
        move to next tab for content
        """
        self.tabs['content'] += ['\n</div>']
        self.tabs['tabno'] += 1
        self.tabs['nav'] += \
            '\n<li><a data-toggle="{}" href="#tab{:d}">{}</a></li>'.format(self.tabtype, self.tabs['tabno'], name)
        self.tabs['content'] += '\n<div id="tab{:d}" class="tab-pane fade">'.format(self.tabs['tabno'])

        return self

    def tabsend(self):
        """
        close tabs and prepare content to render
        """

        self.tabs['nav'] += '\n</ul>'
        self.tabs['content'] += ['\n</div></div>']

        self.height = len(self.relpaths) + 1
        self.context['relpath'] = '../'.join(['' for i in range(self.height)]) + '..'
        self.context['content'] += [self.tabs['nav'] + '\n' + ''.join(self.tabs['content'])]

        return self

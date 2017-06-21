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

        self.forbiddennew = ''
        self.logger = None
        self.print = False
        self.overwrite = True
        self.overwrite_static = False

        self._set_kwargs(**kwargs)

    @valid_attribute
    def _set_kwargs(self, **kwargs):
        """
        set kwargs as attributes if valid else raise attribute exception
        """
        for key, value in kwargs.items():
            setattr(self, key, value)

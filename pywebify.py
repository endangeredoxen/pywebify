import argparse
import configparser
from files import Files
from replaces import Template
import os
osjoin = os.path.join
import pdb
st = pdb.set_trace
import shutil

def _add_javascript(files):
    files = files.split(',')
    files = [f.lstrip() for f in files]
    js = ''
    js_files = []
    for f in files:
        js += '<script type="text/javascript" src="js\%s"></script>\n' % f
        js_files += [osjoin('js',f)]
    return js, js_files

def _move_files(base_path, files):
    for f in files:
        if os.path.exists(f):
            path = os.path.sep.join(osjoin(base_path,f).split(os.path.sep)[0:-1])
            if not os.path.exists(path):
                os.makedirs(path)
            shutil.copy(f, osjoin(base_path,f))

def _parse_command_line():
    '''
    Command-line parsing to get report parameters
    '''
    # Build the parser
    parser = argparse.ArgumentParser()
    parser.add_argument('--p',
                        action='store',
                        dest='base_path',
                        default=None,
                        help='top-level path to htmlerize')
    parser.add_argument('--config',
                        action='store',
                        dest='config_file',
                        default=None,
                        help='path to configuration file')
    parser.add_argument('--t',
                        action='store',
                        dest='title',
                        default=None,
                        help='report title')
    parser.add_argument('-l',
                        action='store_true',
                        dest='launch',
                        default=False,
                        help='launch report in browser')

    return parser.parse_args()

def _parse_config_file(path):
    '''
    Config file parsing
    '''
    if not path:
        path = r'config.ini'
    config = configparser.RawConfigParser()
    config.read(path)
    return config

def _update_config(args, config):
    '''
    Update the config class with any overrides from command-line arguments
    :param args: argparse class containing command-line arguments
    :param config: configparser class containing user configuration options
    :return: updated config
    '''
    if hasattr(args,'title'):
        config['LABELS']['title'] = args.title
    # add others as needed
    return config

def main():
    pass
    # config.get('BROWSER','launch')

if __name__ == '__main__':

    # main()

    args = _parse_command_line()
    config = _parse_config_file(args.config_file)
    config = _update_config(args, config)
    f = Files(args.base_path, config.get('FILES','ext'))

    css = Template(r'%s' % config.get('TEMPLATES','css'),
                   [dict(config.items('COLORS')), dict(config.items('FONTS')), dict(config.items('NAVBAR'))])
    css.write(dest=osjoin(args.base_path, 'html', 'css', 'webify.css'))

    html_dict = {}
    html_dict['FILETREE'] = ''.join(list(f.files.link))
    html_dict['JS_FILES'], js_files = _add_javascript(config.get('JAVASCRIPT','files'))
    html = Template(r'%s' % config.get('TEMPLATES','html'),[html_dict])
    html.write(dest=osjoin(args.base_path, 'html', 'webify.html'))

    _move_files(osjoin(args.base_path, 'html'), js_files)

    os.startfile(osjoin(args.base_path, 'html', 'webify.html'))

    # Make the image links
    # Make all substitutions
    # Dump files
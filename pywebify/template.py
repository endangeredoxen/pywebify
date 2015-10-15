import os
import string
import pdb
st = pdb.set_trace

class Template():
    def __init__(self, template, subs):
        self.templatePath = template
        self.raw = ''

        if len(subs) > 1:
            self.subs = self.merge_dicts(subs)
        else:
            self.subs = subs[0]

    def merge_dicts(self, subs):
        merged = subs[0]
        for i in range(1, len(subs)):
            merged.update(subs[i])
        return merged

    def substitute(self, caps=None):
        if caps:
            self.subs = dict((k.upper(), v) for k,v in self.subs.items())
        self.raw = self.raw.safe_substitute(self.subs)

    def write(self, dest=None, caps=True, bonus=''):
        self.raw = string.Template(open(self.templatePath).read())
        self.substitute(caps)
        if dest:
            dest_path = os.path.sep.join(dest.split(os.path.sep)[0:-1])
            if not os.path.exists(dest_path):
                os.makedirs(dest_path)
            with open(dest, 'w') as temp:
                temp.write(self.raw + '\n' + bonus)
        else:
            return self.raw
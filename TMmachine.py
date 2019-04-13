import re
import jinja2
from collections import namedtuple
from itertools import chain

"""
The format is:
(ccy)(swap_type)[forward term](maturity)
Ccy can be a list of configurable currencies, eg 'us', 'eu', 'cd'...
Similarly, swap_type can be 'sw', 'ois', 'ff' etc.
Maturity can be '3m', '6m', '1y', '10y', '30y' etc
Forward term is optional, and have same format as Maturity.
"""

class TemplateBase(object):
    @classmethod
    def _flattemplate(cls):
        return '|'.join(cls.templates) if isinstance(cls.templates, (list, tuple)) else cls.templates

    @classmethod
    def jtemplate(cls):
        return jinja2.Template(cls._flattemplate())

    @classmethod
    def _vars(cls):
        if isinstance(cls.templates, (list, tuple)):
            vars = [re.findall("\{\{(\w+)\}\}+", temp) for temp in cls.templates]
            return list(chain(*vars))
        else:
            return re.findall("\{\{(\w+)\}\}+", cls.templates)

    @classmethod
    def _pattern(cls):
        vars = cls._vars()
        fills = ['(%s)' % "|".join(getattr(cls, v)) for v in vars]
        pattern = "^" + cls.jtemplate().render(dict(zip(vars, fills))) + "$"
        return re.compile(pattern, re.I)

    @classmethod
    def matches(self, sym):
        res = re.match(self._pattern(), sym)
        if res:
            vars = self._vars()
            matchedresults = namedtuple('matchedresults', vars)
            for i, v in enumerate(res.groups()):
                setattr(matchedresults, vars[i], v)
            return matchedresults
        return False


class SwapTemplate(TemplateBase):
    templates = "{{ccy}}{{swap_type}}{{forward}}{{maturity}}"
    ccy = ['us', 'eu', 'cd', 'bp']
    swap_type = ['sw', 'ois', 'ff']
    forward = ['[0-9]+[BWMY]+', '']
    maturity = ['[0-9]+[BWMY]?']

class FX(TemplateBase):
  templates = "{{ccy1}}{{ccy2}}"
  ccy1 = ['usd', 'cad', 'jpy', 'eur', 'cny']
  ccy2 = ['usd', 'cad', 'jpy', 'eur', 'cny']

class Ticker(object):
    def __init__(self, typ, res):
        self.typ = typ
        self.fields = res._fields
        for field in self.fields:
            setattr(self, field, getattr(res, field))


REGISTRY = [('IRSwap', SwapTemplate),
            ('FX',     FX)]

def match(ticker):
    for typ, temp in REGISTRY:
        res = temp.matches(ticker)
        if res:
            return Ticker(typ, res)

def run(ticker):
    res = match(ticker)
    if res:
        strList = ['### %s matched successfully with %s template ###' % (ticker, res.typ)]
        for field in res.fields:
            strList.append('%s:\t%s' % (field, getattr(res, field)))
    else:
        strList = ['*** %s can NOT match with any template! ***' % ticker]

    return '\n'.join(strList)


# Ticker Input
for ticker in ('usois10y', 'bpff5y10y', 'ussw10x', 'USDEUR', 'CADJPY'):
    s = run(ticker)
    print(s+'\n')
"""
The ``macrosdef`` module defines the argument structure of macros
Macros not listed in macros_def will be parsed as zero-argument macros
and any arguments parsed as adjacent LatexGroupNode objects

"""

from pylatexenc.latexwalker import MacrosDef

import logging
log = logging.getLogger(__name__)

'''
From the LatexWalker documentation:

class pylatexenc.latexwalker.MacrosDef(macname, optarg, numargs)

1. macname stores the name of the macro, without the leading backslash.

2. optarg may be one of True, False, or None.

    if True, the macro expects as first argument an optional argument in square brackets. 
        Then, numargs specifies the number of additional mandatory arguments to the command, 
        given in usual curly braces (or simply as one TeX token)

    if False, the macro only expects a number of mandatory arguments given by numargs. 
        The mandatory arguments are given in usual curly braces (or simply as one TeX token)

    if None, then numargs is a string of either characters "{" or "[", in which each 
    curly brace specifies a mandatory argument and each square bracket specifies an 
    optional argument in square brackets. For example, "{{[{" expects two mandatory arguments,
    then an optional argument in square brackets, and then another mandatory argument.
    
MacrosDef = namedtuple('MacrosDef', ['macname', 'optarg', 'numargs'])
For example:  MacrosDef('newcommand', None, "{[{") 

'''

default_macro_list = (
    MacrosDef('documentclass', True, 1),
    MacrosDef('usepackage', True, 1),
    MacrosDef('selectlanguage', True, 1),
    MacrosDef('setlength', True, 2),
    MacrosDef('addlength', True, 2),
    MacrosDef('setcounter', True, 2),
    MacrosDef('addcounter', True, 2),
    MacrosDef('newcommand', None, "{[{"),
    MacrosDef('renewcommand', None, "{[{"),
    MacrosDef('DeclareMathOperator', False, 2),
    MacrosDef('input', False, 1),    
    MacrosDef('hspace', False, 1),
    MacrosDef('vspace', False, 1),
    MacrosDef('\\', True, 0), # (Note: single backslash) end of line with optional spacing, e.g.  \\[2mm]
    MacrosDef('item', True, 0),
    MacrosDef('input', False, 1),
    MacrosDef('include', False, 1),
    MacrosDef('includegraphics', True, 1),
    MacrosDef('textit', False, 1),
    MacrosDef('textbf', False, 1),
    MacrosDef('textsc', False, 1),
    MacrosDef('textsl', False, 1),
    MacrosDef('text', False, 1),
    MacrosDef('mathrm', False, 1),
    MacrosDef('label', False, 1),
    MacrosDef('ref', False, 1),
    MacrosDef('eqref', False, 1),
    MacrosDef('url', False, 1),
    MacrosDef('hypersetup', False, 1),
    MacrosDef('footnote', True, 1),
    MacrosDef('keywords', False, 1),
    MacrosDef('hphantom', True, 1),
    MacrosDef('vphantom', True, 1),
    MacrosDef("'", False, 1),
    MacrosDef("`", False, 1),
    MacrosDef('"', False, 1),
    MacrosDef("c", False, 1),
    MacrosDef("^", False, 1),
    MacrosDef("~", False, 1),
    MacrosDef("H", False, 1),
    MacrosDef("k", False, 1),
    MacrosDef("=", False, 1),
    MacrosDef("b", False, 1),
    MacrosDef(".", False, 1),
    MacrosDef("d", False, 1),
    MacrosDef("r", False, 1),
    MacrosDef("u", False, 1),
    MacrosDef("v", False, 1),
    MacrosDef("vec", False, 1),
    MacrosDef("dot", False, 1),
    MacrosDef("hat", False, 1),
    MacrosDef("check", False, 1),
    MacrosDef("breve", False, 1),
    MacrosDef("acute", False, 1),
    MacrosDef("grave", False, 1),
    MacrosDef("tilde", False, 1),
    MacrosDef("bar", False, 1),
    MacrosDef("ddot", False, 1),
    MacrosDef('frac', False, 2),
    MacrosDef('nicefrac', False, 2),
    MacrosDef('sqrt', True, 1),
    MacrosDef('ket', False, 1),
    MacrosDef('bra', False, 1),
    MacrosDef('braket', False, 2),
    MacrosDef('ketbra', False, 2),
    MacrosDef('texorpdfstring', False, 2),
    MacrosDef('exercise', False, '{['),
    MacrosDef('keywords', False, 1),
    MacrosDef('hint', False, 1),
    MacrosDef('hints', False, 1),
)
    
new_macro_list = (
    MacrosDef('chapter', True, 1),
    MacrosDef('section', True, 1),
    MacrosDef('subsection', True, 1),
    MacrosDef('title', False, 1),
    MacrosDef('author', False, 1),
    MacrosDef('date', False, 1),
    MacrosDef('cym', False, 1),
    MacrosDef('wel', False, 1),
    MacrosDef('eng', False, 1),
    MacrosDef('texttt', False, 1),
    MacrosDef('emph', False, 1),
    MacrosDef('pagestyle', False, 1),
    MacrosDef('thispagestyle', False, 1),
    MacrosDef('bibliographystyle', False, 1),
    MacrosDef('bibliography', False, 1),
    MacrosDef('caption', False, 1),
    MacrosDef('modulecode', False, 1),
    MacrosDef('moduletitle', False, 1),
    MacrosDef('academicyear', False, 1),
    MacrosDef('pageref', False, 1),
    MacrosDef('autoref', False, 1),
    MacrosDef('nameref', False, 1),
    MacrosDef('cite', False, 1),
    MacrosDef('hyperref', True, 1),
    MacrosDef('href', False, 2),
    MacrosDef('includevideo', True, 1),
    MacrosDef('includemedia', True, 2),
    MacrosDef('graphicspath', False, 1),
    MacrosDef('startcontents', True, 0),
    MacrosDef('stopcontents', True, 0),
    MacrosDef('mathbb', False, 1),
    MacrosDef('mathbf', False, 1),
    MacrosDef('mathcal', False, 1),
    MacrosDef('resp', False, 1),
    MacrosDef('addcontentsline', False, 3),
    MacrosDef('institution', False, 1),
    MacrosDef('nocite', False, 1),
    MacrosDef('question', True, 0),
    MacrosDef('part', True, 0),
    MacrosDef('subpart', True, 0),
    MacrosDef('subsubpart', True, 0),
    MacrosDef('resp', False, 1),
    MacrosDef('correct', False, 0),
    MacrosDef('incorrect', False, 0),
    MacrosDef('subfigure', True, 1),    
)

macro_list = default_macro_list + new_macro_list
macro_dict = dict([(m.macname, m) for m in macro_list])

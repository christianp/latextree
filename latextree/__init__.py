"""
`LaTeX <http://en.wikipedia.org/wiki/LaTeX>`_ is a typesetting system for mathematics.
The :mod:`latextree` module can parse LaTeX files and write them out in various formats.
The parsed data are returned as a :class:`LatexDocument' object.

Example:
>>> import latextree
>>> filename - '/path/to/main.tex'
>>> doc = latextree.load(tex_file)
>>> doc.xml() # export as xml 
>>> doc.web() # export as standalone website
>>> doc.bbq() # export questions in Blackboard format
"""


__all__ = [
    'loads', 'load', 'document', 'parser',
]
__version__ = '0.1'

import sys

from .document import LatexDocument
from .parser import LatexParser

def load(latex_file, parser=None):
    """
    Load a :class:`LatexDocument` object from a file
    :param latex_file: input file to be parsed
    :type latex_file: file
    :param parser: custom parser to use (optional)
    :type parser: LatexParser
    :returns: document object
    :rtype: LatexDocument
    Example::
        >>> import latexparser
        >>> doc = latextree.load('/path/to/main.tex')
    """
    if parser is None:
        parser = LatexParser()
    return parser.parse_latex_file(latex_file)

def loads(latex_string, parser=None):
    """
    Load :class:`LatexDocument` object from a string
    :param latex_string: input string to be parsed
    :type latex_string: str (ascii)
    :param parser: custom parser to use (optional)
    :type parser: LatexParser
    :returns: document object
    :rtype: LatexDocument
    Example::
        >>> import latexparser
        >>> text = "\documentclass{article}\begin{document}\begin{itemize}\item apples \item oranges\end{itemize}\end{document}"
        >>> doc = latextree.load(text)
    """
    if parser is None:
        parser = LatexParser()
    return parser.parse_latex_document(text)


# test_walker.py
import pytest
from preprocessor import LatexPreProcessor

doc = r'''
    \documentclass{article}
    some preamble nonsense
    \def\it{\item}
    \def\bit{\begin{itemize}}
    \def\eit{\end{itemize}}
    \def\ben{\begin{enumerate}}
    \def\een{\end{enumerate}}
    \begin{document} 
    An unordered list:
    \bit
    \it apples 
    \it oranges 
    \eit 
    An ordered list:
    \ben
    \it first 
    \it second 
    \een 
    \end{document}
'''

cleaned = r'''
    \documentclass{article}
    some preamble nonsense
    \begin{document} 
    An unordered list:
    \begin{itemize}
    \item apples 
    \item oranges 
    \end{itemize}
    An ordered list:
    \begin{enumerate}
    \item first 
    \item second 
    \end{enumerate}
    \end{document}
'''

#def test_expand_defs():
#    pp = LatexPreProcessor()
#    doc2 = doc.replace('\n','')
#    cleaned2 = cleaned.replace('\n','')
#    assert pp.expand_defs(doc2) == cleaned2

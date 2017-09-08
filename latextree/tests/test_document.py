# test_document.py
import pytest
from document import LatexDocument
from parser import LatexParser

documents = []

documents.append(r'''
    \documentclass{article}
    \usepackage{camel}
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
''')

documents.append(r'''
    \documentclass{article}
    \usepackage{camel}
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
''')

documents.append(r'''
    \documentclass{article}
    \usepackage{camel}
    \begin{document} 
    Cram\'{e}r-Rao
    \end{document}
''')

documents.append(r'''
    \documentclass{article}
    \usepackage{camel}
    \begin{document}
    \begin{equation}
    \begin{array}{ccc}
    1 & 2 & 3\\
    1 & 2 & 3
    \end{array}
    \end{equation}
    \end{document}
''')     

documents.append(r'''
    \documentclass{article}
    \usepackage{camel}
    \institution{CU}
    \modulecode{MA1234}
    \moduletitle{Introduction to Camel}
    \location{Cardiff University}
    \begin{document}
    \[
    e^{-i\pi}+1=0
    \]
    \end{document}
''')    


# this is not likely to work
@pytest.mark.parametrize("latex_source", documents)
def test_walker(latex_source):
    source1 = ''.join([x.strip() for x in latex_source.split('\n')])
    pa = LatexParser()
    doc = pa.parse_latex_document(latex_source)
    source2 = doc.root.get_latex()
    source2 = ''.join([x.strip() for x in source2.split('\n')])
    assert source1 == source2

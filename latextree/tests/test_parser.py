# test_parser.py
import pytest
from parser import LatexParser, LatexDocument

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
    \begin{document} 
    An unnamed (displaymath) equation:
    \[
    e^{i\pi}+1=0
    \]
    A named equation:
    \begin{equation}\label{eq:euler}
    e^{i\pi}+1=0
    \end{equation}
    \end{document}
''')


pics = []
pics.append(r'''
    \documentclass[tikz]{standalone}
    \begin{document}
    \begin{tikzpicture}
    \draw (0,0) rectangle (2,1) node [midway] {Example};
    \end{tikzpicture}
    \end{document}
''')
pics.append('''
    \begin{tikzpicture}
    %\draw (-1.5,0) -- (1.5,0);
    %\draw (0,-1.5) -- (0,1.5);
    %\draw (0,0) circle [radius=1cm];
    \end{tikzpicture}
''')

equations = [
    r'\begin{equation}a+b=c\end{equation}',
    r'\begin{align}a+b=c\end{align}\end{document}',
    r'$a=b+c$\begin{equation}a+b=c\end{equation}\[a+b=c\]',
    r'\[e^{i\pi}+1=0\]'
]
equations.append(r'''
    An equation environment:
    \begin{equation}
    \sum_{n=1}^{\infty}\frac{1}{n^2} = \frac{\pi^2}{6}.
    \end{equation}
    Does it work?
''')

media = [
    r'\includegraphics[scale=0.25]{mypic}',
    r'\includegraphics[width=5cm]{mypic}',
    r'\includegraphics[width=0.2\linewidth]{mypic}',
]

accents = [
    r'Cram\'{e}r-Rao',
]

lists = [
    r'\itemize \item apples \item oranges \enditemize',    
]


# strip CR-LF for a sporting chance (would be nice to reproduce them)
for i, s in enumerate(tests):
    tests[i] = '\n'.join([x.strip() for x in s.split('\n') if not x.isspace()])

# What does success look like?

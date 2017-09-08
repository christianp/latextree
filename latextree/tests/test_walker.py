# test_walker.py
import pytest
from walker import parse, nodelist_to_latex

test_strings = (
    r'\alpha',
    r'\textbf{bold}',
    r'\usepackage[blanks]{camel}',
    r'\begin{itemize}\item first\item second\end{itemize}',
    r'\newcommand{\prob}{\mathbb{P}}',
    r'\renewcommand{\emph}[1]{\textbf{#1}}',
    r'\begin{tabular}{ccc} a & b & c \\ d & e & f \end{tabular}',
    r'The equation $F=ma\text{ where }F\text{ is the force}$ works too.',
)

@pytest.mark.parametrize("latex_str", test_strings)
def test_walker(latex_str):
    assert latex_str == nodelist_to_latex(parse(latex_str))

"""
taxonomy.py 
Wrappers for the `pylatexenc.latexwalker` parser.

The `pylatexenc.latexwalker` package defines six classes of LatexNode objects:

LatexMacroNode
    macroname:  ascii
    nodeoptarg: LatexNode or None
    nodeargs:   list of LatexNodes (possibly empty)

LatexEnvironmentNode
    envname:    ascii
    nodelist:   list of LatexNodes (content)
    optargs:    list of LatexNodes e.g. \begin{theorem}[Pythagoras]
    args:       list of LatexNodes (contents of mandatory arguments) e.g. \begin{tabular}{ccc}

LatexMathNode
    displaytype ascii
    nodelist:   list of LatexNodes (content)

LatexGroupNode
    nodelist:   list of LatexNodes (contents of a '{' '}' pair)

LatexCommentNode
    comment     ascii

LatexCharsNode
    chars       ascii

The main function here is `nodelist_to_latex()` which converts a list of LatexNode objects back to the original latex source text. 

\[...\] delimiters are parsed as macros. We want to catch everything inbetween, 
to set as the nodelist of a LatexMathNode(displaystyle=normal) object. 

Calling math_node_to_latex on a LatexMathNode object returns well-formatted
latex code, with the _ and ^ macros dealt with correctly. 

For a dispmath environment (equation, align, etc.) we extract its 
contents and set this to be the nodelist of a LatexMathNode 
object. This not as difficult as \[...\] because we can get the nodelist
directly from the env.nodelist. These environments do not typically have
additional arguments, as opposed to say \begin{tabular}{ccc} or 
\begin{theorem}[pythagoras]. 
"""

import re

from pylatexenc.latexwalker import (
    LatexEnvironmentNode, 
    LatexMathNode, 
    LatexCommentNode, 
    LatexMacroNode, 
    LatexCharsNode, 
    LatexGroupNode
)

from pylatexenc.latexwalker import LatexWalker, MacrosDef, LatexWalkerError

from six import string_types

import logging
log = logging.getLogger(__name__)

# import dispmath environment names
from . import taxonomy as tax
from . import macrosdef

def show_node(node, depth=0):
    '''
   Return a nice string representation for debugging (recursive)
    '''
    
    # set indentation string
    istr = '--'
    
    # non-leaf nodes    
    if type(node) == LatexMacroNode:
        print(istr*depth + 'MACRO: ' + node.macroname)
        if node.nodeoptarg:
            show_node(node.nodeoptarg,depth=depth+1)
        for child in node.nodeargs:
            show_node(child,depth=depth+1)

    elif type(node) == LatexMathNode:
        print(istr*depth + 'MATH (' + node.displaytype + '): ')
        for child in node.nodelist:
            show_node(child,depth=depth+1)
        
    elif type(node) == LatexEnvironmentNode:
        print(istr*depth + 'ENV: ' + node.envname)
        for child in node.nodelist:
            show_node(child,depth=depth+1)
        
    elif type(node) == LatexGroupNode:
        for child in node.nodelist:
            show_node(child,depth=depth+1)

    elif type(node) == LatexCommentNode:
        if not node.comment.isspace():
            print(istr*depth + 'COMMENT: ' + node.comment)
        
    elif type(node) == LatexCharsNode:
        if not node.chars.isspace():
            print(istr*depth + 'CHARS: ' + node.chars.strip())
        
   # unknown nodes
    elif node != None:
        print('NODE TYPE NOT RECOGNISED: %s (%s)' % (str(node), type(node)))
        
 
def put_in_braces(brace_char, thestring):
    '''
    Taken from pylatexenc.latexwalker.
    '''
    if (brace_char == '{'):
        return '{%s}' %(thestring)
    if (brace_char == '['):
        return '[%s]' %(thestring)
    if (brace_char == '('):
        return '(%s)' %(thestring)
    if (brace_char == '<'):
        return '<%s>' %(thestring)
    return brace_char + thestring + brace_char


def environment_node_to_latex(wnode):
    '''
    Serialize a LatexEnvionmentNode object back to raw latex.
    
    The contents of the environment are contained in wnode.nodelist.
    We call node_to_latex recursively on these objects in turn.
    '''

    if not wnode.isNodeType(LatexEnvironmentNode):
        raise TypeError("Expected LatexEnvironmentNode type, not `%s'" % type(wnode))
        
    # crop starred environment names
    envname = wnode.envname[:-1] if wnode.envname[-1]=='*' else wnode.envname

    # Special case: dispmath 
    # These are outer math environments, e.g. equation, eqnarray, ...
    # not inner math environments e.g. cases, array, ...
    # 1. We transfer this environment's nodelist to a new LatexMathMode,
    # 2. then set the 'displaytype' attribute to transmit the environment name
    # This allows us to use math_node_to_latex directly
    if envname in tax.environments['dispmath']:
        math_node = LatexMathNode(displaytype=envname, nodelist=wnode.nodelist)
        return math_node_to_latex(math_node)
    
    # opening
    latex = r'\begin{%s}' % (wnode.envname)
    
    # optional arguments
    for optarg in wnode.optargs:
        latex += put_in_braces('[', node_to_latex(optarg))
    
    # mandatory arguments (curly braces aaargh!)
    for arg in wnode.args:
        latex += put_in_braces('{', node_to_latex(arg))
        
    # contents
    latex += nodelist_to_latex(wnode.nodelist)
    
    # closing
    latex += r'\end{%s}' % (wnode.envname)
    return latex


def macro_node_to_latex(wnode):
    '''
    Serialize a LatexMacroNode object back to raw latex.
    
    The contents of the macro are mostly contained in wnode.nodeargs
    Some content may be contained in an optional argument nodeoptarg.
    The macros_dict specifies the correct braces for each macro.
    These are imported from macrosdef.py
    '''
    
    if not wnode.isNodeType(LatexMacroNode):
        raise TypeError("Expected LatexMacroNode object, not `%s'" % type(wnode))
        
    # displaymath environment, \[ ... \]
    # these should no longer get through provided we only use 
    # nodelist_to_latex when needed. Here the \[ macros are picked up
    # and shelved until the corresponding \] node is encountered.
    # The interim nodes are in the meantime converted to latex (recursively).
    # When the correspoonding \] is reached, a new LatexMathNode object is 
    # created, its content attribute is set to the recovered text, and its 
    # displaytype attribute is set to `displaymath`.
        
    # sanity check
    if wnode.macroname == '[':
        print("THIS SHOULD NOT HAPPEN!")
    
    # set macro name
    macroname = wnode.macroname

    # define sequence of braces from macro_dict specification
    macro = None
    braces = '{'*len(wnode.nodeargs)
    if wnode.macroname in macrosdef.macro_dict:
        macro = macrosdef.macro_dict[wnode.macroname]
        if isinstance(macro.numargs, string_types):
            braces = macro.numargs
        elif macro.optarg:
            braces = '{'*macro.numargs
        
    # check number of arguments against number specified in macro_dict
    if len(wnode.nodeargs) != len(braces):
        raise LatexWalkerError(
            "Error: number of arguments (%d) provided to macro `\\%s' does not match its specification of `%s'"
            % (len(wnode.nodeargs), wnode.macroname, braces)
        )
        
    # fix expansion problem for renewcommand
    if wnode.macroname in ['renewcommand', 'providecommand']:
        new_macro_obj = wnode.nodeargs[0].nodelist[0]
        new_macro_str = (r'\%s' % new_macro_obj.macroname)
        wnode.nodeargs[0] = LatexCharsNode(chars=new_macro_str)

    # opening
    latex = r'\%s' % wnode.macroname
    
    # process optional argument (if any). These also include e.g. \\[2ex]
    # [2ex] is an optional to the \ command (newline) 
    # we write \\ to 'escape' the control character \
    # macros can have at most one optional argument (optarg=True)
    # this covers macros of the form \macroname[opt]{man1}{man2} etc
    # macro.numargs is the number of mandatory arguments in this case
    if macro and macro.optarg and wnode.nodeoptarg is not None:
        latex += put_in_braces('[', node_to_latex(wnode.nodeoptarg))
    
    # process mandatory arguments 
    # macro.numargs is the number of mandatory arguments
    # pesky curly-brackets around LatexGroupNode objects
    for idx, arg in enumerate(wnode.nodeargs):
        if arg is not None:
            latex += put_in_braces(braces[idx], node_to_latex(arg))

            
    # closing
    return latex


def math_node_to_latex(wnode, **kwargs):
    '''
    Serialize a LatexMathNode object back to raw latex.
    This deals with internal stuff:
        subscript (_) and superscript(^) commands
    
    Internal environments (e.g. array) will have been parsed by
    LatexWalker into LatexEnvironmentNode objects:
        Contents are contained in wnode.nodelist
        We call node_to_latex recursively on these objects in turn
        
    This is not where we deal with \[...\]. These have already been turned
    into LatexMathNode objects in `parse_nodelist`. 
    '''
    if (not wnode.isNodeType(LatexMathNode)):
        raise TypeError("Expected math node, got '%s'" % type(wnode))
    
    # init
    content = ''
    
    # iterate over contents
    idx = 0
    while idx < len(wnode.nodelist):
        wnode2 = wnode.nodelist[idx]
        
        # check for NoneType
        if wnode2 is not None:
            
            # check for subscript and superscript commands (to fix braces problem!)
            if wnode2.isNodeType(LatexCharsNode) and wnode2.chars[-1] in ['_', '^']:
                content += wnode2.chars
                
                # next
                if idx < len(wnode.nodelist) - 1:
                    wnode3 = wnode.nodelist[idx+1]
                    
                    # put brackets around a group. We should also do it for 
                    # simple macros like \infty so that the latex markup
                    # is more robust against cms rewriters. For tex2bbq we
                    # need to remove all spaces from within Maths objects!
                    # Pesky curly braces around LatexGroupNode objects part II
                    if wnode3.isNodeType(LatexGroupNode):
                        content += put_in_braces('{', node_to_latex(wnode3))
                        idx = idx + 1
                    
                    elif wnode3.isNodeType(LatexMacroNode):
                        if 'insert_strict_braces' in kwargs and kwargs['insert_strict_braces']:
                            content += put_in_braces('{', node_to_latex(wnode3))
                            idx = idx + 1
                    
            # otherwise
            else:
                content += node_to_latex(wnode2)
        # next
        idx = idx + 1

        # process text        
        if 'non_breaking_spaces' in kwargs and kwargs['non_breaking_spaces']:
            content = content.replace(' ', '~')

        if 'insert_strict_braces' in kwargs and kwargs['insert_strict_braces']:
            content = content.replace(' ', '~')

    
    # output according to displaytype
    if wnode.displaytype == 'inline':
        if 'strict_inline_maths' in kwargs and kwargs['strict_inlne_maths']:
            return (r'\(%s\)' % content)
        return (r'$%s$' % content)
    
    elif wnode.displaytype == 'displaymath':
        if 'strict_display_maths' in kwargs and kwargs['strict_display_maths']:
            return (r'\begin{displaymath}%s\end{displaymath}' % content)
        return (r'\[%s\]' % content)
    
    else:
        return (r'\begin{%s}%s\end{%s}' % (wnode.displaytype, content, wnode.displaytype))


def node_to_latex(wnode, **kwargs):
    '''
    Serialize a LatexNode object back to raw latex.
    '''
    if wnode.isNodeType(LatexMathNode):
        return math_node_to_latex(wnode, **kwargs)

    elif wnode.isNodeType(LatexCharsNode):
        return wnode.chars

    elif wnode.isNodeType(LatexCommentNode):
        return '%' + wnode.comment + '\n'
    
    elif wnode.isNodeType(LatexGroupNode):
        # return put_in_braces('{', nodelist_to_latex(wnode.nodelist))
        return nodelist_to_latex(wnode.nodelist)

    elif wnode.isNodeType(LatexEnvironmentNode):
        return environment_node_to_latex(wnode)

    elif wnode.isNodeType(LatexMacroNode):
        return macro_node_to_latex(wnode)

    else:
        return ''


def nodelist_to_latex(nodelist, **kwargs):
    '''
    Serialize a list of LatexNode objects back to raw latex.
    
    We replace a sequence of nodes falling between '\[' and '\]' macros into
    a single LatexMathNode object, then call node_to_latex on each
    member of this (possibly reduced) list.
    
    Warning. Possible bug in LatexWalker?
    Creating a new LatexMathNode object as follows:
        new_math_node = LatexMathNode(displaytype='displaymath")
    this does not appear to set the new_math_node.nodelist to []
    '''
    idx = 0
    latex = ''
    while idx < len(nodelist):
        if nodelist[idx]:
            
            # check for dispmath environments
            if nodelist[idx].isNodeType(LatexEnvironmentNode) and nodelist[idx].envname in tax.environments['dispmath']:
                new_math_node = LatexMathNode(
                    displaytype = nodelist[idx].envname,
                    nodelist = nodelist[idx].nodelist
                )
                latex += math_node_to_latex(new_math_node, **kwargs)

            # check for displaymath macro \[
            elif nodelist[idx].isNodeType(LatexMacroNode) and nodelist[idx].macroname == '[':
                new_math_node = LatexMathNode(displaytype='displaymath', nodelist=[])
                while idx < len(nodelist):
                    idx = idx + 1
                    if nodelist[idx].isNodeType(LatexMacroNode) and nodelist[idx].macroname == ']':
                        break
                    new_math_node.nodelist.append(nodelist[idx])
                latex += math_node_to_latex(new_math_node, **kwargs)

            # check for latex mathnode 
            # we don't need this: it will be caught by the else statement
            elif nodelist[idx].isNodeType(LatexMathNode):
                latex += math_node_to_latex(nodelist[idx], **kwargs)

            # check for LatexGroupNode
            # we don't need this: it will be caught by the else statement
            elif nodelist[idx].isNodeType(LatexGroupNode):
                latex += put_in_braces('{', nodelist_to_latex(nodelist[idx].nodelist))

            # everything else
            else:
                latex += node_to_latex(nodelist[idx], **kwargs)

        idx = idx + 1

    return latex
            
    
def parse(text, **kwargs):
    '''
    A wrapper for LatexWalker.get_latex_nodes()
    Returns a list of LatexNodes
    
    Loads macro definitions from macrosdef.py
    "keep_inline_math=True" creates LatexMathNode objects from $....$ (inline maths)
    LatexWalker does not parse displaymath environments
        \[ and \] are parsed as zero-argument macros
        \begin{equation}...\end{equation} is completely parsed like any other environment
    '''

    walker = LatexWalker(text, macro_dict=macrosdef.macro_dict, keep_inline_math=True)
    nodes = walker.get_latex_nodes()[0]
    return nodes
   

#------------------------------------------------
def main(args=None):
    print('walker.py')

    import pprint
    pp = pprint.PrettyPrinter(indent=4)

    tests = []
    tests.append(r'\alpha')
    tests.append(r'\textbf{bold}')
    tests.append(r'\usepackage[blanks]{camel}')
    tests.append(r'\begin{itemize}\item first\item second\end{itemize}')
    tests.append(r'\newcommand{\prob}{\mathbb{P}}')
    tests.append(r'\renewcommand{\emph}[1]{\textbf{#1}}')
    tests.append(r'\begin{tabular}{ccc} a & b & c \\ d & e & f \end{tabular}')
    tests.append(r'equation $F=ma\text{ where }F\text{ is the force.}$ works too.')
    tests.append(r'fraction $\frac{1}{2}$ is ...?')
    tests.append(r'fraction $\frac{\var(X)}{\expe(X)}$ is ...?')
    tests.append(r'equation $\sum_{n=1}^{\infty} a_n = 1$ is ...?')
    
    tests.append(r'''
        A named displayed equation:
        \begin{equation}
        \sum_{n=1}^{\infty} a_n = 1.
        \end{equation}
        ''')
    
    tests.append(r'''
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
        ''')

    tests.append(r'''
        Some inline maths: $\alpha+\beta=\gamma$.
        ''')
    
    tests.append(r'''
        An equation environment:
        \begin{equation}
        \sum_{n=1}^{\infty}\frac{1}{n^2} = \frac{\pi^2}{6}.
        \end{equation}
        ''')
    
    tests.append(r'''
        An align environment:
        \begin{align}
        x & = a\cos t \\
        y & = b\sin t
        \end{align}
        ''')
    
    tests.append(r'''
        An internal cases environment:
        \[
        x = \begin{cases}
            0 & \text{if } x < 0, \\
            1 & \text{if } x \geq 0. \\
        \end{cases}
        \]
        ''')

    tests.append(r'''
        An unnamed displayed equation:
        \[
        \sum_{n=1}^\infty a_n = 1.
        \]
        ''')
    
    tests.append(r'''
        An unnamed displayed equation:
        \[
        e^{i\pi}+1=0
        \]
        ''')
    
#    tests.extend([
#        r'English \begin{cymraeg}Cymraeg\end{cymraeg}',
#        r'English \cym{Cymraeg}',
#        r'{\bf bold text}',
#        r'{English \cy Cymraeg}',
#        r'English $a+b=c$ \cy Cymraeg $c+d=e$',
#    ])

    tests.append(r'helo {\bf trwm} doli \textbf{bold}. \begin{center}shw mae\end{center}')
        
    tests.append(r'\begin{minipage}{\linewidth}This is the minipage text.\end{minipage}')

    tests.append(r'''
        \begin{document}
        \begin{tikzpicture}[decoration=Koch snowflake]
        \draw decorate{ decorate{ decorate{ decorate{
            (0,0) -- ++(60:3)  -- ++(300:3) -- ++(180:3)}}}};
            \end{tikzpicture}
            \end{document}
        ''')

    tests.append(r'''
        \begin{tabular}{ll}
        a & b \\[2ex]
        c & d \\[3ex]
        \end{tabular}
    ''')
    
    tests.append(r'''
        \begin{theorem}[Pythagoras]$a^2+b^2=c^2$\end{theorem}
    ''')

    tests.append(r'helo {red \cy coch} doli \textbf{bold}. \begin{center}shw mae\end{center}')
    
    tests.append(r'The {\tt latextree} package.')
    
    tests.append(r'Both {\en english \cy cymraeg} both.')

    tests.append(r'''
        \begin{verbatim}
        To get an alpha type \alpha. 
        For quizzes use the \begin{quiz}...\end{quiz} environment.
        \end{verbatim}
    ''')

    tests.append(r'''
        \begin{figure}[htb]
        \centering
        \subfigure[Union]{\includegraphics[scale=0.25]{AcupB}\label{fig:union}}\par
        \subfigure[Intersection]{\includegraphics[scale=0.25]{AcapB}\label{fig:intersection}}\par
        \subfigure[Complement]{\includegraphics[scale=0.25]{Acomp}\label{fig:complement}}
        \caption{Three figures using \texttt{subfigure}.\label{fig:setops-subfig}}
        \end{figure}
    ''')
    
    tests.append(r'''
        \subfigure[Union]{\includegraphics[scale=0.25]{AcupB}\label{fig:union}}
    ''')
    


    # strip out CRLF
    # we are losing a carriage return after \begin{environment} and elsewhere.
    # so we strip these out for a fair comparison.
    # it would be nice to get this fixed, at least we might pass more tests!
    # for idx, s in enumerate(tests):
    #     tests[idx] = ''.join([x.strip() for x in s.split('\n')])
        
    # iterate over tests    
    for idx, s in enumerate(tests):
        print('==================================')
        print('TEST %d' % idx)
        print(s)
        wnodes = parse(s)      
        s2 = nodelist_to_latex(wnodes,
            non_breaking_spaces = False,
            insert_strict_braces = False,
            strict_display_maths = False,
        )        
        print('------------------------')
        print(wnodes)
        print('------------------------')
        print(s2)
        print('------------------------')
        print((s == s2))
        print('------------------------')
    
    
    
if __name__ == '__main__':
    main()





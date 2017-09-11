# -*- coding: utf-8 -*-
"""
Created on Sun Jul 16 20:01:27 2017

@author: scmde
"""

import logging
logger = logging.getLogger(__name__)


class LatexPreProcessorError(Exception):
    '''
    Generic exception class raised by LatexPreProcessor.
    '''
    def __init__(self, msg):
        self.msg = msg
        LatexPreProcessorError.__init__(self, msg)

class LatexPreProcessor(object):    
    '''
    Class to pre-process latex markup before passing to LatexWalker
    In particular we must expand \def\bit{\begin{itemize}} and similar.
    '''
    def __init__(self):
        pass        

    def preprocess(self, text):
        text = self.expand_defs(text)
        text = self.replace_backticks(text)
        text = self.replace_double_dollars(text)
        return text

    def replace_double_dollars(self, text):
        parts = text.split('$$')
        if len(parts) > 1:
            parts[1::2] = [r'\[' + s + r'\]' for s in parts[1::2]]
            return ''.join(parts)
        return text

    def replace_backticks(self, text):
        return text.replace(r"`", r"'")
        
    def replace_tildes(self, text):
        return text.replace(r'~', r' ')
        
    def expand_defs(self, text):
        
        import re
        pattern = re.compile(r'\\def\s*(\\\w+)\s*')

        # find matches (and remove as we go)
        def_dict = dict()
        match = re.search(pattern, text)
        while match:

            # check that first character is "{" (catch space here)
            idx = match.end()
            if text[idx] != '{':
                logger.error('The first character should be a "{"')
                print('First character should be a "{" at position %s' % idx)
                continue

            # find the closing brace
            stack = ['{']
            idx = idx + 1
            while len(stack) > 0 and idx < len(text):
                if text[idx] == '{': stack.append('{')
                if text[idx] == '}': stack.pop()
                idx = idx + 1

            # record the macro name and its definition
            def_dict[match.group(1)]  = text[match.end()+1:idx-1]
            
            # cut the definition out of the text
            text = text[:match.start()] + text[idx:]

            # move to next match (exits on None)
            match = re.search(pattern, text) 

        # expand (copy the whitespace across)
        import re
        for key, val in def_dict.items():
            text = re.sub('\\' + key +'(\s+)', '\\' + val + r'\1', text)
            
        return text

#------------------------------------------------
def main(args=None):
    
    s = ''
    s += r'\def\it{\item}'
    s += r'some nonsense'
    s += r'\def\bit{\begin{itemize}}'
    s += r'\def\eit{\end{itemize}}'
    s += r'\def\ben{\begin{enumerate}}'
    s += r'\def\een{\end{enumerate}}'
    s += r'\begin{document} blah...'
    s += r'\bit\it apples \it oranges \eit '
    s += r'\ben\it first \it second \een '
    s += r'...blah \end{document}'

    s = r'''
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
        \item first 
        \item second 
        \een 
        \end{document}
    '''
#    # parse to create LatexTree
    pp = LatexPreProcessor()
    print(pp.expand_defs(s))
    
if __name__ == '__main__':
    main()

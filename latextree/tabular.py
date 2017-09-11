"""
tabular.py
We deal with tabular environments directly (rather than via latexwalker
"""

from . import walker
from .node import LatexTreeNode

import logging
logger = logging.getLogger(__name__)

class Row(LatexTreeNode):
    def __init__(self):
        LatexTreeNode.__init__(self)
        
class Cell(LatexTreeNode):
    def __init__(self):
        LatexTreeNode.__init__(self)
        
class Tabular(LatexTreeNode):    
    '''
    Class to represent tabular environments.
    '''
    def __init__(self, spec, text):
        LatexTreeNode.__init__(self)
        
        from parser import LatexParser
        pa = LatexParser()

        # compute column specifications
        chars = list(spec)
        col_spec = []; 
        col_borders = [''] 
        for idx, ch in enumerate(chars):
            # border ...
            if ch == '|':
                col_borders[-1] += "L"
            # ... or column
            else:
                col_spec.append(ch)
                col_borders.append('')
        
        # process right-hand border of final column
        rh_border_spec = col_borders.pop()
        col_borders[-1] += 'R'*len(rh_border_spec)
        
        # split table into rows
        # \hline macros are always at the *start* of a line
        # a final \hline must come on a line of its own
        s_rows = text.split(r'\\')
        
        # set row borders according to location of \hlines
        row_borders = []
        for s_row in s_rows:
            row_borders.append('t'*s_row.count(r'\hline'))
        s_rows = [s_row.replace(r'\hline','') for s_row in s_rows]
        
        if not s_rows[-1].strip() and len(row_borders) > 1:
            bottom_border = row_borders.pop()
            row_borders[-1] += 'b'*len(bottom_border)
            s_rows = s_rows[:-1]

        # iterate over rows
        for ridx, s_row in enumerate(s_rows):
            
            # create row and set border spec
            row = Row()
            row.content = row_borders[ridx]
            
            # iterate over cells
            s_cells = s_row.split(r'&')
            for cidx, contents in enumerate(s_cells):
                
                # create cell and set border and align spec
                cell = Cell()
                cell.content = col_spec[cidx] + col_borders[cidx]
                
                # parse contents
                stack = [cell]
                walker_nodes =  walker.parse(contents)
                for wnode in walker_nodes:
                    stack = pa.parse_walker_node(wnode, stack)
                    while len(stack) > 1:
                        node = stack2.pop()
                        stack[-1].append_child(node)
                
                # append cell to row
                row.append_child(cell)
    
            # append row to self
            self.append_child(row)


#------------------------------------------------
def main(args=None):
    
    spec = r'|lc|cr|'
    text = r'''
        \hline 
        a & b & c & d \\ 
        e & f & g & h \\
        \hline 
        \hline 
        i & j & k & l \\ 
        \hline
    '''

    tab = Tabular(spec=spec, text=text)

    # xml is a bit dodgy here - the row and cell specifications are 
    # not being parsed as attributes. The LatexTreeNode.get_xml()
    # function will have to be expanded. It was only a quick hack anyway!
    from lxml import etree
    print(etree.tostring(tab.get_xml(), pretty_print=True))
    
if __name__ == '__main__':
    main()


# -*- coding: utf-8 -*-
"""
Created on Wed Apr 26 00:02:18 2017

@author: scmde

We use NodeFactory for unlisted fields
"""

import re, bibtexparser

from .factory import NodeFactory
from .node import LatexTreeNode
from .content import Text

class BibItem(LatexTreeNode):

    def __init__(self):
        LatexTreeNode.__init__(self)

    def harvard_dict(self):
        '''
        This should be done in a template!
        '''
        harv = dict()
        bibtex_fields = ('title', 'author', 'year', 'publisher', 'isbn')
        
        surnames = []
        initials = []
        for child in self.children:

            if child.get_species() == 'author':

                # split on authors (, or 'and') then on names (. or space)
                author_str = child.content                
                author_list = [x.split(' ') for x in re.split(',|and', author_str)]
                author_list = [[x.strip() for x in au if x] for au in author_list]
                for author in author_list:
                    surnames.append(author[-1])
                    initials.append('.'.join([x[0] for x in author[:-1]]) + '.')
                names = ['%s, %s' % name for name in zip(surnames, initials)]
                harv['author'] = ' and '.join([', '.join(names[:-1]), names[-1]])

            elif child.get_species() in bibtex_fields:
                harv[child.get_species()] = child.content
            
            else:
                pass

        # set citation text e.g. (Evans 2012)
        if len(surnames) == 1:
            harv['citation'] = '(%s, %s)' % (surnames[0], harv['year'])
        elif len(surnames) == 2:
            harv['citation'] = '(%s & %s, %s)' % (surnames[0], surnames[1], harv['year'])
        elif len(surnames) > 3:
            harv['citation'] = '(%s et al. %s)' % (surnames[0], harv['year'])

        return harv

    
    def harvard(self):
        '''
        This should be done in a template!
        '''
        title = ''
        author = ''
        date = ''
        publisher = ''
        for child in self.children:
            if child.get_species() == 'title':
                title = child.content
            elif child.get_species() == 'author':
                author_str = child.content
                auth_list = [x.split('.') for x in re.split(',|and', author_str)]
                auth_list = [[x.strip() for x in au] for au in auth_list]
                auth_parts = []
                for auth in auth_list:
                    name = auth[-1] + ' ' + '.'.join([x[0] for x in auth[:-1]]) + '.'
                    auth_parts.append(name)
                author = ' and '.join([', '.join(auth_parts[:-1]), auth_parts[-1]])
            elif child.get_species() == 'year':
                year = child.content
            elif child.get_species() == 'publisher':
                publisher = child.content
            else:
                pass
        return '%s (%s) %s. %s.' % (author, year, title, publisher)

class Bibliography(LatexTreeNode):
    
    def __init__(self, text):
        LatexTreeNode.__init__(self)
        bibtex_db = bibtexparser.loads(text)
        for entry in bibtex_db.entries:
            bibitem = BibItem()
            for key, val in entry.items():
                if key == 'ID':
                    bibitem.label = val
                else:
                    node = NodeFactory(str(key), BaseClass=Text)
                    node.content = val
                    bibitem.append_child(node)
            self.append_child(bibitem)
        
    def harvard(self):
        return '\n'.join([x.harvard() for x in self.children])

#------------------------------------------------
def main(args=None):
    
    test_file = '~/python/latextree/tex/references.bib'
    with open(test_file) as bibtex_file:
        text = bibtex_file.read()
        
    bib = Bibliography(text)
    print(bib.harvard())
      
    # xml output
    from lxml import etree
    bibx = bib.xml() 
    print(etree.tostring(bibx, pretty_print=True))

if __name__ == '__main__':
    main()
                

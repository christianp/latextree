#! /usr/bin/env python 
"""
This module provides command line tools for LatexTree.
"""

import sys
from optparse import OptionParser

from .reader import read_latex_document
from .node import LatexTreeNode
from . import taxonomy as tax

import logging
log = logging.getLogger(__name__)

#------------------------------------------------
def main(args=None):
	   

    oparser = OptionParser(usage="%prog main.tex [-opts]", version="%prog: version 1.0", add_help_option=True)
    oparser.add_option("-b", "--bbq", action="store_true", dest="bbq", help="typeset questions in blackboard format")
    oparser.add_option("-e", "--exex", action="store_true", dest="exex", help="extract and typeset exercises")
    oparser.add_option("-i", "--info", action="store_true", dest="info", help="print(document info to stdout"))
    oparser.add_option("-c", "--xrefs", action="store_true", dest="xrefs", help="print((label, entity) pairs to stdout"))
    oparser.add_option("-p", "--pdf", action="store_true", dest="pdf", help=" create pdf")
    oparser.add_option("-s", "--show", action="store_true", dest="show", help=" print(tree to stdout (recursive)"))
    oparser.add_option("-v", "--verbose", action="store_false", dest="verbose", help="verbose output")
    oparser.add_option("-w", "--web", action="store_true", dest="web", help="create standalone website")
    oparser.add_option("-x", "--xml", action="store_true", dest="xml", help="print(xml tree to stdout"))
    oparser.set_defaults(verbose=True, tex=False, html=False, xml=False)

    # parse arguments
    (options, args) = oparser.parse_args()
    if not args:
        print('usage: $ltree.py main.tex [opts]')
        return

    # parse document
    from parser import LatexParser
    pa = LatexParser()
    main_tex = args[0]
    doc =  pa.parse_latex_file(main_tex)

    # show tree (recursive)
    if options.show:
        print(doc.root.show())

    # xml
    if options.xml:
        from lxml import etree        
        print(etree.tostring(doc.root.get_xml(), pretty_print=True))

    # blackboard questions
    if options.bbq:
        questions = doc.bbq()
        sys.stdout.write('\n'.join(questions))

    # website
    if options.web:
        webzip = doc.make_website()
      
    # extract exercises
    if options.exex:
        exercises = doc.body.get_phenotypes('exercise')
        if exercises:
            for ex in exercises:
                print(etree.tostring(ex.xml(), pretty_print=True))
        else:
            print('No exercises!')

    # print(doccument information)
    if options.info:
        print('==============================')
        print('Document information')
        print('------------------------------')
        for param in tax.preamble_capture:
            print("%s: %s" % (param.ljust(15), doc.preamble[param] if param in doc.preamble else ''))
        print('==============================')

    # print(xrefs)
    if options.xrefs:
        col_width = max( [len(key) for key in doc.xrefs.keys()] ) + 2  # padding
        print('==============================')
        print('Labels')
        print('==============================')
        print('Label'.ljust(col_width) + 'TreeNode')
        print('------------------------------')
        for key, val in doc.xrefs.items():
            print(key.ljust(col_width) + repr(val))
        print('==============================')

if __name__ == '__main__':
    main()



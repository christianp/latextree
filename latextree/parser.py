"""
The ``parser`` module provides an API for parsing LaTeX documents and
constructs a representation as a tree structure based on nodes classes.
LatexParser understands the syntax of most common macros but is NOT a
replacement for a full LaTeX engine. The parser shouldonly be invoked 
after the input has been successfully compiled under LaTeX.

Example
>>> from parser import LatexParser
>>> pa = LatexParser()

# parse raw latex
>>> s = r'\[E=mc^2\]'
>>> root = pa.parse_latex(s)

# parse document
>>> test_file = './test/tex/main.tex'
>>> doc = pa.parse_latex_document(s)

# extract all quizzes
>>> doc.root.get_phenotypes('quiz')
"""

"""
The LatexParser class.

There are three main families of LatexTreeNode
    container nodes: environments, chapters, style, ...
    content nodes: text, maths, dispmath, labels, ...
    directive nodes: setcounter (not considered at the moment)

Numbers 
    Numbers are set retrospectively (after the tree has been created).
    Numbered classes are defined in taxonomy.counters
    These include level, theorem and float classes
    Counter dependencies need to be specified externally (curr. all reset on chapter)

Labels 
    Labes are attached as an attribute of the parent container
    The parent container is the node currently at stack_top

Titles
    The parser includes titles as child elements.
        levels: \chapter{Introduction}
        theorems: \begin{theorem}[Zorn's Lemma]
        tloats: \caption{Look at this.}
        The `title` attribute of parent containers are set retrospectively. 
        These are pointers to Title() nodes


Content is always plain ascii text

    Text: plain text visible in the document, 
    Latex: latex code (text for MathJax to handle)
    Points: integer value
    Image: image file (filename)
    Media: video (url)
    Href: external hyperlink (url)
    Xref: internal cross-references (label)

 """
import os

from pylatexenc.latexwalker import (
    LatexEnvironmentNode, 
    LatexMathNode, 
    LatexCommentNode, 
    LatexMacroNode, 
    LatexCharsNode, 
    LatexGroupNode
)

from . import walker
from . import taxonomy as tax

from .node import LatexTreeNode, Macro, Environment, Switch
from .content import Content, Xref, Url, Image, Media, Latex, Comment, Text, Points
from .factory import ClassFactory, NodeFactory
from .tabular import Tabular, Row, Cell
from .bibliography import Bibliography
from .document import LatexDocument

import logging
logger = logging.getLogger(__name__)


# some catch-all classes. These should be hived off somewhere else
class Title(LatexTreeNode):
    ''' 
    This neds to be defined as a LatexTreeContent node. The chilren contain
    the title and content attribute set to equal a short tile (as specified
    by an optional argument: \chapter[short title]{full title}    
    cases: level, theorem, float (caption)
    '''
    def __init__(self):
        LatexTreeNode.__init__(self)

class Break(LatexTreeNode):
    def __init__(self):
        LatexTreeNode.__init__(self)

class Space(LatexTreeNode):
    def __init__(self):
        LatexTreeNode.__init__(self)
    

class LatexParserError(Exception):
    '''
    Generic exception class raised by LatexParser.
    '''
    def __init__(self, msg):
        self.msg = msg
        Exception.__init__(self, msg)

class LatexParser(object):
    '''
    Yet another parser for Latex. Returns a LatexDocument object.
    
    The LatexDocument object records the source file location (main.tex).
    We need this when exporting the document in various (for default locations).
    
    \bibliography, \includegraphices and other post-processing tasks will
    also need to locate files whose location are specified relative to main.tex 
    '''
    
    def __init__(self):       

        # filename will be set by parse_latex_document
        # probably not needed anymore
        self.filename = None

        # create classes        
        abstract_macro_classes = dict([(genus, ClassFactory(genus, {}, BaseClass=Macro)) for genus in tax.macros])
        abstract_environment_classes = dict([(genus, ClassFactory(genus, {}, BaseClass=Environment)) for genus in tax.environments])
        abstract_switch_classes = dict([(genus, ClassFactory(genus, {}, BaseClass=Switch)) for genus in tax.switches])

        macro_classes = dict([(species, ClassFactory(species, {}, BaseClass=abstract_macro_classes[genus])) for genus in tax.macros for species in tax.macros[genus]])
        environment_classes = dict([(species, ClassFactory(species, {}, BaseClass=abstract_environment_classes[genus])) for genus in tax.environments for species in tax.environments[genus]])
        switch_classes = dict([(species, ClassFactory(species, {}, BaseClass=abstract_switch_classes[genus])) for genus in tax.switches for species in tax.switches[genus]])

        self.classes = macro_classes.copy()
        self.classes.update(environment_classes)
        self.classes.update(switch_classes)
        
    def parse_walker_chars_node(self, wnode, stack):
        '''
        Parse a LatexCharsNode object.
        Double newlines are replaced by a Break() object.
        '''
        if not wnode.isNodeType(LatexCharsNode):
            raise LatexParserError("Expected LatexCharsNode object, not `%s'" % type(wnode))
        
        paragraphs = wnode.chars.split('\n\n') 
        node = Text(text = paragraphs[0])
        stack[-1].append_child(node)
        if len(paragraphs) > 1:
            for para in paragraphs[1:]:
                stack[-1].append_child(Break())
                stack[-1].append_child(Text(text=para))
        return stack
        
    def parse_walker_comment_node(self, wnode, stack):
        '''
        Parse a LatexCommentNode object.
        '''
        if not wnode.isNodeType(LatexCommentNode):
            raise LatexParserError("Expected LatexCommentNode type, not `%s'" % type(wnode))
        node = Comment(comment = wnode.comment)
        stack[-1].append_child(node)
        return stack

    def parse_walker_group_node(self, wnode, stack, **kwargs):
        '''
        Parse a LatexGroupNode object.
        '''
        if not wnode.isNodeType(LatexGroupNode):
            raise LatexParserError("Expected LatexGroupNode object, not `%s'" % type(wnode))
        
        for wnode2 in wnode.nodelist:
            # check for switches
            if wnode2.isNodeType(LatexMacroNode) and wnode2.macroname in tax.switch_species:
                # terminate previous switch (if any)
                if (
                    wnode2.macroname in tax.switches['style'] and stack[-1].get_species() in tax.switches['style']
                ) or (
                    wnode2.macroname in tax.switches['language'] and stack[-1].get_species() in tax.switches['language']
                ):
                    node = stack.pop()
                    stack[-1].append_child(node)
                node = self.classes[wnode2.macroname]()
                stack.append(node)

            # otherwise parse the node (recursively)
            else:
                stack = self.parse_walker_node(wnode2, stack, **kwargs)

        # pop stack if necessary (the scope of a switch extends to next switch or a closing brace)
        if stack[-1].get_species() in tax.switch_species:
            node = stack.pop()
            stack[-1].append_child(node)            

        return stack
        

    def parse_walker_environment_node(self, wnode, stack, **kwargs):
        '''
        Parse a LatexEnvironmentNode object.
        
        tabular and dispmath are processed from scratch and appended to the 
        children of the parent container (stack_top). All others are pushed 
        onto the stack. We then call parse_walker_nodelist recursively on 
        the contents of the environment. For tabular environments, we call 
        parse_walker_nodelist recursively on the contents of each cell.
        '''
        if not wnode.isNodeType(LatexEnvironmentNode):
            raise LatexParserError("Expected LatexGroupNode object, not `%s'" % type(node))

        envname = wnode.envname
        #--------------------
        # 0. starred environments
        # xml will not accept * in an element name
        # but starred environments are important for mathjax numbering
        # better to remove stars in LatexTreeNode.get_xml() rather than here.
        # if envname[-1] == '*':
        #     envname = envname[:-1]

        #--------------------
        # 1A. dispmath (output verbatimm for MathJax to handle)
        if envname in tax.environments['dispmath']:
            new_walker_math_node = LatexMathNode(displaytype=envname, nodelist=wnode.nodelist)
            if envname in self.classes:
                node = self.classes[envname]()
            else:
                node = NodeFactory(envname, BaseClass=Content)
            node.content =  walker.math_node_to_latex(new_walker_math_node, **kwargs)
            
            # append as child of parent and bail out
            stack[-1].append_child(node)
            return stack
            
        #--------------------
        # 1B. preformatted text
        if envname in tax.environments['pre']:
            new_walker_environment_node = LatexEnvironmentNode(envname=envname, nodelist=wnode.nodelist)
            if envname in self.classes:
                node = self.classes[envname]()
            else:
                node = NodeFactory(envname, BaseClass=Content)
            node.content =  walker.nodelist_to_latex(wnode.nodelist)
            
            # append as child of parent and bail out
            stack[-1].append_child(node)
            return stack
            
        #--------------------
        # 2. tabular: parse from scratch (see tabular.py)
        # parse_walker_nodelist is called on the contents of each cell
        if envname == 'tabular':
            from tabular import Tabular
            colspec = list(walker.nodelist_to_latex(wnode.args[0].nodelist))
            text = walker.nodelist_to_latex(wnode.nodelist)
            node = Tabular(spec=colspec, text=text)
            
            # append as child of parent and bail out
            stack[-1].append_child(node)
            return stack

        #--------------------                             
        # 3. default: unlisted environments are subclassed from Environment (no genus)
        if envname in self.classes:
            node = self.classes[envname]()
        else:
            node = NodeFactory(envname, BaseClass=Environment)

        # push new environment onto stack
        stack.append(node)
        
        # deal with theorem titles (specified as optional argument)
        if wnode.optargs and envname in tax.environments['theorem']:
            stack.append(Title())
            stack = self.parse_walker_nodelist(wnode.optargs[0].nodelist, stack, **kwargs)
            title = stack.pop()
            stack[-1].append_child(title)            

        # call parse_walker_nodelist on the contents of the environment
        stack = self.parse_walker_nodelist(wnode.nodelist, stack, **kwargs)

        # List environments: pop and append final item
        if envname in tax.environments['list']:
            item = stack.pop()
            stack[-1].append_child(item)

        # pop current environment and append to parent
        node = stack.pop()
        stack[-1].append_child(node)

        return stack
                    
    def parse_walker_macro_node(self, wnode, stack, **kwargs):
        '''
        Parse a LatexMacroNode object.

        displaymath:
        \[ and \] are aliases for \begin{displaymath} and \end{displaymath}
        The nodes following a \[ are processed in parse_walker_nodelist, 
        where they are added to a new LatexMathNode object until the
        corresponding \] is encoutered. Species are identified by the
        `displaytype` setting : inline ($...$), displaymath (\[...\]) 
        or the environment name (e.g. `equation` or `eqnarray`)
        '''
        # type check        
        if not wnode.isNodeType(LatexMacroNode):
            raise LatexParserError("Expected LatexMacroNode object, not `%s'" % type(wnode))

        #------------------------------        
        # 0. Starred macros (convert or kill: xml will not accept * in an element name)
        macroname = wnode.macroname
        if macroname[-1] == '*':
            macroname = macroname[:-1]
            if macroname in tax.macros['level']:
                macroname = macroname + 'star'

        #--------------------
        # 1A. Label: set as id attribute of nearest numbered container and bail out
        if macroname == 'label':
            # simple method: the immediate parent. This might be the best option.          
            # stack[-1].label = wnode.nodeargs[0].nodelist[0].chars 
            idx = -1
            while (-idx < len(stack)) and (stack[idx].get_genus() not in tax.numbered_genera) and (stack[idx].get_species() not in tax.numbered_species):
                idx = idx - 1 
            stack[idx].label = wnode.nodeargs[0].nodelist[0].chars
            return stack

        #--------------------
        # 1B. preformatted text
        if macroname in tax.macros['pre']:
            if macroname in self.classes:
                node = self.classes[macroname]()
            else:
                node = NodeFactory(macroname, BaseClass=Content)
            node.content =  walker.macro_node_to_latex(wnode)
            # append to parent and bail out
            stack[-1].append_child(node)
            return stack

        #------------------------------
        # 2: Block macros (bibliography, chapter, item)
        #------------------------------
        
        #--------------------
        # 2.1 Bibliography: reads .bib file
        if macroname == 'bibliography':

            # check we have a LATEX_ROOT
            if not self.filename:
                raise LatexParserError("Cannot create bibliography. Latex source file not known.")

            # find bibtex filename
            bibtex_filename = wnode.nodeargs[0].nodelist[0].chars
            if '.' not in bibtex_filename:
                bibtex_filename += '.bib'
            bibtex_filename  = os.path.join(os.path.abspath(os.path.dirname(self.filename)), bibtex_filename)
            
            # create Bibliography() object
            bib = self.parse_bibtex_file(bibtex_filename)                
            
            # append to root node (document) then bail out
            stack[0].append_child(bib)
            return stack

        #--------------------
        # 2.2 Levels: chapter, section, subsection, subsubsection
        if macroname in tax.macros['level']:

           # pop stack to appropriate level
            if macroname in ['chapter', 'section', 'subsection', 'subsubsection']:
                if stack[-1].get_species() == 'subsubsection':
                    subsubsec = stack.pop()
                    stack[-1].append_child(subsubsec)
                if macroname in ['chapter', 'section', 'subsection']:
                    if stack[-1].get_species() == 'subsection':
                        subsec = stack.pop()
                        stack[-1].append_child(subsec)
                    if macroname in ['chapter', 'section']:
                        if stack[-1].get_species() == 'section':
                            sec = stack.pop()
                            stack[-1].append_child(sec)
                        if macroname == 'chapter':
                            if stack[-1].get_species() == 'chapter':
                                chapter = stack.pop()
                                stack[-1].append_child(chapter)
            
            # create new level node and push onto stack
            node = self.classes[macroname]()
            stack.append(node)

            # parse the level title (recursive). 
            # For theorem titles we used wnode.optargs[0].nodelist because
            # there the title is passed as an optional argument (environment).
            # Here wnode.nodeoptarg contains the short title (not implemented)
            if wnode.nodeargs:
                stack.append(Title())
                stack = self.parse_walker_nodelist(wnode.nodeargs[0].nodelist, stack)
                title = stack.pop()
                stack[-1].append_child(title)
        
            # over and out
            return stack

        #--------------------
        # 2.3 Items
        if macroname in tax.macros['item']:

            # create item object            
            node = self.classes[macroname]()
            
            # pop previous item off stack (if any) and append to parent list
            if stack[-1].get_genus() == 'item':
                prev = stack.pop()
                stack[-1].append_child(prev)
            
            # now append this one
            stack.append(node)           

            # check for optional argument 
            if wnode.nodeoptarg:
                if macroname in ['question', 'part', 'subpart', 'subsubpart']:
                    if wnode.nodeoptarg:
                        pts = walker.node_to_latex(wnode.nodeoptarg)
                        stack[-1].append_child(Points(value=pts))
        
            return stack

        #--------------------
        # 3. short ones

        # breaks
        if macroname == '\\' or macroname in tax.macros['break']:
            node = Break()
        
        # spaces
        elif macroname.isspace() or macroname in tax.macros['space']:
            node = Space()

        # escaped characters
        elif macroname in tax.macros['escaped']:
            code = tax.escaped_encodings[macroname]
            node = Text(text = code)            

        # accents
        elif macroname in tax.macros['accent']:
            accent = macroname.strip()
            character = wnode.nodeargs[0].nodelist[0].chars
            text = character
            if (accent, character) in tax.html_encodings:
                text = tax.html_encodings[(accent, character)]
            node = Text(text = text)            

        #--------------------
        # 4A. subfigure (hack)
        elif macroname == 'subfigure':
            node = NodeFactory('subfigure', BaseClass=Macro)
            stack.append(node)
            if wnode.nodeoptarg:
                stack.append(Title())
                stack = self.parse_walker_node(wnode.nodeoptarg, stack)
                title = stack.pop()
                stack[-1].append_child(title)
            if wnode.nodeargs:
                stack = self.parse_walker_nodelist(wnode.nodeargs, stack)
                node = stack.pop()
                stack[-1].append_child(node)
                return stack

        #--------------------
        # 4B. media
        elif macroname in tax.macros['media']:

            # extract src or url
            node = None
            if wnode.nodeargs and len(wnode.nodeargs) > 0:
                wnode2 = wnode.nodeargs[0].nodelist[0]
                if hasattr(wnode2, 'chars'):
                    if macroname == 'includegraphics':
                        node = Image(src = wnode2.chars)
                    if macroname == 'includevideo':
                        node = Media(src = wnode2.chars)
            
            # compute approx. width from optional argument
            if node and wnode.nodeoptarg:
                pct = 30
                if wnode.nodeoptarg.isNodeType(LatexGroupNode):
                    raw = walker.nodelist_to_latex(wnode.nodeoptarg.nodelist)
                else:
                    raw = walker.nodelist_to_latex(wnode.nodeoptarg)
                pairs = dict([s.split('=') for s in raw.split(',')])
                if 'scale' in pairs:
                    pct = 100*float(pairs['scale'])
                elif 'width' in pairs:
                    wspec = pairs['width']
                    import re
                    m = re.search(r'(.+)\\linewidth', wspec)
                    if m:
                        pct = 100*float(m.groups()[0])
                    m = re.search(r'(.+)cm', wspec)
                    if m:
                        pct = 100*float(m.groups()[0])/15
                node.width = int(float(pct)) # round

        #--------------------
        # 5. xrefs and hrefs
        elif macroname in tax.macros['xref'] + tax.macros['href']:
            
            # extract label or url (and the anchor text for href and hyperref)
            if wnode.nodeargs and len(wnode.nodeargs) > 0:
                node = self.classes[macroname]() 
                node.content = wnode.nodeargs[0].nodelist[0].chars
                if macroname in ['href', 'hyperref'] and len(wnode.nodeargs) > 1:
                    stack.append(node)
                    stack = self.parse_walker_node(wnode.nodeargs[1], stack)
                    node = stack.pop()

        #--------------------
        # 6. the rest
        else:
            if macroname in self.classes:
                node = self.classes[macroname]()
            else:
                node = NodeFactory(macroname, BaseClass=Macro)
    
            # call parse_walker_nodelist on the macro arguments (recursive)
            if wnode.nodeargs:
                stack.append(node)
                stack = self.parse_walker_nodelist(wnode.nodeargs, stack, **kwargs)
                node = stack.pop()

        # append new node (if any) to children of parent and bail out
        if node:
            stack[-1].append_child(node)           
        return stack
  

    def parse_walker_math_node(self, wnode, stack, **kwargs):
        '''
        Returns a Latex() or Dismpath() object.
        '''
        if not wnode.isNodeType(LatexMathNode):
            raise LatexParserError("Expected LatexMathNode type, not `%s'" % type(wnode))

        if wnode.displaytype == 'inline':
            node = Latex()
        elif wnode.displaytype in tax.environments['dispmath']:
            node = self.classes[wnode.displaytype]()        
        else:
            node = NodeFactory(wnode.displaytype, BaseClass=Environment)

        content = walker.math_node_to_latex(wnode, **kwargs)
        node.content =  content
        stack[-1].append_child(node)
        return stack
        

    def parse_walker_node(self, wnode, stack, **kwargs):
        '''
        Parse a walker node object. Returns a LatexTreeNode object 
        '''
        if wnode.isNodeType(LatexCharsNode):
            return self.parse_walker_chars_node(wnode, stack)
        
        elif wnode.isNodeType(LatexCommentNode):
            return self.parse_walker_comment_node(wnode, stack)
        
        elif wnode.isNodeType(LatexMathNode):
            return self.parse_walker_math_node(wnode, stack, **kwargs)
        
        elif wnode.isNodeType(LatexGroupNode):
            return self.parse_walker_group_node(wnode, stack, **kwargs)

        elif wnode.isNodeType(LatexEnvironmentNode):
            return self.parse_walker_environment_node(wnode, stack, **kwargs)
        
        elif wnode.isNodeType(LatexMacroNode):
            return self.parse_walker_macro_node(wnode, stack, **kwargs)
        else:
            raise LatexParserError("Expected LatexNode object, not `%s'" % type(wnode))
            return None
        
    
    def parse_walker_nodelist(self, walker_nodelist, stack, **kwargs):
        '''
        Parse a list of LatexNode objects.
        Returns a list of LatexTreeNode objects 
                
        The function pre-processes the list of LatexNode objects, and 
        combines them where necessary into nicer LatexNode objects, before 
        parsing them to produce LatexTreeNode objects
        
        The \[ command means we enter "dispmathmode", where all subsequent
        nodes are appended to a new LatexMathNode until a \] command is 
        encountered, at which point the new LatexMathNode is closed, i.e. 
        popped from the stack and appended to the children of its parent node.
        
        Having combined LatexNodes in this way, we can then safely use
        parse_walker_node() on each of the (possibly modified) LatexNodes.
        The function parse_walker_math_node is called on the new 
        LatexMathNode objects/ This function deals with the _ and ^ commands.
        
        The individual LatexTreeNode objects are appended as children to
        the stack_top node (parent container) inside their individual
        parse_walker_node functions (parse_walker_macro_node etc.)
        
        STRANGE BEHAVIOUR: if we set
            walker_node = LatexMathNode(displaytype='displaymath')
        you might assume that the walker_node.nodelist will be empty
        but it appears not! Adding nodes directly as
            walker_node.nodelist.append(new_walker_node)
        results in lots of previously-encountered text being present 
        in walker_node.nodelist
        Starting with new_nodelist = [] then adding to this before 
        setting walker_node.nodelist = new_nodelist at the end seems to work.
        '''

        idx = 0
        while idx < len(walker_nodelist):

            if walker_nodelist[idx] is None:
                idx = idx + 1 
                continue
                
            wnode = walker_nodelist[idx]
            
            # check for \[ macro. This is an alias for \begin{displaymath}
            # check also for \(...\), which is an alternative to $....$
            if (walker_nodelist[idx].isNodeType(LatexMacroNode) and 
                    walker_nodelist[idx].macroname in ['[', '(']):
                macroname = walker_nodelist[idx].macroname
                # assemble new nodelist
                new_nodelist = []
                while idx < len(walker_nodelist):
                    idx = idx + 1
                    if (walker_nodelist[idx].isNodeType(LatexMacroNode) and 
                            walker_nodelist[idx].macroname in [']',')']):
                        break
                    new_nodelist.append(walker_nodelist[idx])                
                # create new LatexMathNode
                displaytype = 'displaymath' if macroname == '[' else 'inline'
                walker_node = LatexMathNode(displaytype=displaytype)
                walker_node.nodelist = new_nodelist

            # next look for "\itemize \item \item \enditemize"-type constructions
            elif (walker_nodelist[idx].isNodeType(LatexMacroNode) and 
                    walker_nodelist[idx].macroname in tax.environment_species):
                macroname = walker_nodelist[idx].macroname
                end_macroname = 'end' + macroname
                new_nodelist = []
                while idx < len(walker_nodelist):
                    idx = idx + 1
                    if (walker_nodelist[idx].isNodeType(LatexMacroNode) and 
                            walker_nodelist[idx].macroname == end_macroname):
                        break
                    new_nodelist.append(walker_nodelist[idx])
                # create new LatexEnvironmentNode
                walker_node = LatexEnvironmentNode(envname=macroname, nodelist=[])
                walker_node.nodelist = new_nodelist
                
            # # check for switches
            # elif (walker_nodelist[idx].isNodeType(LatexMacroNode) and
            #         walker_nodelist[idx].macroname in tax.switches):
            #     switchname = walker_nodelist[idx].macroname
            #     print('***********************%s' % walker_nodelist[idx].macroname)
            
            # otherwise just take next one
            else:
                walker_node = walker_nodelist[idx]
            
            # parse the walker_wnode and move to next
            stack = self.parse_walker_node(walker_node, stack, **kwargs)
            idx = idx + 1
        
        return stack
        

    def parse_walker_preamble(self, walker_nodelist):
        '''
        Returns a dict of selected preamble macros 
        These are specified in taxonomy.preamble_capture
        Macros must be registered in macrosdef.py
        Valid preambles contain only LatexMacroNode and LatexCommentNode objects
        LatexCommentNode objects are not processed.
        '''
        preamble = {}

        # iterate over LatexNode objects
        for wnode in walker_nodelist:

            # check for LatexMacroNode
            if not wnode.isNodeType(LatexMacroNode):
                continue

            # parse newcommand macros
            if wnode.macroname in ['newcommand', 'renewcommand', 'providecommand']:
                if 'newcommands' not in preamble:
                    preamble['newcommands'] = []
                preamble['newcommands'].append(walker.node_to_latex(wnode))

            # parse usepackage macros
            elif wnode.macroname == 'usepackage':
                if 'packages' not in preamble:
                    preamble['packages'] = []
                preamble['packages'].append(wnode.nodeargs[0].nodelist[0].chars)

            # parse other macros listed in taxonomy.preamble_capture
            elif wnode.macroname in tax.preamble_capture:
                if wnode.nodeargs and type(wnode.nodeargs[0]) == LatexGroupNode:
                    nlist = wnode.nodeargs[0].nodelist
                    if nlist and nlist[0]:
                        if type(nlist[0]) ==  LatexCharsNode:
                            preamble[wnode.macroname] = nlist[0].chars
                        elif type(nlist[0]) ==  LatexGroupNode:
                            nlist2 = nlist[0].nodelist
                            if nlist2[0] and type(nlist2[0]) == LatexCharsNode:
                                preamble[wnode.macroname] = nlist2[0].chars
            
            # ignore unlisted macros
            else:
                logger.info('preamble: macro %s ignored' % wnode.macroname)

        return preamble


    def parse_latex(self, text, **kwargs):
        '''
        Parse a latex string. Returns a LatexTreeNode object.
        A wrepper for parse_walker_nodelist.
        The parse_latex_document function bypasses this function and 
        creates the root node according to \documentclass (Article, Book etc.)
        '''
        from .preprocessor import LatexPreProcessor
        pp = LatexPreProcessor()
        text = pp.preprocess(text)
        walker_nodes = walker.parse(text)
        root = NodeFactory('root', BaseClass=LatexTreeNode)
        stack = [root]
        self.parse_walker_nodelist(walker_nodes, [root], **kwargs)
        return stack[0]
        

    def parse_latex_document(self, text, **kwargs):
        '''
        Parse a latex document. Returns a LatexDocument object.
        Wrepper for parse_walker_nodelist
        The text must have a \begin{document} ... \end{document} element.
        '''        
        #--------------------
        # preprocess
        from .preprocessor import LatexPreProcessor
        pp = LatexPreProcessor()
        text = pp.preprocess(text)

        #--------------------
        # initial parse using LatexWalker (returns a list of LatexNode objects)
        walker_nodes = walker.parse(text)

        #--------------------
        # init LatexDocument object
        doc = LatexDocument()
        if hasattr(self, 'filename') and self.filename:
            doc.filename = self.filename

        #--------------------
        # parse preamble
        doc.preamble = self.parse_walker_preamble(walker_nodes)
    
        #--------------------
        # parse root
        doc.root = None
        for wnode in walker_nodes:
            if type(wnode) == LatexEnvironmentNode and wnode.envname == 'document':
                
                # check preamble for document class
                doc.root = NodeFactory('root', BaseClass=LatexTreeNode)
                if 'documentclass' in doc.preamble:
                    doc_class = doc.preamble['documentclass']
                    if doc_class in self.classes:
                        doc.root = self.classes[doc_class]()

                # init stack
                stack = [doc.root]
                
                # parse the entire nodelist
                stack = self.parse_walker_nodelist(wnode.nodelist, stack, **kwargs)
                
                # clear the stack (doc.root will be the last element)
                while len(stack) > 1:
                    node = stack.pop()
                    stack[-1].append_child(node)

                # champagne!
                doc.root = stack.pop()
                
        #--------------------
        # postprocess
        if doc.root:
            doc.root.set_numbers()
            doc.root.set_titles()
            doc.xrefs = doc.root.get_xref_dict()
            doc.images = doc.root.get_phenotypes('image')
            doc.videos = doc.root.get_phenotypes('media')
            

        # end
        return doc
        
        
    def parse_latex_file(self, filename, **kwargs):
        '''
        The main entry point.  We record the filename in the LatexParser which
        is passed onto the resulting LatexDocument object.
        We need this to 
            (1) allow access to \include and \bibliography files,
            (2) write outputs in various formats (e.g. html, bbq). 
        By default input and output dirs are computed relative to filename
            e.g. /tex/MA1234/main.tex -> /web/MA1234/index.html
        We also need to copy images
            e.g. /tex/MA1234/figures/pic.png -> /tex/MA1234/static/img/pic.png
        '''
        filename = os.path.abspath(filename) if filename else None
        if filename:
            self.filename = filename
            from . import reader
            text = reader.read_latex_document(filename)
            doc = self.parse_latex_document(text, **kwargs)
            doc.head['filename'] = filename
            doc.head['source'] = text
            return doc            
        return None
        
        
    def parse_bibtex_file(self, bibtex_filename):
        '''
        Create Bibliography() object from a bibtex file
        '''
        with open(bibtex_filename) as bibtex_file:
            text = bibtex_file.read()
        return Bibliography(text)
        

    
#------------------------------------------------
def main(args=None):

    tests = []
    
    # tests.append(r'''
    #     \documentclass{exam}
    #     \usepackage{amsmath}
    #     \begin{document}
    #     \[E = \hbar\nu\]
    #     \end{document}
    #     ''')

    tests.append(r'''
        An unordered list:
        \begin{itemize}
        \item[3] apples
        \item[4] oranges
        \end{itemize}
        An ordered list:
        \begin{enumerate}
        \item first 
        \item second 
        \end{enumerate}
    ''')

    tests.append(r'''
        \begin{questions}
        \question[5]
        First question.
        \question[5]
        Second question.
        \end{questions}
        ''')    
    
    tests.append(r'''
        Here is a \textbf{quiz} for you.
        \begin{quiz}\label{quiz:history}
        \begin{questions} 
        \question[5]
        Which is the odd one out?  
        \begin{choices}
        \incorrect John \resp{Bad luck!}
        \incorrect Paul \resp{Bad luck!}
        \incorrect George \resp{Bad luck!}
        \correct Bingo \resp{Well done!}
        \end{choices}
        \begin{answer}
        Bingo was not a member of the Beatles.
        \end{answer}
        \question[5]
        \label{qu:series}
        Which of the following series are convergent?
        \begin{checkboxes}
        \incorrect $\sum_{n=1}^{\infty}\frac{1}{\sqrt{n}}$
        \incorrect $\sum_{n=1}^{\infty}\frac{1}{n}$\resp{This is the \emph{harmonic} series, which is divergent.}
        \correct $\sum_{n=1}^{\infty}\frac{1}{n^2}$
        \correct $x = \sum_{n=1}^\infty \frac{1}{n^3}$
        \end{checkboxes}
        \end{questions}
        \end{quiz}
    ''')

    tests.append(r'''
        \chapter{First chapter}
        Some text.
        \chapter{Second chapter}
        Some more text.
    ''')
    
    tests.append(r'''
        \subsection*{Accents}
        \begin{itemize}
        \item Cram\'{e}r-Rao.
        \item Y m\^{o}r coch.
        \it He is blas\'{e} about it.
        \end{itemize}
    ''')
    
    tests.append(r'''
        \subsection*{Escaped characters}
        Here are some escaped characters:
        \begin{itemize}
        \item ampersand: \& 
        \item percent: \%
        \item dollar: \$
        \end{itemize}
    ''')
    
    tests.append(r'''
        Both {\en english \cy cymraeg} both.
    ''')

    tests.append(r'''
        The {\tt latextree} package.
    ''')

    tests.append(r'''
        \subsection*{Verbatim environments}
        \begin{verbatim}
        To get an alpha type \alpha. 
        For quizzes use the \begin{quiz}...\end{quiz} environment.
        \end{verbatim}
    ''')
    
    tests.append(r'''
        \begin{figure}
        \centering
        \subfigure[Union]{\includegraphics[scale=0.25]{AcupB}\label{fig:union}}\par
        \subfigure[Intersection]{\includegraphics[scale=0.25]{AcapB}\label{fig:intersection}}\par
        \subfigure[Complement]{\includegraphics[scale=0.25]{Acomp}\label{fig:complement}}
        \caption{Three figures using \texttt{subfigure}.\label{fig:setops-subfig}}
        \end{figure}
    ''')

    tests.append(r'''
        \subfigure[Union]{\includegraphics[scale=0.25]{AcupB}\label{fig:union}}\par
    ''')
        
    pa = LatexParser()
    
    for idx, text in enumerate(tests):
        print('==================================')
        print('TEST %d' % idx)
        root = pa.parse_latex(text,
                insert_strict_braces=True,
                non_breaking_spaces=True,
            )

        print('------------------------')
        from lxml import etree
        print(etree.tostring(root.get_xml(), pretty_print=True))
        # from lxml.html import tostring
        # print(tostring(root.get_xml(), pretty_print=True))
        print('------------------------')
        print(root.children)
        print('------------------------')
        text2 = root.get_latex()
        text  = ''.join([x.strip() for x in text.split('\n')])
        text2  = ''.join([x.strip() for x in text2.split('\n')])
        print(text)
        print('--------------')
        print(text2)
        print(text == text2)
        print('--------------')


    return None
    
    # parse from file
    # test_file = '~/python/latextree/tex/LatexTreeTestArticle/main.tex'
    test_file = '~/python/latextree/tex/LatexTreeTestBook/main.tex'
    # test_file = '~/python/latextree/tex/LatexTreeTestExam/main.tex'

    pa = LatexParser()
    doc = pa.parse_latex_file(test_file,
        insert_strict_braces=True,
        non_breaking_spaces=True,
    )


    # xml output
    from lxml import etree
    print(etree.tostring(doc.root.get_xml(), pretty_print=True))

    # info
    print('--------------------')
    print(doc.preamble)
    print('--------------------')
    print(doc.xrefs)
    print('--------------------')
    print(doc.images)
    print('--------------------')
    print(doc.root.get_phenotypes('figure'))
    print('--------------------')


if __name__ == '__main__':
    main()

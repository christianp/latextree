"""
node.py 
Define base classes for LatexTree objects

LatexTreeNode is the base class
LatexTreeNode is subclassed into families: Macro, Environment, Switch and Content (defined elsewhere)
Families are subclassed into genera: Level, List, etc.
Genera are subclassed into species: Chapter, Section etc. or Itemize, Enumerate, etc.
"""

from . import taxonomy as tax

import logging
logger = logging.getLogger(__name__)

#------------------------------------------------
# base class
#------------------------------------------------
class LatexTreeNode(object):
    '''
    Basic node class for LatexTree objects
    
    class variables:
        counter - uniqe node_id for each instance

    instance variables:
        parent - pointer to parent LatexTreeNode 
        children - ordered list of LatexTreeNode objects
        label - text label
        number - sequential counter for genus (e.g. theorem) or species (e.g. chapter)
        title - pointer to another LatexTreeNode
    
    instance variables that may be attached to some species
        width - for Image and Video nodes (percentagae)
        spec - column specification for Tabular nodes
    '''
    counter = 0    
    
    def __init__(self):
        self.node_id = LatexTreeNode.counter
        LatexTreeNode.counter += 1
        self.parent = None
        self.children = []
        logger.info('Node %d created.', self.counter)        

    def __str__(self):
        return self.__repr__()

    def __repr__(self):
        if hasattr(self, 'content') and self.content:       
            return "%s(%s)" % (self.__class__.__name__, self.content)
        else:
            return "%s()" % (self.__class__.__name__)

    #-----------------------------------------------
    # Access functions
    #-----------------------------------------------
    # @classmethod
    # def species(cls):
    #     return cls.__name__.lower()
    #
    # @classmethod
    # def genus(cls):
    #     return cls.__bases__[0].__name__.lower()

    @classmethod
    def get_species(cls):
        return cls.__name__.lower()

    @classmethod
    def get_genus(cls):
        return cls.__bases__[0].__name__.lower()

    @classmethod
    def get_family(cls):
        if cls.__bases__[0].__bases__ and len(cls.__bases__[0].__bases__) > 0:
            return cls.__bases__[0].__bases__[0].__name__.lower()
        return None

    # @classmethod
    # def get_node_type(cls):
    #     return cls.__name__.lower()
    #
    # @classmethod
    # def get_node_class(cls):
    #     return cls.__bases__[0].__name__.lower()


    #-----------------------------------------------
    # Basic operations
    #-----------------------------------------------
    def is_root(self):
        return not self.parent

    def is_leaf(self):
        return not self.children

    def append_child(self, node):
        '''
        Append a child node.
        :param node: the child node
        :param type: LatexTreeNode
        '''
        node.parent = self
        self.children.append(node)

    #-----------------------------------------------
    # Output
    #-----------------------------------------------

    def show(self, depth=0):
        '''
        Print node and its descendants for debugging (recursive).
        '''
        s = []
        istr = '--'
        ss = istr*depth + self.get_genus() + ':' + self.get_species() 
        if hasattr(self, 'content') and self.content:
            ss += '(' + self.content + ')'
        s.append(ss)
        for child in self.children:
            s.append(child.show(depth=depth+1))
        return '\n'.join(s)


    def get_slug(self):
        '''
        Get a text representation of node contents (recursive).
        Useful for titles.
        '''
        s = []
        if hasattr(self, 'content') and self.content:
            import re
            cont = re.sub(r'([^\s\w]|_)+', '', self.content)
            parts = cont.lower().split(' ')
            s.append('-'.join(parts))
        for child in self.children:
            s.append(child.get_slug())
        return '_'.join(s)

    def get_latex(self):
        '''
        Serialize the node back to raw latex.
        We are on a hiding to nothing here - it will be very difficult to reconstruct the
        latex source from the tree. In particular, switches such as ... {\tt teletype} ...
        are represented by <tt>teletype</tt>. It's hard to keep track of where the curly 
        brackets should go.
        '''
        s = []

        # content
        if hasattr(self, 'content') and self.content:
            s.append(self.content)        

        # root node
        if self.get_species() == 'root':
            for child in self.children:
                s.append(child.get_latex())

        # item
        elif self.get_genus() == 'item':
            s.append('\\'+self.get_species())
            pts = self.get_first_child_by_species('points')
            if pts: 
                s.append('[%s]' % pts.get_value())
            # s.append(' ')
            if hasattr(self, 'label') and self.label:
                s.append(r'\label{%s}' % self.label)
            for child in self.children:
                if not pts or (pts and child != pts):
                    s.append(child.get_latex())

        # macros
        elif self.get_species() in tax.macro_species: 
            s.append('\\'+self.get_species()+'{')           
            for child in self.children:
                s.append(child.get_latex())
            s.append(r'}')
            if hasattr(self, 'label') and self.label:
                s.append(r'\label{%s}' % self.label)
            
        # environments
        elif self.get_species() in tax.environment_species:
            s.append('\\begin{%s}' % self.get_species())
            if hasattr(self, 'label') and self.label:
                s.append(r'\label{%s}' % self.label)
            for child in self.children:
                s.append(child.get_latex())
            s.append('\\end{%s}' % self.get_species())
        
        # switches
        elif self.get_species() in tax.switch_species:
            s.append('{\\%s' % self.get_species())
            for child in self.children:
                s.append(child.get_latex())
            s.append('}')
        
        # ignore unlisted species: we don't know if they're 
        # macros or environments. Perhaps we could record this
        # in LatexParser() wne we first encounter unknown species.
        else:
            for child in self.children:
                if child.get_species() in tax.species:
                    s.append(child.get_latex())

        # return ''.join([x.lstrip() for x in s])
        return ''.join(s)


    def get_mpath(self):
        '''
        Compute materialized path (two hex digits = max. 256 children).
        '''
        if not self.parent:
            return ''
        idx = self.parent.children.index(self)
        hexstr = hex(idx)[2:].zfill(2)
        return self.parent.get_mpath() + '.' + hexstr


    def get_xml(self):
        '''
        Serialize as XML. Elements correspond to species.
        '''
        from lxml import etree
        ename = self.get_species()
        if ename[-1] == '*':
             ename = ename[:-1] + 'star'
        element = etree.Element(ename)
        
        # attributes (some block nodes)
        if hasattr(self, 'number') and self.number:     
            element.set('number', str(self.number))
        if hasattr(self, 'label') and self.label:       
            element.set('label', self.label)
        
        # titles are pointers to other LatexTreeNode objects
        # they might contain characters that offends xml
        # the get_slug function comes in handy here!
        if hasattr(self, 'title') and self.title:
            text_title = self.title.get_slug()
            element.set('title', text_title)

        # width attributes are sometimes attached to Image and Media nodes
        # this is basically a hack. To do it properly, nodes should have
        # ann optional "styles" dict. Useful for row and column specs etc.
        if hasattr(self, 'width') and self.width:       
            element.set('width', str(self.width))

        # content 
        if hasattr(self, 'content') and self.content:
            element.text = self.content.strip()
       
        # recursive call
        for child in self.children:
            element.append(child.get_xml())
        
        return element

    #-----------------------------------------------
    # Post-Processing
    #-----------------------------------------------

    def set_titles(self): 
        '''
        Set titles of chapters, figures, etc.
        Wrapper for the recursive function set_title.
        '''
        self.set_title()

    def set_title(self):
        '''
        Set title attribute. This is a pointer to another LatexTreeNode object.
        First child of type "title" is taken.
        '''
        title = next((child for child in self.children if child.get_species() == 'title'), None)
        if title:
            self.title = title
        # recurse
        for child in self.children:
            child.set_title()


    def set_numbers(self): 
        '''
        Set numbers of chapters, figures, etc.
        Wrapper for the recursive function set_number.
        '''
        counters = dict.fromkeys(tax.counters, 0)
        self.set_number(counters)

    def set_number(self, counters):
        '''
        Set number. Applied recursively.
        '''
        if self.get_genus() in counters or self.get_species() in counters:
            
            # chapter (reset all)
            if self.get_species() == 'chapter':
                counters['chapter'] += 1
                for key in counters:
                    if key != 'chapter':
                        counters[key] = 0
                self.number = counters['chapter']

            # section (reset subsection)
            elif self.get_species() == 'section':
                counters['section'] += 1
                counters['subsection'] = 0
                self.number = counters['section']
                                    
            # subsection
            elif self.get_species() == 'subsection':
                counters['subsection'] += 1
                self.number = counters['subsection']

            # figure (reset subfigure)
            elif self.get_species() == 'figure':
                counters['figure'] += 1
                counters['subfigure'] = 0
                self.number = counters['figure']

            # table (reset subtable)
            elif self.get_species() == 'table':
                counters['table'] += 1
                counters['subtable'] = 0
                self.number = counters['table']
                                    
            # all others with counters (as defined in taxonomy.py)
            elif self.get_genus() in tax.counters:
                counters[self.get_genus()] += 1
                self.number = counters[self.get_genus()]

            elif self.get_species() in tax.counters:
                counters[self.get_species()] += 1
                self.number = counters[self.get_species()]

        # recurse
        for child in self.children:
            child.set_number(counters)

    #-----------------------------------------------
    # For applications
    #-----------------------------------------------

    def get_phenotypes(self, species):
        '''
        Get an ordered list of all children of the given species (recursive).
        Include self if appropriate.
        '''
        phenotypes=[]
        if self.get_species() == species:
            phenotypes.append(self)
        for child in self.children:
            phenotypes.extend(child.get_phenotypes(species))
        return phenotypes


    # create label -> LatexTreeNode object map (recursive)
    def get_xref_dict(self): 
        '''
        Create a dictionary of labels mapped to LatexTreeNode objects (recursive).
        '''
        xref_dict = {}        
        if hasattr(self, 'label') and self.label:
            xref_dict[self.label] = self
        for child in self.children:
            xref_dict.update(child.get_xref_dict())
        return xref_dict
#
    def get_first_child_by_species(self, species):
        '''
        Get first node of a given species among children (if any).
        For recovering attributes that are parsed as child nodes
        e.g. title, caption or points
        '''
        for child in self.children:
            if child.get_species() == species:
                return child
        return None

    def get_title_node(self):
        '''
        Get first title node among children (if any).
        '''
        for child in self.children:
            if child.get_species() == 'title':
                return child
        return None

    def get_caption_node(self):
        '''
        Get first caption node among children (if any).
        '''
        for child in self.children:
            if child.get_species() == 'caption':
                return child
        return None

    def get_enclosing_chapter(self):
        '''
        Get parent chapter (if any).
        '''        
        node = self
        while node.get_species() != 'chapter' and node.parent:
            node = node.parent
        if node.get_species() == 'chapter':
            return node
        return None

    def get_enclosing_section(self):
        '''
        Get parent section (if any).
        '''        
        node = self
        while node.get_species() != 'section' and node.parent:
            node = node.parent
        if node.get_species() == 'section':
            return node
        return None

#------------------------------------------------
# derived classes
#------------------------------------------------
class Macro(LatexTreeNode):
    def __init__(self):
        LatexTreeNode.__init__(self)
            
class Environment(LatexTreeNode):
    def __init__(self):
        LatexTreeNode.__init__(self)
            
class Switch(LatexTreeNode):
    def __init__(self):
        LatexTreeNode.__init__(self)
            
#------------------------------------------------
def main(args=None):
    print("node.py")
    root = LatexTreeNode()
    n1 = LatexTreeNode()
    n1.number = 5
    n1.label = 'lab:first'
    root.append_child(n1)
    n2 = LatexTreeNode()
    n2.label = 'lab:second'
    n2.content="hello world!"
    root.append_child(n2)
    n3 = LatexTreeNode()
    n3.content = "The Title"
    root.append_child(n3)
    n2.title = n3
    from lxml import etree
    xtree = root.get_xml()
    print(etree.tostring(xtree, pretty_print=True))
    xrefs = root.get_xref_dict()
    print(xrefs)
    root.set_numbers()
    root.set_titles()
    
    print(tax.switch_species)
    print(n1.get_species())
    print(n1.get_genus())
    print(n1.get_family())
    
if __name__ == '__main__':
#    import logging.config
#    logging.config.fileConfig('logging.conf', disable_existing_loggers=False)
    main()


    

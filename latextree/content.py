"""
content.py 
Content nodes for LatexTree objects
"""

from .node import LatexTreeNode

class Content(LatexTreeNode):
    r'''
    Abstract class for content nodes.
    
    Media (content=`src`): from \includevideo{src}
    Image (content=`src`): from includegraphics{src}
    Href: (content=`url`): from hyperlink macros \href{}{} or \url{}
    Xref: (`label`): from x-ref macros e: \ref, \eqref, \pageref, \autoref, \nameref, \cite 
    Latex (`latex`): mathmode text, found between $....$ or \(...\) (MathJax)
    Text: (`text`): mormalmode text
    Mark: (`mark`): from optional argument to question, part and subpart items
    Comment: (`comment`): comment text

    Content nodes are not necessarily leaf nodes. For example
        1. the content field of href objects is the url itself (ascii)
        2. linked content is stored in the children

    Image and Media objects are given a "width" attribute (hack)
    Tabular objects are given a "colspec" attribute (hack)
    '''

    def __init__(self):
        LatexTreeNode.__init__(self)

    def __repr__(self):
        '''
        Show content if any (crop if too long)
        '''
        s = []
        s.append('%s(' % self.__class__.__name__)
        if hasattr(self, 'content') and self.content:
            preview = self.content
            preview_length = 23
            if len(preview) > preview_length:
                preview = preview[:preview_length] + '...'
            s.append(repr(preview))
        s.append(')')
        return ''.join(s)

    def html(self):
        '''
        Return HTML representation. Doesn't work!
        '''
        s = []
        s.append('<span class="%s">' % self.get_node_type())
        if hasattr(self, 'content') and self.content:
            s.append(self.content)
        for child in self.children:
            s.append(child.html())
        s.append('</span>')
        return ''.join(s)



class Url(Content):
    '''
    Content node for external hyperlinks.
    Argument: `url` 
    '''
    def __init__(self, url=None):
        Content.__init__(self)
        self.content = url

    def get_url(self):
        return self.url


class Xref(Content):
    '''
    Content node for internal cross-references.
    Argument: `label` 
    '''
    def __init__(self, label=None):
        Content.__init__(self)
        self.content = label

    def get_label(self):
        return self.content


class Image(Content):
    '''
    Content node for images (file name).
    Argument: `src` 
    '''
    def __init__(self, src=None):
        Content.__init__(self)
        self.content = src

    def get_src(self):
        return self.content


class Media(Content):
    '''
    Content node for videos (url).
    Argument: `src` 
    '''
    def __init__(self, src=None):
        Content.__init__(self)
        self.content = src

    def get_src(self):
        return self.content



class Latex(Content):
    '''
    Content node for latex markup.
    Argument: `latex` 
    '''
    def __init__(self, latex=None):
        Content.__init__(self)
        self.content = latex

    def get_latex(self):
        return self.content


class Comment(Content):
    '''
    Content node for comments.
    Argument: `comment` 
    '''
    def __init__(self, comment=None):
        Content.__init__(self)
        self.content = comment

    def get_commment(self):
        return self.content


class Text(Content):
    '''
    Content node for plain text.
    Argument: `text` 
    '''
    def __init__(self, text=None):
        Content.__init__(self)
        self.content = text

    def get_text(self):
        return self.content

class Points(Content):
    '''
    Content node for points (marks available for a question)
    Argument: `points` 
    '''
    def __init__(self, value=None):
        Content.__init__(self)
        self.content = value

    def get_value(self):
        return self.content

#------------------------------------------------
# Links (experimental)

class LatexTreeLink(LatexTreeNode):
    '''
    Class mapping labels to LatexTreeNodes. These are computed during post-processing
    after the nodes have all been created. These turns the tree into a graph.
    Linked content stored as children
    The URL can point to any web resource (e.g. webpage, image, video clip, elements within a webpage)
    Perhaps ctree2html could include these within iframes. 
    '''
    def __init__(self, destination=None):
        LatexTreeNode.__init__(self)
        self.source = source            # anchor LatexTreeNode
        self.destination = destination # destination LatexTreeNode

    def __repr__(self):
        s = []
        s.append('%s(' % self.__class__.__name__)
        if hasattr(self, 'source') and self.source:
            s.append(repr(self.source))
        if hasattr(self, 'destination') and self.destination:
            s.append(', ')
            s.append(repr(self.destination))
        s.append(')')
        return ''.join(s)


#------------------------------------------------
def main():
    print("content.py")
    
    mama = LatexTreeNode()
    c1 = Text(text='hello ')
    c2 = Latex(latex=r'$\alpha+\beta$')
    c3 = Text(text=' goodbye.')
    mama.children = [c1, c2, c3]
    print(mama.show())
      
if __name__ == '__main__':
    main()


"""
The ``document`` module provides an API for parsing LaTeX documents and
constructs a representation as a tree structure based on nodes classes.
LatexParser understands the syntax of most common macros but is NOT a
replacement for a full LaTeX engine. The parser shouldonly be invoked 
after the input has been successfully compiled under LaTeX.

Example
>>> from parser import LatexParser
>>> pa = LatexParser()

# parse raw latex
>>> text = r'\[E=mc^2\]'
>>> root = pa.parse_latex(text)

# parse file
>>> filename = './test/tex/main.tex'
>>> doc = pa.parse_latex_file(filename)

# extract all quizzes
>>> doc.root.get_phenotypes('quiz')
"""

import os
from jinja2 import Environment, FileSystemLoader

from . import settings

import logging
logger = logging.getLogger(__name__)

class LatexDocumentError(Exception):
    '''
    Generic exception class raised by LatexDocument.
    '''
    pass

class LatexDocumentParseError(LatexDocumentError):
    '''
    Parse error.
    '''
    def __init__(self, msg):
        self.msg = msg
        LatexDocumentError.__init__(self, msg)


class LatexDocument(object):    
    '''
    Class to represent a Latex document. 
    '''
    def __init__(self, 
                filename=None,
                text=None, 
                head=dict(), 
                preamble=dict(), 
                newcommands=list(), 
                xrefs=dict(), 
                root=None, 
        ):
        self.filename = filename
        self.text = text
        self.head = head
        self.preamble = preamble
        self.newcommands = newcommands
        self.root = root
        self.xrefs = xrefs

        
    def make_website(self, copy_static=True, copy_figures=True, LATEX_ROOT=None, WEB_ROOT=None):
        '''
        Create standalone website.

        LATEX_ROOT is computed from self.head['filename'] unless specified otherwise.
        The filename is set by the LatexParser.parse_latex_file function
        (not parse_latex or parse_latex_document)

        WEB_ROOT = LATEX_ROOT/web-filename-noext unless specified otherwise.
        HTML files are written to WEB_ROOT (WEB_ROOT/index.html etc.)
        
        If \modulecode{} is specified in the preamble we write to 
        WEB_ROOT/modulecode/web-filename-noext

        Options:
            copy_static: css files written to WEB_ROOT/static/css
            copy_figures: image files written to WEB_ROOT/static/img        
        '''

        #----------------------------------------------
        # create directories
        #----------------------------------------------
        # Compute the latex source directory
        # We need this for copying image files from LATEX_ROOT/figures
        # The `filename` attribute of LatexDocument object must be set
        # This is done automatically by LatexParser.parse_latex_document
        # which returns LatexDocument objects. This is in contrast with
        # LatexParser.parse_latex_document which returns LatexTreeNode 
        # objects.
        if not LATEX_ROOT:
            if 'filename' in self.head and self.head['filename']:
                main_tex = self.head['filename']
                LATEX_ROOT = os.path.dirname(os.path.abspath(main_tex))
            else:
                import sys
                sys.stderr.write('LatexDocument object has no filename attribute\n')
                return 0

        # Create output directory (default is LATEX_ROOT/web-filename-noext)
        if not WEB_ROOT:
            fname_base = os.path.basename(self.head['filename'])
            fname_noext = os.path.splitext(fname_base)[0]
            WEB_ROOT = os.path.join(LATEX_ROOT, 'web-' + fname_noext)
            
#        # time stamp for output folder
#        from datetime import datetime
#        time_str = datetime.now().strftime('%Y-%m-%d-%H-%M-%S')
#        WEB_ROOT = os.path.join(WEB_ROOT, time_str)

        # create the output directory if necessary
        if not os.path.exists(WEB_ROOT):
            os.makedirs(WEB_ROOT)
    
 
        #----------------------------------------------
        # assemble context dict
        #----------------------------------------------

        # initialise
        context = {}
        context['doc'] = self
        chapters = None
        sections = None

        # extract chapters (if any)
        chapters = [child for child in self.root.children if child.get_species() == 'chapter']
        context['chapters'] = chapters
        
        # if no chapters, extract sections
        if not chapters:
            sections = [child for child in self.root.children if child.get_species() == 'section']
            context['sections'] = sections
            
        # extract bibliography from level-one children
        bibliography = next((child for child in self.root.children if child.get_species() == 'bibliography'), None)
        context['bibliography'] = bibliography
        
        #----------------------------------------------
        # create urls
        #----------------------------------------------

        def make_url(node, include_label=True):
            '''
            This function defines the url structure for the website,
            based on chapter and section numbers.
            '''
            if node.get_species() == 'bibliography':
                return 'bibliography.html'
            if node.get_genus() == 'document':
                return 'index.html'
            chap = node.get_enclosing_chapter()
            sect = node.get_enclosing_section()
            cno = chap.number if chap and hasattr(chap, 'number') else 0
            sno = sect.number if sect and hasattr(sect, 'number') else 0

            url = (r'ch%02dsec%02d.html' % (cno, sno))
            if include_label:
                if hasattr(node, 'label') and node.label:
                    url += ('#%s' % label)
            return url

        # make page urls
        page_urls = {}
        if chapters:
            for chapter in chapters:
                page_urls[chapter] = make_url(chapter, include_label=False)
                for section in [child for child in chapter.children if child.get_species() == 'section']:
                    page_urls[section] = make_url(section, include_label=False)
        elif sections:
            for section in sections:
                page_urls[section] = make_url(section, include_label=False)
        if bibliography:
                page_urls[bibliography] = 'bibliography.html'
        context['page_urls'] = page_urls

        # make xref urls
        xref_urls = {}
        for label in self.xrefs:
            logger.info('processing label %s' % label)
            xref_urls[label] = make_url(self.xrefs[label])        
        context['xref_urls'] = xref_urls
        
        # get image sources
        image_files = {}
        image_dir = LATEX_ROOT
        if 'graphicspath' in self.preamble and self.preamble['graphicspath']:
            image_dir = os.path.join(image_dir, self.preamble['graphicspath'])
        
        for image in self.images:
            file_name = image.get_src()
            if file_name[-4:] != '.png':
                file_name = file_name + '.png'
            image_files[image] = os.path.join('static/img/', file_name)
        context['image_files'] = image_files

        #----------------------------------------------
        # create pages
        #----------------------------------------------

        # load templates
        env = Environment(loader=FileSystemLoader(settings.TEMPLATE_ROOT), trim_blocks=True, lstrip_blocks=True)
        # env = Environment(loader=FileSystemLoader(settings.TEMPLATE_ROOT), trim_blocks=True)

        #--------------------------
        # create index page
        # if there are no chapters or sections, we include the bibiliography on the index page.
        template = env.get_template('index.html')
        context["nxt"] = sections[0] if sections else chapters[0] if chapters else None
        output = template.render(context)
        output_file = os.path.join(WEB_ROOT, 'index.html')
        with open(output_file, "wb") as f:
            f.write(output.encode('utf-8'))

        #--------------------------
        # create chapter pages (assumes that chapters are ordered correctly)
        # we use "enumerate" to extract the previous and next chapters
        template = env.get_template('chapter_detail.html')
        
        for idx, chapter in enumerate(chapters):
            context['chapter'] = chapter
            context['sections'] = [child for child in chapter.children if child.get_species() == 'section']
            context["prv"] = chapters[idx-1] if idx > 0 else None
            context["nxt"] = chapters[idx+1] if idx+1 < len(chapters) else (bibliography if bibliography else None)
            
            output = template.render(context)
            output_file = os.path.join(WEB_ROOT, make_url(chapter, include_label=False))
            with open(output_file, "wb") as f:
                f.write(output.encode('utf-8'))
        
        #--------------------------
        # create section pages (assumes that sections are ordered correctly)
        template = env.get_template('section_detail.html')
        
        if chapters:
            for cidx, chapter in enumerate(chapters):
                sections = [child for child in chapter.children if child.get_species() == 'section']
                context['chapter'] = chapter
                context['sections'] = sections 
                for sidx, section in enumerate(sections):
                    context['section'] = section
                    context["prv"] = sections[sidx-1] if sidx > 0 else (chapters[cidx-1] if cidx > 0 else None)
                    context["nxt"] = sections[sidx+1] if sidx+1 < len(sections) else (chapters[cidx+1] if cidx+1 < len(chapters) else (bibliography if bibliography else None))
                    output = template.render(context)
                    output_file = os.path.join(WEB_ROOT, make_url(section, include_label=False))
                    with open(output_file, "wb") as f:
                        f.write(output.encode('utf-8'))
            # if bibliography:
            #     context["prv"] = chapters[-1] if chapters else None
            #     context["nxt"] = None
            #     template = env.get_template('bibliography_page.html')
            #     output = template.render(context)
            #     output_file = os.path.join(WEB_ROOT, 'bibliography.html')
            #     with open(output_file, "wb") as f:
            #         f.write(output)
            
        elif sections:
            for sidx, section in enumerate(sections):
                context['section'] = section
                context["prv"] = sections[sidx-1] if sidx > 0 else None
                context["nxt"] = sections[sidx+1] if sidx+1 < len(sections) else (bibliography if bibliography else None)                
                output = template.render(context)
                output_file = os.path.join(WEB_ROOT, make_url(section, include_label=False))
                with open(output_file, "wb") as f:
                    f.write(output.encode('utf-8'))
            # if bibliography:
            #     context["prv"] = sections[-1] if sections else None
            #     context["nxt"] = None
            #     template = env.get_template('bibliography_page.html')
            #     output = template.render(context)
            #     output_file = os.path.join(WEB_ROOT, 'bibliography.html')
            #     with open(output_file, "wb") as f:
            #         f.write(output)
    
        #--------------------------
        # create bibliography page
        if bibliography and (chapters or sections):
            if chapters:
                context["prv"] = chapters[-1] if chapters else None
            elif sections:
                context["prv"] = sections[-1] if sections else None
            context["nxt"] = None
            template = env.get_template('bibliography_page.html')
            output = template.render(context)
            output_file = os.path.join(WEB_ROOT, 'bibliography.html')
            with open(output_file, "wb") as f:
                f.write(output.encode('utf-8'))
        
        #--------------------------
        # copy static files to WEB_ROOT
        if copy_static:
            import shutil
            from_path = settings.STATIC_ROOT
            if os.path.exists(from_path):
                to_path = os.path.join(WEB_ROOT, 'static/')
                if os.path.exists(to_path):
                    shutil.rmtree(to_path)
                shutil.copytree(from_path, to_path)
    
        #--------------------------
        # copy figures to WEB_ROOT
        if copy_figures:
            
            from_path = LATEX_ROOT
            if 'graphicspath' in self.preamble and self.preamble['graphicspath']:
                from_path = os.path.join(from_path, self.preamble['graphicspath'])

            to_path = os.path.join(WEB_ROOT, 'static/img/')
            if not os.path.exists(to_path):
                os.makedirs(to_path)
                
            import fnmatch
            file_list = os.listdir(from_path)
            formats = ('png', 'pdf',' jpg')
            image_files = []
            for fmt in formats:
                wildcard = r'*.%s' % fmt
                image_files.extend(fnmatch.filter(file_list, wildcard))

            import shutil
            for image_file in image_files:
                image_file = os.path.join(from_path, image_file)
                shutil.copy(image_file, to_path)
                    

        #--------------------------
        # end: create and return zip file
        return None


    def bbq(self, include_mathjax_header=False):
        '''
        Extract questions and typeset for Blackboard.
        '''    
        
        # set mathjax header
        mathjax_header = ''
        if include_mathjax_header:
            # mathjax_header += '<script type="text/x-mathjax-config">%s</script>' % settings.mathjax_config
            mathjax_header += '<script type="text/javascript">%s</script>' % settings.mathjax_source
             

        # set newcommands
        if 'newcommands' in self.preamble and self.preamble['newcommands']:
            nc_list = [r'\(%s\)' % nc for nc in self.preamble['newcommands']]
            new_commands = '<div style="display: none;">' + ''.join(nc_list) + '</div>' 
    

        # load templates
        from jinja2 import Environment, FileSystemLoader
        env = Environment(loader=FileSystemLoader('templates'), trim_blocks=True, lstrip_blocks=True)

        # init question pool
        pool = []
    
        #-------------------------
        # start: iterate over quizzes
        quizzes = self.root.get_phenotypes('quiz')
        if quizzes:
            for quiz in quizzes:
                
                #-------------------------
                # scan children for question set
                for child in quiz.children:
                    if child.get_species() == 'questions':
                        
                        #-------------------------
                        # start: iterate over questions
                        questions = child.children
                        for question in questions:
                            
                            bbq = []
                            choices = None
                            points = None
                            
                            # examine question components
                            for qchild in question.children:
    
                                # find choices or checkboxes (and set question_type)
                                if qchild.get_species() == 'choices':
                                    question_type = 'MC'
                                    choices = qchild
                                elif qchild.get_species() == 'checkboxes':
                                    question_type = 'MA'
                                    choices = qchild
                                    
                                # find points
                                if qchild.get_species() == 'points':
                                    points = qchild.get_value()
                                
                                
                            # ignore others
                            if not choices:
                                continue
    
                            # append question type as first field of bbq question
                            bbq.append(question_type)
                            
                            # set points (testing: not relevant for bbq)
                            # if points:
                            #     bbq.append('[%s]' % points)
                                
                            # render template for question
                            context = {}
                            context['node'] = question
                            context['points'] = points
                            template = env.get_template('bbq.html')
                            output = template.render(context)
    
                            bbq.append(mathjax_header + output)
                            
                            if choices:
                                for choice in choices.children:
                                    
                                    # render template for answer
                                    # the bbqset template is recursive so
                                    # answers can contain dispmath and 
                                    # other environments
                                    context['node'] = choice
                                    output = template.render(context)
                                    bbq.append(output)
                                    
                                    # set answer as correct or incorrect
                                    # Blackboard wants CAPS!
                                    if choice.get_species() == 'correct':
                                        bbq.append('CORRECT')
                                    else:
                                        bbq.append('INCORRECT')
    
                            # assemble question (tab-separated) and append to pool
                            pool.append('\t'.join(bbq))
                        
                        # ignore multiple question sets within one exercise
                        # this helps with unique numbering
                        break
    
                        # end: iterate over questions
                        #-------------------------

                # end: scan over children of quiz for question sets
                #-------------------------
    
            # end: iterate over quizzes
            #-------------------------
            return '\n'.join(pool)


    def tex2stack(self):
        '''Extract questions and typeset for Stack.'''
        pass
        
    def tex2numbas(self):
        '''Extract questions and typeset for Numbas.'''    
        pass

    def tex2dewis(self):
        '''Extract questions and typeset for Dewis.'''    
        pass

    def tex2pdf(self, blanks=False, proofs=True, answers=True):
        '''
        Export PDF.
        It would be nice to have a command line application which
        would create main-web.zip in the same directory. Simple!
        $ latextree main.tex --web --noproofs --noanswers
        $ latextree main.tex --pdf --blanks --2up --slides
        $ latextree main.tex --tex2blackboard
        ''' 
        pass  
                                
#------------------------------------------------
def main():
    print("latextree.document.py")
    
    from utils import read_latex_document
    from parser import LatexParser

    tests = []    
    tests.append(r'''
        \documentclass{article}
        \usepackage{camel}
        %----------------------------------------
        \begin{document}
        \begin{quiz}\label{quiz:history}
        \begin{questions} 
        
        \question[5]
        Which is the odd one out?  
        \begin{choices}
        \incorrect John %\resp{Bad luck!}
        \correct Bingo %\resp{Well done}
        \incorrect Paul %\resp{Bad luck!}
        \incorrect George %\resp{Bad luck!}
        \end{choices}
        \begin{answer}
            Bingo was not a member of the Beatles.
        \end{answer}

        \question[5]
        \label{qu:series}
        Which of the following series are convergent?
        \begin{checkboxes}
        \incorrect $\sum_{n=1}^{\infty}\frac{1}{\sqrt{n}}$
        \incorrect $\sum_{n=1}^{\infty}\frac{1}{n}$
        %\resp{This is the \emph{harmonic} series, which is divergent.}
        \correct $\sum_{n=1}^{\infty}\frac{1}{n^2}$
        \correct $x = \sum_{n=1}^\infty \frac{1}{n^3}$
        \end{checkboxes}

        \end{questions}
        \end{quiz}

        \end{document}
    
    ''')

    tests.append(r'''
        \documentclass{article}
        \begin{document}
        \chapter{First chapter}
        Some text.
        \addtocontentsline{bingo}
        \chapter{Second chapter}
        Some more text.
        \end{document}    
    ''')
    
    pa = LatexParser()
    for idx, s in enumerate(tests):
        print('==================================')
        print('TEST %d' % idx)
        doc = pa.parse_latex_document(s, insert_strict_braces=True, non_breaking_spaces=True)
        from lxml import etree
        print('------------------------')
        print(etree.tostring(doc.root.get_xml(), pretty_print=True))
        print('------------------------')
        print(doc.bbq())
        print('--------------------')

    # return None

    # parse file
    test_file = '/Users/scmde/Dropbox/python/latextree/tex/LatexTreeTestBook/main.tex'
    # test_file = '~/python/latextree/tex/LatexTreeTestBook/main.tex'
    # test_file = '~/python/latextree/tex/LatexTreeTestArticle/main.tex'
    # test_file = '~/python/latextree/tex/LatexTreeTestExam/main.tex'
    pa = LatexParser()
    doc = pa.parse_latex_file(test_file)

    # output
    from lxml import etree
    print(etree.tostring(doc.root.get_xml(), pretty_print=True))
    # from lxml.html import tostring
    # print(tostring(doc.root.get_xml(), pretty_print=True))
    # print('--------------------')
    # print(doc.root.show())
    print('--------------------')
    print('Preamble:')
    print(doc.preamble)
    print('--------------------')
    print('Blackboard questions:')
    print(doc.bbq())
    print('--------------------')
    print('Labelled nodes:')
    print(doc.xrefs)
    print('--------------------')
    print('Website:')
    print(doc.make_website())
    print('--------------------')
    
if __name__ == '__main__':
    main()




    

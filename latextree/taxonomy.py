"""
taxonomy.py 
Taxonomy of LatexTree objects

Macros and environments are classified as shown below.
Latex objects are partitioned into classes called "genera" (e.g. level, list)
The objects themselves are referred to as "species" (e.g. chapter, itemize)
For example: the \chapter macro is of genus "level" and species "chapter".
"""

macros = {
    'level':    ('chapter', 'section', 'subsection', 'subsubsection', 'bibliography'),
    'heading':  ('chapterstar', 'sectionstar', 'subsectionstar'),
    'item':     ('item', 'bibtem', 'question', 'part', 'subpart', 'subsubpart', 'correct', 'incorrect'),
    'break':    ('par', 'vspace', 'smallskip', 'bigskip'),
    'xref':     ('ref', 'pageref', 'autoref', 'nameref', 'cite', 'hyperref'),
    'href':     ('url', 'href'),
    'media':    ('includegraphics', 'includevideo'),
    'language': ('eng', 'wel'),
    'style':    ('emph', 'textbf', 'textit', 'texttt', 'textsl', 'textsc', 'underline'),
    'space':    ('hspace', 'quad', 'qquad', ' ', ','),
    'counter':  ('newcounter', 'setcounter'),
    'preamble': ('documentclass', 'usepackage', 'title', 'author', 'date', 'institution', 'providecommand', 'newcommand', 'renewcommand'),
    'accent':   ("'", '`', '"', '^', 'c'),
    'escaped':  (' ', ',', '$', '%', '&', '{', '}', '(', ')'),
    'feedback': ('resp',),
    'pre':      ('eqref',),
    'misc':     ('subfigure',)
}         
                                      
environments = {
    'document':     ('book', 'article', 'standalone'),
    'list':         ('itemize', 'enumerate', 'thebibliography', 'questions', 'parts', 'subparts', 'choices', 'checkboxes'),
    'theorem':      ('theorem', 'lemma',  'proposition', 'corollary', 'definition', 'remark', 'example', 'note'),
    'float':        ('table', 'figure',  'video'),
    'hidden':       ('proof', 'solution', 'answer', 'hint'),
    'box':          ('abstract', 'framed', 'center', 'quote', 'minipage', 'response'),
    'task':         ('exercise', 'quiz'),
    'language':     ('english', 'welsh'),
    'tabular':      ('tabular', 'tabbing'),
    'picture':      ('picture', 'tikzpicture', 'pspicture'),
    'dispmath':     ('displaymath', 'equation', 'eqnarray', 'align', 'equation*', 'eqnarray*', 'align*',),
    'feedback':     ('response',),
    'pre':          ('verbatim', 'lstlisting',),

}
switches = {
    'style':    ('bf', 'it', 'tt', 'sl', 'sc', 'normalfont'),
    'language': ('cy', 'en', 'fr', 'de', 'bi')
}

macro_species = [mac for key in macros for mac in macros[key]]
environment_species = [env for key in environments for env in environments[key]]
switch_species = [sw for key in switches for sw in switches[key]]
species = macro_species + environment_species + switch_species

# set parameters to be captured from document preamble
preamble_capture = (
    'documentclass',
    'institution',
    'modulecode',
    'moduletitle',
    'moduleterm',
    'academicyear',
    'title',
    'author',
    'date',
    'version',
    'graphicspath',
    'usepackage',
    'hypersetup',
    'newcommand',
    'renewcommand',
)

# numbered
numbered_genera = ['level', 'theorem', 'float', 'item', 'task', 'subfigure']
numbered_species = ['subfigure']

# titled (not used)
titled_genera   = ['document', 'level', 'theorem', 'float']

# define counters
counters = (
    'chapter',
    'section',
    'subsection',
    'theorem',
    'figure',
    'subfigure',
    'table',
    'subtable',
    'video',
    'task',
)

html_encodings = {
    ('^', 'a'): r'&#226;',                
    ('c', 'c'): r'&#231;',                
    ('`', 'e'): r'&#232;',
    ("'", 'e'): r'&#233;',
    ('^', 'e'): r'&#234;',                
    ('"', 'e'): r'&#235;',                
    ('^', 'i'): r'&#238;',                
    ('"', 'i'): r'&#239;',                
    ('"', 'o'): r'&#246;',                
    ('^', 'o'): r'&#244;',                
    ('^', 'u'): r'&#251;',                
    ('^', 'w'): r'&#373;',                
}

escaped_encodings = {
    ' ' : r'&#32;',
    ',' : r'&#32;',
    '$' : r'&#36;',
    '%' : r'&#37;', 
    '&' : r'&#38;', 
    '{' : r'{', 
    '}' : r'}',
    'pounds': r'&#163;',
}

    

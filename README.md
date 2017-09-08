# The `latextree` Package

Creates a document oject model for LaTeX and provides some useful functions. The `LatexParser` methods understand the syntax of most common macros but is NOT a replacement for a full LaTeX engine. The parser shouldonly be invoked only after the input has been successfully compiled under LaTeX.The package assumes that 

Example:
```python
>>> from latextree.parser import LatexParser
>>> pa = LatexParser()
>>> filename = "/path/to/main.tex""
>>> doc = pa.parse_latex_file(filename)
>>> doc.make_website()			# create website 
>>> bbqs = doc.bbq()			# extract mc/ma questions in Blackboard format (plain text)
>>> docx = doc.root.get_xml()	# create xml document
>>> from lxml import etree
>>> print etree.tostring(docx, pretty_print=True) 
```

If `latextree` is installed as a package:
```python
>>> import latextree
>>> filename = "/path/to/main.tex""
>>> doc = load(filename)
>>> doc.make_website()	# create website
>>> bbqs = doc.bbq()	# extract mc/ma questions in Blackboard format (plain text)
>>> exit()
```

---
## Help!

The following are yet to be implemented properly. 

* Exception handling
* Testing
* Logging
* Documentation

These need the attention of a software engineer. 

---
## `make_website`

* style files are copied to WEB_ROOT/static/css. Tthese can be modified post-production.
* figures are copied to WEB_ROOT/static/img
* LATEX_ROOT is the directory containing the main latex file.
* html files are written to WEB_ROOT (default is the latex root directory)
* urls are constructed from chapter and/or section numbers (if any)

### Templates
The `LatexDocument.make_website()` function uses `jinja2` templates. 

* `scripts.html` loads the `MathJax` and `jquery` CDNs from cloudflare.
* `node.html` does most of the work. This needs to be broken up.

### Static files

* `css/`: The stylesheets are rough-and-ready and need a lot of work (especially for phones and tablets).
* `img/`: Image files are copied into here.
* `js/`:  Currently contains only a simple show/hide function. 

---
## Modules

* `bibliography`: wrapper for `bibtexparser`
* `content`: content nodes
* `document`: `LatexDocument` class and output functions
* `factory`: creates node classes and objects
* `ltree`: command line tools
* `macrosdef`: macro definitions for `pylatexenc.latexwalker`
* `node`: base class for LatexTreeNode` objects.
* `parser`: `LatexParser` class. Creates `LatexDocument` objects.
* `preprocessor`: prepare latex source `pylatexenc.latexwalker`(replace $$...$$ etc.)
* `reader`: input functions and minor utilities
* `settings`: settings file for website.
* `tabular`: parse tabular environments from latex source.
* `taxonomy`: taxonomy of document elements.
* `walker`: wrapper for `pylatexenc.latexwalker`.

### Dependencies

* `bibtexparser`
* `jinja2`
* `lxml`
* `pylatexenc`

## Test files
The `tex` directory contains: 
* `LatexTreeTestBook` for testing the `book` document class 
* `LatexTreeTestArticle` for testing the `article` document class
* `LatexTreeTestExam` for testing the `exam` document class


## Existing software for Latex processing

* pylatexenc 
	- LaTeX -> Unicode
	- python package

* plasTeX
	- LaTeX -> XML and XHTML
	- python package

* tex4ht
	- LaTeX -> XML, HTML and Braille!
	- java and c libraries
	- provides a `htlatex` cmd to replace latex.

* pandoc 
	- LaTeX -> HTML
	- haskell library

* tralics (INRIA)
	- LaTeX -> XML





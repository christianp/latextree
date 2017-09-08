from setuptools import setup

setup(name='latextree',
    version='0.1',
    description='A document object model and related tools for Latex',
    url='http://github.com/dimbyd/latextree',
    author='D Evans',
    author_email='evansd8@cardiff.ac.uk',
    license='MIT',
    packages=['latextree'],
    install_requires=[
        'jinja2',
        'pylatexenc',
        'bibtexparser',
        'lxml',
    ],
    entry_points = {
        'console_scripts': ['ltree=latextree.ltree:main'],
    },
    zip_safe=False,
)

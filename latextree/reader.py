"""
reader.py 
Utility functions for reading latex files.
    read_latex_document (recursive)
    parse_latex_opt_args
"""
    
import os, re
import logging
log = logging.getLogger(__name__)

    

def read_latex_document(filename):
    """
    Read latex document from file (recursive via input|include commands)
    """
    
    def read_source(filename, level=0):
        
        # careful now!
        if level > 4:
            log.warning('Recursion depth limit exceeded')
            return ''
        
        with open(filename) as f:
            log.info('Reading from %s', filename)
            text = f.read()
            
        
        # find input commands
        pattern = re.compile(r'[^%+]\\(input|include)\{([^\}]*)\}')
        matches = re.finditer(pattern, text)
        
        # return contents if none found (end recursion)
        if not matches:
            return text
        
        # otherwise process input commands (recursive calls)
        else:
            s = ''
            start_index = 0
            for match in matches:
                
                end_index = match.start()
                s += text[start_index:end_index]
                start_index = match.end()
                nested_filename = match.groups()[1]
                
                # append .tex extension if necessary
                if not re.search(r'\.', nested_filename):
                    nested_filename = nested_filename + '.tex'
                
                nested_filename = os.path.join(os.path.dirname(filename), nested_filename)
                log.info('Reading from %s', nested_filename)
                
                # recursive call
                s += read_source(nested_filename, level=level+1)
            s += text[start_index:]
            return s
    
    return read_source(filename)
    
def parse_latex_opt_args(self, text):
    '''
    Parse the contents of e.g. '[arg1, arg2, key1=val1, key2=val2]'
    '''
    if text[0]=='[' and text[-1]==']':
        text = text[1:-1]
    items =  text.split(',')
    args = [item.strip() for item in items if '=' not in item]
    pairs = [item.split('=') for item in items if '=' in item]
    pairs = [(x.strip(), y.strip())for x,y in pairs]
    kwargs = dict(pairs)
    return (args, kwargs)


def parse_latex_length(self, text, paperwidth_mm='210'):
    '''
    Converts Latex lengths (e.g 0.25\textwidth) into percentages
    '''
    scale_factor_mm = {
        'px': 0.26,
        'pt': 0.35,
        'mm': 1.0,
        'cm': 10.0,
        'ex': 1.5,  # approx.
        'em': 3.5,  # approx. (depends on font size)
        'bp': 0.35,
        'dd': 0.38,
        'pc': 4.22,
        'in': 25.4,
    }
    import re
    
    # textwidth and linewidth
    match = re.search(r'(.+)\\[textwidth,linewidth]', text)
    if match:
        pct = 100*float(match.groups()[0])
        return (r'%d\%' % int(pct))
    
    # css lengths
    match = re.search(r'(.+)(em|ex|mm|cm|in|pt|px)', text)
    if match:
        length = match.groups()[0]
        unit = match.groups()[1]
        if unit in scale_factor_mm:
            length_mm = float(length)*scale_factor_mm[unit]
        pct = 100*length_mm/float(paperwidth_mm)
        return (r'%d%%' % int(pct))

    # failed
    return None


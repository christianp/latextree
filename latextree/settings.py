'''
settings for LatexDocument export functions 
'''
import os

# directories
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATE_ROOT = os.path.join(BASE_DIR, 'templates')
STATIC_ROOT = os.path.join(BASE_DIR, 'static')
CSS_ROOT = os.path.join(STATIC_ROOT, 'css')
JS_ROOT = os.path.join(STATIC_ROOT, 'js')
IMAGE_ROOT = os.path.join(STATIC_ROOT, 'img')
PACKAGE_DIR = os.path.abspath(os.path.join(BASE_DIR, os.pardir))
LATEX_ROOT  = os.path.join(PACKAGE_DIR, 'tex')
WEB_ROOT  = os.path.join(PACKAGE_DIR, 'web')

# not used
javascript_paths = (
    "https://cdnjs.cloudflare.com/ajax/libs/jquery/3.2.1/jquery.min.js",
    "static/js/showhide.js",

)

# used in tex2bb but not in tex2web (where they are set in the scripts.html template)
mathjax_source = "https://cdnjs.cloudflare.com/ajax/libs/mathjax/2.7.0/MathJax.js?config=TeX-MML-AM_CHTML"
mathjax_config  = '''
      MathJax.Hub.Config({
        extensions: ["tex2jax.js"],
        jax: ["input/TeX", "output/HTML-CSS"],
        tex2jax: {
          inlineMath: [ ['$','$'], ["\\(","\\)"] ],
          displayMath: [ ['$$','$$'], ["\\[","\\]"] ],
          processEscapes: true
        },
        TeX: {
          Macros: {
            RR: "{\\bf R}",
            pounds: '{\\unicode{xA3}}',
          }
        },
        "HTML-CSS": {
    		availableFonts: ["TeX"],
    		linebreaks: { 
    			automatic: true, 
    			width: "container"
    		}
    	 }
      });
    '''

if __name__ == '__main__':
    print(BASE_DIR)
    print(STATIC_ROOT)
    print(TEMPLATE_ROOT)
    print(LATEX_ROOT)

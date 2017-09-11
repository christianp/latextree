# -*- coding: utf-8 -*-
"""
Created on Thu Apr 27 07:02:26 2017
@author: scmde
"""

from .node import LatexTreeNode
  
def ClassFactory(name, argnames, BaseClass=LatexTreeNode):
    '''
    Factory for producing classes to represent different node types.
    '''
    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            if key not in argnames:
                raise TypeError("Argument %s not valid for %s" 
                    % (key, self.__class__.__name__))
            setattr(self, key, value)
        BaseClass.__init__(self)
    newclass = type(name.capitalize(), (BaseClass,),{"__init__": __init__})
    return newclass

def NodeFactory(name, BaseClass=LatexTreeNode):
    '''
    Factory for producing nodes of different classes
    '''
    NodeClass = ClassFactory(name, {}, BaseClass=BaseClass)
    return NodeClass()

#------------------------------------------------
def main():
    from node import Macro, Environment, Switch
    import taxonomy as tax
    
    abstract_macro_classes = dict([(genus, ClassFactory(genus, {}, BaseClass=Macro)) for genus in tax.macros])
    abstract_environment_classes = dict([(genus, ClassFactory(genus, {}, BaseClass=Environment)) for genus in tax.environments])
    abstract_switch_classes = dict([(genus, ClassFactory(genus, {}, BaseClass=Switch)) for genus in tax.switches])

    macro_classes = dict([(species, ClassFactory(species, {}, BaseClass=abstract_macro_classes[genus])) for genus in tax.macros for species in tax.macros[genus]])
    environment_classes = dict([(species, ClassFactory(species, {}, BaseClass=abstract_environment_classes[genus])) for genus in tax.environments for species in tax.environments[genus]])
    switch_classes = dict([(species, ClassFactory(species, {}, BaseClass=abstract_switch_classes[genus])) for genus in tax.switches for species in tax.switches[genus]])

    classes = macro_classes.copy()
    classes.update(environment_classes)
    classes.update(switch_classes)

    print(classes)
    print(abstract_switch_classes)
    print(switch_classes)
    

if __name__ == '__main__':
    main()

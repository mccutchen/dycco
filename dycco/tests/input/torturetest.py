#!/usr/bin/env python
# coding=utf8

"""
## A Module-Level Docstring

Lorem ipsum dolor sit amet, consectetuer adipiscing elit. Aenean commodo
ligula eget dolor. Aenean massa. Cum sociis natoque penatibus et magnis dis
parturient montes, nascetur ridiculus mus. Donec quam felis, ultricies nec,
pellentesque eu, pretium quis, sem. Nulla consequat massa quis enim. Donec
pede justo, fringilla vel, aliquet nec, vulputate eget, arcu. In enim justo,
rhoncus ut, imperdiet a, venenatis vitae, justo. Nullam dictum felis eu pede
mollis pretium. Integer tincidunt. Cras dapibus.

Vivamus elementum semper nisi. Aenean vulputate eleifend tellus. Aenean leo
ligula, porttitor eu, consequat vitae, eleifend ac, enim. Aliquam lorem ante,
dapibus in, viverra quis, feugiat a, tellus. Phasellus viverra nulla ut metus
varius laoreet. Quisque rutrum. Aenean imperdiet. Etiam ultricies nisi vel
augue. Curabitur ullamcorper ultricies nisi.
"""

# Some imports
import sys, os, re
from functools import wraps
import itertools


### This is an important class
class Foo(object):
    "Single-line docstring"

    def __init__(self):
        """A multiline docstring with no leading or trailing breaks, asdf asdf
        asdf asdf asfd asdf asd fasdf."""
        pass

    #### A singly-decorated method
    @classmethod
    def method1(cls):
        """
        A multiline docstring with leading and trailing breaks.

        What do you think of that?
        """
        pass

    @property
    @wraps(method1)
    @classmethod
    def method2(self):
        # A mutliply-decorated method, with no docstring. How will this look
        # to your parents?

        def foo():
            """Plus, a function-in-a-function with a docstring. WORLDS ARE
            COLLIDING JERRY.
            """
            return 42

        return foo

    @property
    @wraps(method1)
    @classmethod
    def method2(self):
        """A mutliply-decorated method, *with* a docstring. Better? I
        certainly hope so.
        """
        # And also some explanatory comments.
        return 99


### Utility functions

def bar(a, b, c):
    # Return the args we get, for some reason.
    return a, b, c

def really_long_function_definition(function, which, takes, many, args, whose,
                                    definition, wraps, across, multiple,
                                    lines):
    """A long function definition with some very important documentation."""
    return 2 ** 128

@wraps(bar)
def decorated_function_definition(function, which, takes, many, args, whose,
                                  definition, wraps, across, multiple, lines):
    """A *decorated* long function definition With some very important
    documentation.
    """
    print('Hello!')

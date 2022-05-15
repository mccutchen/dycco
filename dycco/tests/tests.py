import unittest
from utils import with_setup

# Adjusted for Python 3 version - v1.0.2 and above, RJL 2022
# For example, `print` now is `print()`. There are also some changes
# due to the AST / compiler changes in Python 3

class ParserTests(unittest.TestCase):

    @with_setup
    def test_skip_shebang(self):
        self.assertEqual(
            self.results,
            {1: {'docs': [], 'code': ["print('Hello, World!')"]}})

    @with_setup
    def test_skip_coding(self):
        self.assertEqual(
            self.results,
            {1: {'docs': [], 'code': ["print('Hello, World!')"]}})

    @with_setup
    def test_skip_emacs_coding(self):
        self.assertEqual(
            self.results,
            {1: {'docs': [], 'code': ["print('Hello, World!')"]}})

    @with_setup
    def test_skip_shebang_and_coding(self):
        self.assertEqual(
            self.results,
            {2: {'docs': [], 'code': ["print('Hello, World!')"]}})

    @with_setup
    def test_bad_shebang_and_coding(self):
        self.assertEqual(
            self.results,
            {3: {'docs': ['Shebang must come first\n!/usr/bin/env/python2.6\n -*- coding: utf8 -*-'],
                 'code': ["print('Hello, World!')"]}})

    @with_setup
    def test_module_docstring(self):
        self.assertEqual(
            self.results,
            {0: {'docs': ['This is a module-level docstring.'], 'code': []}})

    @with_setup
    def test_non_module_docstring(self):
        self.assertEqual(
            self.results,
            {0: {'docs': [],
                 'code': ['import sys',
                          '',
                          '"""',
                          'Is this is a module-level docstring?',
                          '', 'It has multiple lines.',
                          '"""',
                          '',
                          'sys.exit(1)']}})

    @with_setup
    def test_torturetest(self):
        # The output test has been adjusted slightly - the old code
        # occasionally separated decorators (not always).
        self.maxDiff = None
        self.assertEqual(
            self.results,
            {3: {'docs': ['## A Module-Level Docstring\n\nLorem ipsum dolor sit amet, consectetuer adipiscing elit. Aenean commodo\nligula eget dolor. Aenean massa. Cum sociis natoque penatibus et magnis dis\nparturient montes, nascetur ridiculus mus. Donec quam felis, ultricies nec,\npellentesque eu, pretium quis, sem. Nulla consequat massa quis enim. Donec\npede justo, fringilla vel, aliquet nec, vulputate eget, arcu. In enim justo,\nrhoncus ut, imperdiet a, venenatis vitae, justo. Nullam dictum felis eu pede\nmollis pretium. Integer tincidunt. Cras dapibus.\n\nVivamus elementum semper nisi. Aenean vulputate eleifend tellus. Aenean leo\nligula, porttitor eu, consequat vitae, eleifend ac, enim. Aliquam lorem ante,\ndapibus in, viverra quis, feugiat a, tellus. Phasellus viverra nulla ut metus\nvarius laoreet. Quisque rutrum. Aenean imperdiet. Etiam ultricies nisi vel\naugue. Curabitur ullamcorper ultricies nisi.'],
                 'code': []},
             22: {'docs': ['Some imports'],
                  'code': ['import sys, os, re',
                           'from functools import wraps',
                           'import itertools',
                           '',
                           '']},
             28: {'docs': [
                 '## This is an important class',
                 'Single-line docstring'],
                 'code': ['class Foo(object):', '']},
             37: {'docs': ['### A singly-decorated method'],
                  'code': []},
             38: {'docs': ['A multiline docstring with leading and trailing breaks.\n\nWhat do you think of that?'],
                  'code': ['    @classmethod', '    def method1(cls):', '        pass', '']},
             73: {'docs': ['## Utility functions'],
                  'code': ['']},
             74: {'docs': [None],
                  'code': ['def bar(a, b, c):']},
             76: {'docs': ['Return the args we get, for some reason.'],
                  'code': ['    return a, b, c', '']},
             46: {'docs': [None],
                  'code': ['    @property',
                           '    @wraps(method1)',
                           '    @classmethod',
                           '    def method2(self):']},
             53: {'docs': ['Plus, a function-in-a-function with a docstring. WORLDS ARE\nCOLLIDING JERRY.'],
                  'code': ['        def foo():',
                           '            return 42',
                           '',
                           '        return foo', '']},
             85: {'docs': ['A *decorated* long function definition With some very important\ndocumentation.'],
                  'code': [
                        '@wraps(bar)',
                        'def decorated_function_definition(function, which, takes, many, args, whose,',
                        '                                  definition, wraps, across, multiple, lines):',
                        "    print('Hello!')"]},
             78: {'docs': ['A long function definition with some very important documentation.'],
                  'code': ['def really_long_function_definition(function, which, takes, many, args, whose,',
                           '                                    definition, wraps, across, multiple,',
                           '                                    lines):',
                           '    return 2 ** 128',
                           '']},
             52: {'docs': ['A mutliply-decorated method, with no docstring. How will this look\n to your parents?'],
                  'code': ['']},
             64: {'docs': ['A mutliply-decorated method, *with* a docstring. Better? I\ncertainly hope so.'],
                  'code': ['    @property',
                           '    @wraps(method1)',
                           '    @classmethod',
                           '    def method2(self):']},
             69: {'docs': ['And also some explanatory comments.'], 'code': ['        return 99', '', '']},
             31: {'docs': ['A multiline docstring with no leading or trailing breaks, asdf asdf\nasdf asdf asfd asdf asd fasdf.'],
                  'code': ['    def __init__(self):',
                           '        pass',
                           '']}})


if __name__ == '__main__':
    unittest.main()

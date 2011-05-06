#!/usr/bin/env python

import ast
import os
import re
import sys
from collections import defaultdict

import markdown
import pystache
from pygments import highlight
from pygments.lexers import get_lexer_by_name
from pygments.formatters import HtmlFormatter


DEFAULT_OUTPUT_DIR = 'docs'
COMMENT_PATTERN = '^\s*#'


def document(path, output_dir=DEFAULT_OUTPUT_DIR):
    """Generates documentation for the Python file at the given path."""
    title = os.path.basename(path)
    sections = parse(path)
    html = render(title, sections)

    # Figure out where to store the generated documentation
    output_path = os.path.join(output_dir, '%s.html' % title)

    # Make sure the directory exists
    if not os.path.exists(output_dir) or not os.path.isdir(output_dir):
        os.path.makedirs(output_dir)

    # Create/overwrite the documentation at the given path
    with open(output_path, 'w') as f:
        f.write(html)

def parse(path):
    """Parse the source code at the given path, in two passes. The first pass
    walks the Abstract Syntax Tree of the code, gathering up any
    docstrings. The second pass processes the code line by line, grouping the
    code into sections based on docstrings and comments.

    The data structure returned is a special `dict` whose keys are the line
    numbers where sections start, which map to `dict`s containing the docs and
    code associated with those sections. The docs and code are stored as
    lists, which will be joined in post processing.

    It will look a little like this:

        { 1: { 'docs': ['...', '...'],
               'code': ['...', '...'] },
          9: { 'docs': ['...', '...'],
               'code': ['...', '...'] } }

    The docs for each section can come from docstrings (the first pass) or
    from comments (the second pass). The line numbers start at zero, for
    simplicity's sake.

    Any module-level documentation is stored in the section under the `None`
    key, and will come before any other sections in the output.
    """

    def section():
        """A callable that will generate the datastructure used to store each
        section. Used as the argument to `defaultdict()` below.
        """
        return { 'docs': [],
                 'code': [], }

    # Read the whole source file into memory.
    with open(path) as f:
        src = f.read()

    # The basic `sections` datastructure we'll use to keep track of code and
    # documentation.
    sections = defaultdict(section)

    # **First Pass:** Find any docstrings in the source code by walking its
    # AST.
    visitor = DocStringVisitor()
    visitor.visit(ast.parse(src))

    # Add all of the docstrings we've found to the appropriate places in the
    # `sections` datastructure. The corresponding code will be added later.
    for doc, start_line, end_line in visitor.docstrings:
        sections[start_line]['docs'].append(doc)

    # Build a set of the line numbers where we found docstrings, so we know to
    # skip them in the second pass. **FIXME:** If we have a module-level
    # docstring, this will ignore any code that came before it, because its
    # `target_line` will be None after walking the AST.
    skip_lines = set()
    for doc, target_line, end_line in visitor.docstrings:
        start = target_line if target_line else 0
        skip_lines.update(xrange(start, end_line))

    # **Second Pass**: Now iterate through each line of source code to gather
    # up comments and code listings and add them to the sections structure.
    current_comment = None
    current_section = None
    for i, line in enumerate(src.splitlines()):
        # Skip any lines that were in docstrings
        if i in skip_lines:
            continue

        # Are we looking at a comment? If so, and we do not have a current
        # comment block, we're starting a new section. If we do have a current
        # comment block, we just add this comment to it (e.g. multi-line
        # comments).
        if re.match(COMMENT_PATTERN, line):
            comment = re.sub(COMMENT_PATTERN, '', line)
            if current_comment is None:
                current_comment = comment
                current_section = None
            else:
                current_comment += '\n' + comment

        # Otherwise, we're looking at a line of code and we need to add it to
        # the appropriate section, along with any preceding comments.
        else:
            # If we have a current comment, that means we're starting a new
            # section with this line of code.
            if current_comment:
                sections[i]['docs'].append(current_comment)
                current_comment = None
                current_section = i

            # Any module-level documentation will be in section None, so any
            # code should come after that section. This handles the case where
            # there are no other doc sections between the module-level docs
            # and the start of the code.
            elif current_section is None:
                current_section = i

            # Figure out where to add this line of code. If the current line
            # is already in the sections dict, this line of code is (probably)
            # associated with a docstring, which takes precedence over the
            # current section we're in.
            if i in sections:
                current_section = i
            sections[current_section]['code'].append(line)

    return sections


def render(title, sections):
    """Renders the given sections, which should be the result of calling
    `parse` on a source code file, into HTML.
    """
    # Transform the `sections` `dict` we were given into a format suitable for
    # our Mustache template. Along the way, preprocess each block of
    # documentation and code, via Markdown and Pygments.
    sections = [{
        'num': key,
        'docs_html': preprocess_docs(value['docs']),
        'code_html': preprocess_code(value['code'])
    } for key, value in sorted(sections.items())]

    context = {
        'title': title,
        'sections': sections
        }
    with open('template.html') as f:
        return pystache.render(f.read(), context)

def preprocess_docs(docs):
    """Preprocess the given `docs`, which should be a `list` of strings, by
    joining them together and running them through Markdown.
    """
    assert isinstance(docs, list)
    return markdown.markdown('\n\n'.join(docs))

def preprocess_code(code):
    """Preprocess the given code, which should be a `list` of strings, by
    joining them together and running them through the Pygments syntax
    highlighter.
    """
    assert isinstance(code, list)
    lexer = get_lexer_by_name("python")
    formatter = HtmlFormatter()
    result = highlight('\n'.join(code), lexer, formatter)
    return result


class DocStringVisitor(ast.NodeVisitor):
    """A `NodeVisitor` subclass that walks an Abstract Syntax Tree and gathers
    up and notes the positions of any docstrings it finds.
    """

    def __init__(self):
        # Docstrings will be tracked as a list of 3-tuples that contain the
        # docstring, its starting line and its ending line.
        self.docstrings = []
        self.current_node = None
        self.current_doc = None

    def _visit_docstring_node(self, node):
        """A method to be called when visiting any node that might have an
        associated docstring (ie, module, function and class nodes). This uses
        `ast.get_docstring` to grab and sanitize the docstring, and notes
        which node we're currently looking at.
        """
        self.current_node = node
        self.current_doc = ast.get_docstring(node)
        super(DocStringVisitor, self).generic_visit(node)

    # Use the `_visit_docstring_node` method when visiting all of these nodes.
    visit_Module = _visit_docstring_node
    visit_FunctionDef = _visit_docstring_node
    visit_ClassDef = _visit_docstring_node

    def visit_Expr(self, node):
        """We need to actually visit the nodes representing the docstrings to
        record their positions. Docstring nodes show up as `Expr` nodes whose
        values are `Str` nodes.
        """
        if isinstance(node.value, ast.Str) and self.current_node:
            # Manually calculate the starting line of the docstring based on
            # the number of lines in it and its last line. This lets us handle
            # module-level docstrings and others the same way (since
            # `ast.Module` nodes don't record a line number). Make sure to
            # adjust line numbers to start at 0.
            end_line = node.lineno - 1
            lines = len(node.value.s.splitlines())
            start_line = end_line - (lines if lines > 1 else 0)

            # Add the sanitized version of the current docstring and its
            # starting and finishing line numbers to our list of docstrings.
            self.docstrings.append(
                (self.current_doc, start_line, node.lineno))

        # Reset the accounting variables even if we didn't find a docstring,
        # so that we don't accidentally add "unattached" docstrings to
        # whatever class/def/module happened to come before them.
        if self.current_node:
            self.current_node = None
            self.current_doc = None

        super(DocStringVisitor, self).generic_visit(node)


def main(paths, output_dir):
    """Main method to be used when run from the command line."""
    for path in paths:
        document(path, output_dir)


if __name__ == '__main__':
    if len(sys.argv) > 1:
        main(sys.argv[1:], DEFAULT_OUTPUT_DIR)

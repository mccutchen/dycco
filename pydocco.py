import ast
import os
import re
import sys
from collections import defaultdict

import markdown
import pystache


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
    """Parse the source code at the given path."""

    with open(path) as f:
        src = f.read()

    # The basic datastructure we'll use to keep track of code and
    # documentation is a special dict mapping line numbers to dicts containing
    # lists of documentation and source code lines. See `section` for more
    # info.
    sections = defaultdict(section)

    # Find any docstrings in the source code by walking its AST.
    visitor = DocStringVisitor()
    visitor.visit(ast.parse(src))

    # Add all of the docstrings we've found to the appropriate places in the
    # sections structure. The corresponding code will be added later.
    for doc, parent_line, end_line in visitor.docstrings:
        key = parent_line - 1 if parent_line else None
        sections[key]['docs'].append(doc)

    # Build a set of the line numbers where we found docstrings, so we know to
    # skip them in the step that follows.
    skip_lines = set()
    for doc, target_line, end_line in visitor.docstrings:
        start = target_line if target_line else 0
        skip_lines.update(xrange(start, end_line))

    # Now iterate through each line of source code to gather up comments and
    # code listings and add them to the sections structure.
    current_comment = None
    current_section = None
    for i, line in enumerate(src.splitlines()):
        # Skip any lines that were in docstrings
        if i in skip_lines:
            continue

        if re.match(COMMENT_PATTERN, line):
            comment = re.sub(COMMENT_PATTERN, '', line)
            if current_comment:
                current_comment += '\n' + comment
            else:
                current_comment = comment
            current_section = None

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
                current_section = 0

            # Figure out where to add this line of code. If the current line
            # is already in the sections dict, this line of code is (probably)
            # associated with a docstring, which takes precedence over the
            # current section we're in.
            in_section = i if i in sections else current_section
            sections[in_section]['code'].append(line)

    return sections


def render(title, sections):
    """Renders the given sections, which should be the result of calling
    `parse` on a source code file, into HTML.
    """
    # Need to transform the sections dict we were given into a format suitable
    # for our Mustache template. Along the way, we need to send each
    # documentation block through Markdown.
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
    return markdown.markdown('\n\n'.join(docs))

def preprocess_code(code):
    return '<pre>%s</pre>' % '\n'.join(code)


class DocStringVisitor(ast.NodeVisitor):

    def __init__(self):
        self.docstrings = []
        self.current_node = None
        self.current_doc = None

    def _visit_docstring_node(self, node):
        self.current_node = node
        self.current_doc = ast.get_docstring(node)
        super(DocStringVisitor, self).generic_visit(node)

    visit_Module = _visit_docstring_node
    visit_FunctionDef = _visit_docstring_node
    visit_ClassDef = _visit_docstring_node

    def visit_Expr(self, node):
        if isinstance(node.value, ast.Str) and self.current_node:
            parent_line = getattr(self.current_node, 'lineno', None)
            self.docstrings.append(
                (self.current_doc, parent_line, node.lineno))
            self.current_node = None
            self.current_doc = None
        super(DocStringVisitor, self).generic_visit(node)


def section():
    """The sections dict maps line numbers where sections start to a dict
    containing the docs and the code for that section. It will look a little
    like this:

        { 1: { 'docs': ['...', '...'],
               'code': ['...', '...'] },
          9: { 'docs': ['...', '...'],
               'code': ['...', '...'] } }

     Which means the docs and the code for each section are tracked as
     individual lines.
     """
    return { 'docs': [],
             'code': [], }


def main(paths, output_dir):
    """Main method to be used when run from the command line."""
    for path in paths:
        document(path, output_dir)


if __name__ == '__main__':
    if len(sys.argv) > 1:
        main(sys.argv[1:], DEFAULT_OUTPUT_DIR)

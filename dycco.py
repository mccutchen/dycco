#!/usr/bin/env python

"""
**Dycco** is another Python port of [Docco][docco], the quick-and-dirty,
hundred-line-long, literate-programming-style documentation generator.

Dycco reads Python source files and produces annotated source documentation in
HTML format. Comments and docstrings are formatted with [Markdown][markdown]
and presented as annotations alongside the source code, which is
syntax-highlighted by [Pygments][pygments]. This page is the result of running
Dycco against its [own source file][dycco].

Currently, there is no setup for Dycco, so you'll have to fetch its [source
code][dycco] and the prerequisites yourself. Dycco can then be run like so

    dycco.py *.py

to generate documentation for each Python file in the current directory. The
documentation is output into a `docs/` directory in the current directory.

Dycco differs from Nick Fitzgerald's [Pycco][pycco], the first Python port of
[Docco][docco] in that it only knows how to generate documenation on Python
source code and it uses that specialization to more accurately parse
documentation. It does so using a two-pass parsing stage, first walking the
*Abstract Syntax Tree* of the code to gather up docstrings, then examining the
code line-by-line to extract comments.

[Docco][docco]'s gorgeous HTML and CSS are taken verbatim. Like
[Pycco][pycco], Dycco uses [Mustache][mustache] templates rendered by
[Pystache][pystache]. The first version of Dycco's templates and CSS were
taken straight from [Pycco][pycco], then updated to match the latest changes
to [Docco][docco]'s output.

[docco]: http://jashkenas.github.com/docco/
[markdown]: http://daringfireball.net/projects/markdown/
[pygments]: http://pygments.org/
[dycco]: https://github.com/mccutchen/dycco
[pycco]: http://fitzgen.github.com/pycco/
[mustache]: http://mustache.github.com/
[pystache]: https://github.com/defunkt/pystache
"""

### Prerequisites
# Dycco requires the `markdown`, `pystache` and `pygments` modules to be
# installed.
import markdown
import pystache
from pygments import highlight
from pygments.lexers import get_lexer_by_name
from pygments.formatters import HtmlFormatter

import ast
import os
import re
import sys
from collections import defaultdict


DEFAULT_OUTPUT_DIR = 'docs'
COMMENT_PATTERN = '^\s*#'


### Main Documentation Generation Function
def document(paths, output_dir=DEFAULT_OUTPUT_DIR):
    """Generates documentation for the Python files at the given `paths` by
    parsing each file into pairs of documentation and source code and
    rendering those pairs into an HTML file. The `paths` param can be a `list`
    of paths or a single `str` path.
    """

    # If we get a single path, stick it in a list so we can still pretend
    # we're operating on multiple paths.
    if isinstance(paths, basestring):
        paths = [paths]

    # Make sure the directory exists
    if not os.path.exists(output_dir) or not os.path.isdir(output_dir):
        os.path.makedirs(output_dir)

    # Build a list of (path, filename, output_path) tuples, which will be used
    # to build the links to other source code docs in the templates
    filenames = map(os.path.basename, paths)
    output_paths = [make_output_path(f, output_dir) for f in filenames]
    sources = zip(paths, filenames, output_paths)

    # Parse each input file into sections, render the sections as HTML into a
    # string, and create or overwrite the documentation at the appropriate
    # output path.
    for path, filename, output_path in sources:
        with open(path) as f:
            src = f.read()
            sections = parse(src)
            html = render(filename, sections, sources)
            with open(output_path, 'w') as f:
                f.write(html)

### Parsing the Source
def parse(src):
    """Parse the source code at the given path, in two passes. The first pass
    walks the *Abstract Syntax Tree* of the code, gathering up any
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
    """

    def section():
        """A callable that will generate the datastructure used to store each
        section. Used as the argument to `defaultdict` below.
        """
        return { 'docs': [],
                 'code': [], }

    # The basic `sections` datastructure we'll use to keep track of code and
    # documentation.
    sections = defaultdict(section)

    # First pass: Parse all of the docstrings and get a list of lines we
    # should skip when parsing the rest of the code. Modifies `sections` in
    # place.
    skip_lines = parse_docstrings(src, sections)

    # Second pass: Parse the rest of the code, adding code and comments to the
    # appropriate sections. Modifies `sections` in place.
    parse_code(src, sections, skip_lines)

    return sections

#### First Pass
def parse_docstrings(src, sections):
    """Parse the given `src` to find any docstrings, add them to the
    appropriate place in `sections`, and return a `set` of line numbers where
    the docstrings are. **Note:** Modifies `sections` in place.
    """
    # Find any docstrings in the source code by walking its AST.
    visitor = DocStringVisitor()
    visitor.visit(ast.parse(src))

    # Add all of the docstrings we've found to the appropriate places in the
    # `sections` datastructure. The corresponding code will be added later.
    for doc, target_line, _, _ in visitor.docstrings:
        sections[target_line]['docs'].append(doc.strip())

    # Build a set of the line numbers where we found docstrings, so we know to
    # skip them in the second pass.
    skip_lines = set()
    for doc, _, start_line, end_line in visitor.docstrings:
        skip_lines.update(xrange(start_line, end_line + 1))

    return skip_lines

#### Second Pass
def parse_code(src, sections, skip_lines=set()):
    """Parse the given `src` line by line to gather source code and comments
    into the appropriate places in `sections`. Any line numbers in
    `skip_lines` are skipped. **Note:** Modifies `sections` in place.
    """
    # Iterate through each line of source code to gather up comments and code
    # listings and add them to the sections structure.
    current_comment = None
    current_section = None
    for i, line in enumerate(src.splitlines()):
        # Skip any lines that were in docstrings
        if i in skip_lines or should_filter(line, i):
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
                current_comment = current_comment.strip()
                docs = sections[i]['docs']
                # If we've already got docs for this section, that (hopefully)
                # means we're looking at a function/class def that has a
                # docstring, but that the current comments precede the def. In
                # this case, we prepend the comments, so they come before the
                # docstring.
                if docs:
                    docs.insert(0, current_comment)
                else:
                    docs.append(current_comment)
                # The next comment we encounter will start a new section, but
                # any lines of code that follow this one belong to this
                # section.
                current_comment = None
                current_section = i

            # We don't have a current section, so we should be at our first
            # bit of code (aside from any module-level docstrings), and should
            # start a new section. But we want to skip any empty leading blank
            # lines.
            elif current_section is None and line:
                current_section = i

            # If the current line is already in the `sections` datastructure,
            # it is (probably) associated with a docstring from the first
            # pass, and we should  it to that section instead of whatever
            # current section we have.
            if i in sections:
                current_section = i

            # Finally, append the current line of code to the current
            # section's code block. Skip any empty leading lines of code,
            # which will not have a current section.
            if current_section:
                sections[current_section]['code'].append(line)

### Rendering
def render(title, sections, sources):
    """Renders the given sections, which should be the result of calling
    `parse` on a source code file, into HTML. **FIXME:** The `sources`
    argument is ignored at the moment, but will eventually be used to generate
    linked documentation.
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

#### Preprocessors
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


### Support Functions
def should_filter(line, num):
    """Test the given line to see if it should be included. Excludes shebang
    lines, for now.
    """
    if num == 0 and line.startswith('#!'):
        return True
    return False

def make_output_path(filename, output_dir):
    """Creates an appropriate output path for the given source file and output
    directory. The output file name will be the name of the source file
    without its extension.
    """
    name, ext = os.path.splitext(filename)
    return os.path.join(output_dir, '%s.html' % name)


#### AST Parsing
class DocStringVisitor(ast.NodeVisitor):
    """A `NodeVisitor` subclass that walks an Abstract Syntax Tree and gathers
    up and notes the positions of any docstrings it finds.
    """

    def __init__(self):
        # Docstrings will be tracked as a list of 4-tuples that contain the
        # docstring, the line of the code to which it applies, its starting
        # line and its ending line.
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

            # Adjust for 0-based line counting
            end_line = node.lineno - 1

            # Module docstrings have to have their starting lines and targets
            # calculated manually, since `ast.Module` objects have no line
            # numbers.
            if isinstance(self.current_node, ast.Module):
                line_count = len(node.value.s.splitlines())
                start_line = end_line - line_count
                target_line = start_line

            # For all other nodes, just assume that the target is on the
            # previous line. **TODO:** This probably breaks on, e.g.,
            # multiline function defs.
            else:
                start_line = self.current_node.lineno
                target_line = start_line - 1

            # Add the sanitized version of the current docstring, its target
            # and its starting and finishing line numbers to our list of
            # docstrings.
            self.docstrings.append(
                (self.current_doc, target_line, start_line, end_line))

        # Reset the accounting variables even if we didn't find a docstring,
        # so that we don't accidentally add "unattached" docstrings to
        # whatever class/def/module happened to come before them.
        if self.current_node:
            self.current_node = None
            self.current_doc = None

        super(DocStringVisitor, self).generic_visit(node)


### Command Line Entry Point
# When executed from the command line, the paths to one or more Python source
# files should be provided. Documentation will be generated and written into a
# `docs/` directory inside the current directory.
if __name__ == '__main__':
    # For now, only try to generate documentation if we did get some command
    # line arguments. This allows the file to still be executed in ipython or
    # Emacs's python-mode without failing.
    if len(sys.argv) > 1:
        document(sys.argv[1:], DEFAULT_OUTPUT_DIR)

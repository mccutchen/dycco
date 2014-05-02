import os
import re
from functools import wraps

import dycco


### Test decorator methods

def with_setup_src(path):
    """A decorator-generator, used to wrap parser test methods so that each
    method has a corresponding source code file read, parsed, and made
    available as instance variables when the test method is called.

    The source code will be available as a string at `self.src`, and the
    results of running the source code through `dycco.parse` will be available
    at `self.results`.

    This version of the decorator requires that an explicit path to the
    corresponding source code be given. See `with_setup`, below, for a
    shortcut that uses the test method's name to find the corresponding source
    code.
    """
    def decorator(method):
        @wraps(method)
        def decorated(self, *args, **kwargs):
            self.src = open(path).read()
            self.results = dict(dycco.parse(self.src))
            return method(self, *args, **kwargs)
        return decorated
    return decorator


def with_setup(method):
    """A shortcut version of `with_setup_src` that determines the path to the
    corresponding source code file based on the test method's name (with any
    leading `"test_"` removed).

    This is probably the decorator to use, unless you're reusing the same
    source code files for multiple tests.
    """
    filename = '%s.py' % re.sub('^test_', '', method.__name__)
    path = os.path.join(os.path.dirname(__file__), 'input', filename)
    return with_setup_src(path)(method)

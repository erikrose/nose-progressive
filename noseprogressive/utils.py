from os.path import abspath, realpath

from nose.tools import nottest
import nose.util


@nottest
def test_address(test):
    """Return the result of nose's test_address(), None if it's stumped."""
    try:
        return nose.util.test_address(test)
    except TypeError:  # Explodes if the function passed to @with_setup applied
                       # to a test generator has an error.
        pass


def nose_selector(test):
    """Return the string you can pass to nose to run `test`.

    Return "Unknown test" if it can't construct a decent path.

    """
    address = test_address(test)
    if address:
        file, module, rest = address

        if module:
            if rest:
                return '%s:%s' % (module, rest)
            else:
                return module
    return 'Unknown test'


def human_path(path, cwd):
    """Return the most human-readable representation of the given path.

    If an absolute path is given that's within the current directory, convert
    it to a relative path to shorten it. Otherwise, return the absolute path.

    """
    path = abspath(path)
    if path.startswith(cwd):
        path = path[len(cwd) + 1:]  # Make path relative. Remove leading slash.
    return path


class OneTrackMind(object):
    """An accurate simulation of my brain

    I can know one thing at a time, at some level of confidence. You can tell
    me other things, but if I'm not as confident of them, I'll forget them. If
    I'm more confident of them, they'll replace what I knew before.

    """
    def __init__(self):
        self.confidence = 0
        self.best = None

    def know(self, what, confidence):
        """Know something with the given confidence, and return self for chaining.

        If confidence is higher than that of what we already know, replace
        what we already know with what you're telling us.

        """
        if confidence > self.confidence:
            self.best = what
            self.confidence = confidence
        return self


@nottest
def frame_of_test(test_address_result, exception_type, exception_value,
                  extracted_tb):
    """Return the frame of a traceback that points to the test that failed.

    If exception_type is SyntaxError, may return None for the frame's function
    name and exception text.

    Sometimes this is hard. It takes its best guess.

    Args:
        test_address_result: The result of a call to test_address(), indicating
            which test failed
        exception_type, exception_value: Needed in case this is a SyntaxError
            and therefore doesn't have the whole story in extracted_tb
        extracted_tb: The traceback, after having been passed through
            extract_tb()

    """
    # SyntaxErrors don't make it into the extracted traceback. Catch them
    # separately:
    if (exception_type is SyntaxError and
        exception_value.filename != '<string>'):  # Tolerate eval() and input()
        return exception_value.filename, exception_value.lineno, None, None

    test_file, _, test_call = test_address_result

    # OneTrackMind helps us favor the latest frame, even if there's more than
    # one match of equal confidence.
    knower = OneTrackMind().know(extracted_tb[-1], 1)

    if isinstance(test_file, basestring):
        test_file_path = realpath(test_file)

        # TODO: Perfect. Right now, I'm just comparing by function name within
        # a module. This should break only if you have two identically-named
        # functions from a single module in the call stack when your test
        # fails. However, it bothers me. I'd rather be finding the actual
        # callables and comparing them directly.
        for frame in reversed(extracted_tb):
            file, line, function, text = frame
            if file is not None and test_file_path == realpath(file):
                knower.know(frame, 2)
                if (hasattr(test_call, 'rsplit') and  # test_call can be None
                    function == test_call.rsplit('.')[-1]):
                    knower.know(frame, 3)
                    break
    return knower.best

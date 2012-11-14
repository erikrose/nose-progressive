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
    """Return the string you can pass to nose to run `test`, including argument
    values if the test was made by a test generator.

    Return "Unknown test" if it can't construct a decent path.

    """
    address = test_address(test)
    if address:
        file, module, rest = address

        if module:
            if rest:
                try:
                    return '%s:%s%s' % (module, rest, test.test.arg or '')
                except AttributeError:
                    return '%s:%s' % (module, rest)
            else:
                return module
    return 'Unknown test'


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


@nottest  # still needed?
def index_of_test_frame(extracted_tb, exception_type, exception_value, test):
    """Return the index of the frame that points to the failed test or None.

    Sometimes this is hard. It takes its best guess. If exception_type is
    SyntaxError or it has no idea, it returns None.

    Args:
        address: The result of a call to test_address(), indicating which test
            failed
        exception_type, exception_value: Needed in case this is a SyntaxError
            and therefore doesn't have the whole story in extracted_tb
        extracted_tb: The traceback, after having been passed through
            extract_tb()

    """
    try:
        address = test_address(test)
    except TypeError:
        # Explodes if the function passed to @with_setup
        # applied to a test generator has an error.
        address = None

    # address is None if the test callable couldn't be found. No sense trying
    # to find the test frame if there's no such thing:
    if address is None:
        return None

    test_file, _, test_call = address

    # OneTrackMind helps us favor the latest frame, even if there's more than
    # one match of equal confidence.
    knower = OneTrackMind()

    if test_file is not None:
        test_file_path = realpath(test_file)

        # TODO: Perfect. Right now, I'm just comparing by function name within
        # a module. This should break only if you have two identically-named
        # functions from a single module in the call stack when your test
        # fails. However, it bothers me. I'd rather be finding the actual
        # callables and comparing them directly, but that might not work with
        # test generators.
        for i, frame in enumerate(extracted_tb):
            file, line, function, text = frame
            if file is not None and test_file_path == realpath(file):
                # TODO: Now that we're eliding until the test frame, is it
                # desirable to have this confidence-2 guess when just the file
                # path is matched?
                knower.know(i, 2)
                if (hasattr(test_call, 'rsplit') and  # test_call can be None
                    function == test_call.rsplit('.')[-1]):
                    knower.know(i, 3)
                    break
    return knower.best


def human_path(path, cwd):
    """Return the most human-readable representation of the given path.

    If an absolute path is given that's within the current directory, convert
    it to a relative path to shorten it. Otherwise, return the absolute path.

    """
    # TODO: Canonicalize the path to remove /kitsune/../kitsune nonsense.
    path = abspath(path)
    if cwd and path.startswith(cwd):
        path = path[len(cwd) + 1:]  # Make path relative. Remove leading slash.
    return path

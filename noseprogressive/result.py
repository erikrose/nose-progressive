from collections import defaultdict
from curses import tigetstr, setupterm, tparm
from os import isatty
from traceback import format_list, extract_tb, format_exception_only

from nose.result import TextTestResult
from nose.util import src, isclass

from noseprogressive.bar import ProgressBar
from noseprogressive.utils import (nose_selector, human_path, frame_of_test,
                                   test_address)


class ProgressiveResult(TextTestResult):
    """Test result which updates a progress bar instead of printing dots

    Nose's ResultProxy will wrap it, and other plugins can still print
    stuff---but without smashing into my progress bar, care of my Plugin's
    stderr/out wrapping.

    """
    def __init__(self, cwd, totalTests, stream, showAdvisories, config=None):
        super(ProgressiveResult, self).__init__(stream, None, 0, config=config)
        self._cwd = cwd
        self._codes = self._terminalCodes(stream)

        # 1 in case test counting failed and returned 0
        self.bar = ProgressBar(stream, totalTests or 1, self._codes)

        # Declare errorclass-savviness so the errorclass plugin doesn't
        # monkeypatch half my methods away:
        self.errorClasses = {}

        self._showAdvisories = showAdvisories

    def _terminalCodes(self, stream):
        """Return a hash of termcap codes and values for the terminal `stream`.

        If `stream` is not a terminal, return empty values so you can pipe this
        to a file without making a mess of it. (I'm not sure why you would want
        to do that; this is mostly in place to make the Progressive's test
        suite run.)

        """
        capabilities = ['bold', 'sc', 'rc', 'sgr0', 'el']
        if hasattr(stream, 'fileno') and isatty(stream.fileno()):
            # Explicit args make setupterm() work even when -s is passed:
            setupterm(None, stream.fileno())  # so things like tigetstr() work
            codes = dict((x, tigetstr(x)) for x in capabilities)
            cup = tigetstr('cup')
            codes['cup'] = lambda line, column: tparm(cup, line, column)
        else:
            # If you're crazy enough to pipe this to a file or something, don't
            # output terminal codes:
            codes = defaultdict(lambda: '', cup=lambda line, column: '')
        return codes

    def startTest(self, test):
        """Update the progress bar."""
        super(ProgressiveResult, self).startTest(test)
        self.bar.update(test, self.testsRun)

    def _printError(self, kind, err, test, isFailure=True):
        """Output a human-readable error report to the stream.

        kind -- the (string) type of incident the precipitated this call
        err -- exc_info()-style traceback triple
        test -- the test that precipitated this call

        """
        if isFailure or self._showAdvisories:
            # Don't bind third item to a local var; that can create circular
            # refs which are expensive to collect. See the sys.exc_info() docs.
            exception_type, exception_value = err[:2]
            extracted_tb = extract_tb(err[2])
            formatted_traceback = ''.join(format_list(extracted_tb))
            # TODO: Canonicalize the path to remove /kitsune/../kitsune
            # nonsense. Don't relativize, though, as that hurts the ability to
            # paste into running editors.
            writeln = self.stream.writeln
            write = self.stream.write
            with self.bar.dodging():
                writeln('\n' + (self._codes['bold'] if isFailure else '') +
                        '%s: %s' % (kind, nose_selector(test)))

                if isFailure:  # Then show traceback
                    # File name and line num in a format vi can take:
                    try:
                        address = test_address(test)
                    except TypeError:
                        # Explodes if the function passed to @with_setup
                        # applied to a test generator has an error.
                        address = None
                    if address:  # None if no such callable found. No sense
                                 # trying to find the test frame if there's no
                                 # such thing.
                        file, line = frame_of_test(address, extracted_tb)[:2]
                        writeln(' ' * len(kind) + '  $EDITOR +%s %s' %
                                (line, human_path(src(file), self._cwd)))

                    write(self._codes['sgr0'])  # end bold

                    # Traceback:
                    # TODO: Think about using self._exc_info_to_string, which
                    # does some pretty whizzy skipping of unittest frames.
                    write(formatted_traceback)

                    # Exception:
                    write(''.join(format_exception_only(exception_type,
                                                        exception_value)))
                else:
                    write(self._codes['sgr0'])  # end bold

    def addError(self, test, err):
        exc, val, tb = err
        # We don't read this, but some other plugin might conceivably expect it
        # to be there:
        excInfo = self._exc_info_to_string(err, test)

        # We duplicate the errorclass handling from super rather than calling
        # it and monkeying around with flags to keep it from printing anything.
        isErrorClass = False
        for cls, (storage, label, isFailure) in self.errorClasses.iteritems():
            if isclass(exc) and issubclass(exc, cls):
                if isFailure:
                    test.passed = False
                storage.append((test, excInfo))
                isErrorClass = True
        if not isErrorClass:
            self.errors.append((test, excInfo))
            test.passed = False

        with self.bar.dodging():
            self._printError(label if isErrorClass else 'ERROR',
                             err,
                             test,
                             isFailure=not isErrorClass or isFailure)

    def addFailure(self, test, err):
        super(ProgressiveResult, self).addFailure(test, err)
        self._printError('FAIL', err, test)

    def printSummary(self, start, stop):
        """As a final summary, print number of tests, broken down by result."""
        def renderResultType(type, number, isFailure):
            """Return a rendering like '2 failures'.

            Args:
                type: A singular label, like "failure"
                number: The number of tests with a result of that type
                isFailure: Whether that type counts as a failure.

            """
            # I'd rather hope for the best with plurals than totally punt on
            # being Englishlike:
            ret = '%s %s%s' % (number, type, 's' if number != 1 else '')
            if isFailure and number:
                ret = self._codes['bold'] + ret + self._codes['sgr0']
            return ret

        # Summarize the special cases:
        counts = [('test', self.testsRun, False),
                  ('failure', len(self.failures), True),
                  ('error', len(self.errors), True)]
        # Support custom errorclasses as well as normal failures and errors.
        # Lowercase any all-caps labels, but leave the rest alone in case there
        # are hard-to-read camelCaseWordBreaks.
        counts.extend([(label.lower() if label.isupper() else label,
                        len(storage),
                        isFailure)
                        for (storage, label, isFailure) in
                            self.errorClasses.itervalues() if len(storage)])
        summary = (', '.join(renderResultType(*a) for a in counts) +
                   ' in %.1fs' % (stop - start))

        # Erase progress bar. Bash doesn't clear the whole line when printing
        # the prompt, leaving a piece of the bar. Also, the prompt may not be
        # at the bottom of the terminal.
        self.bar.erase()
        self.stream.writeln()
        if self.wasSuccessful():
            self.stream.write('OK!  ')
        self.stream.writeln(summary)

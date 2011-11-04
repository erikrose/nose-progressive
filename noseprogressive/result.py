from nose.result import TextTestResult
from nose.util import isclass

from noseprogressive.bar import ProgressBar
from noseprogressive.terminal import Terminal
from noseprogressive.tracebacks import format_traceback, extract_relevant_tb
from noseprogressive.utils import nose_selector, index_of_test_frame


class ProgressiveResult(TextTestResult):
    """Test result which updates a progress bar instead of printing dots

    Nose's ResultProxy will wrap it, and other plugins can still print
    stuff---but without smashing into my progress bar, care of my Plugin's
    stderr/out wrapping.

    """
    def __init__(self, cwd, totalTests, stream, config=None):
        super(ProgressiveResult, self).__init__(stream, None, 0, config=config)
        self._cwd = cwd
        self._term = Terminal(stream=stream)

        # 1 in case test counting failed and returned 0
        self.bar = ProgressBar(stream, totalTests or 1, self._term)

        # Declare errorclass-savviness so the errorclass plugin doesn't
        # monkeypatch half my methods away:
        self.errorClasses = {}

        self._options = config.options

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
        if isFailure or self._options.show_advisories:
            writeln = self.stream.writeln
            write = self.stream.write
            with self.bar.dodging():
                writeln('\n' +
                        (self._term.bold if isFailure else '') +
                        '%s: %s' % (kind, nose_selector(test)) +
                        (self._term.normal if isFailure else ''))  # end bold

                if isFailure:  # Then show traceback
                    # Don't bind third item to a local var; that can create
                    # circular refs which are expensive to collect. See the
                    # sys.exc_info() docs.
                    exception_type, exception_value = err[:2]
                    extracted_tb = extract_relevant_tb(
                        err[2],
                        exception_type,
                        exception_type is test.failureException)
                    test_frame_index = index_of_test_frame(
                        extracted_tb,
                        exception_type,
                        exception_value,
                        test)
                    if test_frame_index:
                        # We have a good guess at which frame is the test, so
                        # trim everything until that. We don't care to see test
                        # framework frames.
                        extracted_tb = extracted_tb[test_frame_index:]

                    write(''.join(
                        format_traceback(
                            extracted_tb,
                            exception_type,
                            exception_value,
                            self._cwd,
                            self._term,
                            self._options.function_color,
                            self._options.dim_color,
                            self._options.editor)))

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
                ret = self._term.bold + ret + self._term.normal
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

import os
from traceback import format_list, extract_tb, format_exception_only

from nose.result import TextTestResult
from nose.util import src, isclass

from noseprogressive.bar import ProgressBar
from noseprogressive.terminal import Terminal
from noseprogressive.utils import (nose_selector, human_path,
                                   index_of_test_frame, test_address)


class ProgressiveResult(TextTestResult):
    """Test result which updates a progress bar instead of printing dots

    Nose's ResultProxy will wrap it, and other plugins can still print
    stuff---but without smashing into my progress bar, care of my Plugin's
    stderr/out wrapping.

    """
    def __init__(self, cwd, totalTests, stream, showAdvisories, config=None):
        super(ProgressiveResult, self).__init__(stream, None, 0, config=config)
        self._cwd = cwd
        self._term = Terminal(stream=stream)

        # 1 in case test counting failed and returned 0
        self.bar = ProgressBar(stream, totalTests or 1, self._term)

        # Declare errorclass-savviness so the errorclass plugin doesn't
        # monkeypatch half my methods away:
        self.errorClasses = {}

        self._showAdvisories = showAdvisories

    def startTest(self, test):
        """Update the progress bar."""
        super(ProgressiveResult, self).startTest(test)
        self.bar.update(test, self.testsRun)

    def _format_traceback(self, extracted_tb, exception_type, exception_value, test):
        """Return an iterable of formatted traceback frames, rather like traceback.format_list().

        Format things more compactly than the stock formatter, and make every line
        an editor shortcut. Embolden the line representing the stack frame of the
        test, if we can figure that out based on `address`.

        """
        # TODO: Relativize paths by default, but provide a flag to keep them
        # absolute for pasting into editors and other terminal windows.
        # TODO: Test with SyntaxErrors in the test frame. Make sure the test
        # frame gets emboldened.

        # Shorten file paths:
        for i, (file, line, function, text) in enumerate(extracted_tb):
            extracted_tb[i] = human_path(src(file), self._cwd), line, function, text

        # Column widths:
        line_width = len(str(max(the_line for _, the_line, _, _ in extracted_tb)))
        file_width = max(len(f) for f, _, _, _ in extracted_tb)

        template = '  %s +%%-%ss %%-%ss  # %%s%%s%%s\n    %%s\n' % \
                   (os.environ.get('EDITOR', 'vi'), line_width, file_width)

        test_frame_index = index_of_test_frame(extracted_tb,
                                               exception_type,
                                               exception_value,
                                               test)

        for i, (file, line, function, text) in enumerate(extracted_tb):
            if i == test_frame_index:
                bold, unbold = self._term.bold, self._term.normal
            else:
                bold, unbold = '', ''

            yield template % (line, file, bold, function, unbold, text or '')
    
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
            
            writeln = self.stream.writeln
            write = self.stream.write
            with self.bar.dodging():
                writeln('\n' +
                        (self._term.bold if isFailure else '') +
                        '%s: %s' % (kind, nose_selector(test)) +
                        (self._term.normal if isFailure else ''))  # end bold

                if isFailure:  # Then show traceback
                    # File name and line num in a format vi can take:
                    formatted_traceback = ''.join(
                            self._format_traceback(extracted_tb,
                                                   exception_type,
                                                   exception_value,
                                                   test))

                    # Traceback:
                    # TODO: Think about using self._exc_info_to_string, which
                    # does some pretty whizzy skipping of unittest frames.
                    write(formatted_traceback)

                    # Exception:
                    write(''.join(format_exception_only(exception_type,
                                                        exception_value)))

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

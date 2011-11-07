from __future__ import with_statement
from itertools import cycle
from signal import signal, SIGWINCH

from noseprogressive.utils import nose_selector


class ProgressBar(object):
    SPINNER_CHARS = r'/-\|'
    _is_dodging = 0  # Like a semaphore

    def __init__(self, max, term):
        """max is the highest value I will attain. Must be >0."""
        self.stream = term.stream
        self.max = max
        self._term = term
        self.last = ''  # The contents of the previous progress line printed
        self._spinner = cycle(self.SPINNER_CHARS)
        self._measure_terminal()
        signal(SIGWINCH, self._handle_winch)

    def _measure_terminal(self):
        self.lines, self.cols = self._term.height, self._term.width

    def _handle_winch(self, *args):
        #self.erase()  # Doesn't seem to help.
        self._measure_terminal()
        # TODO: Reprint the bar but at the new width.

    def update(self, test, number):
        """Draw an updated progress bar.

        At the moment, the graph takes a fixed width, and the test identifier
        takes the rest of the row, truncated from the left to fit.

        test -- the test being run
        number -- how many tests have been run so far, including this one

        """
        # TODO: Play nicely with absurdly narrow terminals. (OS X's won't even
        # go small enough to hurt us.)

        # Figure out graph:
        GRAPH_WIDTH = 14
        # min() is in case we somehow get the total test count wrong. It's tricky.
        num_markers = int(round(min(1.0, float(number) / self.max) * GRAPH_WIDTH))
        # If there are any markers, replace the last one with the spinner.
        # Otherwise, have just a spinner:
        markers = '=' * (num_markers - 1) + self._spinner.next()
        graph = '[%s%s]' % (markers, ' ' * (GRAPH_WIDTH - len(markers)))

        # Figure out the test identifier portion:
        test_path = nose_selector(test)
        cols_for_path = self.cols - len(graph) - 2  # 2 spaces between path & graph
        if len(test_path) > cols_for_path:
            test_path = test_path[len(test_path) - cols_for_path:]
        else:
            test_path += ' ' * (cols_for_path - len(test_path))

        # Put them together, and let simmer:
        self.last = self._term.bold + test_path + '  ' + graph + self._term.normal
        with self._at_last_line():
            self.stream.write(self.last)

    def erase(self):
        """White out the progress bar."""
        with self._at_last_line():
            self.stream.write(self._term.clear_eol)
        self.stream.flush()

    def _at_last_line(self):
        """Return a context manager that positions the cursor at the last line, lets you write things, and then returns it to its previous position."""
        return self._term.location(0, self.lines)

    def dodging(bar):
        """Return a context manager which erases the bar, lets you output things, and then redraws the bar.

        It's reentrant.

        """
        class ShyProgressBar(object):
            """Context manager that implements a progress bar that gets out of the way"""

            def __enter__(self):
                """Erase the progress bar so bits of disembodied progress bar don't get scrolled up the terminal."""
                # My terminal has no status line, so we make one manually.
                bar._is_dodging += 1  # Increment before calling erase(), which
                                      # calls dodging() again.
                if bar._is_dodging <= 1:  # It *was* 0.
                    bar.erase()

            def __exit__(self, type, value, tb):
                """Redraw the last saved state of the progress bar."""
                if bar._is_dodging == 1:  # Can't decrement yet; write() could
                                          # read it.
                    # This is really necessary only because we monkeypatch
                    # stderr; the next test is about to start and will redraw
                    # the bar.
                    with bar._at_last_line():
                        bar.stream.write(bar.last)
                    bar.stream.flush()
                bar._is_dodging -= 1

        return ShyProgressBar()

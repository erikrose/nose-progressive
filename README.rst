================
nose-progressive
================

nose-progressive is a nose_ plugin which displays progress in a stationary
progress bar, freeing the rest of the screen (as well as the scrollback buffer)
for the compact display of test failures, which it formats beautifully and
usefully. It displays failures and errors as soon as they occur and avoids
scrolling them off the screen in favor of less useful output. It also offers a
number of other human-centric features to speed the debugging process.

.. _nose: http://somethingaboutorange.com/mrl/projects/nose/

.. image:: https://github.com/erikrose/nose-progressive/raw/master/in_progress.png

The governing philosophy of nose-progressive is to get useful information onto
the screen as soon as possible and keep it there as long as possible while
still indicating progress.

Features
========

Progress Bar
------------

nose-progressive indicates progress in a stationary progress bar at the bottom
of the screen. It supports a wide variety of terminal types and reacts to
terminal resizing with all the grace it can muster. And unlike with the
standard dot-strewing testrunner, you can always see what test is running.

Tracebacks: Prompt, Pretty, and Practical
-----------------------------------------

nose typically waits until the bitter end to show error and failure tracebacks,
which wastes a lot of time in large tests suites that take many minutes to
complete. We show tracebacks as soon as they occur so you can start chasing
them immediately, and we format them much better:

* Judicious use of color and other formatting makes the traceback easy to scan.
  It's especially easy to slide down the list of function names to keep your
  place while debugging.
* Omitting the *Traceback (most recent call last)* line and using relative
  paths (optional), along with many other tweaks, fits much more in limited
  screen space.
* Identifying failed tests in a format that can be fed back to nose makes it
  easy to re-run them::

    FAIL: kitsune.apps.wiki.tests.test_parser:TestWikiVideo.test_video_english

  To re-run the above, do this::

    nosetests --with-progressive kitsune.apps.wiki.tests.test_parser:TestWikiVideo.test_video_english
* The frame of the test itself always comes first; we skip any setup frames
  from test harnesses and such. This keeps your concentration where it counts.
  Also, like unittest itself, we hide any frames that descend into trivial
  comparison helpers like ``assertEquals()`` or ``assertRaises()``.

  (We're actually better at it than unittest. We don't just start hiding
  frames at the first unittest one after the test; we snip off only the last
  contiguous run of unittest frames. This lets you wrap your tests in the
  decorators from the mock library, which masquerades as unittest, and still
  see your tracebacks.)
* Editor shortcuts (see below) let you jump right to any problem line in your
  editor.

Editor Shortcuts
----------------

For each frame of a traceback, nose-progressive provides an editor shortcut.
This is a combination of a filesystem path and line number in a format
understood by vi, emacs, the BBEdit command-line tool, and a number of other
editors::

  vi +361 apps/notifications/tests.py  # test_notification_completeness

Just triple-click (or what have you) to select the line, and copy and paste it
onto the command line. You'll land right at the offending line in your editor
of choice. As a bonus, the editor shortcut is more compact than the stock
traceback formatting.

You can set which editor to use by setting any of these, which nose-progressive
checks in order:

* The ``--progressive-editor`` commandline option
* The ``NOSE_PROGRESSIVE_EDITOR`` environment variable
* The ``$EDITOR`` environment variable

Custom Error Classes
--------------------

nose-progressive fully supports custom error classes like Skip and
Deprecated. We note the tests that raise them in realtime, just like normal
errors and failures::

  TODO: kitsune.apps.sumo.tests.test_readonly:ReadOnlyModeTest.test_login_error

However, when an error class is not considered a failure, we don't show it
unless the ``--progressive-advisories`` option is used, and, even in that case,
we don't show a traceback (since usually the important bit of information is
*that* the test was skipped, not the line it was skipped on). This stems from
our philosophy of prioritizing useful information.

Custom error classes are summarized in the counts after the run, along with
failures and errors::

  4 tests, 1 failure, 1 error, 1 skip in 0.0s
           ^^^^^^ Bold ^^^^^^

The non-zero counts of error classes that represent failures are bold to draw
the eye and to correspond with the bold details up in the scrollback. Just
follow the bold, and you'll find your bugs.

Django Support
--------------

nose-progressive can run your Django tests via django-nose_. Just install
django-nose, then run your tests like so::

  ./manage.py test --with-progressive --logging-clear-handlers

.. _django-nose: https://github.com/jbalogh/django-nose

Installation
============

::

  pip install nose-progressive

Or, get the bleeding-edge, unreleased version::

  pip install -e git://github.com/erikrose/nose-progressive.git#egg=nose-progressive

Upgrading
=========

To upgrade from an older version of nose-progressive, assuming you didn't
install it from git::

  pip install --upgrade nose-progressive

Use
===

The simple way::

  nosetests --with-progressive

My favorite way, which suppresses any noisy log messages thrown by tests unless
they fail::

  nosetests --with-progressive --logging-clear-handlers

To `use nose-progressive by default`_, add ``with-progressive=1`` to
``.noserc``.

.. _`use nose-progressive by default`: http://readthedocs.org/docs/nose/en/latest/usage.html#basic-usage

Options
=======

General Options
---------------

``--progressive-editor``
  The editor to use for the shortcuts in tracebacks. Defaults to the value of
  ``$EDITOR`` and then "vi". Equivalent environment variable:
  ``NOSE_PROGRESSIVE_EDITOR``.
``--progressive-abs``
  Display paths in traceback as absolute, rather than relative to the current
  working directory. This lets you copy and paste it to a shell in a different
  cwd or to another program entirely. Equivalent environment variable:
  ``NOSE_PROGRESSIVE_ABSOLUTE_PATHS``.
``--progressive-advisories``
  Show even non-failure custom errors, like Skip and Deprecated, during test
  runs. Equivalent environment variable: ``NOSE_PROGRESSIVE_ADVISORIES``.
``--progressive-with-styling``
  nose-progressive automatically omits bold and color formatting when its
  output is directed to a non- terminal. Specifying
  ``--progressive-with-styling`` forces such styling to be output regardless.
  Equivalent environment variable: ``NOSE_PROGRESSIVE_WITH_STYLING``.
``--progressive-with-bar``
  nose-progressive automatically omits the progress bar when its output is
  directed to a non-terminal. Specifying ``--progressive-with-bar`` forces the
  bar to be output regardless. This option implies
  ``--progressive-with-styling``. Equivalent environment variable:
  ``NOSE_PROGRESSIVE_WITH_BAR``.

Color Options
-------------

Each of these takes an ANSI color expressed as a number from 0 to 15.

``--progressive-function-color=<0..15>``
  Color of function names in tracebacks. Equivalent environment variable:
  ``NOSE_PROGRESSIVE_FUNCTION_COLOR``.
``--progressive-dim-color=<0..15>``
  Color of de-emphasized text (like editor shortcuts) in tracebacks. Equivalent
  environment variable: ``NOSE_PROGRESSIVE_DIM_COLOR``.
``--progressive-bar-filled=<0..15>``
  Color of the progress bar's filled portion. Equivalent environment variable:
  ``NOSE_PROGRESSIVE_BAR_FILLED_COLOR``.
``--progressive-bar-empty=<0..15>``
  Color of the progress bar's empty portion. Equivalent environment variable:
  ``NOSE_PROGRESSIVE_BAR_EMPTY_COLOR``.

Caveats and Known Bugs
======================

* Makes a cosmetic mess when used with ``ipdb``. Consider ``pdbpp`` instead.
* Some logging handlers will smear bits of the progress bar upward if they
  don't print complete lines. I hope to fix this with some monkeypatching, but
  in the meantime, passing ``--logging-clear-handlers`` works around this.
* Requires Python 2.5 or greater and doesn't support Python 3 yet.

Having trouble? Pop over to the `issue tracker`_.

.. _`issue tracker`: https://github.com/erikrose/nose-progressive/issues

Kudos
=====

Thanks to Kumar McMillan for his nose-nicedots_ plugin, which provided
inspiration and starting points for the path formatting. Thanks to my
support.mozilla.com teammates for writing so many tests that this became
necessary. Thanks to Jeff Balogh for django-nose, without which I would have
had little motivation to write this.

.. _nose-nicedots: https://github.com/kumar303/nose-nicedots

Author
======

Erik Rose, while waiting for tests to complete ;-)

License
=======

GPL

Version History
===============

1.4
  * Make the final "OK!" green and bold. This helps me pick it out faster.
  * Warn when using ``--with-id`` and ``--verbosity=2`` or higher. (Jason Ward)
  * Add experimental Python 3 support. Functionality might work, but
    tests need to be ported to pass.
  * Allow other nose plugins to process the test loader. (Ratnadeep Debnath)
  * Show parameter values in the names of generated tests. (Bruno Binet)
  * Tolerate a corner case in skipped tests without crashing. (Will
    Kahn-Greene)
  * Swallow chars that don't decode with UTF-8 when printing tracebacks: both
    in filenames and source code. (Thanks to Bruno Binet for some patches
    inspiring a rethink here.)

1.3
  * Redo progress bar. Now it is made of beautiful terminal magic instead of
    equal signs. It looks best when your terminal supports at least 16 colors,
    but there's a monochrome fallback for fewer. Or, you can customize the
    colors using several new command-line options.
  * Fix a Unicode encoding error that happened when non-ASCII chars appeared in
    traceback text. (Naoya INADA)

1.2.1
  * Tolerate empty tracebacks in the formatter. This avoids exacerbating
    crashes that occur before any test frames.

1.2
  * Fix Python 2.5 support. (David Warde-Farley)
  * Fix display of skipped tests in Python 2.7.
  * Require nose 0.11.0 or greater. Before that, test counting didn't work
    sometimes when test generators were involved. (David Warde-Farley)
  * Hide the progress bar by default when not outputting to a terminal. This
    lets you redirect nose-progressive's output to a file or another process
    and get a nice list of tracebacks.
  * Add an option for forcing the display of terminal formatting, even when
    redirecting the output to a non-terminal.
  * Factor out the terminal formatting library into `its own package`_.
  * Start using tox for testing under multiple versions of Python.

.. _`its own package`: http://pypi.python.org/pypi/blessings/

1.1.1
  * Fix a bug that would cause the formatter to crash on many SyntaxErrors.
    This also improves the heuristics for identifying the test frame when
    there's a SyntaxError: we can now find it as long as the error happens at a
    frame below that of the test.

1.1
  * You can now set the editor nose-progressive uses separately from the
    ``$EDITOR`` shell variable.

1.0
  * Every stack frame is now an editor shortcut. Not only does this make it
    easier to navigate, but it's shorter in both height and width.
  * Reformat tracebacks for great justice. Subtle coloring guides the eye down
    the list of function names.
  * Hide unittest-internal and other pre-test stack frames when printing
    tracebacks. Fewer frames = less noise onscreen = less thinking = win!
  * Add an option to use absolute paths in tracebacks.

0.7
  * Pick the correct stack frame for editor shortcuts to syntax errors. Had to
    handle syntax errors specially, since they don't make it into the traceback
    proper.
  * Show the actual value of the $EDITOR env var rather than just "$EDITOR".
    I'm hoping it makes it a little more obvious what to do with it, plus it
    gives a working default if $EDITOR is not set. Plus plus it doesn't explode
    if you have flags in your $EDITOR, e.g. ``bbedit -w``.

0.6.1
  * Fix a crash triggered by a test having no defined module. --failed should
    always work now.

0.6
  * Major refactoring. nose-progressive now has its own testrunner and test
    result class. This makes it fully compatible with the ``capture`` plugin
    and other plugins that make output.
  * Fully support custom error classes, like Skips and Deprecations. They are
    printed during the test run, bolded if they represent failure, and
    summarized in the counts after the run.
  * Tests which write directly to stderr or stdout no longer smear the progress
    bar.
  * Add $EDITOR to editor shortcut: no more typing!
  * Work with tests that don't have an address() method.
  * Work with tests that return a null filename from test_address().
  * Don't pave over pdb prompts (anymore?).
  * Don't obscure the traceback when the @with_setup decorator on a test
    generator fails.

0.5.1
  * Fix a crash on error when file of a stack frame or function of a test are
    None.

0.5
  * Guess the frame of the test, and spit that out as the editor shortcut. No
    more pointers to eq_()!
  * More reliably determine the editor shortcut pathname, e.g. when running
    tests from an egg distribution directory.
  * Embolden bits of the summary that indicate errors or failures.

0.4
  * Add time elapsed to the final summary.
  * Print "OK!" if no tests went ill. I seem to need this explicit affirmation
    in order to avoid thinking after a test run.
  * In the test failure output, switch the order of the line number and file
    name. This makes it work with the BBEdit command-line tool in addition to
    emacs and vi.

0.3.1
  * Cowboy attempt to fix a crasher on error by changing the entry_point to
    nose.plugin.0.10

0.3
  * Progress bar now works with plain old nosetests, not just django-nose.
    Sorry about that!
  * Stop printing the test name twice in the progress bar.
  * Add basic terminal resizing (SIGWINCH) support. Expanding is great, but
    contracting is still a little ugly. Suggestions welcome.

0.2
  * Real progress bar!
  * Don't crash at the end when ``--no-skips`` is passed.
  * Print the exception, not just the traceback. That's kind of important. :-)
  * Don't crash when a requested test doesn't exist.

0.1.2
  * More documentation tweaks. Package ``long_description`` now contains
    README.

0.1.1
  * Add instructions for installing without git.
  * Change package name in readme to the hypenated one. No behavior changes.

0.1
  * Initial release

================
nose-progressive
================

nose-progressive is a nose_ plugin which displays progress in a stationary
progress bar, freeing the rest of the screen (as well as the scrollback buffer)
for the compact display of test failures. It displays failures and errors as
soon as they occur and avoids scrolling them off the screen in favor of less
useful output. It also offers a number of other human-centric features to speed
the debugging process.

.. _nose: http://somethingaboutorange.com/mrl/projects/nose/

The governing philosophy of nose-progressive is to get useful information onto
the screen as soon as possible and keep it there as long as possible while
still indicating progress.

Features
========

Progress Bar
------------

nose-progressive indicates progress in a stationary progress bar at the
bottom of the screen::

  thing.tests.test_templates:TaggingTests.test_add_new         [===========-  ]

It is glorious. It supports a wide variety of terminal types and reacts to
terminal resizing with all the grace it can muster.

Tracebacks: Realtime, Compact, and Closed-Loop
----------------------------------------------

nose typically waits until the bitter end to show error and failure tracebacks,
which wastes a lot of time in large tests suites that take many minutes to
complete. We show tracebacks as soon as they occur so you can start chasing
them immediately.

A few other niceties further improve the debugging experience:

* Strip the *Traceback (most recent call last)* line off tracebacks, and use
  bold formatting rather than two lines of dividers to delimit them. This fits
  much more in limited screen space::

    FAIL: kitsune.apps.notifications.tests.test_events:MailTests.test_anonymous
          vi +361 apps/notifications/tests/test_events.py
      File "/opt/local/Library/Frameworks/Python.framework/Versions/2.6/lib/python2.6/unittest.py", line 279, in run
        testMethod()
      File "/Users/erose/Checkouts/kitsune/../kitsune/apps/notifications/tests/test_events.py", line 361, in test_anonymous
        eq_(1, len(mail.outbox))
      File "/Users/erose/Checkouts/kitsune/vendor/packages/nose/nose/tools.py", line 31, in eq_
        assert a == b, msg or "%r != %r" % (a, b)
    AssertionError: 1 != 0

    ERROR: kitsune.apps.questions.tests.test_templates:TemplateTestCase.test_woo
           vi +494 apps/questions/tests/test_templates.py
      File "/opt/local/Library/Frameworks/Python.framework/Versions/2.6/lib/python2.6/unittest.py", line 279, in run
        testMethod()
      File "/Users/erose/Checkouts/kitsune/vendor/packages/mock/mock.py", line 196, in patched
        return func(*args, **keywargs)
      File "/Users/erose/Checkouts/kitsune/../kitsune/apps/questions/tests/test_templates.py", line 494, in test_woo
        attrs_eq(mail.outbox[0], to=['some@bo.dy'],
    IndexError: list index out of range

  The preceding doesn't quite reflect reality; in an actual terminal, the two
  lines after FAIL or ERROR are **bold** to aid visual chunking.

* Identify failed tests in a format that can be fed back to nose, so it's
  easy to re-run them::

    FAIL: notifications.tests:MailTests.test_anonymous

  To re-run the above, do this::

    nosetests --with-progressive notifications.tests:MailTests.test_anonymous

Editor Shortcuts
----------------

For each failure or error, nose-progressive provides an editor shortcut. This
is a combination of a filesystem path and line number in a format understood
by vi, emacs, the BBEdit command-line tool, and a number of other editors::

  FAIL: kitsune.apps.notifications.tests.test_events:MailTests.test_anonymous
        vi +361 apps/notifications/tests.py

Just triple-click (or what have you) to select the second line above, and copy
and paste it onto the command line. You'll land right at the offending line in
your editor of choice, determined by the ``$EDITOR`` environment variable.

In addition, we apply some heuristics to choosing which file and line to show
for the above: we try to find the stack frame of your actual test, rather than
plopping you down unhelpfully in the middle of a nose helper function like
eq_(). Even if you create your own assertion helper functions, like
``xml_eq()``, we still track down your test.

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

Or, to get the bleeding-edge, unreleased version::

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

Options
=======

``--progressive-advisories``
  Show even non-failure custom errors, like Skip and Deprecated, during test
  runs.

Caveats and Known Bugs
======================

* Some logging handlers will smear bits of the progress bar upward if they
  don't print complete lines. I hope to fix this with some monkeypatching, but
  in the meantime, passing ``--logging-clear-handlers`` works around this.
* I haven't tried this in anything but Python 2.6. Bug reports are welcome. I
  don't plan to support Python versions earlier than 2.5 unless there's
  overwhelming demand, but I would like to support later ones.

Having trouble? Pop over to the `issue tracker`_.

.. _`issue tracker`: https://github.com/erikrose/nose-progressive/issues

Future Plans
============

* Commandline switches for every little thing

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

Version History
===============

0.7
  * Pick the correct stack frame for editor shortcuts to syntax errors. Had to
    handle syntax errors specially, since they don't make it into the traceback
    proper.
  * Show the actual value of the $EDITOR env var rather than just "$EDITOR".
    I'm hoping it makes it a little more obvious what to do with it, plus it
    gives a working default if $EDITOR is not set.

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

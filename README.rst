================
Nose Progressive
================

Nose Progressive is a nose_ plugin which displays progress in a stationary
progress bar, freeing the rest of the screen (as well as the scrollback buffer)
for the compact display of test failures. It displays failures and errors as
soon as they occur and avoids scrolling them off the screen in favor of less
useful output.

.. _nose: http://somethingaboutorange.com/mrl/projects/nose/

The governing philosophy of Nose Progressive is to get useful information onto
the screen as soon as possible and keep it there as long as possible while
still indicating progress.

Features
========

* Indicate progress in a stationary progress bar rather than scrolling useful
  tracebacks off the screen or spacing them out with dots and cruft.
* Show tracebacks as soon as they occur rather than waiting until the bitter
  end. Strip the "Traceback (most recent call last):" off tracebacks so they
  take less space.
* Identify failed tests in a format that can be fed back to nose, so it's easy
  to re-run them.
* Print a filesystem path complete with vi-style line number, so you can paste
  it to the commandline and be taken straight to the bug in your editor. It
  tries to be intelligent about choosing which file and line to choose: it does
  its best to find the stack frame of your actual test, rather than plopping
  you down unhelpfully in the middle of nose helper functions like eq_().
* Work great with Django via django-nose_ (of course).

.. _django-nose: https://github.com/jbalogh/django-nose

Installation
============

::

  pip install nose-progressive

Or, to get the bleeding-edge, unreleased version::

  pip install -e \
    git://github.com/erikrose/nose-progressive.git#egg=nose-progressive

Use
===

::

  nosetests --with-progressive

Example
=======

The following doesn't quite do it justice; in an actual terminal, the 2
pathname lines after FAIL or ERROR are **bold** to aid visual chunking, and the
progress bar at the bottom is bold as well::

  % nosetests --with-progressive
  
  FAIL: kitsune.apps.notifications.tests.test_events:MailTests.test_anonymous
        +361 apps/notifications/tests/test_events.py
    File "/opt/local/Library/Frameworks/Python.framework/Versions/2.6/lib/python2.6/unittest.py", line 279, in run
      testMethod()
    File "/Users/erose/Checkouts/kitsune/../kitsune/apps/notifications/tests/test_events.py", line 361, in test_anonymous
      eq_(1, len(mail.outbox))
    File "/Users/erose/Checkouts/kitsune/vendor/packages/nose/nose/tools.py", line 31, in eq_
      assert a == b, msg or "%r != %r" % (a, b)
  AssertionError: 1 != 0

  ERROR: kitsune.apps.questions.tests.test_templates:TemplateTestCase.test_woo
         +494 apps/questions/tests/test_templates.py
    File "/opt/local/Library/Frameworks/Python.framework/Versions/2.6/lib/python2.6/unittest.py", line 279, in run
      testMethod()
    File "/Users/erose/Checkouts/kitsune/vendor/packages/mock/mock.py", line 196, in patched
      return func(*args, **keywargs)
    File "/Users/erose/Checkouts/kitsune/../kitsune/apps/questions/tests/test_templates.py", line 494, in test_woo
      attrs_eq(mail.outbox[0], to=['some@bo.dy'],
  IndexError: list index out of range

  kitsune.apps.questions.tests.test_templates:TaggingViewTestsAsAdmin.test_add_new_canonicalizes         [===========-  ]

Caveats and known bugs
======================

* Skipped tests get counted in Python 2.6, but they don't get printed. I
  consider skips something to be discouraged, so I plan to fix this.
* Tests which themselves write to stderr will smear bits of the progress bar
  upward if they don't print complete lines. I hope to fix this with some
  monkeypatching, but in the meantime, passing ``--logging-clear-handlers``
  fixes most of these in practice.
* I haven't tried this in anything but Python 2.6. Bug reports are welcome!
* Horrible test coverage. Ironic? :-)

Got more? Pop over to the `issue tracker`_.

.. _`issue tracker`: https://github.com/erikrose/nose-progressive/issues

Future plans
============

* Commandline switches for every little thing

Kudos
=====

Thanks to Kumar McMillan for his nose-nicedots_ plugin, which provided
inspiration and starting points for the path formatting. Thanks to my
support.mozilla.com teammates for writing so many tests that this became
necessary.

.. _nose-nicedots: https://github.com/kumar303/nose-nicedots

Version history
===============

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
  * More documentation tweaks. Package ``long_description`` now contains README.

0.1.1
  * Add instructions for installing without git.
  * Change package name in readme to the hypenated one. No behavior changes.

0.1
  * Initial release

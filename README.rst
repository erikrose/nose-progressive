================
Nose Progressive
================

Nose Progressive is a nose_ plugin which displays progress in a stationary
progress bar, gives you useful information as soon as possible, and avoids
scrolling things off the screen in favor of less useful things.

.. _nose: http://somethingaboutorange.com/mrl/projects/nose/

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
  it to the commandline and be taken straight to the bug in your editor.
* Work great with Django via django-nose (of course).

Installation
============

  pip install -e \
    git://github.com/erikrose/nose-progressive.git#egg=noseprogressive

Use
===

  nosetests --with-progressive

Example
=======

This doesn't quite do it justice; in an actual terminal, the 2 pathname lines
after FAIL or ERROR are bold to aid visual chunking, and the progress bar is
bold as well::

  % nosetests --with-progressive
  
  FAIL: kitsune.apps.notifications.tests.test_events:MailTests.test_anonymous
        apps/notifications/tests/test_events.py +31
    File "/opt/local/Library/Frameworks/Python.framework/Versions/2.6/lib/python2.6/unittest.py", line 279, in run
      testMethod()
    File "/Users/erose/Checkouts/kitsune/../kitsune/apps/notifications/tests/test_events.py", line 361, in test_anonymous
      eq_(1, len(mail.outbox))
    File "/Users/erose/Checkouts/kitsune/vendor/packages/nose/nose/tools.py", line 31, in eq_
      assert a == b, msg or "%r != %r" % (a, b)
  
  ERROR: kitsune.apps.questions.tests.test_templates:TemplateTestCase.test_woo
         apps/questions/tests/test_templates.py +494
    File "/opt/local/Library/Frameworks/Python.framework/Versions/2.6/lib/python2.6/unittest.py", line 279, in run
      testMethod()
    File "/Users/erose/Checkouts/kitsune/vendor/packages/mock/mock.py", line 196, in patched
      return func(*args, **keywargs)
    File "/Users/erose/Checkouts/kitsune/../kitsune/apps/questions/tests/test_templates.py", line 494, in test_woo
      attrs_eq(mail.outbox[0], to=['some@bo.dy'],
  
  kitsune.apps.search.tests.test_json:JSONTest.test_json_format             458

Caveats and known bugs
======================

* Skipped tests get counted in Python 2.6, but they don't get printed. I
  consider skips something to be discouraged, so I plan to fix this.
* Tests which themselves write to stderr will smear bits of the progress bar
  upward if they don't print complete lines. I hope to fix this with some
  monkeypatching, but in the meantime, passing --logging-clear-handlers fixes
  most of these in practice.
* I haven't tried this in anything but Python 2.6. Bug reports are welcome!
* No tests yet. Ironic? :-)

Future plans
============

* A proper progress bar. nose doesn't count tests for us ahead of time, so
  we'll have to preflight ourselves.

Kudos
=====

Thanks to Kumar McMillan for his nose-nicedots plugin, which provided
inspiration and starting points for the pretty-printing. Thanks to the
support.mozilla.com team for writing so many tests that this became necessary.

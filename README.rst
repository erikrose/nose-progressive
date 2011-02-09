================
Nose Progressive
================

Nose Progressive is a nose_ plugin whose aim is to give you useful information
as soon as possible, avoid scrolling it off the screen in favor of less useful
things, and, meanwhile, indicate progress through the test suite.

.. _nose: http://somethingaboutorange.com/mrl/projects/nose/

Other niceties:

* Prints the paths to tests in a format that you can feed right back to nose
* Prints a filesystem path complete with vi-style line number, so you can paste
  it to the commandline and be taken straight to the bug in your editor

Installation
============

  pip install -e \
    git+git://github.com/erikrose/nose-progessive.git#egg=noseprogressive

Use
===

  nosetests --with-progressive

Example
=======

::

  $ nosetests --with-progressive

  apps/devhub/tests/test_views.py:TestActivity
  ..............

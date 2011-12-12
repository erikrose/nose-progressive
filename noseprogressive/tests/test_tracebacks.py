# -*- coding: utf-8 -*-
"""Tests for traceback formatting."""

from noseprogressive.tracebacks import format_traceback


syntax_error_tb = ([
     ("setup.py", 79, '?', """classifiers = ["""),
     ("/usr/lib64/python2.4/distutils/core.py", 149, 'setup', """dist.run_commands()"""),
     ("/usr/lib64/python2.4/distutils/dist.py", 946, 'run_commands', """self.run_command(cmd)"""),
     ("/usr/lib64/python2.4/distutils/dist.py", 966, 'run_command', """cmd_obj.run()"""),
     ("/usr/lib/python2.4/site-packages/setuptools/command/install.py", 76, 'run', """self.do_egg_install()"""),
     ("/usr/lib/python2.4/site-packages/setuptools/command/install.py", 100, 'do_egg_install', """cmd.run()"""),
     ("/usr/lib/python2.4/site-packages/setuptools/command/easy_install.py", 211, 'run', """self.easy_install(spec, not self.no_deps)"""),
     ("/usr/lib/python2.4/site-packages/setuptools/command/easy_install.py", 427, 'easy_install', """return self.install_item(None, spec, tmpdir, deps, True)"""),
     ("/usr/lib/python2.4/site-packages/setuptools/command/easy_install.py", 473, 'install_item', """self.process_distribution(spec, dist, deps)"""),
     ("/usr/lib/python2.4/site-packages/setuptools/command/easy_install.py", 518, 'process_distribution', """distros = WorkingSet([]).resolve("""),
     ("/usr/lib/python2.4/site-packages/pkg_resources.py", 481, 'resolve', """dist = best[req.key] = env.best_match(req, self, installer)"""),
     ("/usr/lib/python2.4/site-packages/pkg_resources.py", 717, 'best_match', """return self.obtain(req, installer) # try and download/install"""),
     ("/usr/lib/python2.4/site-packages/pkg_resources.py", 729, 'obtain', """return installer(requirement)"""),
     ("/usr/lib/python2.4/site-packages/setuptools/command/easy_install.py", 432, 'easy_install', """dist = self.package_index.fetch_distribution("""),
     ("/usr/lib/python2.4/site-packages/setuptools/package_index.py", 462, 'fetch_distribution', """self.find_packages(requirement)"""),
     ("/usr/lib/python2.4/site-packages/setuptools/package_index.py", 303, 'find_packages', """self.scan_url(self.index_url + requirement.unsafe_name+'/')"""),
     ("/usr/lib/python2.4/site-packages/setuptools/package_index.py", 612, 'scan_url', """self.process_url(url, True)"""),
     ("/usr/lib/python2.4/site-packages/setuptools/package_index.py", 190, 'process_url', """f = self.open_url(url)"""),
     ("/usr/lib/python2.4/site-packages/setuptools/package_index.py", 579, 'open_url', """return open_with_auth(url)"""),
     ("/usr/lib/python2.4/site-packages/setuptools/package_index.py", 676, 'open_with_auth', """fp = urllib2.urlopen(request)"""),
     ("/usr/lib64/python2.4/urllib2.py", 130, 'urlopen', """return _opener.open(url, data)"""),
     ("/usr/lib64/python2.4/urllib2.py", 358, 'open', """response = self._open(req, data)"""),
     ("/usr/lib64/python2.4/urllib2.py", 376, '_open', """'_open', req)"""),
     ("/usr/lib64/python2.4/urllib2.py", 337, '_call_chain', """result = func(*args)"""),
     ("/usr/lib64/python2.4/urllib2.py", 573, '<lambda>', """lambda r, proxy=url, type=type, meth=self.proxy_open: \\"""),
     ("/usr/lib64/python2.4/urllib2.py", 580, 'proxy_open', """if '@' in host:""")
     # Was originally TypeError: iterable argument required
    ], SyntaxError, SyntaxError('invalid syntax', ('/Users/erose/Checkouts/nose-progress/noseprogressive/tests/test_integration.py', 97, 5, '    :bad\n')))
attr_error_tb = ([
     ("/usr/share/PackageKit/helpers/yum/yumBackend.py", 2926, 'install_signature', """self.yumbase.getKeyForPackage(pkg, askcb = lambda x, y, z: True)"""),
     ("/usr/lib/python2.6/site-packages/yum/__init__.py", 4309, 'getKeyForPackage', """result = ts.pgpImportPubkey(misc.procgpgkey(info['raw_key']))"""),
     ("/usr/lib/python2.6/site-packages/rpmUtils/transaction.py", 59, '__getattr__', """return self.getMethod(attr)"""),
     ("/usr/lib/python2.6/site-packages/rpmUtils/transaction.py", 69, 'getMethod', """return getattr(self.ts, method)""")
    ], AttributeError, AttributeError("'NoneType' object has no attribute 'pgpImportPubkey'"))


def test_syntax_error():
    """Exercise special handling of syntax errors to show it doesn't crash."""
    ''.join(format_traceback(*syntax_error_tb))


def test_non_syntax_error():
    """Exercise typical error formatting to show it doesn't crash."""
    ''.join(format_traceback(*attr_error_tb))


def test_empty_tracebacks():
    """Make sure we don't crash on empty tracebacks.

    Sometimes, stuff crashes before we even get to the test. pdbpp has been
    doing this a lot to me lately. When that happens, we receive an empty
    traceback.

    """
    list(format_traceback(
        [],
        AttributeError,
        AttributeError("'NoneType' object has no attribute 'pgpImportPubkey'")))


def test_unicode():
    """Don't have encoding explosions when a line of code contains non-ASCII."""
    unicode_tb = ([
         ("/usr/lib/whatever.py", 69, 'getMethod', """return u'あ'""")
        ], AttributeError, AttributeError("'NoneType' object has no pants.'"))
    ''.join(format_traceback(*unicode_tb))

import sys
import codecs

# Prevent spurious errors during `python setup.py test`, a la
# http://www.eby-sarna.com/pipermail/peak/2010-May/003357.html:
try:
    import multiprocessing
except ImportError:
    pass

from setuptools import setup, find_packages


extra_setup = {}
if sys.version_info >= (3,):
    extra_setup['use_2to3'] = True

setup(
    name='nose-progressive',
    version='1.5.1',
    description='A testrunner with a progress bar and smarter tracebacks',
    long_description=codecs.open('README.rst', encoding='utf-8').read(),
    author='Erik Rose',
    author_email='erikrose@grinchcentral.com',
    license='MIT',
    packages=find_packages(exclude=['ez_setup']),
    install_requires=['nose>=1.2.1', 'blessings>=1.3,<2.0'],
    test_suite='nose.collector',
    url='https://github.com/erikrose/nose-progressive',
    include_package_data=True,
    entry_points="""
        [nose.plugins.0.10]
        noseprogressive = noseprogressive:ProgressivePlugin
        """,
    classifiers = [
        'Development Status :: 5 - Production/Stable',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'Natural Language :: English',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.2',
        'Programming Language :: Python :: 3.3',
        'Topic :: Software Development :: Testing'
        ],
    **extra_setup
)

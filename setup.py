import sys

from setuptools import setup, find_packages


extra_setup = {}
if sys.version_info >= (3,):
    extra_setup['use_2to3'] = True

setup(
    name='nose-progressive',
    version='1.4',
    description='Nose plugin to show progress bar and tracebacks during tests',
    long_description=open('README.rst').read(),
    author='Erik Rose',
    author_email='erikrose@grinchcentral.com',
    license='GPL',
    packages=find_packages(exclude=['ez_setup']),
    install_requires=['Nose>=0.11.0', 'blessings>=1.3,<2.0'],
    url='',
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
        'License :: OSI Approved :: GNU General Public License (GPL)',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.5',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Topic :: Software Development :: Testing'
        ],
    **extra_setup
)

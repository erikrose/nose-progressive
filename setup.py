import sys

from setuptools import setup, find_packages

extra_setup = {}
if sys.version_info >= (3,):
    extra_setup['use_2to3'] = True

setup(
    name='nose-progressive',
    version='0.3',
    description='Nose plugin to show progress bar and tracebacks during tests',
    long_description=open('README.rst').read(),
    author='Erik Rose',
    author_email='erikrose@grinchcentral.com',
    license='GPL',
    packages=find_packages(exclude=['ez_setup']),
    install_requires=['Nose'],
    url='',
    include_package_data=True,
    entry_points="""
        [nose.plugins]
        noseprogressive = noseprogressive:ProgressivePlugin
        """,
    classifiers = [
        'Intended Audience :: Developers',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Topic :: Software Development :: Testing'
        ],
    **extra_setup
)

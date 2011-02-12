import sys

from setuptools import setup, find_packages

extra_setup = {}
if sys.version_info >= (3,):
    extra_setup['use_2to3'] = True

setup(
    name='nose-progressive',
    version='0.1',
    description='Nose plugin to show progress bar and tracebacks during tests',
    long_description="""The philosophy of noseprogressive is to get useful information onto the screen as soon as possible and keep it there as long as possible while still indicating progress. Thus, it refrains from printing dots, since that tends to scroll informative tracebacks away. Instead, it draws a nice progress bar and the current test path, all on one line.""",
    author='Erik Rose',
    author_email='erikrose@grinchcentral.com',
    license='GPL',
    packages=find_packages(exclude=['ez_setup']),
    install_requires=['Nose'],
    url='',
    include_package_data=True,
    entry_points="""
        [nose.plugins.0.10]
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

"""A setuptools based setup module.

"""
# Always prefer setuptools over distutils
from setuptools import setup, find_packages
from setuptools.dist import Distribution
import distutils.log

# To use a consistent encoding
from codecs import open
import os
import subprocess
import pyzceqsolver
import sys
import platform

from distutils.command.build import build

def get_target_system_shared_library_name():
     """Helper function that scans command line arguments whether platform
     tag has been explicitely specified (indicates a cross build) and
     tailors the system name for it
     """
     platform_tag_map = {
          'win_amd64': 'Windows',
          'win32': 'Windows',
     }
     target_system_name = platform.system()
     # Check whether for platform tag presence
     for arg in sys.argv[1:]:
          if arg.startswith("--plat-name="):
               plat_name = arg.split('=', 1)[1]
               try:
                    target_system_name = platform_tag_map[plat_name]
               except KeyError as e:
                    print('Unsupported platform name ({}) for cross compilation '\
                          'specified via --plat-name'.format(plat_name))
                    sys.exit(1)
               break
     return pyzceqsolver.get_library_filename(target_system_name)

class MyDist(Distribution):
     def has_ext_modules(self):
         return True

def sconsbuild(command_subclass):
    """A decorator for classes subclassing one of the setuptools commands.

    It modifies the run() method so that it also runs the scons build
    for the C shared library.
    """
    orig_run = command_subclass.run
    orig_initialize_options = command_subclass.initialize_options
    orig_finalize_options = command_subclass.finalize_options

    command_subclass.user_options.extend([
         ('scons-opts=', 's', 'SCons options'),
    ])

    def modified_initialize_options(self):
         self.scons_opts=[]
         orig_initialize_options(self)

    def modified_finalize_options(self):
         orig_finalize_options(self)

    def modified_run(self):
         scons_opts_list = [s.strip() for s in self.scons_opts.split(',')]
         command = ['scons']
         command.extend(scons_opts_list)
         command.append('pyinstall')

         self.announce('Building zceq solver C library (scons options: {})'.format(
              scons_opts_list), distutils.log.INFO)
         try:
              subprocess.check_call(command)
         except subprocess.CalledProcessError as e:
              self.announce('SCons build failed (command: {0}, {1})'.format(
                   ' '.join(command), command), distutils.log.ERROR)
              raise(e)
         else:
              orig_run(self)

    command_subclass.run = modified_run
    command_subclass.initialize_options = modified_initialize_options
    command_subclass.finalize_options = modified_finalize_options

    return command_subclass


@sconsbuild
class BuildCommand(build):
     pass

# Get the long description from the README file
with open(os.path.join(os.path.abspath(os.path.dirname(__file__)),
                       'README.md'), encoding='utf-8') as f:
     long_description = f.read()

package = 'pyzceqsolver'
library_filename = get_target_system_shared_library_name()

setup(
     name=package,

     # Versions should comply with PEP440.  For a discussion on single-sourcing
     # the version across setup.py and the project code, see
     # https://packaging.python.org/en/latest/single_source_version.html
     version='1.0.0',

     description='Python Interface to Zcash CPU solver library',
     long_description=long_description,

     # The project's main homepage.
     url='https://github.com/slushpool/zceq-solver',

     # Author details
     author='Slushpool',

     # Choose your license
     license='MIT',

     # See https://pypi.python.org/pypi?%3Aaction=list_classifiers
     classifiers=[
          # How mature is this project? Common values are
          #   3 - Alpha
          #   4 - Beta
          #   5 - Production/Stable
          'Development Status :: 3 - Alpha',

          # Indicate who your project is intended for
          'Intended Audience :: Developers',

          # Pick your license as you wish (should match "license" above)
          'License :: OSI Approved :: MIT License',

          # Specify the Python versions you support here. In particular, ensure
          # that you indicate whether you support Python 2, Python 3 or both.
          'Programming Language :: Python :: 2.7',
          'Programming Language :: Python :: 3.4',
          'Programming Language :: Python :: 3.5',
     ],

     # What does your project relate to?
     keywords='equihash solver zcash mining',

     # You can just specify the packages manually here if your project is
     # simple. Or you can use find_packages().
     packages=find_packages(),

     eager_resources=['{0}/{1}'.format(package, library_filename)],
     # setup requires cffi, since it already uses parts of this package
     setup_requires=['cffi'],
     # List run-time dependencies here.  These will be installed by pip when
     # your project is installed. For an analysis of "install_requires" vs pip's
     # requirements files see:
     # https://packaging.python.org/en/latest/requirements.html
     # mako is suggested by pyopencl
     install_requires=['cffi'],

     package_data={
          package: [library_filename],
     },
     cmdclass={
          'build': BuildCommand,
     },
     distclass = MyDist,
)

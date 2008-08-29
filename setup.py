"""
Handling of EDI related data formats.
See https://cybernetics.hudora.biz/projects/wiki/benEDIct for details.
"""

from ez_setup import use_setuptools
use_setuptools()
from setuptools import setup

hubarcode = setup(name='benEDIct',
      maintainer='Maximillian Dornseif',
      maintainer_email='md@hudora.de',
      url='https://cybernetics.hudora.biz/projects/wiki/benEDIct',
      version='0.01',
      description='handling of various EDI formats',
      long_description=__doc__,
      classifiers=['License :: OSI Approved :: BSD License',
                   'Intended Audience :: Developers',
                   'Programming Language :: Python'],
      zip_safe=True,
      packages = ['edilib', 'edilib.cctop'], 
      package_dir = {'edilib': ''})

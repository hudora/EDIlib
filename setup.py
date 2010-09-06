"""
Handling of EDI related data formats.
"""

from ez_setup import use_setuptools
use_setuptools()
from setuptools import setup

hubarcode = setup(name='edilib',
      maintainer='Maximillian Dornseif',
      maintainer_email='md@hudora.de',
      version='0.01',
      description='handling of various EDI formats',
      long_description=__doc__,
      classifiers=['License :: OSI Approved :: BSD License',
                   'Intended Audience :: Developers',
                   'Programming Language :: Python'],
      zip_safe=True,
      packages = ['edilib', 'edilib.cctop'], 
      install_requires = ['huSoftM'],
      dependency_links = ['http://cybernetics.hudora.biz/dist/huSoftM/'],
      )

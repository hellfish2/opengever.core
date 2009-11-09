from setuptools import setup, find_packages
import os

version = open('opengever/document/version.txt').read().strip()

setup(name='opengever.document',
      version=version,
      description="OpenGever Document content type",
      long_description=open("README.txt").read() + "\n" +
                       open(os.path.join("docs", "HISTORY.txt")).read(),
      # Get more strings from http://www.python.org/pypi?%3Aaction=list_classifiers
      classifiers=[
        "Programming Language :: Python",
        "Topic :: Software Development :: Libraries :: Python Modules",
        ],
      keywords='opengever document',
      author='Jonas Baumann, 4teamwork GmbH',
      author_email='info@4teamwork.ch',
      url='https://svn.4teamwork.ch/repos/opengever/opengever.document/',
      license='GPL2',
      packages=find_packages(exclude=['ez_setup']),
      namespace_packages=['opengever'],
      include_package_data=True,
      zip_safe=False,
      install_requires=[
          'setuptools',
          'ftw.sendmail',
          'opengever.sqlfile',
          'plone.app.dexterity',
          'plone.principalsource',
          'plone.versioningbehavior',
          'plone.stagingbehavior',
          'collective.filepreviewbehavior',
          'Products.CMFCore',
          'Products.MimetypesRegistry',
          'Products.ARFilePreview'
          'stoneagehtml', # required by ftw.sendmail, but there is no dependency in the current release
      ],
      entry_points="""
      # -*- Entry points: -*-
      """,
      )

from setuptools import setup, find_packages, Extension
from arver import APPNAME, VERSION, URL

with open('README.md', encoding='utf-8') as f:
    readme = f.read()

setup(name=APPNAME,
      version=VERSION,
      description='Application for verifying ripped audio files using AccurateRip database.',
      long_description=readme,
      long_description_content_type="text/markdown",
      author='arcctgx',
      author_email='arcctgx@o2.pl',
      url=URL,
      license='GPLv3',
      classifiers=[
          'Development Status :: 4 - Beta', 'Environment :: Console',
          'Intended Audience :: End Users/Desktop',
          'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
          'Natural Language :: English', 'Operating System :: POSIX :: Linux',
          'Programming Language :: C', 'Programming Language :: Python :: 3.7',
          'Programming Language :: Python :: 3.8', 'Programming Language :: Python :: 3.9',
          'Programming Language :: Python :: 3.10', 'Programming Language :: Python :: 3.11',
          'Topic :: Multimedia :: Sound/Audio :: Analysis',
          'Topic :: Multimedia :: Sound/Audio :: CD Audio :: CD Ripping'
      ],
      python_requires='>=3.7',
      packages=find_packages(),
      entry_points={
          'console_scripts': [
              'arver = arver.main:main', 'arver-discinfo = arver.disc_info:main',
              'arver-ripinfo = arver.rip_info:main', 'arver-bin-parser = arver.bin_parser:main'
          ]
      },
      ext_modules=[
          Extension('arver.checksum.accuraterip',
                    sources=['arver/checksum/accuraterip.c'],
                    libraries=['sndfile'])
      ],
      install_requires=['discid', 'musicbrainzngs', 'pycdio', 'requests'])

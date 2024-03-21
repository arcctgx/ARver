from setuptools import Extension, find_packages, setup

from arver import APPNAME, URL, VERSION

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
          'Development Status :: 5 - Production/Stable', 'Environment :: Console',
          'Intended Audience :: End Users/Desktop',
          'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
          'Natural Language :: English', 'Operating System :: POSIX :: Linux',
          'Programming Language :: C', 'Programming Language :: Python :: 3 :: Only',
          'Programming Language :: Python :: 3.7', 'Programming Language :: Python :: 3.8',
          'Programming Language :: Python :: 3.9', 'Programming Language :: Python :: 3.10',
          'Programming Language :: Python :: 3.11',
          'Topic :: Multimedia :: Sound/Audio :: Analysis',
          'Topic :: Multimedia :: Sound/Audio :: CD Audio :: CD Ripping'
      ],
      python_requires='>=3.7',
      packages=find_packages(),
      entry_points={
          'console_scripts': [
              'arver = arver.arver_main:main', 'arver-discinfo = arver.arver_discinfo:main',
              'arver-ripinfo = arver.arver_ripinfo:main',
              'arver-bin-parser = arver.arver_bin_parser:main'
          ]
      },
      ext_modules=[
          Extension('arver.audio._audio',
                    sources=['arver/audio/_audio.c'],
                    libraries=['sndfile', 'z'])
      ],
      install_requires=['discid', 'musicbrainzngs', 'pycdio', 'requests'])

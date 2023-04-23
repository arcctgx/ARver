from setuptools import setup, find_packages, Extension

from arver import APPNAME, VERSION, URL

setup(name=APPNAME,
      version=VERSION,
      description='Application for verifiyng ripped WAV files using AccurateRip database.',
      author='arcctgx',
      url=URL,
      license='GPLv3',
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
      ])

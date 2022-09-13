from setuptools import setup, find_packages, Extension
from arver import APPNAME, VERSION, URL

setup(
    name = APPNAME,
    version = VERSION,
    description = 'Application for verifiyng ripped WAV files using AccurateRip database.',
    author = 'arcctgx',
    url = URL,
    license = 'GPLv3',

    packages = find_packages(),

    entry_points = {
        'console_scripts': [
            'arver-cdtoc = arver.cdtoc:main',
            'arver-mbtoc = arver.mbtoc:main',
            'arver-crc = arver.crc:main',
            'arver-arcrc = arver.ar:main'
        ],
    },

    ext_modules = [
        Extension('arver.checksum.accuraterip',
            sources = ['arver/checksum/accuraterip.c'],
            libraries = ['sndfile']
        )
    ]
)

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
            'arver = arver.arver:main',
            'arver-cdtoc = arver.cdtoc:main',
            'arver-mbtoc = arver.mbtoc:main',
            'arver-copy-crc = arver.crc:main',
            'arver-accurip-crc = arver.ar:main'
        ],
    },

    ext_modules = [
        Extension('arver.checksum.accuraterip',
            sources = ['arver/checksum/accuraterip.c'],
            libraries = ['sndfile']
        )
    ]
)

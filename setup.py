from distutils.core import setup, Extension
import version

setup(
    name = version.APPNAME,
    version = version.VERSION,
    description = 'Application for verifiyng ripped WAV files using AccurateRip database.',
    author = 'arcctgx',
    url = 'https://github.com/arcctgx/ARver',
    license = 'GPLv3',

    ext_modules = [
        Extension('accuraterip.checksum',
            sources = ['accuraterip/checksum.c'],
            libraries = ['sndfile']
        )
    ]
)

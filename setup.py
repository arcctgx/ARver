"""ARver C extension definitions."""

from setuptools import Extension, setup

PYTHON_API_VERSION = '0x03070000'

setup(
    ext_modules=[
        Extension('arver.audio._audio',
                  sources=['arver/audio/_audio.c'],
                  libraries=['pthread', 'sndfile', 'z'],
                  extra_compile_args=['-std=c99', '-O3', '-D_DEFAULT_SOURCE'],
                  define_macros=[('Py_LIMITED_API', PYTHON_API_VERSION)],
                  py_limited_api=True),
        Extension('arver.disc._cdio',
                  sources=['arver/disc/_cdio.c'],
                  libraries=['cdio'],
                  extra_compile_args=['-std=c99', '-O3', '-Wall', '-Werror']),
    ],
    options={
        'bdist_wheel': {
            'py_limited_api': 'cp37'
        },
    },
)

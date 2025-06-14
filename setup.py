"""ARver C extension definition."""

from setuptools import Extension, setup

setup(
    ext_modules=[
        Extension('arver.audio._audio',
                  sources=['arver/audio/_audio.c'],
                  libraries=['pthread', 'sndfile', 'z'],
                  extra_compile_args=['-std=c99', '-O3', '-D_DEFAULT_SOURCE'],
                  define_macros=[('Py_LIMITED_API', '0x03070000')],
                  py_limited_api=True),
    ],
    options={
        'bdist_wheel': {
            'py_limited_api': 'cp37'
        },
    },
)

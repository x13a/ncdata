from setuptools import (
    find_packages,
    setup,
)

import ncdata

lib_name = ncdata.__name__
setup(
    name=lib_name,
    description=ncdata.__doc__,
    version=ncdata.__version__,
    url='https://github.com/x13a/{}'.format(lib_name),
    packages=find_packages(),
    entry_points={
        'console_scripts': [
            '{0} = {0}.__main__:main'.format(lib_name),
        ],
    },
    platforms=['darwin'],
    python_requires='>=3.8',
)

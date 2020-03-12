from setuptools import (
    find_packages,
    setup,
)

import ncprivacy

lib_name = ncprivacy.__name__
setup(
    name=lib_name,
    description=ncprivacy.__doc__,
    version=ncprivacy.__version__,
    url='https://bitbucket.org/x31a/{}'.format(lib_name),
    packages=find_packages(),
    entry_points={
        'console_scripts': [
            '{0} = {0}.__main__:main'.format(lib_name),
        ],
    },
    platforms=['darwin'],
    python_requires='>=3.7',
)

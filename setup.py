from setuptools import setup

import gspreadsheet as app

setup(
    name=app.__name__,
    version=app.__version__,
    description=app.__doc__.strip().splitlines()[0],
    author='The Texas Tribune',
    author_email='cchang@texastribune.org',
    url='http://github.com/crccheck/gspreadsheet/',  # TODO
    license='Apache Software License',
    install_requires=[
        'gdata>=2.0.14',
    ],
    packages=['gspreadsheet'],
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Apache Software License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
    ],
)

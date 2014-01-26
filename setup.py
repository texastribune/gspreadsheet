from setuptools import setup

with open('README.rst') as f:
    long_description = f.read()

setup(
    name="gspreadsheet",
    version="0.4.0",
    description="A wrapper around a wrapper to get Google spreadsheets to look like DictReader",
    long_description=long_description,
    author='The Texas Tribune',
    author_email='cchang@texastribune.org',
    maintainer="Chris Chang",
    url='https://github.com/texastribune/gspreadsheet',
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
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
    ],
)

from setuptools import setup

setup(
    name="gspreadsheet",
    version="0.1.0",
    description="Google Spreadsheets the easy way",
    author='The Texas Tribune',
    author_email='cchang@texastribune.org',
    maintainer="Chris Chang",
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

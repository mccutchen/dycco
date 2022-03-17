import os
from distutils.core import setup


def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()


setup(
    name='dycco',
    version='1.0.2',
    description='Literate-programming-style documentation generator.',
    long_description=read('README.rst'),
    url='https://github.com/mccutchen/dycco',
    license='MIT',
    author='Will McCutchen',
    author_email='will@mccutch.org',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'Intended Audience :: Information Technology',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Topic :: Documentation',
        'Topic :: Software Development :: Documentation',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ],
    packages=['dycco'],
    package_data={
        'dycco': ['resources/*'],
    },
    scripts=['bin/dycco'],
    install_requires=read('requirements.txt').splitlines(),
)

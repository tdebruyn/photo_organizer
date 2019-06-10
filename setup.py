#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from setuptools import setup, find_packages
import os, re

def get_version(package):
    """
    Return package version as listed in `__init__.py`.
    """
    path = os.path.join(os.path.dirname(__file__), package, '__init__.py')
    with open(path, 'rb') as f:
        init_py = f.read().decode('utf-8')
    return re.search("__version__ = ['\"]([^'\"]+)['\"]", init_py).group(1)



with open('README.md') as f:
    readme = f.read()

with open('LICENSE') as f:
    license = f.read()

setup(
    name='photo-organizer',
    version=get_version('photo_organizer'),
    description='Browse through subdirectories for photos to move/rename/delete',
    long_description=readme,
    author='Tom Debruyne',
    url='',
    license=license,
    packages=find_packages(exclude=('tests')),
    install_requires=['PySide2',
                      'Send2Trash'],
    include_package_data=True,
    entry_points = {
        'gui_scripts': [
            'photo_organizer = photo_organizer.main:main',
        ]
    }
)

# Copyright 2017 Verily Life Sciences Inc.
#
# Use of this source code is governed by a BSD-style
# license that can be found in the LICENSE file.

from setuptools import find_packages
from setuptools import setup

REQUIRED_PACKAGES = ['Jinja2==2.8']

setup(
    name='trainer',
    version='0.1',
    install_requires=REQUIRED_PACKAGES,
    packages=find_packages(),
    include_package_data=True,
    description='TensorFlow clustering example',
    requires=[])

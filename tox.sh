#!/bin/bash

# This script runs tox with Python 3.6 and Python 3.7 with pyenv managed virtualenvs.

set +e

original_pyenv=$PYENV_VERSION

# Test with Python 3.6
export PYENV_VERSION=hookery-36
pip install -r requirements.txt
tox -e py36

# Test with Python 3.7
export PYENV_VERSION=hookery-37
pip install -r requirements.txt
tox -e py37

# Set back to current Python
export PYENV_VERSION=${original_pyenv}

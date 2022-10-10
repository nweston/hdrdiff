#!/bin/bash

BASEDIR=$(dirname $(realpath $0))

# Find the virtualenv in the project and activate it. We could use
# "pipenv --venv" or just "pipenv run", but both of those take about
# half a second, which is longer than the actual app startup. So do
# this the hard way to avoid the annoying delay.
. ${BASEDIR}/.venv/bin/activate

python ${BASEDIR}/hdrdiff.py $*

#!/bin/sh

# This is small helper script for git diff.
# You can do something setup git to use wbdiff by
# export GIT_EXTERNAL_DIFF=git-wbdiff.sh
# and then all git diff, will by passed to wbdiff.
# Make sure that everything is in your PATH,
# or update this variable and script accordingly.

path=$1
old_file=$2
old_hex=$3
old_mode=$4
new_file=$5
new_hex=$6
new_mode=$7

exec wbdiff.py -- "${old_file}" "${new_file}"

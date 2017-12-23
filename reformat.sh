#!/bin/sh

set -e

find . -name '*.py' -print0 | xargs -0 -n1 -P8 yapf -i

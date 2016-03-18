#!/usr/bin/env python3
# Copyright (c) 2016 Nuxi, https://nuxi.nl/
#
# This file is distributed under a 2-clause BSD license.
# See the LICENSE file for details.

from src.abi import *
from src.generators.c import *

abi = Abi('cloudabi.txt')

CHeaderGenerator(prefix='cloudabi_').generate_abi(abi)

#!/bin/bash

set -e

SRCDIR="$(cd "$(dirname "$0")" && pwd)"

DIR="$(mktemp -d)"

cd "$DIR"

function cleanup {
	rm -rf "$DIR"
}

trap cleanup EXIT

$SRCDIR/generate_c_headers.py

for m in 32 64; do

x86_64-unknown-cloudabi-cc -m$m -x c -c -fsyntax-only - <<EOF
#include <stdint.h>
#include <stddef.h>

#include "syscalldefs-mi.h"
#include "syscalldefs-md.h"
#include "syscalldefs-md-32.h"
#include "syscalldefs-md-64.h"

#include "syscalls.h"
#include "syscalls-x86_64.h"
EOF

done

aarch64-unknown-cloudabi-cc -x c -c -fsyntax-only - <<EOF
#include <stdint.h>
#include <stddef.h>

#include "syscalldefs-mi.h"
#include "syscalldefs-md.h"
#include "syscalldefs-md-32.h"
#include "syscalldefs-md-64.h"

#include "syscalls.h"
#include "syscalls-aarch64.h"
EOF

echo "Generated C header files compiled succesfully."

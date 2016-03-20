#!/bin/sh

set -e

SRCDIR="$(cd "$(dirname "$0")" && pwd)"

DIR="$(mktemp -d)"

cd "$DIR"

cleanup() {
	rm -rf "$DIR"
}

trap cleanup EXIT

$SRCDIR/generate_c_headers.py

for compiler in x86_64-unknown-cloudabi-cc aarch64-unknown-cloudabi-cc cc 'cc -m32'; do

$compiler -x c -c -fsyntax-only - <<EOF
#include <stdint.h>
#include <stddef.h>

#include "syscalldefs-mi.h"
#include "syscalldefs-md.h"
#include "syscalldefs-md-32.h"
#include "syscalldefs-md-64.h"

#include "syscalls.h"
#ifdef __aarch64__
#include "syscalls-aarch64.h"
#endif
#ifdef __x86_64__
#include "syscalls-x86_64.h"
#endif
EOF

done

echo "Generated C header files compiled succesfully."

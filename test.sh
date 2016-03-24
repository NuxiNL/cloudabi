#!/bin/sh

set -e

SRCDIR="$(cd "$(dirname "$0")" && pwd)"

DIR="$(mktemp -d)"

cd "$DIR"

cleanup() {
	rm -rf "$DIR"
}

trap cleanup EXIT

mkdir headers freebsd docs

$SRCDIR/generate.py

for compiler in x86_64-unknown-cloudabi-cc aarch64-unknown-cloudabi-cc cc 'cc -m32'; do

$compiler -Iheaders -x c -c -fsyntax-only - <<EOF
#include "cloudabi_types.h"
#include "cloudabi32_types.h"
#include "cloudabi64_types.h"
#if defined(__aarch64__)
#include "cloudabi_syscalls_aarch64.h"
#elif defined(__x86_64__)
#include "cloudabi_syscalls_x86_64.h"
#endif
EOF

done

echo "Generated C header files compiled succesfully."

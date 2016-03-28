if exists("b:current_syntax")
	finish
endif

let b:current_syntax = "abi"

syn match abiComment "#.*$"

syn match abiDoc "| .*$" contains=abiDocLink
syn match abiDoc "|$"

syn match abiDocLink '\[[a-zA-Z0-9_.]\+\]' contained

syn match abiDecl '^syscall\s'
syn match abiDecl '^alias\s'
syn match abiDecl '^opaque\s'
syn match abiDecl '^enum\s'
syn match abiDecl '^flags\s'
syn match abiDecl '^function\s'
syn match abiDecl '^\s*struct\s'
syn match abiDecl '^\s*variant\s'

syn match abiAnn '^\s*@cprefix\>'

syn keyword abiType uint8 uint16 uint32 uint64
syn keyword abiType int8 int16 int32 int64
syn keyword abiType char void size
syn keyword abiType range crange ptr cptr array atomic

syn match abiInOut '^\s*in\s*$'
syn match abiInOut '^\s*out\s*$'
syn match abiInOut '^\s*noreturn\s*$'

syn match abiNum '\<\d\+\>'
syn match abiNum '\<0[xX][0-9a-fA-F]\+\>'
syn match abiNum '\<0[oO][0-7]\+\>'
syn match abiNum '\<0[bO][01]\+\>'

hi def link abiComment Comment
hi def link abiDoc Comment
hi def link abiDocLink PreProc
hi def link abiDecl Statement
hi def link abiAnn PreProc
hi def link abiType Type
hi def link abiInOut Statement
hi def link abiNum Constant

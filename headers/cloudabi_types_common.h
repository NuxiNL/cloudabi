// Copyright (c) 2016 Nuxi (https://nuxi.nl/) and contributors.
//
// Redistribution and use in source and binary forms, with or without
// modification, are permitted provided that the following conditions
// are met:
// 1. Redistributions of source code must retain the above copyright
//    notice, this list of conditions and the following disclaimer.
// 2. Redistributions in binary form must reproduce the above copyright
//    notice, this list of conditions and the following disclaimer in the
//    documentation and/or other materials provided with the distribution.
//
// THIS SOFTWARE IS PROVIDED BY THE AUTHOR AND CONTRIBUTORS ``AS IS'' AND
// ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
// IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
// ARE DISCLAIMED.  IN NO EVENT SHALL THE AUTHOR OR CONTRIBUTORS BE LIABLE
// FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
// DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS
// OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION)
// HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
// LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY
// OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF
// SUCH DAMAGE.
//
// This file is automatically generated. Do not edit.
//
// Source: https://github.com/NuxiNL/cloudabi

#ifndef CLOUDABI_TYPES_COMMON_H
#define CLOUDABI_TYPES_COMMON_H

#if defined(__FreeBSD__) && defined(_KERNEL)
#include <sys/stdint.h>
#elif defined(__linux__) && defined(__KERNEL__)
#include <linux/types.h>
#else
#include <stddef.h>
#include <stdint.h>
#endif

typedef uint8_t cloudabi_advice_t;
#define CLOUDABI_ADVICE_DONTNEED   1
#define CLOUDABI_ADVICE_NOREUSE    2
#define CLOUDABI_ADVICE_NORMAL     3
#define CLOUDABI_ADVICE_RANDOM     4
#define CLOUDABI_ADVICE_SEQUENTIAL 5
#define CLOUDABI_ADVICE_WILLNEED   6

typedef uint32_t cloudabi_auxtype_t;
#define CLOUDABI_AT_ARGDATA      256
#define CLOUDABI_AT_ARGDATALEN   257
#define CLOUDABI_AT_BASE           7
#define CLOUDABI_AT_CANARY       258
#define CLOUDABI_AT_CANARYLEN    259
#define CLOUDABI_AT_NCPUS        260
#define CLOUDABI_AT_NULL           0
#define CLOUDABI_AT_PAGESZ         6
#define CLOUDABI_AT_PHDR           3
#define CLOUDABI_AT_PHNUM          4
#define CLOUDABI_AT_SYSINFO_EHDR 262
#define CLOUDABI_AT_TID          261

typedef uint32_t cloudabi_backlog_t;

typedef uint32_t cloudabi_clockid_t;
#define CLOUDABI_CLOCK_MONOTONIC          1
#define CLOUDABI_CLOCK_PROCESS_CPUTIME_ID 2
#define CLOUDABI_CLOCK_REALTIME           3
#define CLOUDABI_CLOCK_THREAD_CPUTIME_ID  4

typedef uint32_t cloudabi_condvar_t;
#define CLOUDABI_CONDVAR_HAS_NO_WAITERS 0

typedef uint64_t cloudabi_device_t;

typedef uint64_t cloudabi_dircookie_t;
#define CLOUDABI_DIRCOOKIE_START 0

typedef uint16_t cloudabi_errno_t;
#define CLOUDABI_E2BIG            1
#define CLOUDABI_EACCES           2
#define CLOUDABI_EADDRINUSE       3
#define CLOUDABI_EADDRNOTAVAIL    4
#define CLOUDABI_EAFNOSUPPORT     5
#define CLOUDABI_EAGAIN           6
#define CLOUDABI_EALREADY         7
#define CLOUDABI_EBADF            8
#define CLOUDABI_EBADMSG          9
#define CLOUDABI_EBUSY           10
#define CLOUDABI_ECANCELED       11
#define CLOUDABI_ECHILD          12
#define CLOUDABI_ECONNABORTED    13
#define CLOUDABI_ECONNREFUSED    14
#define CLOUDABI_ECONNRESET      15
#define CLOUDABI_EDEADLK         16
#define CLOUDABI_EDESTADDRREQ    17
#define CLOUDABI_EDOM            18
#define CLOUDABI_EDQUOT          19
#define CLOUDABI_EEXIST          20
#define CLOUDABI_EFAULT          21
#define CLOUDABI_EFBIG           22
#define CLOUDABI_EHOSTUNREACH    23
#define CLOUDABI_EIDRM           24
#define CLOUDABI_EILSEQ          25
#define CLOUDABI_EINPROGRESS     26
#define CLOUDABI_EINTR           27
#define CLOUDABI_EINVAL          28
#define CLOUDABI_EIO             29
#define CLOUDABI_EISCONN         30
#define CLOUDABI_EISDIR          31
#define CLOUDABI_ELOOP           32
#define CLOUDABI_EMFILE          33
#define CLOUDABI_EMLINK          34
#define CLOUDABI_EMSGSIZE        35
#define CLOUDABI_EMULTIHOP       36
#define CLOUDABI_ENAMETOOLONG    37
#define CLOUDABI_ENETDOWN        38
#define CLOUDABI_ENETRESET       39
#define CLOUDABI_ENETUNREACH     40
#define CLOUDABI_ENFILE          41
#define CLOUDABI_ENOBUFS         42
#define CLOUDABI_ENODEV          43
#define CLOUDABI_ENOENT          44
#define CLOUDABI_ENOEXEC         45
#define CLOUDABI_ENOLCK          46
#define CLOUDABI_ENOLINK         47
#define CLOUDABI_ENOMEM          48
#define CLOUDABI_ENOMSG          49
#define CLOUDABI_ENOPROTOOPT     50
#define CLOUDABI_ENOSPC          51
#define CLOUDABI_ENOSYS          52
#define CLOUDABI_ENOTCONN        53
#define CLOUDABI_ENOTDIR         54
#define CLOUDABI_ENOTEMPTY       55
#define CLOUDABI_ENOTRECOVERABLE 56
#define CLOUDABI_ENOTSOCK        57
#define CLOUDABI_ENOTSUP         58
#define CLOUDABI_ENOTTY          59
#define CLOUDABI_ENXIO           60
#define CLOUDABI_EOVERFLOW       61
#define CLOUDABI_EOWNERDEAD      62
#define CLOUDABI_EPERM           63
#define CLOUDABI_EPIPE           64
#define CLOUDABI_EPROTO          65
#define CLOUDABI_EPROTONOSUPPORT 66
#define CLOUDABI_EPROTOTYPE      67
#define CLOUDABI_ERANGE          68
#define CLOUDABI_EROFS           69
#define CLOUDABI_ESPIPE          70
#define CLOUDABI_ESRCH           71
#define CLOUDABI_ESTALE          72
#define CLOUDABI_ETIMEDOUT       73
#define CLOUDABI_ETXTBSY         74
#define CLOUDABI_EXDEV           75
#define CLOUDABI_ENOTCAPABLE     76

typedef uint16_t cloudabi_eventrwflags_t;
#define CLOUDABI_EVENT_FD_READWRITE_HANGUP 0x0001

typedef uint8_t cloudabi_eventtype_t;
#define CLOUDABI_EVENTTYPE_CLOCK          1
#define CLOUDABI_EVENTTYPE_CONDVAR        2
#define CLOUDABI_EVENTTYPE_FD_READ        3
#define CLOUDABI_EVENTTYPE_FD_WRITE       4
#define CLOUDABI_EVENTTYPE_LOCK_RDLOCK    5
#define CLOUDABI_EVENTTYPE_LOCK_WRLOCK    6
#define CLOUDABI_EVENTTYPE_PROC_TERMINATE 7

typedef uint32_t cloudabi_exitcode_t;

typedef uint32_t cloudabi_fd_t;
#define CLOUDABI_PROCESS_CHILD 0xffffffff
#define CLOUDABI_MAP_ANON_FD   0xffffffff

typedef uint16_t cloudabi_fdflags_t;
#define CLOUDABI_FDFLAG_APPEND   0x0001
#define CLOUDABI_FDFLAG_DSYNC    0x0002
#define CLOUDABI_FDFLAG_NONBLOCK 0x0004
#define CLOUDABI_FDFLAG_RSYNC    0x0008
#define CLOUDABI_FDFLAG_SYNC     0x0010

typedef uint16_t cloudabi_fdsflags_t;
#define CLOUDABI_FDSTAT_FLAGS  0x0001
#define CLOUDABI_FDSTAT_RIGHTS 0x0002

typedef int64_t cloudabi_filedelta_t;

typedef uint64_t cloudabi_filesize_t;

typedef uint8_t cloudabi_filetype_t;
#define CLOUDABI_FILETYPE_UNKNOWN            0
#define CLOUDABI_FILETYPE_BLOCK_DEVICE      16
#define CLOUDABI_FILETYPE_CHARACTER_DEVICE  17
#define CLOUDABI_FILETYPE_DIRECTORY         32
#define CLOUDABI_FILETYPE_FIFO              48
#define CLOUDABI_FILETYPE_POLL              64
#define CLOUDABI_FILETYPE_PROCESS           80
#define CLOUDABI_FILETYPE_REGULAR_FILE      96
#define CLOUDABI_FILETYPE_SHARED_MEMORY    112
#define CLOUDABI_FILETYPE_SOCKET_DGRAM     128
#define CLOUDABI_FILETYPE_SOCKET_SEQPACKET 129
#define CLOUDABI_FILETYPE_SOCKET_STREAM    130
#define CLOUDABI_FILETYPE_SYMBOLIC_LINK    144

typedef uint16_t cloudabi_fsflags_t;
#define CLOUDABI_FILESTAT_ATIM     0x0001
#define CLOUDABI_FILESTAT_ATIM_NOW 0x0002
#define CLOUDABI_FILESTAT_MTIM     0x0004
#define CLOUDABI_FILESTAT_MTIM_NOW 0x0008
#define CLOUDABI_FILESTAT_SIZE     0x0010

typedef uint64_t cloudabi_inode_t;

typedef uint32_t cloudabi_linkcount_t;

typedef uint32_t cloudabi_lock_t;
#define CLOUDABI_LOCK_UNLOCKED       0x00000000
#define CLOUDABI_LOCK_WRLOCKED       0x40000000
#define CLOUDABI_LOCK_KERNEL_MANAGED 0x80000000
#define CLOUDABI_LOCK_BOGUS          0x80000000

typedef uint32_t cloudabi_lookupflags_t;
#define CLOUDABI_LOOKUP_SYMLINK_FOLLOW 0x00000001

typedef uint8_t cloudabi_mflags_t;
#define CLOUDABI_MAP_ANON    0x01
#define CLOUDABI_MAP_FIXED   0x02
#define CLOUDABI_MAP_PRIVATE 0x04
#define CLOUDABI_MAP_SHARED  0x08

typedef uint8_t cloudabi_mprot_t;
#define CLOUDABI_PROT_EXEC  0x01
#define CLOUDABI_PROT_WRITE 0x02
#define CLOUDABI_PROT_READ  0x04

typedef uint8_t cloudabi_msflags_t;
#define CLOUDABI_MS_ASYNC      0x01
#define CLOUDABI_MS_INVALIDATE 0x02
#define CLOUDABI_MS_SYNC       0x04

typedef uint16_t cloudabi_msgflags_t;
#define CLOUDABI_MSG_CTRUNC  0x0001
#define CLOUDABI_MSG_EOR     0x0002
#define CLOUDABI_MSG_PEEK    0x0004
#define CLOUDABI_MSG_TRUNC   0x0008
#define CLOUDABI_MSG_WAITALL 0x0010

typedef uint32_t cloudabi_nthreads_t;

typedef uint16_t cloudabi_oflags_t;
#define CLOUDABI_O_CREAT     0x0001
#define CLOUDABI_O_DIRECTORY 0x0002
#define CLOUDABI_O_EXCL      0x0004
#define CLOUDABI_O_TRUNC     0x0008

typedef uint64_t cloudabi_rights_t;
#define CLOUDABI_RIGHT_FD_DATASYNC            0x0000000000000001
#define CLOUDABI_RIGHT_FD_READ                0x0000000000000002
#define CLOUDABI_RIGHT_FD_SEEK                0x0000000000000004
#define CLOUDABI_RIGHT_FD_STAT_PUT_FLAGS      0x0000000000000008
#define CLOUDABI_RIGHT_FD_SYNC                0x0000000000000010
#define CLOUDABI_RIGHT_FD_TELL                0x0000000000000020
#define CLOUDABI_RIGHT_FD_WRITE               0x0000000000000040
#define CLOUDABI_RIGHT_FILE_ADVISE            0x0000000000000080
#define CLOUDABI_RIGHT_FILE_ALLOCATE          0x0000000000000100
#define CLOUDABI_RIGHT_FILE_CREATE_DIRECTORY  0x0000000000000200
#define CLOUDABI_RIGHT_FILE_CREATE_FILE       0x0000000000000400
#define CLOUDABI_RIGHT_FILE_CREATE_FIFO       0x0000000000000800
#define CLOUDABI_RIGHT_FILE_LINK_SOURCE       0x0000000000001000
#define CLOUDABI_RIGHT_FILE_LINK_TARGET       0x0000000000002000
#define CLOUDABI_RIGHT_FILE_OPEN              0x0000000000004000
#define CLOUDABI_RIGHT_FILE_READDIR           0x0000000000008000
#define CLOUDABI_RIGHT_FILE_READLINK          0x0000000000010000
#define CLOUDABI_RIGHT_FILE_RENAME_SOURCE     0x0000000000020000
#define CLOUDABI_RIGHT_FILE_RENAME_TARGET     0x0000000000040000
#define CLOUDABI_RIGHT_FILE_STAT_FGET         0x0000000000080000
#define CLOUDABI_RIGHT_FILE_STAT_FPUT_SIZE    0x0000000000100000
#define CLOUDABI_RIGHT_FILE_STAT_FPUT_TIMES   0x0000000000200000
#define CLOUDABI_RIGHT_FILE_STAT_GET          0x0000000000400000
#define CLOUDABI_RIGHT_FILE_STAT_PUT_TIMES    0x0000000000800000
#define CLOUDABI_RIGHT_FILE_SYMLINK           0x0000000001000000
#define CLOUDABI_RIGHT_FILE_UNLINK            0x0000000002000000
#define CLOUDABI_RIGHT_MEM_MAP                0x0000000004000000
#define CLOUDABI_RIGHT_MEM_MAP_EXEC           0x0000000008000000
#define CLOUDABI_RIGHT_POLL_FD_READWRITE      0x0000000010000000
#define CLOUDABI_RIGHT_POLL_MODIFY            0x0000000020000000
#define CLOUDABI_RIGHT_POLL_PROC_TERMINATE    0x0000000040000000
#define CLOUDABI_RIGHT_POLL_WAIT              0x0000000080000000
#define CLOUDABI_RIGHT_PROC_EXEC              0x0000000100000000
#define CLOUDABI_RIGHT_SOCK_ACCEPT            0x0000000200000000
#define CLOUDABI_RIGHT_SOCK_BIND_DIRECTORY    0x0000000400000000
#define CLOUDABI_RIGHT_SOCK_BIND_SOCKET       0x0000000800000000
#define CLOUDABI_RIGHT_SOCK_CONNECT_DIRECTORY 0x0000001000000000
#define CLOUDABI_RIGHT_SOCK_CONNECT_SOCKET    0x0000002000000000
#define CLOUDABI_RIGHT_SOCK_LISTEN            0x0000004000000000
#define CLOUDABI_RIGHT_SOCK_SHUTDOWN          0x0000008000000000
#define CLOUDABI_RIGHT_SOCK_STAT_GET          0x0000010000000000

typedef uint8_t cloudabi_sa_family_t;
#define CLOUDABI_AF_UNSPEC 0
#define CLOUDABI_AF_INET   1
#define CLOUDABI_AF_INET6  2
#define CLOUDABI_AF_UNIX   3

typedef uint8_t cloudabi_scope_t;
#define CLOUDABI_SCOPE_PRIVATE 4
#define CLOUDABI_SCOPE_SHARED  8

typedef uint8_t cloudabi_sdflags_t;
#define CLOUDABI_SHUT_RD 0x01
#define CLOUDABI_SHUT_WR 0x02

typedef uint8_t cloudabi_signal_t;
#define CLOUDABI_SIGABRT    1
#define CLOUDABI_SIGALRM    2
#define CLOUDABI_SIGBUS     3
#define CLOUDABI_SIGCHLD    4
#define CLOUDABI_SIGCONT    5
#define CLOUDABI_SIGFPE     6
#define CLOUDABI_SIGHUP     7
#define CLOUDABI_SIGILL     8
#define CLOUDABI_SIGINT     9
#define CLOUDABI_SIGKILL   10
#define CLOUDABI_SIGPIPE   11
#define CLOUDABI_SIGQUIT   12
#define CLOUDABI_SIGSEGV   13
#define CLOUDABI_SIGSTOP   14
#define CLOUDABI_SIGSYS    15
#define CLOUDABI_SIGTERM   16
#define CLOUDABI_SIGTRAP   17
#define CLOUDABI_SIGTSTP   18
#define CLOUDABI_SIGTTIN   19
#define CLOUDABI_SIGTTOU   20
#define CLOUDABI_SIGURG    21
#define CLOUDABI_SIGUSR1   22
#define CLOUDABI_SIGUSR2   23
#define CLOUDABI_SIGVTALRM 24
#define CLOUDABI_SIGXCPU   25
#define CLOUDABI_SIGXFSZ   26

typedef uint8_t cloudabi_ssflags_t;
#define CLOUDABI_SOCKSTAT_CLEAR_ERROR 0x01

typedef uint32_t cloudabi_sstate_t;
#define CLOUDABI_SOCKSTATE_ACCEPTCONN 0x00000001

typedef uint16_t cloudabi_subclockflags_t;
#define CLOUDABI_SUBSCRIPTION_CLOCK_ABSTIME 0x0001

typedef uint16_t cloudabi_subflags_t;
#define CLOUDABI_SUBSCRIPTION_ADD     0x0001
#define CLOUDABI_SUBSCRIPTION_CLEAR   0x0002
#define CLOUDABI_SUBSCRIPTION_DELETE  0x0004
#define CLOUDABI_SUBSCRIPTION_DISABLE 0x0008
#define CLOUDABI_SUBSCRIPTION_ENABLE  0x0010
#define CLOUDABI_SUBSCRIPTION_ONESHOT 0x0020

typedef uint16_t cloudabi_subrwflags_t;
#define CLOUDABI_SUBSCRIPTION_FD_READWRITE_POLL 0x0001

typedef uint32_t cloudabi_tid_t;

typedef uint64_t cloudabi_timestamp_t;

typedef uint8_t cloudabi_ulflags_t;
#define CLOUDABI_UNLINK_REMOVEDIR 0x01

typedef uint64_t cloudabi_userdata_t;

typedef uint8_t cloudabi_whence_t;
#define CLOUDABI_WHENCE_CUR 1
#define CLOUDABI_WHENCE_END 2
#define CLOUDABI_WHENCE_SET 3

typedef struct {
	_Alignas(8) cloudabi_dircookie_t d_next;
	_Alignas(8) cloudabi_inode_t d_ino;
	_Alignas(4) uint32_t d_namlen;
	_Alignas(1) cloudabi_filetype_t d_type;
} cloudabi_dirent_t;
_Static_assert(offsetof(cloudabi_dirent_t, d_next) == 0, "Incorrect layout");
_Static_assert(offsetof(cloudabi_dirent_t, d_ino) == 8, "Incorrect layout");
_Static_assert(offsetof(cloudabi_dirent_t, d_namlen) == 16, "Incorrect layout");
_Static_assert(offsetof(cloudabi_dirent_t, d_type) == 20, "Incorrect layout");
_Static_assert(sizeof(cloudabi_dirent_t) == 24, "Incorrect layout");
_Static_assert(_Alignof(cloudabi_dirent_t) == 8, "Incorrect layout");

typedef struct {
	_Alignas(1) cloudabi_filetype_t fs_filetype;
	_Alignas(2) cloudabi_fdflags_t fs_flags;
	_Alignas(8) cloudabi_rights_t fs_rights_base;
	_Alignas(8) cloudabi_rights_t fs_rights_inheriting;
} cloudabi_fdstat_t;
_Static_assert(offsetof(cloudabi_fdstat_t, fs_filetype) == 0, "Incorrect layout");
_Static_assert(offsetof(cloudabi_fdstat_t, fs_flags) == 2, "Incorrect layout");
_Static_assert(offsetof(cloudabi_fdstat_t, fs_rights_base) == 8, "Incorrect layout");
_Static_assert(offsetof(cloudabi_fdstat_t, fs_rights_inheriting) == 16, "Incorrect layout");
_Static_assert(sizeof(cloudabi_fdstat_t) == 24, "Incorrect layout");
_Static_assert(_Alignof(cloudabi_fdstat_t) == 8, "Incorrect layout");

typedef struct {
	_Alignas(8) cloudabi_device_t st_dev;
	_Alignas(8) cloudabi_inode_t st_ino;
	_Alignas(1) cloudabi_filetype_t st_filetype;
	_Alignas(4) cloudabi_linkcount_t st_nlink;
	_Alignas(8) cloudabi_filesize_t st_size;
	_Alignas(8) cloudabi_timestamp_t st_atim;
	_Alignas(8) cloudabi_timestamp_t st_mtim;
	_Alignas(8) cloudabi_timestamp_t st_ctim;
} cloudabi_filestat_t;
_Static_assert(offsetof(cloudabi_filestat_t, st_dev) == 0, "Incorrect layout");
_Static_assert(offsetof(cloudabi_filestat_t, st_ino) == 8, "Incorrect layout");
_Static_assert(offsetof(cloudabi_filestat_t, st_filetype) == 16, "Incorrect layout");
_Static_assert(offsetof(cloudabi_filestat_t, st_nlink) == 20, "Incorrect layout");
_Static_assert(offsetof(cloudabi_filestat_t, st_size) == 24, "Incorrect layout");
_Static_assert(offsetof(cloudabi_filestat_t, st_atim) == 32, "Incorrect layout");
_Static_assert(offsetof(cloudabi_filestat_t, st_mtim) == 40, "Incorrect layout");
_Static_assert(offsetof(cloudabi_filestat_t, st_ctim) == 48, "Incorrect layout");
_Static_assert(sizeof(cloudabi_filestat_t) == 56, "Incorrect layout");
_Static_assert(_Alignof(cloudabi_filestat_t) == 8, "Incorrect layout");

typedef struct {
	_Alignas(4) cloudabi_fd_t fd;
	_Alignas(4) cloudabi_lookupflags_t flags;
} cloudabi_lookup_t;
_Static_assert(offsetof(cloudabi_lookup_t, fd) == 0, "Incorrect layout");
_Static_assert(offsetof(cloudabi_lookup_t, flags) == 4, "Incorrect layout");
_Static_assert(sizeof(cloudabi_lookup_t) == 8, "Incorrect layout");
_Static_assert(_Alignof(cloudabi_lookup_t) == 4, "Incorrect layout");

typedef struct {
	_Alignas(1) cloudabi_sa_family_t sa_family;
	union {
		struct {
			_Alignas(1) uint8_t addr[4];
			_Alignas(2) uint16_t port;
		} sa_inet;
		struct {
			_Alignas(1) uint8_t addr[16];
			_Alignas(2) uint16_t port;
		} sa_inet6;
	};
} cloudabi_sockaddr_t;
_Static_assert(offsetof(cloudabi_sockaddr_t, sa_family) == 0, "Incorrect layout");
_Static_assert(offsetof(cloudabi_sockaddr_t, sa_inet.addr) == 2, "Incorrect layout");
_Static_assert(offsetof(cloudabi_sockaddr_t, sa_inet.port) == 6, "Incorrect layout");
_Static_assert(offsetof(cloudabi_sockaddr_t, sa_inet6.addr) == 2, "Incorrect layout");
_Static_assert(offsetof(cloudabi_sockaddr_t, sa_inet6.port) == 18, "Incorrect layout");
_Static_assert(sizeof(cloudabi_sockaddr_t) == 20, "Incorrect layout");
_Static_assert(_Alignof(cloudabi_sockaddr_t) == 2, "Incorrect layout");

typedef struct {
	_Alignas(2) cloudabi_sockaddr_t ss_sockname;
	_Alignas(2) cloudabi_sockaddr_t ss_peername;
	_Alignas(2) cloudabi_errno_t ss_error;
	_Alignas(4) cloudabi_sstate_t ss_state;
} cloudabi_sockstat_t;
_Static_assert(offsetof(cloudabi_sockstat_t, ss_sockname) == 0, "Incorrect layout");
_Static_assert(offsetof(cloudabi_sockstat_t, ss_peername) == 20, "Incorrect layout");
_Static_assert(offsetof(cloudabi_sockstat_t, ss_error) == 40, "Incorrect layout");
_Static_assert(offsetof(cloudabi_sockstat_t, ss_state) == 44, "Incorrect layout");
_Static_assert(sizeof(cloudabi_sockstat_t) == 48, "Incorrect layout");
_Static_assert(_Alignof(cloudabi_sockstat_t) == 4, "Incorrect layout");

#endif

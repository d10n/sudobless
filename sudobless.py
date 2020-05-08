#!/usr/bin/env python

import ctypes
import os
import pwd
import sys
import time


def usage():
    print('Usage: sudobless <pid of shell>', file=sys.stderr)
    sys.exit(1)


try:
    if not int(sys.argv[1]):
        usage()
except Exception:
    usage()

pid = int(sys.argv[1])
VERBOSE = 'VERBOSE' in os.environ
DRY_RUN = 'DRY_RUN' in os.environ

TS_GLOBAL = 0x01
TS_TTY = 0x02
TS_PPID = 0x03
TS_LOCKEXCL = 0x04
TS_DISABLED = 0x01
TS_ANYUID = 0x02


def flags_to_string(teflags):
    flags = teflags
    out = []
    if flags & TS_DISABLED:
        out.append('TS_DISABLED')
        flags &= ~TS_DISABLED
    if flags & TS_ANYUID:
        out.append('TS_ANYUID')
        flags &= ~TS_ANYUID
    if flags:
        out.append('0x{:X}'.format(flags))
    return ', '.join(out)


def ttydev_to_string(ttydev):
    pretty_name = '{}:{}'.format(os.major(ttydev), os.minor(ttydev))
    for pts in ['/dev/pts/{}'.format(os.minor(ttydev))]:  # glob.iglob('/dev/pts/*'):
        try:
            pts_stat = os.lstat(pts)
            if pts_stat.st_rdev == ttydev:
                pretty_name = pts[len('/dev/'):]
                break
        except FileNotFoundError:
            pass
    return '{} ({})'.format(ttydev, pretty_name)


class TimestampU(ctypes.Union):
    _fields_ = [
        ('ttydev', ctypes.c_ulong),
        ('ppid', ctypes.c_int)
    ]


class Timespec(ctypes.Structure):
    _fields_ = [
        ('tv_sec', ctypes.c_long),
        ('tv_nsec', ctypes.c_long)
    ]


class TimestampEntry(ctypes.Structure):
    """ sudo timestamp """
    _fields_ = [
        ('version', ctypes.c_ushort),
        ('size', ctypes.c_ushort),
        ('type', ctypes.c_ushort),
        ('flags', ctypes.c_ushort),
        ('auth_uid', ctypes.c_int),
        ('sid', ctypes.c_uint),
        ('start_time', Timespec),
        ('ts', Timespec),
        ('u', TimestampU),
    ]

    def print(self):
        print('version:', self.version)
        print('size:', self.size)
        print('type:', self.type)
        print('flags:', flags_to_string(self.flags))
        print('auth uid:', self.auth_uid)
        print('session ID:', self.sid)
        print('start time (sec):', self.start_time.tv_sec)
        print('start time (nsec):', self.start_time.tv_nsec)
        print('time stamp (sec):', self.ts.tv_sec)
        print('time stamp (nsec):', self.ts.tv_nsec)
        print('tty:', ttydev_to_string(self.u.ttydev))
        print('parent pid:', self.u.ppid)
        print()


stat_info = os.lstat('/proc/{}'.format(pid))
uid = stat_info.st_uid

with open('/proc/{}/stat'.format(pid), 'r') as stat_fd:  # man procfs
    stat_fields = stat_fd.read().split(' ')
    ppid = int(stat_fields[3])  # 4th field

    sid = int(stat_fields[5])  # 6th field

    tty_nr = int(stat_fields[6])  # 7th field
    tty_maj = os.major(tty_nr)
    tty_min = os.minor(tty_nr)

    ticks = int(stat_fields[21])  # 22nd field
    ticks_per_second = os.sysconf(os.sysconf_names['SC_CLK_TCK'])
    start_time_tv_sec = ticks // ticks_per_second
    start_time_tv_nsec = ((ticks % ticks_per_second) * (1000000000 // ticks_per_second))

if tty_nr == 0:
    usage()

with open('/var/run/sudo/ts/{}'.format(pwd.getpwuid(uid).pw_name), 'r+b') as f:
    entry_number = 0
    te = TimestampEntry()
    found_entry = False
    while f.peek() and not found_entry:
        f.readinto(te)
        entry_number += 1
        if VERBOSE:
            print('position: ', entry_number)
            te.print()
        if te.u.ttydev == tty_nr and te.sid == sid:
            found_entry = True
    if found_entry:
        f.seek(-(ctypes.sizeof(te)), os.SEEK_CUR)

    te.version = 2
    te.size = ctypes.sizeof(te)
    te.flags = 0
    te.auth_uid = uid

    te.type = TS_TTY
    te.sid = sid
    te.u.ttydev = tty_nr

    te.start_time.tv_sec = start_time_tv_sec
    te.start_time.tv_nsec = start_time_tv_nsec

    gettime_ns = time.clock_gettime_ns(time.CLOCK_BOOTTIME)
    te.ts.tv_sec = gettime_ns // 1000000000
    te.ts.tv_nsec = gettime_ns - ((gettime_ns // 1000000000) * 1000000000)

    if VERBOSE:
        print('writing:')
        print('position: ', (f.tell() // te.size) + 1)
        te.print()
    if not DRY_RUN:
        f.write(te)

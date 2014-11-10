#!/usr/bin/env python
"""
vncauthproxy-passwd - vncauthproxy passwd file mgmt tool
"""
#
# Copyright (c) 2010-2013 Greek Research and Technology Network S.A.
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA
# 02110-1301, USA.

import argparse
import crypt
import getpass
import os
import random
import re
import string
import sys
import tempfile


def parse_arguments():
    """ Parse cli args. """
    parser = argparse.ArgumentParser()

    parser.add_argument("-n", "--dry-run", action="store_true", dest="dry_run",
                        help="Display the results on stdout without updating "
                        "the passwd file")
    parser.add_argument("-d", "--delete", action="store_true",
                        dest="delete_user", help="delete user from file")
    parser.add_argument("-p", "--password", dest="password",
                        metavar='PASSWORD', default=None,
                        help="use cli-provided password")
    parser.add_argument("passwdfile", metavar="file", type=str, nargs=1,
                        help="Path to the passwd file")
    parser.add_argument("user", metavar="user", type=str, nargs=1,
                        help="User to edit")

    args = parser.parse_args()

    if args.delete_user is True and args.password is not None:
        parser.print_help()
        fail("Cannot specify -d and -p opts at the same time")

    return args


def gen_salt():
    """ Generate 16-char salt string. """
    chars = list(string.ascii_letters + string.digits + "./")
    return "".join(random.choice(chars) for x in range(16))


def gen_hash(username, password):
    """ Generate SHA-512 hash in crypt() format. """
    salt = "$6$%s$" % gen_salt()
    return "%s:%s\n" % (username, crypt.crypt(password, salt))


def fail(reason):
    """ Print reason for failure and exit. """
    sys.stderr.write("%s\n" % reason)
    sys.exit(1)


def find_user(lines, user):
    """ Return user info from passwd file, if the users exists. """
    for (idx, line) in enumerate(lines):
        (username, _) = line.split(":", 1)
        if user == username:
            return (idx, line)

    return None


def write_wrapper(passwdfile, lines, dry_run):
    """ Dry-run wrapper for write. """
    if not dry_run:
        (fd, fpath) = tempfile.mkstemp(dir=os.path.dirname(passwdfile))
        with os.fdopen(fd, "w+") as f:
            f.write("".join(lines))
        os.rename(fpath, passwdfile)
    else:
        sys.stdout.write("".join(lines))


def delete_user(user, passwdfile):
    """ Delete user from passwdfile. """
    if not os.path.isfile(passwdfile):
        fail("Cannot delete user from non-existent file")

    lines = open(passwdfile).readlines()
    user_line = find_user(lines, user)
    if not user_line:
        fail("User not found!")

    (_, line) = user_line
    lines.remove(line)
    return lines


def add_or_update_user(user, passwdfile, password):
    """ Add or update user from passwdfile. """
    if password is None:
        password = getpass.getpass()
        if password == "":
            fail("Password cannot be empty")

    newline = gen_hash(user, password)

    lines = [newline]
    if os.path.isfile(passwdfile):
        lines = open(passwdfile).readlines()
        user_line = find_user(lines, user)
        if not user_line:
            lines.append(newline)
        else:
            (idx, _) = user_line
            lines[idx] = newline

    return lines


def main():
    """ Run the tool from the command line. """
    try:
        args = parse_arguments()

        user = args.user[0]
        passwdfile = args.passwdfile[0]
        password = args.password

        user_re = r'^[a-z_][a-z0-9_]{0,30}$'
        if re.match(user_re, user) is None:
            fail("Username must match the following regexp: %s" % user_re)

        if args.delete_user:
            lines = delete_user(user, passwdfile)
        else:
            lines = add_or_update_user(user, passwdfile, password)

        write_wrapper(passwdfile, lines, args.dry_run)
    except KeyboardInterrupt:
        pass

    sys.exit(0)

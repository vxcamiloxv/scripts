#!/usr/bin/python2

import re
import os
import subprocess


def set_credentials(repo, user, pw):
    KEYRING_NAME = "offlineimap"
    attrs = {"repo": repo, "user": user}
    # keyring = gkey.get_default_keyring_sync()
    # gkey.item_create_sync(keyring, gkey.ITEM_NETWORK_PASSWORD,
    #                      KEYRING_NAME, attrs, pw, True)


def get_credentials(account, port):
    s = "machine %s ([^ ]*) (.*) port %s password ([^ ]*)\n" \
        % (account, port)
    p = re.compile(s)
    authinfo = os.popen("gpg -q --no-tty -d ~/.authinfo.gpg").read()
    return p.search(authinfo).group(1)


def get_username(account, port):
    return get_credentials(account, port)

def get_password(machine, login, port):
    s = "machine %s login %s port %s password ([^ ]*)\n" \
        % (machine, login, port)
    p = re.compile(s)
    authinfo = os.popen("gpg -q --no-tty -d ~/.authinfo.gpg").read()
    return p.search(authinfo).group(1)

def get_password_emacs(machine, account, port):
    return get_password(machine, account, port)

if __name__ == "__main__":
    import sys
    import getpass
    if len(sys.argv) != 3:
        print "Usage: %s <repository> <username>" \
            % (os.path.basename(sys.argv[0]))
        sys.exit(0)
    repo, username = sys.argv[1:]
    password = getpass.getpass("Enter password for user '%s': " % username)
    password_confirmation = getpass.getpass("Confirm password: ")
    if password != password_confirmation:
        print "Error: password confirmation does not match"
        sys.exit(1)
    set_credentials(repo, username, password)

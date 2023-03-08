#!/usr/bin/env python3
#
# Description: Proof-of-concept LSF/SSH dynamic access daemon
# Author: Phil Fox
# Date: 30Mar2022
#
# NOTES:
# lsfadmin group always has SSH access
# lsfusers group manages dynamic access
# lsfusers group needs to be added manually prior to execution
#
# The following line needs to be added to /etc/ssh/sshd_config:
# AllowGroups lsfadmin lsfusers

import time
import os

DEBUG = True
INTERVAL = 2

# Very minimal logging function
def mprint(*args):
    if DEBUG:
        print(*args)

while True:

    mprint('START CYCLE')

    # Get list of job owners for jobs on this host
    stream = os.popen("bjobs -w -u all -m $(hostname) 2>/dev/null| tail -n +2 | awk '{print $2}' | uniq")
    valid_users = stream.readlines()
    stream.close()

    # Get list of users with SSH access already enabled
    stream = os.popen("grep lsfusers /etc/group | awk -F: '{print $4}' | tr ',' '\n'")
    group_users = stream.readlines()
    stream.close()

    # Remove EOLs and spurious blank space from all entries
    valid_users = [user.strip() for user in valid_users]
    group_users = [user.strip() for user in group_users]

    remove_list = list()
    add_list = list()

    # Identify users that need to be removed from 'lsfusers'
    for user in group_users:
        if user:
            if user in valid_users:
                mprint('user "{}" already has access'.format(user))
            else:
                mprint('user "{}" needs access removed'.format(user))
                remove_list.append(user)

    # Identify users that need to be added to 'lsfusers'
    for user in valid_users:
        if user:
            if user in group_users:
                mprint('user "{}" already has access'.format(user))
            else:
                mprint('user "{}" needs access added'.format(user))
                add_list.append(user)

    # Delete users that are no longer running jobs on this host
    for user in remove_list:
        mprint('removing access for user "{}"'.format(user))
        cmd = 'sudo gpasswd -d {} lsfusers'.format(user)
        stream = os.popen(cmd)
        output = stream.read()
        mprint('output:', output.strip())
        stream.close()

    # Add users that are now running jobs on this host
    for user in add_list:
        mprint('adding access for user "{}"'.format(user))
        cmd = 'sudo gpasswd -a {} lsfusers'.format(user)
        stream = os.popen(cmd)
        output = stream.read()
        mprint('output:', output.strip())
        stream.close()
        
    # Rinse and repeat
    time.sleep(INTERVAL)
    mprint('END CYCLE\n')


#!/usr/bin/env python3


def run_cmd(cmd):
    """ Utility that gets the first line from a cmd launched on a shell """
    pipe = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)
    output = pipe.communicate()[0]
    return str(output)
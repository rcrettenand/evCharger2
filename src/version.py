#!/usr/bin/env python
# -*- coding: utf-8 -*-

__author__ = 'Aurelien Heritier'
__contributors__ = ['Martin Meyer']
__version__ = '2.0.0'


def githash():
    try:
        # get in the HEAD file the path of the actual commit
        with open('../.git/HEAD', 'r') as f:
            file = f.read().strip().split()[1]

            # get in the commit file the hash number
            with open(f'../.git/{file}', 'r') as file2:
                return file2.read().strip()[:8]
    except:
        return "not a git repo"


if __name__ == '__main__':
    print(__version__)
    print(githash())

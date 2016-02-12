#!/usr/bin/env python
import sys

from isort.hooks import git_hook

if __name__ == '__main__':
    sys.exit(git_hook(strict=True))

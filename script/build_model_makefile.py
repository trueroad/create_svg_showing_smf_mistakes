#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Build model makefile.

https://github.com/trueroad/create_svg_showing_smf_mistakes

Copyright (C) 2025 Masamichi Hosoda.
All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions
are met:

* Redistributions of source code must retain the above copyright notice,
  this list of conditions and the following disclaimer.

* Redistributions in binary form must reproduce the above copyright notice,
  this list of conditions and the following disclaimer in the documentation
  and/or other materials provided with the distribution.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
ARE DISCLAIMED.
IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS
OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION)
HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY
OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF
SUCH DAMAGE.
"""

import os
from pathlib import Path
import sys
from typing import Final


REPLACE_STR: Final[str] = '@MAKE_DIR@'
MAKEFILE_FILENAME: Final[Path] = Path('Makefile')
GITIGNORE_FILENAME: Final[Path] = Path('.gitignore')


def relative_to_walk_up(start: Path, target: Path) -> Path:
    """Relative to with walk up."""
    # Python 3.12
    # return target.relative_to(start, walk_up=True)

    # Python 3.9
    walk_up = Path('.')
    while len(walk_up.parts) < 64:
        try:
            r = target.resolve().relative_to((start / walk_up).resolve())
        except ValueError as e:
            walk_up = walk_up / '..'
            continue
        return walk_up / r
    raise ValueError('Exceed limit')


def main() -> None:
    """Do main."""
    if len(sys.argv) != 4:
        print('Usage: ./build_model_makefile.py '
              '(in)TEMPLATE.mk MAKE_DIR MODEL_DIR')
        sys.exit(1)

    template_filename = Path(sys.argv[1])
    make_dir = Path(sys.argv[2]).resolve()
    makefile_dir = Path(sys.argv[3]).resolve()

    makefile_path = makefile_dir / MAKEFILE_FILENAME
    gitignore_path = makefile_dir / GITIGNORE_FILENAME

    # Python 3.12
    # relative = make_dir.relative_to(makefile_dir, walk_up=True)

    # Python 3.9
    relative = relative_to_walk_up(makefile_dir, make_dir)

    with open(template_filename, 'r') as fin:
        with open(makefile_path, 'w') as fout:
            for line in fin:
                print(line.replace(REPLACE_STR, str(relative)),
                      end='', file=fout)

    with open(gitignore_path, 'w') as fout:
        print(str(MAKEFILE_FILENAME), file=fout)
        print(str(GITIGNORE_FILENAME), file=fout)


if __name__ == '__main__':
    main()

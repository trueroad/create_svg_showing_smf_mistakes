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

from pathlib import Path
import sys
from typing import Final


REPLACE_DIR_STR: Final[str] = '@MODELS_SRC_DIR_FROM_MODEL_DIR@'
REPLACE_NAME_STR: Final[str] = '@MODEL_NAME@'


def main() -> None:
    """Do main."""
    if len(sys.argv) != 3:
        print('Usage: ./build_model_makefile.py '
              '(in)TEMPLATE.mk MODEL_NAME > Makefile',
              file=sys.stderr)
        sys.exit(1)

    # モデルディレクトリに格納するMakefileのテンプレートファイル
    template_filename = Path(sys.argv[1])
    # モデル名：モデルソースディレクトリからモデルディレクトリへの相対パス
    model_name = Path(sys.argv[2])

    if model_name.is_absolute():
        # モデル名に絶対パスは不可、相対パスのみ可
        print('Error: MODEL_NAME is absolute path.',
              file=sys.stderr)
        sys.exit(2)

    # モデルディレクトリからモデルソースファイルディレクトリへの
    # 相対パス（つまりmodel_nameの逆）を作る
    models_src_dir_from_model_dir: Path = Path('.')
    for rp in reversed(model_name.parts):
        if rp == '..':
            # モデル名の相対パスは `..` による親ディレクトリへの移動不可
            print('Error: MODEL_NAME has `..`.')
            sys.exit(2)
        if rp == '.':
            # モデル名の相対パスは `.` による自ディレクトリへの移動不可
            print('Error: MODEL_NAME has `.`.')
            sys.exit(2)
        models_src_dir_from_model_dir /= Path('..')

    with open(template_filename, 'r') as f:
        for line in f:
            print(line.
                  replace(REPLACE_NAME_STR, str(model_name)).
                  replace(REPLACE_DIR_STR, str(models_src_dir_from_model_dir)),
                  end='')


if __name__ == '__main__':
    main()

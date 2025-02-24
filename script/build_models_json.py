#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Build models.json.

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

import json
from pathlib import Path
import sys
from typing import Final

# https://gist.github.com/trueroad/b0d051af003c61aafb3eac0c051e5f89
import config_file


CONFIG_FILENAME: Final[str] = 'config.toml'


def main() -> None:
    """Do main."""
    if len(sys.argv) < 3:
        print('Usage: ./build_models_json.py MODELS_DIR '
              'MODEL_NAME ... > models.json',
              file=sys.stderr)
        sys.exit(1)

    models_dir = Path(sys.argv[1]).resolve()
    phrase_list: list[dict[str, str]] = []

    for i in range(2, len(sys.argv)):
        model_name = Path(sys.argv[i])

        cf = config_file.config_file()
        cf.load_config_file(models_dir / model_name / CONFIG_FILENAME)

        phrase: dict[str, str] = {}
        phrase['name'] = str(model_name)
        phrase['title'] = cf.get_value_str('title')
        phrase_list.append(phrase)

    print(json.dumps({'phrase_list': phrase_list},
                     ensure_ascii=False, indent=2), end='')


if __name__ == '__main__':
    main()

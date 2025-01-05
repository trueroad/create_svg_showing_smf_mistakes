#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Create SVG showing SMF (Standard MIDI File) mistakes.

https://github.com/trueroad/create_svg_showing_smf_mistakes

app.py:
  Flask web application

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

import datetime
import json
from pathlib import Path
import re
import tempfile
from typing import BinaryIO, Final, Optional, Union

from flask import Flask, make_response, render_template, request, url_for
import urllib3
from werkzeug import Response

import create_svg_showing_smf_mistakes

MODEL_PATH: Final[Path] = Path('models')
MODEL_MID: Final[Path] = Path('model.mid')
MODEL_LIST: Final[Path] = Path('model.list.txt')
POSTFILE: Final[Path] = Path('post.bin')

app = Flask(__name__)


def iso8601_basic(dt: datetime.datetime, timespec: str = 'auto') -> str:
    """
    ISO8601基本形式の文字列を返す.

    Args:
      dt (datetime.datetime): 文字列にしたい日時
      timespec (str): 秒以下の扱い

    Returns:
      str: ISO8601基本形式の文字列
    """
    # UTCの場合はZに変換する
    retval: str = dt.isoformat(timespec=timespec).replace('+00:00', 'Z')
    # 拡張形式を基本形式に変換する
    retval = re.sub(r'([0-9]+)-([0-9][0-9])-([0-9][0-9])T', r'\1\2\3T',
                    retval, count=1)
    return retval.replace(':', '')


@app.route('/midi/diffsvg', methods=['POST'])
def diffsvg() -> Union[Response, tuple[Response, int]]:
    """
    間違い差分を返すAPI.

    Returns:
      Union[Response, tuple[Response, int]]: 間違い差分コンテンツ
    """
    # 現在日時を取得、現在のタイムゾーンを得る方法が無い？のでUTC固定
    dt: Final[datetime.datetime] = datetime.datetime.now(datetime.timezone.utc)
    iso8601now: Final[str] = iso8601_basic(dt, timespec='microseconds')

    # POSTリクエストボディをファイルに書き込む（デバッグ用）
    with open(POSTFILE, 'wb') as fpost:
        fpost.write(request.get_data())

    # モデル名を取得
    name: Optional[str] = request.form.get('name')
    if name is None:
        return make_response('No name is specified.'), 400

    # モデル名のバリデーション
    pattern: Final[str] = '^[a-zA-Z0-9\\-_/]+$'
    if not re.match(pattern, name):
        return make_response('Invalid name.'), 400

    # モデルディレクトリ存在チェック
    modelpath: Final[Path] = MODEL_PATH / name
    if not modelpath.is_dir():
        return make_response('Name not found.'), 400

    # モデルSMF存在チェック
    modelmid: Final[Path] = modelpath / MODEL_MID
    if not modelmid.is_file():
        return make_response('SMF not found.'), 400

    # モデルLIST存在チェック
    modellist: Final[Path] = modelpath / MODEL_LIST
    if not modellist.is_file():
        return make_response('List not found.'), 400

    # モデル名をベースにテンポラリファイルのプレフィックスを決定
    name_replaced: Final[str] = name.replace('/', '_')
    # 評価対象SMF用テンポラリファイルを作成
    with tempfile.NamedTemporaryFile(suffix='.mid',
                                     prefix='temp_' + name_replaced +
                                     '_' + iso8601now + '_',
                                     dir='.',
                                     delete=False) as tmpmid:
        # リクエスト中の評価対象SMFをテンポラリファイルへ保存
        request.files['foreval'].save(tmpmid.name)

        # 比較
        mst = create_svg_showing_smf_mistakes.mistakes()
        mst.load_text(modellist)
        mst.load_model(modelmid)
        mst.load_foreval(tmpmid.name)
        mst.diff()

        # 差分表示SVG用テンポラリファイルを作成
        with tempfile.NamedTemporaryFile(suffix='.svg',
                                         prefix='temp_' + name_replaced +
                                         '_' + iso8601now + '_',
                                         dir='.',
                                         delete=False) as tmpsvg:
            # 差分表示SVGを作成
            mst.create_svg(tmpsvg.name)

            # レスポンスのボディとヘッダを作成
            body, header = urllib3.encode_multipart_formdata(
                {'diffsvg':  # 差分表示SVG
                 ('diff.svg', open(tmpsvg.name, 'rb').read(),
                  'image/svg+xml'),
                 'json':  # その他の結果（現在はダミー）
                 ('diff.json', json.dumps({'message': 'dummy message',
                                           'result': 'dummy result'}),
                  'application/json')
                 })

            # レスポンスを格納して返す
            resp = make_response()
            resp.data = body
            resp.mimetype = header
            return resp

        return make_response('Failed to create SVG.'), 500

    return make_response('Failed to create diff.'), 500


if __name__ == '__main__':
    app.run(debug=True)

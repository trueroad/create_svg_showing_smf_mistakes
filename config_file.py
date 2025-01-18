#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TOML config file class for python.

https://gist.github.com/trueroad/b0d051af003c61aafb3eac0c051e5f89

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
from typing import Any, BinaryIO, Final, Optional, Union

import tomli


VERSION: Final[str] = '20250118.01'


class config_file:
    """TOML設定ファイルを扱うクラス."""

    def __init__(self,
                 verbose: int = 0) -> None:
        """
        __init__.

        Args:
          verbose (int): Verboseレベル
        """
        self.verbose: Final[int] = verbose

        # 設定ファイル
        self.config_file: Path
        # 設定ファイルディレクトリ
        self.config_dir: Path
        # ロードした設定
        self.config: dict[str, Any]

    def __print_v(self,
                  *args: Any, level: int = 1, **kwargs: Any) -> None:
        """
        Verbose レベルを考慮して print する.

        Args:
          *args (Any): print するもの
          level (int): 出力する最低の verbose レベル
          **kwargs (Any): print に渡すオプション引数
        """
        if self.verbose >= level:
            print(*args, **kwargs)

    def load_config_file(self,
                         filename: Union[str, os.PathLike[str]]) -> bool:
        """
        TOML設定ファイルをロードする.

        Args:
          filename (PathLike): TOML設定ファイル名

        Returns:
          bool: Trueなら成功、Falseならエラー
        """
        self.__print_v(f'load_config_file: {str(filename)}')
        self.config_file = Path(filename).resolve()
        self.__print_v(f'  -> {str(self.config_file)}')
        try:
            with open(filename, 'rb') as f:
                self.config = tomli.load(f)
        except Exception as e:
            self.__print_v(f'Error: tomli.load() exception: {e}')
            return False
        self.config_dir = self.config_file.parent
        self.__print_v(f'  in dir {str(self.config_dir)}')
        return True

    def get_value(self,
                  *args: Union[str, int],
                  toml_dict: Optional[dict[str, Any]] = None) -> Any:
        """
        設定値を取得する.

        参考
        https://gist.github.com/trueroad/f92b4e53efeac8750408b83b302e3eb6

        Args:
          toml_dict (dict[str, Any]):
            TOML辞書、Noneはロードした設定を意味する
          *args (Union[str, int]):
            取得したいテーブル名、キー名、配列インデックス

        Returns:
          Any: 設定値
        """
        da: Union[dict[str, Any], list[Any]] = \
            self.config if toml_dict is None else toml_dict
        list_a: list[Union[str, int]] = list(args)
        list_b: list[Union[str, int]] = []

        while True:
            if type(list_a[0]) is str:
                if type(da) is dict and list_a[0] in da:
                    if len(list_a) == 1:
                        return da[list_a[0]]
                    da = da[list_a[0]]
                else:
                    raise NameError(f'{list_b} does not have '
                                    f'table \'{list_a[0]}\'')
            elif type(list_a[0]) is int:
                if type(da) is list and list_a[0] < len(da):
                    if len(list_a) == 1:
                        return da[list_a[0]]
                    da = da[list_a[0]]
                else:
                    raise IndexError(f'{list_b} does not have '
                                     f'array index {list_a[0]}')
            else:
                raise TypeError('Unknown type')

            list_b.append(list_a[0])
            list_a = list_a[1:]

        raise RuntimeError('Programming error')

    def has_value(self,
                  *args: Union[str, int],
                  toml_dict: Optional[dict[str, Any]] = None) -> bool:
        """
        設定値の存在有無を返す.

        Args:
          toml_dict (dict[str, Any]):
            TOML辞書、Noneはロードした設定を意味する
          *args (Union[str, int]):
            確認したいテーブル名、キー名、配列インデックス

        Returns:
          bool: Trueは存在、Falseは不存在
        """
        try:
            self.get_value(*args, toml_dict=toml_dict)
        except (NameError, IndexError):
            return False
        return True

    def get_value_str(self,
                      *args: Union[str, int],
                      toml_dict: Optional[dict[str, Any]] = None) -> str:
        """
        設定値を文字列として取得する.

        Args:
          toml_dict (dict[str, Any]):
            TOML辞書、Noneはロードした設定を意味する
          *args (Union[str, int]):
            取得したいテーブル名、キー名、配列インデックス

        Returns:
          str: 設定値
        """
        value = self.get_value(toml_dict=toml_dict, *args)
        if type(value) is not str:
            raise TypeError(f'config {args} is not str but {type(value)}')
        return value

    def get_value_int(self,
                      *args: Union[str, int],
                      toml_dict: Optional[dict[str, Any]] = None) -> int:
        """
        設定値を整数として取得する.

        Args:
          toml_dict (dict[str, Any]):
            TOML辞書、Noneはロードした設定を意味する
          *args (Union[str, int]):
            取得したいテーブル名、キー名、配列インデックス

        Returns:
          int: 設定値
        """
        value = self.get_value(toml_dict=toml_dict, *args)
        if type(value) is not int:
            raise TypeError(f'config {args} is not int but {type(value)}')
        return value

    def get_value_float(self,
                        *args: Union[str, int],
                        toml_dict: Optional[dict[str, Any]] = None) -> float:
        """
        設定値を浮動小数点数として取得する.

        Args:
          toml_dict (dict[str, Any]):
            TOML辞書、Noneはロードした設定を意味する
          *args (Union[str, int]):
            取得したいテーブル名、キー名、配列インデックス

        Returns:
          int: 設定値
        """
        value = self.get_value(toml_dict=toml_dict, *args)
        if type(value) is float:
            return value
        if type(value) is int:
            return float(value)
        raise TypeError(f'config {args} is not float nor int '
                        f'but {type(value)}')


def main() -> None:
    """Test main."""
    print(f'TOML config file class for python. {VERSION}\n\n'
          'https://gist.github.com/trueroad/'
          'b0d051af003c61aafb3eac0c051e5f89\n\n'
          'Copyright (C) 2025 Masamichi Hosoda.\n'
          'All rights reserved.\n')
    if len(sys.argv) != 2:
        print('Usage: ./config_file.py [CONFIG.toml]')
        sys.exit(1)

    cf = config_file(verbose=1)
    cf.load_config_file(sys.argv[1])
    print(cf.config)


if __name__ == '__main__':
    main()

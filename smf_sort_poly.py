#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Sort poly notes in SMF (Standard MIDI File).

https://gist.github.com/trueroad/6c577bf87abff8c170cad4c84d048cc3

Copyright (C) 2021, 2022 Masamichi Hosoda.
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

import copy
import sys
from typing import Any, Dict, Final, List, Optional, Tuple

# https://gist.github.com/trueroad/52b7c4c98eec5fdf0ff3f62d64ec17bd
import smf_parse


VERSION: Final[str] = "20220305.01"


class sort_poly:
    """同時に発音された多声を音高の昇順にソートする."""

    # 同時発音とみなす最大のズレ（秒）のデフォルト値
    DEFAULT_MAX_MISALIGNMENT: Final[float] = 0.05

    def __init__(self,
                 max_misalignment: Optional[float] = None,
                 b_octave_reduction: bool = False,
                 verbose: int = 0) -> None:
        """
        __init__.

        Args:
          max_misalignment (Optional[float]): 同時発音とみなす最大のズレ（秒）
            None はデフォルト値を設定する
          b_octave_reduction (bool): オクターブ圧縮するか否か
          verbose (int): Verbose レベル
        """
        # Verbose レベル
        self.verbose: Final[int] = verbose
        # 同時発音とみなす最大のズレ（秒）
        self.max_misalignment: float = sort_poly.DEFAULT_MAX_MISALIGNMENT
        if max_misalignment is not None:
            self.max_misalignment = max_misalignment
        # オクターブ圧縮するか否か
        self.b_octave_reduction: bool = b_octave_reduction
        # 入力ノートリスト
        self.notes: List[smf_parse.note_container] = []
        # ソート済みノートリスト
        self.sorted_notes: List[smf_parse.note_container] = []
        # 同時発音リスト
        self.poly_notes: List[smf_parse.note_container] = []

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

    @staticmethod
    def __poly_sort_key(note: smf_parse.note_container) -> int:
        """音高でソートするため key に指定する関数."""
        return note.note_on.note_event.note

    @staticmethod
    def __poly_sort_octave_reduction_key(note: smf_parse.note_container
                                         ) -> Tuple[int, int]:
        """音高（オクターブ圧縮）でソートするため key に指定する関数."""
        return (note.note_on.note_event.note % 12,
                note.note_on.note_event.note)

    def __flush_poly_notes(self) -> None:
        """同時発音リストを音高の昇順にソートしてフラッシュ."""
        # 同時発音リストをソートする
        if self.b_octave_reduction:
            self.poly_notes.sort(key=self.__poly_sort_octave_reduction_key)
        else:
            self.poly_notes.sort(key=self.__poly_sort_key)
        # 同時発音リストの長さを表示
        self.__print_v(f'\nPoly notes {len(self.poly_notes)}')
        # 同時発音リストの中身を表示
        for n in self.poly_notes:
            self.__print_v(f'  {n.note_on} ~', level=2)
        # ソート済みリストへ同時発音リストの中身を出力
        self.sorted_notes.extend(self.poly_notes)
        # 同時発音リストをクリア
        self.poly_notes = []

    def sorted(self,
               notes: List[smf_parse.note_container]) -> List[
               smf_parse.note_container]:
        """
        ノートリスト中の同時発音を音高の昇順にソートしたものを出力.

        Args:
          notes (List[smf_parse.note_container]): 入力のノートリスト

        Returns:
          List[smf_parse.note_container]: 同時発音がソートされたノートリスト
        """
        # 引数を入力ノートリストへ設定
        self.notes = copy.deepcopy(notes)

        # ソート済みノートリスト、同時発音リストをクリア
        self.sorted_notes = []
        self.poly_notes = []

        while len(self.notes) > 0:
            # 入力ノートリスト先頭の音符を取り出す
            note: smf_parse.note_container = self.notes.pop(0)
            if ((len(self.poly_notes) > 0
                 and ((note.note_on.abs_time
                       - self.poly_notes[0].note_on.abs_time)
                      > self.max_misalignment))):
                # 同時発音リスト先頭との時間差が大きければフラッシュ
                self.__flush_poly_notes()
            # 取り出した音符を同時発音リストに追加
            self.poly_notes.append(note)

        # 最後に残った同時発音リストをフラッシュ
        self.__flush_poly_notes()

        # ソート済みリストを返す
        return self.sorted_notes


def main() -> None:
    """テスト用メイン."""
    print(f'Sort poly notes in SMF (Standard MIDI File) {VERSION}\n\n'
          'https://gist.github.com/trueroad/'
          '6c577bf87abff8c170cad4c84d048cc3\n\n'
          'Copyright (C) 2021, 2022 Masamichi Hosoda.\n'
          'All rights reserved.\n')

    import argparse
    parser: argparse.ArgumentParser = argparse.ArgumentParser()
    parser.add_argument('FILENAME.mid', help='Input SMF.')
    parser.add_argument('--octave-reduction',
                        help='Enable octave reduction.',
                        action='store_true')
    args: argparse.Namespace = parser.parse_args()
    vargs: Dict[str, Any] = vars(args)

    filename: str = vargs['FILENAME.mid']
    b_octave_reduction: bool = vargs['octave_reduction']

    print(f'Filename SMF    : {filename}\n'
          f'Octave reduction: {b_octave_reduction}')

    # ロード
    mid: smf_parse.smf_notes = smf_parse.smf_notes()
    mid.load(filename)

    # ノートリストを取得
    notes: List[smf_parse.note_container] = mid.get_notes()

    # 同時発音を音高の昇順にソート
    sp: sort_poly = sort_poly(b_octave_reduction=b_octave_reduction,
                              verbose=2)
    sorted_notes: List[smf_parse.note_container] = sp.sorted(notes)

    # 結果表示
    print('\nResults')
    print(f'Loaded notes: {len(notes)}')
    print(f'Sorted notes: {len(sorted_notes)}')
    if len(notes) == len(sorted_notes):
        print('  match')
    else:
        print('  error')


if __name__ == "__main__":
    main()

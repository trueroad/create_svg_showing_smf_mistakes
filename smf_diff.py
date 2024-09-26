#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Diff SMF (Standard MIDI File).

https://gist.github.com/trueroad/97477dab8beca099afeb4af5199634e2

Copyright (C) 2021, 2022, 2024 Masamichi Hosoda.
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
import dataclasses
import difflib
import math
import os
import sys
from typing import Any, Dict, Final, List, Optional, Tuple, Union, cast

from mido import MidiFile  # type: ignore[import-untyped]

# https://gist.github.com/trueroad/52b7c4c98eec5fdf0ff3f62d64ec17bd
import smf_parse
# https://gist.github.com/trueroad/6c577bf87abff8c170cad4c84d048cc3
import smf_sort_poly
# https://gist.github.com/trueroad/341afa4ff6045fe05ae945a0697822c5
import diff_levenshtein


VERSION: Final[str] = "20240926.01"


class note_for_diff:
    """Diff 用ノートの基底クラス."""

    def __init__(self,
                 note: smf_parse.note_container) -> None:
        """
        __init__.

        Args:
          note (smf_parse.note_container): 設定するノート
        """
        self.note: smf_parse.note_container = copy.deepcopy(note)

    def __repr__(self) -> str:
        """
        __repr__.

        Returns:
          str: 中身のノートと同じ文字列
        """
        return self.note.__repr__()


class note_for_diff_octave_strict(note_for_diff):
    """Diff 用ノートのオクターブ厳密比較クラス."""

    def __init__(self,
                 note: smf_parse.note_container) -> None:
        """
        __init__.

        Args:
          note (smf_parse.note_container): 設定するノート
        """
        super().__init__(note)

    def __eq__(self, other: Any) -> bool:
        """
        __eq__.

        Diff 用ノート同士が一致しているか比較する。
        Diff 処理用に音程のみ一致していれば他が違っていても
        一致しているとする。

        Args:
          other (Any): 比較対象のオブジェクト

        Returns:
          bool: 音程が一致していれば True そうでなければ False
        """
        if not isinstance(other, note_for_diff):
            return False
        # 音程の一致のみで評価
        return self.note.note_on.note_event.note == \
            other.note.note_on.note_event.note

    def __hash__(self) -> int:
        """
        __hash__.

        Diff 処理用に音程のみでハッシュを計算する。

        Returns:
          int: 音程のみで計算したハッシュ値
        """
        # 音程のみで評価
        return hash(self.note.note_on.note_event.note)


class note_for_diff_octave_reduction(note_for_diff):
    """Diff 用ノートのオクターブ圧縮比較クラス."""

    def __init__(self,
                 note: smf_parse.note_container) -> None:
        """
        __init__.

        Args:
          note (smf_parse.note_container): 設定するノート
        """
        super().__init__(note)

    def __eq__(self, other: Any) -> bool:
        """
        __eq__.

        Diff 用ノート同士がオクターブ無視して一致しているか比較する。
        Diff 処理用に音程のみ一致していれば他が違っていても
        一致しているとする。

        Args:
          other (Any): 比較対象のオブジェクト

        Returns:
          bool: 音程がオクターブ無視して一致していれば True
            そうでなければ False
        """
        if not isinstance(other, note_for_diff):
            return False
        # オクターブ無視した音程の一致のみで評価
        return ((self.note.note_on.note_event.note % 12) ==
                (other.note.note_on.note_event.note % 12))

    def __hash__(self) -> int:
        """
        __hash__.

        Diff 処理用にオクターブ無視した音程のみでハッシュを計算する。

        Returns:
          int: オクターブ無視した音程のみで計算したハッシュ値
        """
        # オクターブ無視した音程のみで評価
        return hash(self.note.note_on.note_event.note % 12)


@dataclasses.dataclass(frozen=True)
class note_timing_container:
    """ノートタイミング比較結果クラス."""

    # モデルの音符
    note_model: smf_parse.note_container
    # 評価対象の音符
    note_foreval: smf_parse.note_container
    # モデルの前の音符との時間差（単位秒）
    model_time_delta: Optional[float]
    # 評価対象の前の音符との時間差（単位秒）
    foreval_time_delta: Optional[float]
    # foreval_time_delta のテンポ補正後
    foreval_time_delta_converted: Optional[float]
    # テンポ補正後の割合
    ratio: Optional[float]
    # テンポ補正後の差分（単位秒）
    diff: Optional[float]
    # モデルの音符の長さ（単位秒）
    model_duration: float
    # 評価対象の音符の長さ（単位秒）
    foreval_duration: float
    # 評価対象の補正後の音符の長さ（単位秒）
    foreval_duration_converted: float
    # 音符の長さ補正後の割合
    ratio_duration: float
    # 音符の長さ補正後の差分（単位秒）
    diff_duration: float
    # ノート ON ベロシティ補正後の差分
    diff_velocity: float

    def __repr__(self) -> str:
        """
        __repr__.

        評価対象とモデルで対応の取れた音符同士の
        タイミング比較結果を文字列化する。

        Returns:
          str: タイミング比較結果文字列
            モデル側 MBT、ノート番号、前の音符との時間比と差分、
            音符の時間比と差分、ベロシティ差分
        """
        mbt: smf_parse.mbt_container = self.note_model.note_on.mbt
        note: int = self.note_model.note_on.note_event.note
        buff: str = f'{mbt}, note {note} {smf_parse.note_to_ipn(note)}, '

        if (self.ratio is None) or (self.diff is None):
            buff += 'no previous notes'
        else:
            buff += f'{(self.ratio * 100):.0f} %, {self.diff} [s]'

        buff += f',\n    {(self.ratio_duration * 100):.0f} %, ' \
            f'{self.diff_duration} [s], velocity {self.diff_velocity}'

        return buff


@dataclasses.dataclass(frozen=True)
class extra_note_container:
    """余計な音符クラス."""

    # 音符（評価対象側）
    note: smf_parse.note_container
    # 余計な音符の前の MBT （モデル側）
    mbt_before_extra: smf_parse.mbt_container
    # 余計な音符の後の MBT （モデル側）
    mbt_after_extra: smf_parse.mbt_container
    # 余計な音符の前の絶対 tick （モデル側）
    abs_tick_before_extra: int
    # 余計な音符の後の絶対 tick （モデル側）
    abs_tick_after_extra: int
    # モデルの最初の音符より前にあるか
    b_before_model_first: bool
    # モデルの最後の音符より後にあるか
    b_after_model_last: bool
    # 余計な音符の前の MBT （評価対象側）
    foreval_mbt_before_extra: Optional[smf_parse.mbt_container]
    # 余計な音符の後の MBT （評価対象側）
    foreval_mbt_after_extra: Optional[smf_parse.mbt_container]
    # 余計な音符の前の絶対 tick （評価対象側）
    foreval_abs_tick_before_extra: Optional[int]
    # 余計な音符の後の絶対 tick （評価対象側）
    foreval_abs_tick_after_extra: Optional[int]


class smf_difference:
    """SMF の差分比較クラス."""

    def __init__(self,
                 filter_velocity: Optional[int] = None,
                 filter_duration: Optional[float] = None,
                 filter_noteno_margin: Optional[int] = None,
                 max_misalignment: Optional[float] = None,
                 b_octave_reduction: bool = False,
                 b_strict_diff: bool = False,
                 verbose: int = 0) -> None:
        """
        __init__.

        Args:
          filer_velocity (Optional[int]): 評価対象のフィルタ設定
            ベロシティが本設定未満のノートをフィルタ
            例：48 なら 48 未満をフィルタ
            デフォルト：None （フィルタ無効）
          filter_duration (Optional[float]): 評価対象のフィルタ設定
            音長が本設定（単位秒）未満のノートをフィルタ
            例：0.1 なら 0.1 秒未満をフィルタ
            デフォルト：None （フィルタ無効）
          filter_noteno_margin (Optional[int]): 評価対象のフィルタ設定
            ノート番号がモデル最高最低値±本設定の範囲外をフィルタ
            例：2 なら± 2 範囲外をフィルタ
            デフォルト：None （フィルタ無効）
          max_misalignment (Optional[float]): 同時発音とみなす最大のズレ（秒）
            None は sort_poly クラスのデフォルト値に設定される
            デフォルト：None
          b_octave_reduction (bool): オクターブ圧縮するか否か
            デフォルト：False
          b_strict_diff (bool): 厳密な差分比較をするか否か
            デフォルト：False
          verbose (int): Verbose レベル
        """
        # 評価対象のフィルタ設定
        # 小さいベロシティ：ベロシティが本設定未満のノートをフィルタ
        self.filter_velocity: int
        # 短い音長：音長が本設定（単位秒）未満のノートをフィルタ
        self.filter_duration: float
        # ノート番号：ノート番号がモデル最高最低値±本設定の範囲外をフィルタ
        self.filter_noteno_margin: int

        self.set_filter(filter_velocity=filter_velocity,
                        filter_duration=filter_duration,
                        filter_noteno_margin=filter_noteno_margin)

        # 同時発音とみなす最大のズレ（秒）
        self.max_misalignment: Optional[float] = max_misalignment
        # オクターブ圧縮するか否か
        self.b_octave_reduction: bool = b_octave_reduction
        # 厳密な差分比較をするか否か
        self.b_strict_diff: bool = b_strict_diff

        # Verbose レベル
        self.verbose: Final[int] = verbose

        # モデル SMF の長さゼロ音符をフィルタするか否か
        self.filter_zero_duration: bool = True

        # モデル SMF
        self.model: smf_parse.smf_notes = smf_parse.smf_notes()
        # モデル SMF の同時発音ソート済みリスト
        self.model_sorted: List[smf_parse.note_container] = []
        # モデル SMF のフィルタ済みリスト
        self.model_filtered: List[smf_parse.note_container] = []
        # モデル SMF の比較用 diff リスト
        self.model_diff: List[note_for_diff] = []
        # モデルの最高最低ノート番号記録用
        self.model_max_noteno: int = -1
        self.model_min_noteno: int = 128
        # モデルのベロシティ平均
        self.model_velocity_mean: float = 0.0
        # 評価対象 SMF
        self.foreval: smf_parse.smf_notes = smf_parse.smf_notes()
        # 評価対象 SMF の同時発音ソート済みリスト
        self.foreval_sorted: List[smf_parse.note_container] = []
        # 評価対象 SMF のフィルタ済みリスト
        self.foreval_filtered: List[smf_parse.note_container] = []
        # 評価対象 SMF の比較用 diff リスト
        self.foreval_diff: List[note_for_diff] = []
        # 評価対象の最高最低ノート番号記録用
        self.foreval_max_noteno: int = -1
        self.foreval_min_noteno: int = 128
        # 評価対象のベロシティ平均
        self.foreval_velocity_mean: float = 0.0

        # マッチングが取れたモデルの音符リスト
        self.matched_note_model: List[smf_parse.note_container] = []
        # マッチングが取れた評価対象の音符リスト
        self.matched_note_foreval: List[smf_parse.note_container] = []
        # 欠落した（モデルの）音符リスト
        self.missing_note: List[smf_parse.note_container] = []
        # 余計な（評価対象の）音符リスト
        self.extra_note: List[extra_note_container] = []

        # 評価対象・モデルの全体時間割合
        self.time_ratio: float = -1.0

        # タイミング比較結果
        self.note_timing: List[note_timing_container] = []

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

    def set_max_misalignment(self, max_misalignment: Optional[float]
                             ) -> None:
        """
        同時発音とみなす最大のズレを変更する.

        Args:
          max_misalignment (Optional[float]): 同時発音とみなす最大のズレ（秒）
            None は sort_poly クラスのデフォルト値に設定される
        """
        self.max_misalignment = max_misalignment

    def set_filter(self,
                   filter_velocity: Optional[int] = None,
                   filter_duration: Optional[float] = None,
                   filter_noteno_margin: Optional[int] = None) -> None:
        """
        評価対象のフィルタ設定を変更する.

        Args:
          filer_velocity (Optional[int]): 評価対象のフィルタ設定
            ベロシティが本設定未満のノートをフィルタ
            例：48 なら 48 未満をフィルタ
            デフォルト：None （フィルタ無効）
          filter_duration (Optional[float]): 評価対象のフィルタ設定
            音長が本設定（単位秒）未満のノートをフィルタ
            例：0.1 なら 0.1 秒未満をフィルタ
            デフォルト：None （フィルタ無効）
          filter_noteno_margin (Optional[int]): 評価対象のフィルタ設定
            ノート番号がモデル最高最低値±本設定の範囲外をフィルタ
            例：2 なら± 2 範囲外をフィルタ
            デフォルト：None （フィルタ無効）
        """
        if filter_velocity is not None:
            self.filter_velocity = filter_velocity
        else:
            self.filter_velocity = 0

        if filter_duration is not None:
            self.filter_duration = filter_duration
        else:
            self.filter_duration = 0.0

        if filter_noteno_margin is not None:
            self.filter_noteno_margin = filter_noteno_margin
        else:
            self.filter_noteno_margin = 128

    def load_model(self, filename: Union[str, bytes, os.PathLike[Any]]
                   ) -> bool:
        """
        モデル SMF をロード.

        Args:
          filename (PathLike): ロードするモデル SMF のファイル名

        Returns:
          bool: True なら成功、False なら失敗
        """
        bload: bool = self.model.load(filename)
        if not bload:
            self.__print_v('Load model failed.')
            return False
        return self.__process_model()

    def read_data_model(self, mid: MidiFile) -> bool:
        """
        モデル SMF データを読み込む.

        Args:
          mid (MidiFile): ロードするモデル SMF の mido.MidiFile オブジェクト

        Returns:
          bool: True なら成功、False なら失敗
        """
        bread: bool = self.model.read_data(mid)
        if not bread:
            self.__print_v('Read-data model failed.')
            return False
        return self.__process_model()

    def __process_model(self) -> bool:
        """モデルを処理."""
        # モデルのスペックを表示
        model_type: int
        model_tpqn: int
        model_tracks: int
        model_type, model_tpqn, model_tracks = self.model.get_smf_specs()
        self.__print_v(f'Model: SMF type {model_type},'
                       f' TPQN {model_tpqn}, tracks {model_tracks}')

        self.model_sorted = self.__note_sort(self.model)
        self.model_filtered \
            = self.__note_filter_zero_duration(self.model_sorted)
        if len(self.model_filtered) == 0:
            self.__print_v('\nError: no model notes.')
            return False
        self.model_velocity_mean \
            = self.__calc_velocity_mean(self.model_filtered)
        self.model_diff, self.model_max_noteno, self.model_min_noteno \
            = self.__make_diff_list(self.model_filtered)

        if len(self.foreval_sorted) > 0:
            self.foreval_filtered = self.__note_filter(self.foreval_sorted)
            self.foreval_velocity_mean \
                = self.__calc_velocity_mean(self.foreval_filtered)
            self.foreval_diff, \
                self.foreval_max_noteno, self.foreval_min_noteno \
                = self.__make_diff_list(self.foreval_filtered)

        for nd in self.model_diff:
            self.__print_v(nd, level=2)

        return True

    def load_foreval(self, filename: Union[str, bytes, os.PathLike[Any]]
                     ) -> bool:
        """
        評価対象 SMF をロード.

        Args:
          filename (PathLike): ロードする評価対象 SMF のファイル名

        Returns:
          bool: True なら成功、False なら失敗
        """
        bload: bool = self.foreval.load(filename)
        if not bload:
            self.__print_v('Load for-eval failed.')
            return False
        return self.__process_foreval()

    def read_data_foreval(self, mid: MidiFile) -> bool:
        """
        評価対象 SMF データを読み込む.

        Args:
          mid (MidiFile): ロードする評価対象 SMF の mido.MidiFile オブジェクト

        Returns:
          bool: True なら成功、False なら失敗
        """
        bread: bool = self.foreval.read_data(mid)
        if not bread:
            self.__print_v('Read-data foreval failed.')
            return False
        return self.__process_foreval()

    def __process_foreval(self) -> bool:
        """評価対象を処理."""
        # 評価対象のスペックを表示
        foreval_type: int
        foreval_tpqn: int
        foreval_tracks: int
        foreval_type, foreval_tpqn, foreval_tracks \
            = self.foreval.get_smf_specs()
        self.__print_v(f'For-eval: SMF type {foreval_type},'
                       f' TPQN {foreval_tpqn}, tracks {foreval_tracks}')

        self.foreval_sorted = self.__note_sort(self.foreval)
        self.foreval_filtered = self.__note_filter(self.foreval_sorted)
        self.foreval_velocity_mean \
            = self.__calc_velocity_mean(self.foreval_filtered)
        self.foreval_diff, self.foreval_max_noteno, self.foreval_min_noteno \
            = self.__make_diff_list(self.foreval_filtered)

        for nd in self.foreval_diff:
            self.__print_v(nd, level=2)

        return True

    def __note_sort(self, notes: smf_parse.smf_notes
                    ) -> List[smf_parse.note_container]:
        """同時発音を音高の昇順にソート."""
        note_sorter: smf_sort_poly.sort_poly \
            = smf_sort_poly.sort_poly(
                max_misalignment=self.max_misalignment,
                b_octave_reduction=self.b_octave_reduction)
        return note_sorter.sorted(notes.get_notes())

    def __note_filter_zero_duration(self,
                                    note_sorted:
                                    List[smf_parse.note_container]
                                    ) -> List[smf_parse.note_container]:
        """長さゼロの音符をフィルタ."""
        # フィルタされたノート
        note_filtered: List[smf_parse.note_container] = []

        note: smf_parse.note_container
        for note in note_sorted:
            if note.note_on.mbt == note.note_off.mbt:
                self.__print_v(f'Warning: zero duration note: {note.note_on}')
                if not self.filter_zero_duration:
                    note_filtered.append(note)
            else:
                note_filtered.append(note)

        return note_filtered

    def __note_filter(self,
                      note_sorted: List[smf_parse.note_container]
                      ) -> List[smf_parse.note_container]:
        """フィルタ."""
        # フィルタ理由のカウント用
        filtered_velocity: int = 0
        filtered_duration: int = 0
        filtered_noteno_max: int = 0
        filtered_noteno_min: int = 0

        # フィルタされたノート
        note_filtered: List[smf_parse.note_container] = []

        for note in note_sorted:
            filtered: bool = False
            if note.note_on.note_event.velocity < self.filter_velocity:
                # ベロシティが設定値未満なのでフィルタする
                filtered_velocity += 1
                filtered = True
            if ((note.note_off.abs_time
                 - note.note_on.abs_time) < self.filter_duration):
                # 音長が設定値未満なのでフィルタする
                filtered_duration += 1
                filtered = True
            if note.note_on.note_event.note > (self.model_max_noteno
                                               + self.filter_noteno_margin):
                # ノート番号が設定範囲外なのでフィルタする
                filtered_noteno_max += 1
                filtered = True
            if note.note_on.note_event.note < (self.model_min_noteno
                                               - self.filter_noteno_margin):
                # ノート番号が設定範囲外なのでフィルタする
                filtered_noteno_min += 1
                filtered = True
            if filtered:
                continue
            note_filtered.append(note)

        # フィルタ理由毎のフィルタ数を表示
        self.__print_v(f'\nFiltered: velocity {filtered_velocity},'
                       f' duration {filtered_duration},'
                       f' note no. max {filtered_noteno_max} '
                       f' min {filtered_noteno_min}')

        return note_filtered

    def __calc_velocity_mean(self,
                             note_sorted: List[smf_parse.note_container]
                             ) -> float:
        """ベロシティの平均を計算."""
        if len(note_sorted) == 0:
            return math.nan
        mean: float = 0.0
        note: smf_parse.note_container
        for note in note_sorted:
            mean += float(note.note_on.note_event.velocity) / len(note_sorted)
        return mean

    def __make_diff_list(self,
                         note_sorted: List[smf_parse.note_container]
                         ) -> Tuple[List[note_for_diff], int, int]:
        """比較用 diff リストを作成."""
        # 最高最低ノート番号記録用
        max_noteno: int = -1
        min_noteno: int = 128

        # diff 用リストを作成
        note_diff: List[note_for_diff] = []
        for note in note_sorted:
            if max_noteno < note.note_on.note_event.note:
                # 最高ノート番号更新
                max_noteno = note.note_on.note_event.note
            if min_noteno > note.note_on.note_event.note:
                # 最低ノート番号更新
                min_noteno = note.note_on.note_event.note
            if self.b_octave_reduction:
                note_diff.append(note_for_diff_octave_reduction(note))
            else:
                note_diff.append(note_for_diff_octave_strict(note))

        return note_diff, max_noteno, min_noteno

    def diff(self) -> None:
        """比較実施."""
        # 比較結果を格納する変数を初期化
        self.matched_note_model = []
        self.matched_note_foreval = []
        self.missing_note = []
        self.extra_note = []
        self.note_timing = []

        # 比較実施
        s: Union[difflib.SequenceMatcher[note_for_diff],
                 diff_levenshtein.LevenshteinMatcher]
        if self.b_strict_diff:
            s = diff_levenshtein.LevenshteinMatcher(a=self.model_diff,
                                                    b=self.foreval_diff)
        else:
            s = difflib.SequenceMatcher(isjunk=None,
                                        a=self.model_diff,
                                        b=self.foreval_diff,
                                        autojunk=False)

        tag: str
        i1: int
        i2: int
        j1: int
        j2: int
        for tag, i1, i2, j1, j2 in s.get_opcodes():
            self.__print_v(f'{tag}: {i1}-{i2} -> {j1}-{j2}')
            if tag == 'equal':
                self.__matched_notes(i1, i2, j1, j2)
            elif tag == 'delete':
                self.__missing_notes(i1, i2)
            elif tag == 'insert':
                self.__extra_notes(i1, i2, j1, j2)
            elif tag == 'replace':
                self.__missing_notes(i1, i2)
                self.__extra_notes(i1, i2, j1, j2)

    def __matched_notes(self, i1: int, i2: int, j1: int, j2: int) -> None:
        """マッチングが取れた音符の処理."""
        i: int
        j: int
        # マッチングが取れた音符がある
        # マッチした最初の音符の MBT
        mbt_match_start: smf_parse.mbt_container = \
            self.model_diff[i1].note.note_on.mbt
        if (i2 - i1) > 1:
            mbt_match_end: smf_parse.mbt_container = \
                self.model_diff[i2 - 1].note.note_on.mbt
            self.__print_v(f'Matched notes: {mbt_match_start} ~'
                           f' {mbt_match_end}')
        elif (i2 - i1) > 0:
            self.__print_v(f'Matched note: {mbt_match_start}')
        for i in range(i1, i2):
            # マッチングが取れたモデルの音符リストに追加
            self.matched_note_model.append(self.model_diff[i].note)
        for j in range(j1, j2):
            # マッチングが取れた評価対象の音符リストに追加
            self.matched_note_foreval.append(
                self.foreval_diff[j].note)

    def __missing_notes(self, i1: int, i2: int) -> None:
        """欠落した音符の処理."""
        i: int
        # 欠落した音符がある
        for i in range(i1, i2):
            # 欠落した音符の MBT
            mbt_miss: smf_parse.mbt_container = \
                self.model_diff[i].note.note_on.mbt
            # 欠落した音符のノート番号
            note_no_miss: int \
                = self.model_diff[i].note.note_on.note_event.note
            self.__print_v(f'Missing note: {mbt_miss},'
                           f' note {note_no_miss}'
                           f' {smf_parse.note_to_ipn(note_no_miss)}')
            # 欠落した音符リストに追加
            self.missing_note.append(self.model_diff[i].note)

    def __extra_notes(self, i1: int, i2: int, j1: int, j2: int) -> None:
        """余計な音符の処理."""
        b_before_model_first: bool = False
        b_after_model_last: bool = False
        mbt_before_extra: smf_parse.mbt_container
        mbt_after_extra: smf_parse.mbt_container
        abs_tick_before_extra: int
        abs_tick_after_extra: int
        if i1 == 0:
            # モデル側の最初の音符の前に余計な音符がある
            b_before_model_first = True
            if len(self.model_diff) > 0:
                # モデル側の最初の音符の MBT を採る
                mbt_before_extra = self.model_diff[i1].note.note_on.mbt
                abs_tick_before_extra = \
                    self.model_diff[i1].note.note_on.abs_tick
            else:
                # モデル側に音符が無い
                mbt_before_extra = smf_parse.mbt_container(
                    measure=0, beat=0, tick=0)
                abs_tick_before_extra = 0
        else:
            # 余計な音符が現れる直前で対応するモデルの音符の MBT
            mbt_before_extra = self.model_diff[i1 - 1].note.note_on.mbt
            abs_tick_before_extra = \
                self.model_diff[i1 - 1].note.note_on.abs_tick
        if i2 == len(self.model_diff):
            # モデル側の最後の音符の後に余計な音符があるか
            # 最後の音符を置き換える余計な音符がある
            b_after_model_last = True
            if i2 > 0:
                # モデル側の最後の音符の MBT を採る
                mbt_after_extra = self.model_diff[i2 - 1].note.note_on.mbt
                abs_tick_after_extra = \
                    self.model_diff[i2 - 1].note.note_on.abs_tick
            else:
                # モデル側に音符が無い
                mbt_after_extra = smf_parse.mbt_container(
                    measure=0, beat=0, tick=0)
                abs_tick_after_extra = 0
        else:
            # 余計な音符が現れた直後で対応するモデルの音符の MBT
            mbt_after_extra = self.model_diff[i2].note.note_on.mbt
            abs_tick_after_extra = \
                self.model_diff[i2].note.note_on.abs_tick

        mbt_before_extra_foreval: Optional[smf_parse.mbt_container]
        mbt_after_extra_foreval: Optional[smf_parse.mbt_container]
        abs_tick_before_extra_foreval: Optional[int]
        abs_tick_after_extra_foreval: Optional[int]
        if j1 == 0:
            # 評価対象側の最初の音符からはじまる
            foreval_mbt_before_extra = None
            foreval_abs_tick_before_extra = None
        else:
            # 余計な音符が現れる直前で対応する評価対象の音符の MBT
            foreval_mbt_before_extra = \
                self.foreval_diff[j1 - 1].note.note_on.mbt
            foreval_abs_tick_before_extra = \
                self.foreval_diff[j1 - 1].note.note_on.abs_tick
        if j2 == len(self.foreval_diff):
            # 評価対象側の最後の音符まで含む
            foreval_mbt_after_extra = None
            foreval_abs_tick_after_extra = None
        else:
            # 余計な音符が現れた直後で対応する評価対象の音符の MBT
            foreval_mbt_after_extra = \
                self.foreval_diff[j2].note.note_on.mbt
            foreval_abs_tick_after_extra = \
                self.foreval_diff[j2].note.note_on.abs_tick

        j: int
        for j in range(j1, j2):
            self.__print_v('Extra note: ', end='')
            if b_before_model_first:
                self.__print_v('~ ', end='')
            if mbt_before_extra == mbt_after_extra:
                self.__print_v(f'{mbt_before_extra}', end='')
            else:
                self.__print_v(f'{mbt_before_extra} ~ {mbt_after_extra}',
                               end='')
            if b_after_model_last:
                self.__print_v(' ~', end='')
            # 余計な音符のノート番号
            note_no_extra: int = \
                self.foreval_diff[j].note.note_on.note_event.note
            self.__print_v(f', note {note_no_extra}'
                           f' {smf_parse.note_to_ipn(note_no_extra)}')

            # 余計な音符リストに追加
            self.extra_note.append(extra_note_container(
                note=self.foreval_diff[j].note,
                mbt_before_extra=mbt_before_extra,
                mbt_after_extra=mbt_after_extra,
                abs_tick_before_extra=abs_tick_before_extra,
                abs_tick_after_extra=abs_tick_after_extra,
                b_before_model_first=b_before_model_first,
                b_after_model_last=b_after_model_last,
                foreval_mbt_before_extra=foreval_mbt_before_extra,
                foreval_mbt_after_extra=foreval_mbt_after_extra,
                foreval_abs_tick_before_extra=foreval_abs_tick_before_extra,
                foreval_abs_tick_after_extra=foreval_abs_tick_after_extra))

    def calc_time_ratio(self) -> float:
        """
        評価対象・モデルの全体時間割合を計算する.

        Returns:
          float: 時間比率
            最後のマッチした音符と最初のマッチした音符の
            ノート ON 時間差の比率
            1.0 なら評価対象とモデルのテンポは同じ、
            2.0 なら評価対象はモデルの半分の速度、
            0.5 なら評価対象はモデルの倍速
        """
        if len(self.matched_note_model) == 0 \
           or len(self.matched_note_foreval) == 0:
            # マッチした音符が無いので計算できない
            self.time_ratio = math.nan
            return self.time_ratio
        # マッチした最初の音符のノート ON（モデル側）
        first_model_note_on: smf_parse.note_event_time_container \
            = self.matched_note_model[0].note_on
        # マッチした最後の音符のノート ON（モデル側）
        last_model_note_on: smf_parse.note_event_time_container \
            = self.matched_note_model[-1].note_on
        if first_model_note_on.mbt == last_model_note_on.mbt:
            # 最初の音符と最後の音符の MBT が同じなので計算できない
            self.time_ratio = math.nan
            return self.time_ratio
        # マッチした最初の音符のノート ON モデル時刻
        first_time_model: float = first_model_note_on.abs_time
        # マッチした最初の音符のノート ON 評価対象時刻
        first_time_foreval: float \
            = self.matched_note_foreval[0].note_on.abs_time
        # マッチした最後の音符のノート ON モデル時刻
        last_time_model: float = last_model_note_on.abs_time
        # マッチした最後の音符のノート ON 評価対象時刻
        last_time_foreval: float \
            = self.matched_note_foreval[-1].note_on.abs_time
        # 評価対象・モデルの全体時間割合
        self.time_ratio = (last_time_foreval - first_time_foreval) \
            / (last_time_model - first_time_model)
        return self.time_ratio

    def calc_note_timing(self) -> None:
        """タイミング系の集計を実施する."""
        self.calc_time_ratio()

        # マッチした音符を i でループ
        i: int
        for i in range(len(self.matched_note_model)):
            # モデル側のノート
            model_note: smf_parse.note_container = self.matched_note_model[i]
            # モデル側の音符の長さ
            model_duration: float = model_note.note_off.abs_time \
                - model_note.note_on.abs_time
            # 評価対象側のノート
            foreval_note: smf_parse.note_container \
                = self.matched_note_foreval[i]
            # 評価対象側の音符の長さ
            foreval_duration: float = foreval_note.note_off.abs_time \
                - foreval_note.note_on.abs_time
            # 評価対象側の音符の長さを全体時間割合で補正してモデル時間に換算
            foreval_duration_converted: float \
                = foreval_duration / self.time_ratio
            # 音符の長さ補正後の評価対象・モデル割合
            ratio_duration: float
            if model_note.note_on.mbt == model_note.note_off.mbt:
                # モデル側の音符の長さがゼロなので計算できない
                ratio_duration = math.nan
            else:
                ratio_duration = foreval_duration_converted / model_duration
            # 音符の長さ補正後の評価対象・モデル差分
            diff_duration: float \
                = foreval_duration_converted - model_duration
            # ノート番号
            model_note_on_note: int = model_note.note_on.note_event.note
            # ベロシティ補正後の評価対象・モデル差分
            diff_velocity: float \
                = ((foreval_note.note_on.note_event.velocity
                    - self.foreval_velocity_mean)
                   -
                   (model_note.note_on.note_event.velocity
                    - self.model_velocity_mean))

            bfound: bool = False
            # 一つ前から最初の音符まで j でループし時間差のある音符を見つける
            for j in range(i - 1, -1, -1):
                # モデル側の前のノート
                model_before_note: smf_parse.note_container \
                    = self.matched_note_model[j]
                # 評価対象側の前のノート
                foreval_before_note: smf_parse.note_container \
                    = self.matched_note_foreval[j]

                # モデル側の時間差を計算
                model_time_delta: float \
                    = model_note.note_on.abs_time \
                    - model_before_note.note_on.abs_time
                # 時間差が正なら計算・格納して j ループを抜ける
                # 時間差が無ければ j ループに戻りもう一つ前の音符と比較する
                if model_time_delta > 0.0:
                    # 評価対象側の時間差
                    foreval_time_delta: float \
                        = foreval_note.note_on.abs_time \
                        - foreval_before_note.note_on.abs_time
                    # 評価対象側時間差を全体時間割合で補正しモデル時間に換算
                    time_delta_conv: float \
                        = foreval_time_delta / self.time_ratio
                    # 格納
                    self.note_timing.append(note_timing_container(
                        note_model=model_note, note_foreval=foreval_note,
                        model_time_delta=model_time_delta,
                        foreval_time_delta=foreval_time_delta,
                        foreval_time_delta_converted=time_delta_conv,
                        ratio=time_delta_conv / model_time_delta,
                        diff=time_delta_conv - model_time_delta,
                        model_duration=model_duration,
                        foreval_duration=foreval_duration,
                        foreval_duration_converted=foreval_duration_converted,
                        ratio_duration=ratio_duration,
                        diff_duration=diff_duration,
                        diff_velocity=diff_velocity))
                    # 時間差のある音符がみつかったので j ループは抜ける
                    bfound = True
                    break
            if not bfound:
                # 時間差のある前の音符無し
                self.note_timing.append(note_timing_container(
                    note_model=model_note, note_foreval=foreval_note,
                    model_time_delta=None, foreval_time_delta=None,
                    foreval_time_delta_converted=None,
                    ratio=None, diff=None,
                    model_duration=model_duration,
                    foreval_duration=foreval_duration,
                    foreval_duration_converted=foreval_duration_converted,
                    ratio_duration=ratio_duration,
                    diff_duration=diff_duration,
                    diff_velocity=diff_velocity))

    def get_model_note_by_range(self,
                                begin: Optional[smf_parse.mbt_container]
                                = None,
                                end: Optional[smf_parse.mbt_container]
                                = None
                                ) -> List[smf_parse.note_container]:
        """
        指定された区間にノート ON があるモデルの音符を取得する.

        指定された区間 [begin, end) にノート ON がある
        モデルの音符のリストを返す。

        Args:
          begin (Optional[smf_parse.mbt_container]): 区間の先頭を指定する。
            モデルの MBT で指定する。指定された MBT は区間に含まれる。
            None は SMF の最初からを意味する。
          end (Optional[smf_parse.mbt_container]): 区間の最後の後を指定する。
            モデルの MBT で指定する。指定された MBT は区間に含まれない。
            None は SMF の最後までを意味する。

        Returns:
          List[smf_parse.note_container]: 区間内のモデルの音符リスト
        """
        retval: List[smf_parse.note_container] = []
        note: smf_parse.note_container
        for note in self.model_filtered:
            if begin is not None and note.note_on.mbt < begin:
                continue
            if end is not None and note.note_on.mbt >= end:
                continue
            retval.append(note)
        return retval

    def get_missing_note_by_range(self,
                                  begin: Optional[smf_parse.mbt_container]
                                  = None,
                                  end: Optional[smf_parse.mbt_container]
                                  = None
                                  ) -> List[smf_parse.note_container]:
        """
        指定された区間にノート ON がある欠落した音符を取得する.

        指定された区間 [begin, end) にノート ON がある
        欠落した音符のリストを返す。

        Args:
          begin (Optional[smf_parse.mbt_container]): 区間の先頭を指定する。
            モデルの MBT で指定する。指定された MBT は区間に含まれる。
            None は SMF の最初からを意味する。
          end (Optional[smf_parse.mbt_container]): 区間の最後の後を指定する。
            モデルの MBT で指定する。指定された MBT は区間に含まれない。
            None は SMF の最後までを意味する。

        Returns:
          List[smf_parse.note_container]: 区間内の欠落した音符リスト
        """
        retval: List[smf_parse.note_container] = []
        note: smf_parse.note_container
        for note in self.missing_note:
            if begin is not None and note.note_on.mbt < begin:
                continue
            if end is not None and note.note_on.mbt >= end:
                continue
            retval.append(note)
        return retval

    def get_extra_note_by_range(self,
                                begin: Optional[smf_parse.mbt_container]
                                = None,
                                end: Optional[smf_parse.mbt_container]
                                = None
                                ) -> List[extra_note_container]:
        """
        指定された区間にノート ON がある余計な音符を取得する.

        指定されたモデル側区間 [begin, end) 相当にノート ON がある
        余計な音符のリストを返す。
        余計な音符はモデル側に対応する音符が存在しないため、
        そのモデル側 MBT は一意に決まらず存在する可能性がある区間
        [mbt_extra_before, mbt_extra_after) で示される
        （mbt_extra_before: 直前に一致した音符、なければ最初の音符の MBT
        mbt_extra_after: 直後に一致した音符、なければ最後の音符の MBT）。
        本関数は指定区間が存在可能性区間を内包する場合に区間内としている。

        Args:
          begin (Optional[smf_parse.mbt_container]): 区間の先頭を指定する。
            モデルの MBT で指定する。指定された MBT は区間に含まれる。
            None は SMF の最初からを意味する。
          end (Optional[smf_parse.mbt_container]): 区間の最後の後を指定する。
            モデルの MBT で指定する。指定された MBT は区間に含まれない。
            None は SMF の最後までを意味する。

        Returns:
          List[extra_note_container]: 区間内の余計な音符リスト
        """
        retval: List[extra_note_container] = []
        en: extra_note_container
        for en in self.extra_note:
            if begin is not None:
                if en.mbt_before_extra < begin:
                    continue
                if en.mbt_after_extra <= begin:
                    continue
            if end is not None:
                if end < en.mbt_after_extra:
                    continue
                if end <= en.mbt_before_extra:
                    continue
            retval.append(en)
        return retval

    def get_note_timing_by_range(self,
                                 begin: Optional[smf_parse.mbt_container]
                                 = None,
                                 end: Optional[smf_parse.mbt_container]
                                 = None
                                 ) -> List[note_timing_container]:
        """
        指定された区間にノート ON があるタイミング比較結果を取得する.

        指定された区間 [begin, end) にノート ON がある音符についての
        タイミング比較結果のリストを返す。

        Args:
          begin (Optional[smf_parse.mbt_container]): 区間の先頭を指定する。
            モデルの MBT で指定する。指定された MBT は区間に含まれる。
            None は SMF の最初からを意味する。
          end (Optional[smf_parse.mbt_container]): 区間の最後の後を指定する。
            モデルの MBT で指定する。指定された MBT は区間に含まれない。
            None は SMF の最後までを意味する。

        Returns:
          List[note_timing_container]: 区間内のタイミング比較結果リスト
        """
        retval: List[note_timing_container] = []
        nt: note_timing_container
        for nt in self.note_timing:
            if begin is not None and nt.note_model.note_on.mbt < begin:
                continue
            if end is not None and nt.note_model.note_on.mbt >= end:
                continue
            retval.append(nt)
        return retval

    def calc_previous_mape(self,
                           begin: Optional[smf_parse.mbt_container] = None,
                           end: Optional[smf_parse.mbt_container] = None
                           ) -> float:
        """
        前の音符との時間差の MAPE を計算する.

        指定された区間 [begin, end) にノート ON がある音符について
        テンポ補正後の評価対象とモデルとの、前の音符との時間差の
        誤差 MAPE を計算する。

        Args:
          begin (Optional[smf_parse.mbt_container]): 区間の先頭を指定する。
            モデルの MBT で指定する。指定された MBT は区間に含まれる。
            None は SMF の最初からを意味する。
          end (Optional[smf_parse.mbt_container]): 区間の最後の後を指定する。
            モデルの MBT で指定する。指定された MBT は区間に含まれない。
            None は SMF の最後までを意味する。

        Returns:
          float: 誤差 MAPE
        """
        nt_ranged: List[note_timing_container] \
            = self.get_note_timing_by_range(begin, end)

        previous: List[float] = []
        nt: note_timing_container
        for nt in nt_ranged:
            if nt.ratio is not None:
                previous.append(1.0 - nt.ratio)
        if len(previous) == 0:
            return math.nan

        mape: float = 0.0
        p: float
        for p in previous:
            mape += abs(p) / len(previous)

        return mape

    def calc_previous_rmspe(self,
                            begin: Optional[smf_parse.mbt_container] = None,
                            end: Optional[smf_parse.mbt_container] = None
                            ) -> float:
        """
        前の音符との時間差の RMSPE を計算する.

        指定された区間 [begin, end) にノート ON がある音符について
        テンポ補正後の評価対象とモデルとの、前の音符との時間差の
        誤差 RMSPE を計算する。

        Args:
          begin (Optional[smf_parse.mbt_container]): 区間の先頭を指定する。
            モデルの MBT で指定する。指定された MBT は区間に含まれる。
            None は SMF の最初からを意味する。
          end (Optional[smf_parse.mbt_container]): 区間の最後の後を指定する。
            モデルの MBT で指定する。指定された MBT は区間に含まれない。
            None は SMF の最後までを意味する。

        Returns:
          float: 誤差 RMSPE
        """
        nt_ranged: List[note_timing_container] \
            = self.get_note_timing_by_range(begin, end)

        previous: List[float] = []
        nt: note_timing_container
        for nt in nt_ranged:
            if nt.ratio is not None:
                previous.append(1.0 - nt.ratio)
        if len(previous) == 0:
            return math.nan

        mspe: float = 0.0
        p: float
        for p in previous:
            mspe += p * p / len(previous)

        return cast(float, mspe ** 0.5)

    def calc_duration_mape(self,
                           begin: Optional[smf_parse.mbt_container] = None,
                           end: Optional[smf_parse.mbt_container] = None
                           ) -> float:
        """
        音の長さの MAPE を計算する.

        指定された区間 [begin, end) にノート ON がある音符について
        テンポ補正後の評価対象とモデルとの、音の長さの
        誤差 MAPE を計算する。

        Args:
          begin (Optional[smf_parse.mbt_container]): 区間の先頭を指定する。
            モデルの MBT で指定する。指定された MBT は区間に含まれる。
            None は SMF の最初からを意味する。
          end (Optional[smf_parse.mbt_container]): 区間の最後の後を指定する。
            モデルの MBT で指定する。指定された MBT は区間に含まれない。
            None は SMF の最後までを意味する。

        Returns:
          float: 誤差 MAPE
        """
        nt_ranged: List[note_timing_container] \
            = self.get_note_timing_by_range(begin, end)
        if len(nt_ranged) == 0:
            return math.nan

        mape: float = 0.0
        nt: note_timing_container
        for nt in nt_ranged:
            mape += abs(1.0 - nt.ratio_duration) / len(nt_ranged)

        return mape

    def calc_duration_rmspe(self,
                            begin: Optional[smf_parse.mbt_container] = None,
                            end: Optional[smf_parse.mbt_container] = None
                            ) -> float:
        """
        音の長さの RMSPE を計算する.

        指定された区間 [begin, end) にノート ON がある音符について
        テンポ補正後の評価対象とモデルとの、音の長さの
        誤差 RMSPE を計算する。

        Args:
          begin (Optional[smf_parse.mbt_container]): 区間の先頭を指定する。
            モデルの MBT で指定する。指定された MBT は区間に含まれる。
            None は SMF の最初からを意味する。
          end (Optional[smf_parse.mbt_container]): 区間の最後の後を指定する。
            モデルの MBT で指定する。指定された MBT は区間に含まれない。
            None は SMF の最後までを意味する。

        Returns:
          float: 誤差 RMSPE
        """
        nt_ranged: List[note_timing_container] \
            = self.get_note_timing_by_range(begin, end)
        if len(nt_ranged) == 0:
            return math.nan

        mspe: float = 0.0
        nt: note_timing_container
        for nt in nt_ranged:
            mspe += (1.0 - nt.ratio_duration) * (1.0 - nt.ratio_duration) \
                / len(nt_ranged)

        return cast(float, mspe ** 0.5)

    def calc_velocity_mae(self,
                          begin: Optional[smf_parse.mbt_container] = None,
                          end: Optional[smf_parse.mbt_container] = None
                          ) -> float:
        """
        ベロシティの MAE を計算する.

        指定された区間 [begin, end) にノート ON がある音符について
        ベロシティ補正後の評価対象とモデルとの
        誤差 MAE を計算する。

        Args:
          begin (Optional[smf_parse.mbt_container]): 区間の先頭を指定する。
            モデルの MBT で指定する。指定された MBT は区間に含まれる。
            None は SMF の最初からを意味する。
          end (Optional[smf_parse.mbt_container]): 区間の最後の後を指定する。
            モデルの MBT で指定する。指定された MBT は区間に含まれない。
            None は SMF の最後までを意味する。

        Returns:
          float: 誤差 MAE
        """
        nt_ranged: List[note_timing_container] \
            = self.get_note_timing_by_range(begin, end)
        if len(nt_ranged) == 0:
            return math.nan

        mae: float = 0.0
        nt: note_timing_container
        for nt in nt_ranged:
            mae += abs(nt.diff_velocity) / len(nt_ranged)

        return mae

    def calc_velocity_rmse(self,
                           begin: Optional[smf_parse.mbt_container] = None,
                           end: Optional[smf_parse.mbt_container] = None
                           ) -> float:
        """
        ベロシティの RMSE を計算する.

        指定された区間 [begin, end) にノート ON がある音符について
        ベロシティ補正後の評価対象とモデルとの、
        誤差 RMSE を計算する。

        Args:
          begin (Optional[smf_parse.mbt_container]): 区間の先頭を指定する。
            モデルの MBT で指定する。指定された MBT は区間に含まれる。
            None は SMF の最初からを意味する。
          end (Optional[smf_parse.mbt_container]): 区間の最後の後を指定する。
            モデルの MBT で指定する。指定された MBT は区間に含まれない。
            None は SMF の最後までを意味する。

        Returns:
          float: 誤差 RMSE
        """
        nt_ranged: List[note_timing_container] \
            = self.get_note_timing_by_range(begin, end)
        if len(nt_ranged) == 0:
            return math.nan

        mse: float = 0.0
        nt: note_timing_container
        for nt in nt_ranged:
            mse += nt.diff_velocity * nt.diff_velocity / len(nt_ranged)

        return cast(float, mse ** 0.5)


def main() -> None:
    """テスト用メイン."""
    print(f'Diff SMF (Standard MIDI File) {VERSION}\n\n'
          'https://gist.github.com/trueroad/'
          '97477dab8beca099afeb4af5199634e2\n\n'
          'Copyright (C) 2021, 2022, 2024 Masamichi Hosoda.\n'
          'All rights reserved.\n')

    import argparse
    parser: argparse.ArgumentParser = argparse.ArgumentParser()
    parser.add_argument('MODEL.mid', help='Model SMF.')
    parser.add_argument('FOR_EVAL.mid', help='For-eval SMF.')
    parser.add_argument('--filter-velocity',
                        help='Filters out notes with less velocity '
                        'than specified from for-eval SMF.',
                        type=int, default=0, required=False)
    parser.add_argument('--filter-duration',
                        help='Filters out notes with less duration '
                        'than specified from for-eval SMF (unit sec).',
                        type=float, default=0.0, required=False)
    parser.add_argument('--filter-noteno-margin',
                        help='Filters out notes outside of '
                        'the model SMF note range plus or minus '
                        'this setting margin range.',
                        type=int, default=128, required=False)
    parser.add_argument('--octave-reduction',
                        help='Enable octave reduction.',
                        action='store_true')
    parser.add_argument('--strict-diff',
                        help='Enable strict diff.',
                        action='store_true')

    args: argparse.Namespace = parser.parse_args()
    vargs: Dict[str, Any] = vars(args)

    model_filename: str = vargs['MODEL.mid']
    foreval_filename: str = vargs['FOR_EVAL.mid']
    filter_velocity: int = vargs['filter_velocity']
    filter_duration: float = vargs['filter_duration']
    filter_noteno_margin: int = vargs['filter_noteno_margin']
    b_octave_reduction: bool = vargs['octave_reduction']
    b_strict_diff: bool = vargs['strict_diff']

    print(f'Model SMF           : {model_filename}\n'
          f'For-eval SMF        : {foreval_filename}\n'
          f'filter-velocity     : {filter_velocity}\n'
          f'filter-duration     : {filter_duration}\n'
          f'filter-noteno-margin: {filter_noteno_margin}\n'
          f'Octave reduction    : {b_octave_reduction}\n'
          f'Strict diff         : {b_strict_diff}\n')

    # 比較クラス
    sd: smf_difference \
        = smf_difference(verbose=1,
                         filter_velocity=filter_velocity,
                         filter_duration=filter_duration,
                         filter_noteno_margin=filter_noteno_margin,
                         b_octave_reduction=b_octave_reduction,
                         b_strict_diff=b_strict_diff)
    # モデルをロード
    if not sd.load_model(model_filename):
        return
    # 評価対象をロード
    if not sd.load_foreval(foreval_filename):
        return

    print('\nDiff notes')
    # 差分をとる
    sd.diff()

    # モデルの音符数
    model_notes: int = len(sd.model_diff)
    # マッチングが取れた音符の数
    matched_notes: int = len(sd.matched_note_model)
    # 評価対象で欠落していた音符の数
    missing_notes: int = len(sd.missing_note)
    # 評価対象にあった余計な音符の数
    extra_notes: int = len(sd.extra_note)

    # ノート系結果表示
    print('\nResults (notes)')
    if model_notes > 0:
        print(f'Model notes: {model_notes},'
              f' note {sd.model_min_noteno}'
              f' {smf_parse.note_to_ipn(sd.model_min_noteno)} ~'
              f' note {sd.model_max_noteno}'
              f' {smf_parse.note_to_ipn(sd.model_max_noteno)}')
        print(f'Matched notes: {matched_notes}'
              f' ({(matched_notes / model_notes * 100):.0f} %)')
        print(f'Missing notes: {missing_notes}'
              f' ({(missing_notes / model_notes * 100):.0f} %)')
        print(f'Extra notes: {extra_notes}'
              f' ({(extra_notes / model_notes * 100):.0f} %)')
    else:
        print(f'Model notes: {model_notes}')
        print(f'Extra notes: {extra_notes}')
    print(f'Velocity mean: model {sd.model_velocity_mean}, '
          f'for-eval {sd.foreval_velocity_mean}')

    # タイミング系の集計
    sd.calc_note_timing()

    max_measure: int
    if len(sd.model_diff) > 0:
        # 小節毎に音符数を表示
        print('\nNotes per measure: model, matched, missing, extra')
        max_measure = sd.model_diff[-1].note.note_on.mbt.measure
        i: int
        for i in range(max_measure + 1):
            begin: smf_parse.mbt_container \
                = smf_parse.mbt_container(measure=i, beat=0, tick=0)
            end: smf_parse.mbt_container \
                = smf_parse.mbt_container(measure=i+1, beat=0, tick=0)
            print(f'  measure {i+1}:'
                  f' {len(sd.get_model_note_by_range(begin, end))},'
                  f' {len(sd.get_note_timing_by_range(begin, end))},'
                  f' {len(sd.get_missing_note_by_range(begin, end))},'
                  f' {len(sd.get_extra_note_by_range(begin, end))}')

    # マッチした音符毎のタイミングを表示
    print('\nMatched note time difference from the previous one '
          f'(conv. ratio {(sd.time_ratio * 100):.0f} %)')
    print('MBT, note, conv. for-eval vs model ratio, delta,\n'
          '    note duration ratio, note duration diff, note velocity diff')

    nt: note_timing_container
    for nt in sd.note_timing:
        print(nt)

    # タイミング系結果表示
    print('\nResults (timing)')
    print(f'Tempo ratio (conv. ratio): {sd.time_ratio * 100} %')
    print('MAPE previous note       : '
          f'{sd.calc_previous_mape() * 100} %')
    print('RMSPE previous note      : '
          f'{sd.calc_previous_rmspe() * 100} %')
    print('MAPE duration            : '
          f'{sd.calc_duration_mape() * 100} %')
    print('RMSPE duration           : '
          f'{sd.calc_duration_rmspe() * 100} %')
    print('MAE velocity             : '
          f'{sd.calc_velocity_mae()}')
    print('RMSE velocity            : '
          f'{sd.calc_velocity_rmse()}')

    if len(sd.model_diff) > 0:
        # 小節毎に誤差を表示
        print('\nErrors per measure: previous MAPE RMSPE,'
              ' duration MAPE RMSPE, velocity MAE RMSE')
        for i in range(max_measure + 1):
            begin = smf_parse.mbt_container(measure=i, beat=0, tick=0)
            end = smf_parse.mbt_container(measure=i+1, beat=0, tick=0)
            print(f'  measure {i+1}:'
                  f' {(sd.calc_previous_mape(begin, end) * 100):.0f} %'
                  f' {(sd.calc_previous_rmspe(begin, end) * 100):.0f} %,'
                  f' {(sd.calc_duration_mape(begin, end) * 100):.0f} %'
                  f' {(sd.calc_duration_rmspe(begin, end) * 100):.0f} %,'
                  f' {(sd.calc_velocity_mae(begin, end)):.0f}'
                  f' {(sd.calc_velocity_rmse(begin, end)):.0f}')


if __name__ == "__main__":
    main()

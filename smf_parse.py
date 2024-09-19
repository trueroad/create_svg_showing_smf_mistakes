#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Parsing SMF (Standard MIDI File).

https://gist.github.com/trueroad/52b7c4c98eec5fdf0ff3f62d64ec17bd

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

from __future__ import annotations
import dataclasses
from functools import total_ordering
import os
import sys
from typing import Any, Dict, Final, List, Optional, Tuple, Union

from mido import (  # type: ignore[import-untyped]
    MidiFile, MidiTrack, merge_tracks, tick2second,
    Message, UnknownMetaMessage)


VERSION: Final[str] = "20240125.01"


@dataclasses.dataclass(frozen=True)
@total_ordering
class mbt_container:
    """MBT （小節、拍、tick）コンテナクラス."""

    measure: int  # 小節（0 開始、表示は +1 する必要あり）
    beat: int     # 拍（0 開始、表示は +1 する必要あり）
    tick: int     # tick

    @classmethod
    def from_str(cls, mbt_str: str) -> mbt_container:
        """
        文字列から MBT コンテナクラスへ変換.

        TPQN (ticks per quater note, time base) は考慮しない。
        失敗したら例外を投げることがある。

        Args:
          mbt_str (str): MBT を記述した文字列
            小節、拍、Tick をそれぞれ 10 進数値表記しコロン区切りしたもの。
            例： 1 小節目 1 拍目 0 Tick （SMF 冒頭を意味する）は "1:1:0"
            余計な 0 詰めがされていても構わない。
            例： "00001:01:000" は "1:1:0" と同様に解釈される

        Returns:
          mbt_container: 変換した MBT
            小節と拍は内部的には 0 開始なので -1 されたものが格納される。
        """
        mbt_list: List[str] = mbt_str.split(sep=':')
        return cls(measure=int(mbt_list[0]) - 1,
                   beat=int(mbt_list[1]) - 1,
                   tick=int(mbt_list[2]))

    def __repr__(self) -> str:
        """
        __repr__.

        MBT コンテナクラスを文字列表記へ変換する。

        Returns:
          str: 文字列表記へ変換した MBT コンテナクラスの内容
            桁数を合わせるため小節・拍・Tick いずれも 0 詰めして、
            それぞれ 5 桁、2 桁、3 桁にしてコロンで区切る。
            小節と拍は内部的には 0 開始なので +1 されたものが出力される。
            例：SMF 冒頭を意味する 1 小節 1 拍 0 Tick は "00001:01:000"
        """
        return f'{self.measure+1:05}:' \
            f'{self.beat+1:02}:' \
            f'{self.tick:03}'

    def __eq__(self, other: object) -> bool:
        """
        __eq__.

        MBT コンテナクラス同士が同じ MBT を指しているか比較する。
        TPQN (ticks per quater note, time base) の違いは考慮せず、
        同じであることを仮定して比較する。

        @total_ordering を付けてあるので、
        __eq__(), __lt__() 以外の比較演算子も自動生成される。

        object の型が違ったら例外 NotImplemented を投げる。

        Args:
          other (object): 比較するオブジェクト

        Returns:
          bool: 同じなら True そうでなければ False
        """
        if not isinstance(other, self.__class__):
            return NotImplemented
        return (self.measure == other.measure
                and self.beat == other.beat
                and self.tick == other.tick)

    def __lt__(self, other: object) -> bool:
        """
        __lt__.

        MBT コンテナクラス同士でどちらが先なのか比較する。
        TPQN (ticks per quater note, time base) の違いは考慮せず、
        同じであることを仮定して比較する。

        @total_ordering を付けてあるので、
        __eq__(), __lt__() 以外の比較演算子も自動生成される。

        object の型が違ったら例外 NotImplemented を投げる。

        Args:
          other (object): 比較するオブジェクト

        Returns:
          bool: 自オブジェクトの方が先なら True そうでなければ False
        """
        if not isinstance(other, self.__class__):
            return NotImplemented
        if self.measure < other.measure:
            return True
        elif self.measure > other.measure:
            return False
        if self.beat < other.beat:
            return True
        elif self.beat > other.beat:
            return False
        if self.tick < other.tick:
            return True
        return False


class mbt_calc:
    """MBT （小節、拍、tick）計算クラス."""

    def __init__(self,
                 tpqn: int,
                 mbt: mbt_container = mbt_container(
                     measure=0, beat=0, tick=0),
                 numerator: int = 4, denominator: int = 4) -> None:
        """
        __init__.

        Args:
          tpqn (int): TPQN (ticks per quater note, time base)
          mbt (mbt_container): 初期 MBT
          numerator (int): 拍子の分子
          denominator (int): 拍子の分母
        """
        self.__tpqn: int = tpqn  # TPQN (ticks per quater note, time base)

        self.mbt = mbt  # MBT

        self.set_time_signature(numerator, denominator)
        self.reset_next: bool = False  # 拍子変更フラグ

    def __repr__(self) -> str:
        """
        __repr__.

        Returns:
          str: 内部 MBT コンテナを文字列化したもの
        """
        return f'{self.mbt}'

    def set_time_signature(self, numerator: int, denominator: int) -> None:
        """
        拍子を設定.

        Args:
          numerator (int): 拍子の分子
          denominator (int): 拍子の分母
        """
        self.__numerator: int = numerator      # 拍子の分子
        self.__denominator: int = denominator  # 拍子の分母

        # 1 拍中の tick 数
        self.__ticks_in_beat: int = \
            int(self.__tpqn * 4 / self.__denominator)

        if self.is_middle_of_measure():
            # 小節途中の拍子変更の場合、
            # 同時刻のメッセージまでは変更前の MBT として処理するが、
            # 以降のメッセージで MBT をリセットするためフラグを立てる
            self.reset_next = True

    def add_ticks(self, ticks: int) -> None:
        """
        Tick を加算して MBT を更新する.

        Args:
          ticks (int): 加算する tick
        """
        if self.reset_next:
            # 小節途中の拍子変更があったので MBT をリセット
            self.reset_to_next_measure()
            self.reset_next = False

        tick: int = self.mbt.tick + ticks
        beat: int = self.mbt.beat + (tick // self.__ticks_in_beat)
        tick = tick % self.__ticks_in_beat
        measure: int = self.mbt.measure + (beat // self.__numerator)
        beat = beat % self.__numerator
        self.mbt = mbt_container(measure=measure, beat=beat, tick=tick)

    def is_middle_of_measure(self) -> bool:
        """
        小節の途中か否か.

        Returns:
          bool: 小節の途中なら True そうでなければ False
        """
        return self.mbt.tick > 0 or self.mbt.beat > 0

    def reset_to_next_measure(self) -> None:
        """次の小節へリセットする."""
        tick: int = 0
        beat: int = 0
        measure: int = self.mbt.measure + 1
        self.mbt = mbt_container(measure=measure, beat=beat, tick=tick)


@dataclasses.dataclass(frozen=True)
class hhmmssSSS:
    """絶対時間（秒）から時分秒へ変換."""

    hour: int
    minute: int
    second: int
    millisecond: int

    def __init__(self, abs_time: float) -> None:
        """
        __init__.

        Args:
          abs_time (float): 絶対時間（秒）
        """
        ms: int = int(abs_time * 1000) % 1000
        s: int = int(abs_time) % 60
        m: int = int(abs_time) // 60
        h: int = m // 60
        m = m % 60
        object.__setattr__(self, 'hour', h)
        object.__setattr__(self, 'minute', m)
        object.__setattr__(self, 'second', s)
        object.__setattr__(self, 'millisecond', ms)

    def __repr__(self) -> str:
        """
        __repr__.

        Returns:
          str: 秒のみの絶対時間を時分秒の固定桁形式に変換した文字列
            00:00:00.000 の形式となる。
        """
        return f'{self.hour:02}:{self.minute:02}:' \
            f'{self.second:02}.{self.millisecond:03}'


@dataclasses.dataclass(frozen=True)
class note_event_container:
    """ノート ON/OFF イベント情報クラス."""

    type: Optional[str] = None
    channel: int = 0
    note: int = 0
    velocity: int = 0

    def __repr__(self) -> str:
        """__repr__."""
        return f"note_event('{self.type}', channel={self.channel}," \
            f' note={self.note} {note_to_ipn(self.note)},' \
            f' velocity={self.velocity})'


@dataclasses.dataclass(frozen=True)
class note_event_time_container:
    """ノート ON/OFF イベント＋時刻情報クラス."""

    abs_time: float
    mbt: mbt_container
    note_event: note_event_container
    abs_tick: int

    def __repr__(self) -> str:
        """__repr__."""
        return f'note_event_time(T {hhmmssSSS(self.abs_time)},' \
            f' MBT {self.mbt},' \
            f" '{self.note_event.type}'," \
            f' channel={self.note_event.channel},' \
            f' note={self.note_event.note}' \
            f' {note_to_ipn(self.note_event.note)},' \
            f' velocity={self.note_event.velocity})'


@dataclasses.dataclass(frozen=True)
class note_container:
    """ノート（ON/OFF 組になっているもの）クラス."""

    note_on: note_event_time_container
    note_off: note_event_time_container

    def __repr__(self) -> str:
        """__repr__."""
        return f'note(On {self.note_on}, Off {self.note_off})'


# mido 1.2.10 向けワークアラウンド要否フラグ
b_workaround_unknown_meta: bool = False

# mido 1.2.10 向けワークアラウンド要否判定
try:
    UnknownMetaMessage(type_byte=8).copy(time=0)
except TypeError:
    b_workaround_unknown_meta = True


class smf_notes:
    """SMF から音符を取り出すクラス."""

    # SMF のデフォルトテンポ
    DEFAULT_TEMPO: Final[int] = 500000

    def __init__(self, b_strict: bool = False, verbose: int = 0) -> None:
        """
        __init__.

        Args:
          b_strict (bool): 不正 SMF をエラーとするか
          verbose (int): Verbose レベル
        """
        # 不正 SMF をエラーとするか否か
        self.b_strict: Final[bool] = b_strict
        # Verbose レベル
        self.verbose: Final[int] = verbose
        # SMF
        self.mid: MidiFile = None
        # マージしたトラック
        self.merged_track: MidiTrack = None
        # ノート ON/OFF リスト
        self.note_on_off: List[note_event_time_container] = []
        # ノートリスト（ON/OFF 組になっているもの）
        self.notes: List[note_container] = []
        # SMF の最後の位置
        self.end_of_smf: Optional[Tuple[float, mbt_container, int]] = None

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

    def load(self, filename: Union[str, bytes, os.PathLike[Any]]) -> bool:
        """
        SMF をロード.

        Args:
          filename (PathLike): ロードする SMF のパス名

        Returns:
          bool: 成功なら True そうでなければ False
        """
        self.__print_v(f'Opening file {str(filename)}')
        self.mid = MidiFile(filename)

        return self.__process_smf()

    def read_data(self, mid: MidiFile) -> bool:
        """
        SMF データを読み込む.

        Args:
          mid (MidiFile): 読み込む SMF データの mido.MidiFile オブジェクト

        Returns:
          bool: 成功なら True そうでなければ False
        """
        self.mid = mid
        return self.__process_smf()

    def __workaround_unknown_meta(self) -> None:
        """
        ワークアラウンド：mido 1.2.10 のバグ回避.

        https://github.com/mido/mido/pull/364
        が mido にマージされれば不要となる。
        処理内容は
        https://gist.github.com/trueroad/44728aaed2ec5cab173900459fbe16e7
        と同じで unknown meta message を削除している。
        """
        if not b_workaround_unknown_meta:
            return

        mid_in: MidiFile = self.mid
        mid_out: MidiFile = MidiFile(type=mid_in.type,
                                     ticks_per_beat=mid_in.ticks_per_beat,
                                     charset=mid_in.charset)

        track_in: MidiTrack
        for track_in in mid_in.tracks:
            track_out: MidiTrack = mid_out.add_track()

            time: int = 0
            msg: Message
            for msg in track_in:
                time += msg.time
                if msg.type == 'unknown_meta':
                    self.__print_v(f'Warning: remove unknown_meta: {msg}')
                else:
                    track_out.append(msg.copy(time=time))
                    time = 0

        self.mid = mid_out

    def __process_smf(self) -> bool:
        """
        読み込んだ SMF を処理.

        Returns:
          bool: 成功なら True そうでなければ False
        """
        # SMF type 2 を弾く
        if self.mid.type < 0 or self.mid.type > 1:
            self.__print_v(f'Unknown SMF type {self.mid.type}',
                           file=sys.stderr)
            return False

        # mido 1.2.10 向けワークアラウンド
        self.__workaround_unknown_meta()

        # 全トラックをマージして 1 つにする
        self.merged_track = merge_tracks(self.mid.tracks)

        # ノート ON/OFF リストを作る
        if not self.__create_note_on_off():
            return False

        # ノートリスト（ON/OFF 組になっているもの）を作る
        if not self.__create_notes():
            return False

        return True

    def __create_note_on_off(self) -> bool:
        """ノート ON/OFF リストを作る."""
        self.__print_v('\nCreating note on/off list')

        # SMF テンポ
        tempo: int = self.DEFAULT_TEMPO

        # 開始からの絶対時間（秒）
        abs_time: float = 0.0

        # MBT （小節、拍、tick）
        mbtc: mbt_calc = mbt_calc(self.mid.ticks_per_beat)

        # 開始からの絶対 tick （小節・拍を無視して tick を累積したもの）
        abs_tick: int = 0

        # ノート ON/OFF 数
        note_ons: int = 0
        note_offs: int = 0

        # ノート ON/OFF リスト初期化
        self.note_on_off = []

        # トラックをイテレートしてメッセージを取り出し、
        # ノート ON/OFF リストを作る
        for msg in self.merged_track:
            # メッセージの内容を表示
            self.__print_v(msg)

            # メッセージの time から delta 秒や MBT （小節・拍・tick）を計算
            if msg.time > 0:
                # メッセージの time を delta 秒に換算
                delta: float = \
                    tick2second(msg.time, self.mid.ticks_per_beat, tempo)

                # 時分秒を更新
                abs_time += delta

                # MBT を更新
                mbtc.add_ticks(msg.time)

                # 絶対 tick を更新
                abs_tick += msg.time

            else:
                # 前回のメッセージと同時刻なので何も更新しない
                delta = 0

            # 時分秒 と MBT と delta 秒を表示
            self.__print_v(f'  T {hhmmssSSS(abs_time)},'
                           f' MBT {mbtc},'
                           f' delta {delta} s')

            # 計算に必要なメタデータやノート ON/OFF を処理
            if msg.type == 'set_tempo':
                # テンポ変更メタデータだったらテンポを変更する
                tempo = msg.tempo
            elif msg.type == 'time_signature':
                # 拍子変更メタデータだったら拍子を変更する
                mbtc.set_time_signature(msg.numerator, msg.denominator)
            elif msg.type == 'note_on' or msg.type == 'note_off':
                # ノート ON/OFF ならリストに追加
                note_event: note_event_container = \
                    note_event_container(msg.type,
                                         msg.channel,
                                         msg.note,
                                         msg.velocity)
                note_event_time: note_event_time_container = \
                    note_event_time_container(abs_time,
                                              mbtc.mbt,
                                              note_event,
                                              abs_tick)
                self.note_on_off.append(note_event_time)
                if msg.type == 'note_on' and msg.velocity > 0:
                    # 真のノート ON 数をカウント
                    note_ons += 1
                elif (msg.type == 'note_off'
                      or
                      (msg.type == 'note_on' and msg.velocity == 0)):
                    # 真のノート OFF 数をカウント
                    note_offs += 1
                else:
                    # ここは実行されないハズ
                    self.__print_v('***Error*** note on/off',
                                   file=sys.stderr)

        # SMF の最後の位置を記録
        self.end_of_smf = (abs_time, mbtc.mbt, abs_tick)
        self.__print_v(f'\nEnd of SMF: T {hhmmssSSS(self.end_of_smf[0])},'
                       f' MBT {self.end_of_smf[1]},'
                       f' Absolute MIDI tick {self.end_of_smf[2]}')
        # ノート ON/OFF リストの長さと
        # 真のノート ON 数、真のノート OFF 数を表示
        self.__print_v('Created note on/off list:'
                       f' len {len(self.note_on_off)},'
                       f' on {note_ons}, off {note_offs}, ', end='')
        # ノート ON/OFF リストの長さと
        # 真のノート ON 数、真のノート OFF 数に問題が無いかチェック
        if ((note_ons != note_offs
             or note_ons + note_offs != len(self.note_on_off))):
            # 矛盾が発生している
            if self.b_strict:
                self.__print_v('error')
                return False
            else:
                self.__print_v('warning')
                return True

        self.__print_v('ok')

        return True

    def __create_notes(self) -> bool:
        """ノートリスト（ON/OFF 組になっているもの）を作る."""
        # ノート ON/OFF リストをイテレートして、ノートリストを作る
        self.__print_v('\nCreating note list')

        # ノートリスト初期化
        self.notes = []

        # 組み合わせ済みノート OFF のインデックスのリスト
        combined_note_off_indexes: List[int] = []

        i: int
        for i in range(len(self.note_on_off)):
            # ノート ON/OFF リスト中のインデックスとその内容を表示
            self.__print_v(f'{i}: {self.note_on_off[i]}')

            # ノートイベントが真のノート ON か否か判定
            note_event: note_event_container = self.note_on_off[i].note_event
            if note_event.type == 'note_on' and note_event.velocity > 0:
                # 真のノート ON だったら、組になるノート OFF を探す
                found: bool = False
                # 探索範囲は次のメッセージから最後まで
                j: int
                for j in range(i + 1, len(self.note_on_off)):
                    if j in combined_note_off_indexes:
                        # 組み合わせ済みのノート OFF なのでスキップ
                        continue
                    note_event2: note_event_container = \
                        self.note_on_off[j].note_event
                    if (((note_event2.type == 'note_off'
                          or
                          (note_event2.type == 'note_on'
                           and note_event2.velocity == 0))
                         and
                         (note_event.channel == note_event2.channel
                          and note_event.note == note_event2.note))):
                        # 組になる真のノート OFF を発見、ノートリストに追加
                        n: note_container = \
                            note_container(self.note_on_off[i],
                                           self.note_on_off[j])
                        self.notes.append(n)
                        # フラグを立てて探索終了
                        found = True
                        combined_note_off_indexes.append(j)
                        break
                if not found:
                    # 組になる真のノート OFF が発見できなかった
                    self.__print_v('*** Missing *** note off not found for'
                                   f' {self.note_on_off[i]}',
                                   file=sys.stderr)
                    if self.b_strict:
                        self.__print_v('  -> error')
                        return False
                    self.__print_v('  -> warning')
                    if self.end_of_smf is not None:
                        # SMF の最後でノート OFF されたとみなす
                        note_event_force_off: note_event_container = \
                            note_event_container('note_off',
                                                 note_event.channel,
                                                 note_event.note,
                                                 0)
                        note_event_time_force_off: \
                            note_event_time_container = \
                            note_event_time_container(self.end_of_smf[0],
                                                      self.end_of_smf[1],
                                                      note_event_force_off,
                                                      self.end_of_smf[2])
                        nf: note_container = \
                            note_container(self.note_on_off[i],
                                           note_event_time_force_off)
                        self.notes.append(nf)
            # ノートイベントが真のノート OFF か否か判定
            if note_event.type == 'note_off' or \
               (note_event.type == 'note_on' and note_event.velocity == 0):
                if i not in combined_note_off_indexes:
                    # 組み合わせ済みではないノート OFF が現れた
                    self.__print_v('*** Missing *** note on not found for'
                                   f' {self.note_on_off[i]}',
                                   file=sys.stderr)
                    if self.b_strict:
                        self.__print_v('  -> error')
                        return False
                    self.__print_v('  -> warning')

        # ノートリストの長さを表示
        self.__print_v(f'\nCreated note list: len {len(self.notes)}, ',
                       end='')
        # ノートリストの長さをノート ON/OFF リストの長さと比較してチェック
        if len(self.note_on_off) != (len(self.notes) * 2):
            # 矛盾が発生している
            if self.b_strict:
                self.__print_v('error')
                return False
            else:
                self.__print_v('warning')
                return True

        self.__print_v('ok')
        return True

    def get_smf_specs(self) -> Tuple[int, int, int]:
        """
        SMF のスペックを取得する.

        Returns:
          Tuple
            int: SMF タイプ
            int: TPQN (ticks per quater note) タイムベース
            int: トラック数
        """
        return (self.mid.type, self.mid.ticks_per_beat, len(self.mid.tracks))

    def get_notes(self) -> List[note_container]:
        """
        ノートリストを取得する.

        Returns:
          List[note_container]: ノートリスト
        """
        return self.notes


def note_to_ipn(note_no: int) -> str:
    """
    ノート番号を international pitch notation へ変換.

    Args:
      note_no (int): MIDI ノート番号

    Returns:
      str: international pitch notation 表記の文字列
        例： 60 は "C4"、61 は "C#/Db4"
    """
    n: int = note_no % 12
    o: int = note_no // 12 - 1
    t: Final[List[str]] = \
        ['C', 'C#/Db', 'D', 'Eb/D#', 'E', 'F',
         'F#/Gb', 'G', 'Ab/G#', 'A', 'Bb/A#', 'B']

    return f'{t[n]}{o}'


def main() -> None:
    """テスト用メイン."""
    print(f'Parsing SMF (Standard MIDI File) {VERSION}\n\n'
          'https://gist.github.com/trueroad/'
          '52b7c4c98eec5fdf0ff3f62d64ec17bd\n\n'
          'Copyright (C) 2021, 2022, 2024 Masamichi Hosoda.\n'
          'All rights reserved.\n')

    import argparse
    parser: argparse.ArgumentParser = argparse.ArgumentParser()
    parser.add_argument('FILENAME.mid', help='SMF to load.')
    parser.add_argument('--strict', help='Be strict checking note on/off.',
                        action='store_true')

    args: argparse.Namespace = parser.parse_args()
    vargs: Dict[str, Any] = vars(args)

    filename: str = vargs['FILENAME.mid']
    b_strict: bool = vargs['strict']

    print('Workaround for mido 1.2.10 unknown meta message: '
          f'{b_workaround_unknown_meta}\n'
          f'Filename: {filename}\n'
          f'Strict  : {b_strict}\n')

    sn: smf_notes = smf_notes(b_strict=b_strict, verbose=2)
    if not sn.load(filename):
        print("Error")
        sys.exit(1)

    print('\nCreated note list')
    i: int
    note: note_container
    for i, note in enumerate(sn.get_notes()):
        print(f'{i}: {note}')


if __name__ == "__main__":
    main()

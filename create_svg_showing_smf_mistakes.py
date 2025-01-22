#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Create SVG showing SMF (Standard MIDI File) mistakes.

https://github.com/trueroad/create_svg_showing_smf_mistakes

Copyright (C) 2024, 2025 Masamichi Hosoda.
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

from dataclasses import dataclass
import math
import os
# import pprint
import sys
from typing import Any, BinaryIO, Final, TextIO, Union

import cairo

# https://gist.github.com/trueroad/97477dab8beca099afeb4af5199634e2
import smf_diff
# https://gist.github.com/trueroad/b0d051af003c61aafb3eac0c051e5f89
import config_file


@dataclass(frozen=True)
class rect_container:
    """Rectangle container class."""

    left: float
    top: float
    right: float
    bottom: float


@dataclass(frozen=True)
class tb_container:
    """Top and bottom container class."""

    top: float
    bottom: float


@dataclass(frozen=True)
class tick_noteno_container:
    """Tick noteno container class."""

    tick: int
    noteno: int


@dataclass(frozen=True)
class noteno_row_container:
    """Noteno row container class."""

    noteno: int
    row: int


@dataclass(frozen=True)
class extra_noteno_tick_container:
    """Extra noteno tick container class."""

    noteno: set[int]
    abs_tick_before_extra: int
    abs_tick_after_extra: int
    b_before_model_first: bool
    b_after_model_last: bool


class tick_note_rect:
    """Tick note rect class."""

    def __init__(self) -> None:
        """__init__."""
        # 絶対tickとノート番号の組み合わせから、符頭の座標を得る辞書
        self.note_dict: dict[tick_noteno_container, rect_container] = {}
        # 絶対tickから、符頭の範囲の座標を得る辞書
        self.tick_rect_dict: dict[int, rect_container] = {}
        # 絶対tickから、行番号を得る辞書
        self.tick_row_dict: dict[int, int] = {}
        # 行番号から、符頭の範囲の座標を得る辞書
        self.row_dict: dict[int, rect_container] = {}
        # ノート番号と行番号の組み合わせから、符頭の範囲の座標を得る辞書
        self.noteno_dict: dict[noteno_row_container, rect_container] = {}
        # 全ノート番号と行番号の組み合わせから、y座標範囲を得る辞書
        self.extra_y_dict: dict[noteno_row_container, tb_container] = {}
        # SVGの幅
        self.svg_width: float
        # SVGの高さ
        self.svg_height: float
        # 標準的な符頭の幅
        self.head_width: float
        # 標準的な不等の高さ
        self.head_height: float

    def load_text(self, filename: Union[str, bytes, os.PathLike[Any]]
                  ) -> None:
        """Load tick note rect text."""
        f: TextIO
        with open(filename, 'r') as f:
            line: str
            for line in f:
                if line.startswith('#'):
                    continue
                items: list[str] = line.split()
                if len(items) == 7:
                    if items[0] == 'note':
                        tn: tick_noteno_container = tick_noteno_container(
                            tick=int(items[1]),
                            noteno=int(items[2]))
                        rect: rect_container = rect_container(
                            left=float(items[3]),
                            top=float(items[4]),
                            right=float(items[5]),
                            bottom=float(items[6]))
                        self.note_dict[tn] = rect
                    elif items[0] == 'tick':
                        tick: int = int(items[1])
                        rect = rect_container(
                            left=float(items[2]),
                            top=float(items[3]),
                            right=float(items[4]),
                            bottom=float(items[5]))
                        row: int = int(items[6])
                        self.tick_rect_dict[tick] = rect
                        self.tick_row_dict[tick] = row
                    elif items[0] == 'noteno':
                        nr: noteno_row_container = noteno_row_container(
                            noteno=int(items[1]),
                            row=int(items[2]))
                        rect = rect_container(
                            left=float(items[3]),
                            top=float(items[4]),
                            right=float(items[5]),
                            bottom=float(items[6]))
                        self.noteno_dict[nr] = rect
                elif len(items) == 5:
                    if items[0] == 'extra-y':
                        nr = noteno_row_container(
                            noteno=int(items[2]),
                            row=int(items[1]))
                        tb: tb_container = tb_container(
                            top=float(items[3]),
                            bottom=float(items[4]))
                        self.extra_y_dict[nr] = tb
                elif len(items) == 6:
                    if items[0] == 'row':
                        row = int(items[1])
                        rect = rect_container(
                            left=float(items[2]),
                            top=float(items[3]),
                            right=float(items[4]),
                            bottom=float(items[5]))
                        self.row_dict[row] = rect
                elif len(items) == 3:
                    if items[0] == 'size':
                        self.svg_width = float(items[1])
                        self.svg_height = float(items[2])
                    elif items[0] == 'head':
                        self.head_width = float(items[1])
                        self.head_height = float(items[2])
        # print(f'width = {self.svg_width}, height = {self.svg_height}')
        # pprint.pprint(self.note_dict)


def draw_cross(context: cairo.Context, rect: rect_container) -> None:
    """Draw cross."""
    context.set_line_width(2)
    context.set_source_rgba(1, 0, 0, 0.7)
    context.move_to(rect.left, rect.top)
    context.line_to(rect.right, rect.bottom)
    context.move_to(rect.right, rect.top)
    context.line_to(rect.left, rect.bottom)
    context.stroke()


def draw_ellipse(context: cairo.Context, rect: rect_container) -> None:
    """Draw ellipse."""
    context.save()
    context.set_source_rgba(1, 0, 0, 0.5)
    context.translate((rect.left + rect.right) / 2,
                      (rect.top + rect.bottom) / 2)
    context.scale((rect.right - rect.left) / 2,
                  (rect.bottom - rect.top) / 2)
    context.arc(0.0, 0.0, 1.0, 0.0, 2 * math.pi)
    context.fill()
    context.restore()


def draw_rectangle(context: cairo.Context, rect: rect_container) -> None:
    """Draw rectangle."""
    context.set_source_rgba(1, 0, 0, 0.5)
    context.rectangle(rect.left, rect.top,
                      rect.right - rect.left, rect.bottom - rect.top)
    context.fill()


def draw_line(context: cairo.Context,
              x1: float, y1: float, x2: float, y2: float) -> None:
    """Draw line."""
    context.set_line_width(1)
    context.set_source_rgba(1, 0, 0, 0.7)
    context.move_to(x1, y1)
    context.line_to(x2, y2)
    context.stroke()


def draw_text(context: cairo.Context,
              rect: rect_container, text: str) -> None:
    """Draw text."""
    context.select_font_face('sans-serif')
    context.set_font_size(rect.bottom - rect.top)
    context.set_source_rgba(1, 0, 0, 0.9)
    # 指定した座標がベースラインの左端になる
    # よくあるフォントはベースラインの上が 0.88 下が 0.12 あるので、
    # rectの上下ピッタリに合わせるには以下のようにする。
    # （和文フォントはだいたい合うが欧文はフォントや環境次第）
    context.move_to(rect.left, rect.top + (rect.bottom - rect.top) * 0.88)
    context.show_text(text)


class mistakes:
    """Mistakes class."""

    def __init__(self) -> None:
        """__init__."""
        self.tnr: tick_note_rect = tick_note_rect()
        self.sd: smf_diff.smf_difference = smf_diff.smf_difference()
        self.cf: config_file.config_file = config_file.config_file()

        self.context: cairo.Context

        # 遅すぎ検出スレッショルド
        self.max_time_ratio: float = 1.2
        # 速すぎ検出スレッショルド
        self.min_time_ratio: float = 0.8
        # 長すぎ検出スレッショルド
        self.max_duration_ratio: float = 1.2
        # 短すぎ検出スレッショルド
        self.min_duration_ratio: float = 0.8

        # 遅すぎ上方パディング（単位：符頭高さの倍数）
        self.too_slow_top_padding: float = 1.0
        # 遅すぎ下方パディング（単位：符頭高さの倍数）
        self.too_slow_bottom_padding: float = 0.0
        # 遅すぎテキスト
        self.too_slow_text: str = 'Too slow'
        # 速すぎ上方パディング（単位：符頭高さの倍数）
        self.too_fast_top_padding: float = 0.0
        # 速すぎ下方パディング（単位：符頭高さの倍数）
        self.too_fast_bottom_padding: float = 1.0
        # 速すぎテキスト
        self.too_fast_text: str = 'Too fast'
        # 長すぎテキスト
        self.too_long_text: str = 'Too long'
        # 短すぎテキスト
        self.too_short_text: str = 'Too short'

        # 左側にはみ出る際の余計な音符（個別）描画領域幅（単位：符頭幅の倍数）
        self.extra_note_row_left: float = 2.0
        # 右側にはみ出る際の余計な音符（個別）描画領域幅（単位：符頭幅の倍数）
        self.extra_note_row_right: float = 2.0

    def load_text(self, filename: Union[str, bytes, os.PathLike[Any]]
                  ) -> None:
        """Load list text."""
        self.tnr.load_text(filename)

    def load_model(self, filename: Union[str, bytes, os.PathLike[Any]]
                   ) -> bool:
        """Load model SMF."""
        return self.sd.load_model(filename)

    def load_config(self, filename: Union[str, os.PathLike[str]]
                    ) -> bool:
        """Load model config."""
        if not self.cf.load_config_file(filename):
            return False

        if self.cf.has_value('threshold', 'max_time_ratio'):
            self.max_time_ratio = self.cf.get_value_float(
                'threshold', 'max_time_ratio')
        if self.cf.has_value('threshold', 'min_time_ratio'):
            self.min_time_ratio = self.cf.get_value_float(
                'threshold', 'min_time_ratio')
        if self.cf.has_value('threshold', 'max_duration_ratio'):
            self.max_duration_ratio = self.cf.get_value_float(
                'threshold', 'max_duration_ratio')
        if self.cf.has_value('threshold', 'min_duration_ratio'):
            self.min_duration_ratio = self.cf.get_value_float(
                'threshold', 'min_duration_ratio')
        if self.cf.has_value('text', 'too_slow'):
            self.too_slow_text = self.cf.get_value_str('text', 'too_slow')
        if self.cf.has_value('text', 'too_fast'):
            self.too_fast_text = self.cf.get_value_str('text', 'too_fast')
        if self.cf.has_value('text', 'too_long'):
            self.too_long_text = self.cf.get_value_str('text', 'too_long')
        if self.cf.has_value('text', 'too_short'):
            self.too_short_text = self.cf.get_value_str('text', 'too_short')

        self.tnr.load_text(self.cf.config_dir /
                           self.cf.get_value_str('model', 'list'))
        return self.sd.load_model(self.cf.config_dir /
                                  self.cf.get_value_str('model', 'smf'))

    def load_foreval(self, filename: Union[str, bytes, os.PathLike[Any]]
                     ) -> bool:
        """Load foreval SMF."""
        return self.sd.load_foreval(filename)

    def diff(self) -> None:
        """Do diff."""
        self.sd.diff()
        self.sd.calc_note_timing()

    def create_svg(self, fobj: Union[str, bytes, BinaryIO]
                   ) -> None:
        """Create SVG."""
        surface: cairo.SVGSurface
        with cairo.SVGSurface(fobj, self.tnr.svg_width, self.tnr.svg_height
                              ) as surface:
            self.context = cairo.Context(surface)
            self.draw_all()

    def draw_notes(self) -> None:
        """Draw notes for debug."""
        for nr in self.tnr.note_dict.values():
            draw_rectangle(self.context, nr)

    def draw_tick_rects(self) -> None:
        """Draw tick rects for debug."""
        for tr in self.tnr.tick_rect_dict.values():
            draw_rectangle(self.context, tr)

    def draw_rows(self) -> None:
        """Draw rows for debug."""
        for rr in self.tnr.row_dict.values():
            draw_rectangle(self.context, rr)

    def draw_notenos(self) -> None:
        """Draw notenos for debug."""
        for nnr in self.tnr.noteno_dict.values():
            draw_rectangle(self.context, nnr)

    def draw_all(self) -> None:
        """Draw all."""
        self.draw_missing_notes()
        self.draw_extra_notes()
        self.draw_too_slow()
        self.draw_too_fast()
        self.draw_too_long()
        self.draw_too_short()

    def draw_missing_notes(self) -> None:
        """Draw missing notes."""
        for nc in self.sd.missing_note:
            # pprint.pprint(nc)
            rect: rect_container = self.tnr.note_dict[tick_noteno_container(
                tick=nc.note_on.abs_tick,
                noteno=nc.note_on.note_event.note)]
            # pprint.pprint(rect)
            draw_cross(self.context, rect)

    def draw_extra_notes(self) -> None:
        """Draw extra notes."""
        entc_list: list[extra_noteno_tick_container] = []
        foreval_noteno: set[int] = set()
        abs_tick_before_extra_before: int = -1
        abs_tick_after_extra_before: int = -1
        b_before_model_first_before: bool = False
        b_after_model_last_before: bool = False
        for enc in self.sd.extra_note:
            if ((abs_tick_before_extra_before ==
                 enc.abs_tick_before_extra
                 and
                 abs_tick_after_extra_before ==
                 enc.abs_tick_after_extra
                 and
                 b_before_model_first_before ==
                 enc.b_before_model_first
                 and
                 b_after_model_last_before ==
                 enc.b_after_model_last)):
                foreval_noteno.add(enc.note.note_on.note_event.note)
                continue

            if abs_tick_before_extra_before >= 0:
                entc_list.append(extra_noteno_tick_container(
                    noteno=foreval_noteno,
                    abs_tick_before_extra=abs_tick_before_extra_before,
                    abs_tick_after_extra=abs_tick_after_extra_before,
                    b_before_model_first=b_before_model_first_before,
                    b_after_model_last=b_after_model_last_before))

            foreval_noteno = {enc.note.note_on.note_event.note}
            abs_tick_before_extra_before = enc.abs_tick_before_extra
            abs_tick_after_extra_before = enc.abs_tick_after_extra
            b_before_model_first_before = enc.b_before_model_first
            b_after_model_last_before = enc.b_after_model_last

        if abs_tick_before_extra_before >= 0:
            entc_list.append(extra_noteno_tick_container(
                noteno=foreval_noteno,
                abs_tick_before_extra=abs_tick_before_extra_before,
                abs_tick_after_extra=abs_tick_after_extra_before,
                b_before_model_first=b_before_model_first_before,
                b_after_model_last=b_after_model_last_before))

        for entc in entc_list:
            row_before: int = \
                self.tnr.tick_row_dict[entc.abs_tick_before_extra]
            row_after: int = \
                self.tnr.tick_row_dict[entc.abs_tick_after_extra]

            left: float = \
                self.tnr.tick_rect_dict[entc.abs_tick_before_extra].left
            right: float = \
                self.tnr.tick_rect_dict[entc.abs_tick_after_extra].right
            top: float = self.tnr.extra_y_dict[noteno_row_container(
                noteno=max(entc.noteno),
                row=row_before)].top
            bottom: float = self.tnr.extra_y_dict[noteno_row_container(
                noteno=min(entc.noteno),
                row=row_before)].bottom

            if row_before != row_after:
                right = \
                    self.tnr.tick_rect_dict[entc.abs_tick_before_extra].right
            if entc.b_before_model_first:
                left -= self.tnr.head_width
            if entc.b_after_model_last or row_before != row_after:
                right += self.tnr.head_width

            rect = rect_container(
                left=left, top=top, right=right, bottom=bottom)
            draw_ellipse(self.context, rect)

    def draw_extra_notes_each(self) -> None:
        """Draw extra notes each."""
        for enc in self.sd.extra_note:
            tick_before = enc.abs_tick_before_extra
            tick_after = enc.abs_tick_after_extra
            row_before = self.tnr.tick_row_dict[tick_before]
            row_after = self.tnr.tick_row_dict[tick_after]

            # 描画候補領域左端：前の対応する音符の左側
            area_left = self.tnr.tick_rect_dict[tick_before].left
            # 描画候補領域右端：後の対応する音符の右側
            area_right = self.tnr.tick_rect_dict[tick_after].right

            # 描画候補領域の補正
            if row_before != row_after:
                # 改行あり
                # 最初の行（前の対応する音符がある行）の右端からはみ出させる
                area_right = self.tnr.row_dict[row_before].right + \
                    self.extra_note_row_right * self.tnr.head_width
            if enc.b_before_model_first:
                # 前の対応する音符無し
                # 最初の音符の左側からはみ出させる
                area_left -= self.extra_note_row_left * self.tnr.head_width
            if enc.b_after_model_last and row_before == row_after:
                # 後の対応する音符無し、かつ改行なし
                # 最後の音符の右側からはみ出させる
                area_right += self.extra_note_row_right * self.tnr.head_width

            # 前後の対応する音符との時間関係を線形補間で求める

            # 前後の対応する音符間のtick
            ticks_foreval = float(enc.foreval_abs_tick_after_extra -
                                  enc.foreval_abs_tick_before_extra)
            # 余計な音符の相対的な位置
            relative = (enc.note.note_on.abs_tick -
                        enc.foreval_abs_tick_before_extra) / ticks_foreval
            # 描画候補領域の幅
            area_width = area_right - area_left

            # 描画位置
            left = area_left + (area_width - self.tnr.head_width) * relative
            right = left + self.tnr.head_width
            tb = self.tnr.extra_y_dict[noteno_row_container(
                noteno=enc.note.note_on.note_event.note,
                row=row_before)]
            top = tb.top
            bottom = tb.bottom

            # 描画
            rect = rect_container(
                left=left, top=top, right=right, bottom=bottom)
            draw_ellipse(self.context, rect)

    def draw_too_slow(self) -> None:
        """Draw too slow."""
        too_slow_tick: set[int] = set()
        for nt in self.sd.note_timing:
            if nt.ratio is not None and nt.ratio > self.max_time_ratio:
                too_slow_tick.add(nt.note_model.note_on.abs_tick)
        for tick in too_slow_tick:
            rect = self.tnr.tick_rect_dict[tick]
            x = (rect.left + rect.right) / 2
            draw_line(self.context,
                      x,
                      rect.top -
                      self.too_slow_top_padding * self.tnr.head_height,
                      x,
                      rect.bottom +
                      self.too_slow_bottom_padding * self.tnr.head_height)
            rect_text = rect_container(
                left=rect.left,
                top=rect.top -
                (self.too_slow_top_padding + 1) * self.tnr.head_height,
                right=rect.right,
                bottom=rect.top -
                self.too_slow_top_padding * self.tnr.head_height)
            draw_text(self.context, rect_text, self.too_slow_text)

    def draw_too_fast(self) -> None:
        """Draw too fast."""
        too_fast_tick: set[int] = set()
        for nt in self.sd.note_timing:
            if nt.ratio is not None and nt.ratio < self.min_time_ratio:
                too_fast_tick.add(nt.note_model.note_on.abs_tick)
        for tick in too_fast_tick:
            rect = self.tnr.tick_rect_dict[tick]
            x = (rect.left + rect.right) / 2
            draw_line(self.context,
                      x,
                      rect.top -
                      self.too_fast_top_padding * self.tnr.head_height,
                      x,
                      rect.bottom +
                      self.too_fast_bottom_padding * self.tnr.head_height)
            rect_text = rect_container(
                left=rect.left,
                top=rect.bottom +
                self.too_fast_bottom_padding * self.tnr.head_height,
                right=rect.right,
                bottom=rect.bottom +
                (self.too_fast_bottom_padding + 1) * self.tnr.head_height)
            draw_text(self.context, rect_text, self.too_fast_text)

    def draw_too_long(self) -> None:
        """Draw too long."""
        for nt in self.sd.note_timing:
            if nt.ratio_duration > self.max_duration_ratio:
                draw_text(self.context,
                          self.tnr.note_dict[tick_noteno_container(
                              tick=nt.note_model.note_on.abs_tick,
                              noteno=nt.note_model.note_on.note_event.note)],
                          self.too_long_text)

    def draw_too_short(self) -> None:
        """Draw too short."""
        for nt in self.sd.note_timing:
            if nt.ratio_duration < self.min_duration_ratio:
                draw_text(self.context,
                          self.tnr.note_dict[tick_noteno_container(
                              tick=nt.note_model.note_on.abs_tick,
                              noteno=nt.note_model.note_on.note_event.note)],
                          self.too_short_text)


def main() -> None:
    """Do main."""
    if len(sys.argv) != 4:
        print('Usage: ./create_svg_showing_smf_mistakes.py '
              '[(in)CONFIG.TOML (in)FOREVAL.MID (out)MISTAKES.SVG]')
        sys.exit(1)

    config_filename: Final[str] = sys.argv[1]
    foreval_filename: Final[str] = sys.argv[2]
    svg_filename: Final[str] = sys.argv[3]

    mst: mistakes = mistakes()

    mst.load_config(config_filename)
    mst.load_foreval(foreval_filename)
    mst.diff()

    mst.create_svg(svg_filename)


if __name__ == '__main__':
    main()

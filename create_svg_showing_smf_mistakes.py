#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Create SVG showing SMF (Standard MIDI File) mistakes.

https://github.com/trueroad/create_svg_showing_smf_mistakes

Copyright (C) 2024 Masamichi Hosoda.
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
from typing import Any, Final, TextIO, Union

import cairo

# https://gist.github.com/trueroad/97477dab8beca099afeb4af5199634e2
import smf_diff


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
        self.note_dict: dict[tick_noteno_container, rect_container] = {}
        self.tick_rect_dict: dict[int, rect_container] = {}
        self.tick_row_dict: dict[int, int] = {}
        self.row_dict: dict[int, rect_container] = {}
        self.noteno_dict: dict[noteno_row_container, rect_container] = {}
        self.extra_y_dict: dict[noteno_row_container, tb_container] = {}
        self.svg_width: float
        self.svg_height: float
        self.head_width: float
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


def main() -> None:
    """Do main."""
    if len(sys.argv) != 5:
        print('Usage: ./create_svg_showing_smf_mistakes.py '
              '[(in)LIST.TXT (in)MODEL.MID (in)FOREVAL.MID (out)MISTAKES.SVG]')
        sys.exit(1)

    list_filename: Final[str] = sys.argv[1]
    model_filename: Final[str] = sys.argv[2]
    foreval_filename: Final[str] = sys.argv[3]
    svg_filename: Final[str] = sys.argv[4]

    tnr: tick_note_rect = tick_note_rect()
    tnr.load_text(list_filename)

    sd: smf_diff.smf_difference = smf_diff.smf_difference()
    sd.load_model(model_filename)
    sd.load_foreval(foreval_filename)
    sd.diff()

    surface: cairo.SVGSurface
    with cairo.SVGSurface(svg_filename, tnr.svg_width, tnr.svg_height
                          ) as surface:
        context: cairo.Context = cairo.Context(surface)

        for nc in sd.missing_note:
            # pprint.pprint(nc)
            rect: rect_container = tnr.note_dict[tick_noteno_container(
                tick=nc.note_on.abs_tick,
                noteno=nc.note_on.note_event.note)]
            # pprint.pprint(rect)
            draw_cross(context, rect)

        entc_list: list[extra_noteno_tick_container] = []
        foreval_noteno: set[int] = set()
        abs_tick_before_extra_before: int = -1
        abs_tick_after_extra_before: int = -1
        b_before_model_first_before: bool = False
        b_after_model_last_before: bool = False
        for enc in sd.extra_note:
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
            row_before: int = tnr.tick_row_dict[entc.abs_tick_before_extra]
            row_after: int = tnr.tick_row_dict[entc.abs_tick_after_extra]

            left: float = tnr.tick_rect_dict[entc.abs_tick_before_extra].left
            right: float = tnr.tick_rect_dict[entc.abs_tick_after_extra].right
            top: float = tnr.extra_y_dict[noteno_row_container(
                noteno=max(entc.noteno),
                row=row_before)].top - tnr.head_height
            bottom: float = tnr.extra_y_dict[noteno_row_container(
                noteno=min(entc.noteno),
                row=row_before)].bottom + tnr.head_height

            if row_before != row_after:
                right = tnr.tick_rect_dict[entc.abs_tick_before_extra].right
            if entc.b_before_model_first:
                left -= tnr.head_width
            if entc.b_after_model_last or row_before != row_after:
                right += tnr.head_width

            rect = rect_container(
                left=left, top=top, right=right, bottom=bottom)
            draw_ellipse(context, rect)


if __name__ == '__main__':
    main()

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Create tick note rect list.

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
import os
import sys
from typing import Any, Final, Optional, TextIO, Union

# https://gist.github.com/trueroad/52b7c4c98eec5fdf0ff3f62d64ec17bd
import smf_parse


@dataclass(frozen=True)
class rect_container:
    """Rectangle container class."""

    left: float
    top: float
    right: float
    bottom: float


@dataclass(frozen=True)
class point_and_click_container:
    """Point and click container class."""

    row: int
    column: int


@dataclass(frozen=True)
class note_container:
    """Note container class."""

    tick: int
    noteno: int
    point_and_click: point_and_click_container


class link_text:
    """Link text class."""

    def __init__(self, tpqn: int) -> None:
        """__init__."""
        # TPQN
        self.tpqn: Final[int] = tpqn
        # PDF CropBox
        self.cropbox: rect_container
        # PDF links
        self.links: dict[point_and_click_container, rect_container] = {}
        # notes
        self.notes: list[note_container] = []

    def load_link(self, filename: Union[str, bytes, os.PathLike[Any]]
                  ) -> None:
        """Load link text."""
        f: TextIO
        with open(filename, 'r') as f:
            line: str
            for line in f:
                items: list[str] = line.split()
                if len(items) == 5 and items[0] == 'CropBox':
                    self.cropbox = rect_container(left=float(items[1]),
                                                  bottom=float(items[2]),
                                                  right=float(items[3]),
                                                  top=float(items[4]))
                elif len(items) == 6 and items[0] == 'Link':
                    if not items[5].startswith('textedit://'):
                        continue
                    pc_items: list[str] = items[5].split(':')
                    self.links[
                        point_and_click_container(
                            row=int(pc_items[-3]),
                            column=int(pc_items[-2]))] = \
                        rect_container(
                            left=float(items[1]),
                            bottom=float(items[2]),
                            right=float(items[3]),
                            top=float(items[4]))

    def load_notes(self, filename: Union[str, bytes, os.PathLike[Any]]
                   ) -> None:
        """Load notes."""
        f: TextIO
        with open(filename, 'r') as f:
            line: str
            for line in f:
                items: list[str] = line.split('\t')
                if len(items) == 6 and items[1] == 'note':
                    pc_items: list[str] = items[5].split()
                    if len(pc_items) != 3 or \
                       pc_items[0] != 'point-and-click':
                        raise RuntimeError('Notes file format error.')
                    if '-' in items[0]:
                        raise RuntimeError('Time format error.'
                                           ' Does not support grace notes.')
                    self.notes.append(note_container(
                        tick=int(float(items[0]) * 4 * self.tpqn),
                        noteno=int(items[2]),
                        point_and_click=point_and_click_container(
                            row=int(pc_items[2]),
                            column=int(pc_items[1]))))

    def calc_size(self) -> tuple[float, float]:
        """
        Calc SVG size.

        Returns:
          tuple[float, float]: SVG width (pt), height (pt)
        """
        width: float = self.cropbox.right - self.cropbox.left
        height: float = self.cropbox.top - self.cropbox.bottom
        return (width, height)

    def conv_axis(self, x: float, y: float) -> tuple[float, float]:
        """
        Convert axis PDF to SVG.

        Args:
          x (float): PDF x axis (pt)
          y (float): PDF y axis (pt)

        Returns:
          tuple[float, float]: SVG x axis (pt) ,y axis (pt)
        """
        svg_x: float = x - self.cropbox.left
        svg_y: float = self.cropbox.top - self.cropbox.bottom - y
        return (svg_x, svg_y)

    def conv_rect(self, rect: rect_container) -> rect_container:
        """
        Convert rect PDF to SVG.

        Args:
          rect (rect_container): PDF rect

        Returns:
          rect_container: SVG rect
        """
        svg_left: float
        svg_top: float
        svg_right: float
        svg_bottom: float
        svg_left, svg_top = self.conv_axis(rect.left, rect.top)
        svg_right, svg_bottom = self.conv_axis(rect.right, rect.bottom)
        return rect_container(left=svg_left, top=svg_top,
                              right=svg_right, bottom=svg_bottom)


def get_tpqn(filename: Union[str, bytes, os.PathLike[Any]]) -> int:
    """
    SMF の TPQN を取得する.

    Args:
      filename (PathLike): SMF のパス名
    Returns:
      int: TPQN
    """
    sn: smf_parse.smf_notes = smf_parse.smf_notes()
    if not sn.load(filename):
        raise RuntimeError('SMF error.')
    tpqn: int
    _, tpqn, _ = sn.get_smf_specs()
    return tpqn


def main() -> None:
    """Do main."""
    if len(sys.argv) != 5:
        print('Usage: ./create_tick_note_rect_list.py '
              '[(in)SMF.MID (in)LINK.TXT (in)STAFF.NOTES (out)LIST.TXT')
        sys.exit(1)

    smf_filename: str = sys.argv[1]
    link_filename: str = sys.argv[2]
    notes_filename: str = sys.argv[3]
    list_filename: str = sys.argv[4]

    tpqn: int = get_tpqn(smf_filename)

    lt: link_text = link_text(tpqn)
    lt.load_link(link_filename)
    lt.load_notes(notes_filename)

    width: float
    height: float
    width, height = lt.calc_size()

    f: TextIO
    with open(list_filename, 'w') as f:
        print('#size\twidth\theight', file=f)
        print(f'size\t{width}\t{height}', file=f)

        print('#note\ttick\tnoteno\tleft\ttop\tright\tbottom', file=f)
        nc: note_container
        for nc in lt.notes:
            rect: rect_container = lt.conv_rect(lt.links[nc.point_and_click])
            print(f'note\t{nc.tick}\t{nc.noteno}\t'
                  f'{rect.left}\t{rect.top}\t{rect.right}\t{rect.bottom}',
                  file=f)


if __name__ == '__main__':
    main()

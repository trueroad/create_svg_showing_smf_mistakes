#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Show PDF link annots.

https://gist.github.com/trueroad/4810ab0845d86fb97510e4e3d3bbed13

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

import sys
from typing import cast, Optional, Union

from pypdf import PageObject, PdfReader
from pypdf.generic import (ArrayObject, DictionaryObject,
                           IndirectObject, PdfObject, RectangleObject)


def main() -> None:
    """Do main."""
    if len(sys.argv) != 2:
        print('Usage: ./show_pdf_link.py [INPUT.PDF]', file=sys.stderr)
        sys.exit(1)

    reader: PdfReader = PdfReader(sys.argv[1])

    page: PageObject
    for page in reader.pages:
        cropbox: RectangleObject = page.cropbox
        crop_left: float = cropbox.left.as_numeric()
        crop_bottom: float = cropbox.bottom.as_numeric()
        crop_right: float = cropbox.right.as_numeric()
        crop_top: float = cropbox.top.as_numeric()
        print(f'\nCropBox\t{crop_left}\t{crop_bottom}'
              f'\t{crop_right}\t{crop_top}')

        if '/Annots' in page:
            annot: Union[IndirectObject, PdfObject]
            for annot in cast(ArrayObject, page['/Annots']):
                if type(annot) is not IndirectObject:
                    raise RuntimeError('It is not IndirectObject.')
                obj: Optional[Union[DictionaryObject, PdfObject]] = \
                    annot.get_object()
                if obj is None:
                    raise RuntimeError('get_object() returns None.')
                if type(obj) is not DictionaryObject:
                    raise RuntimeError('It is not DictionaryObject.')
                if str(obj['/Subtype']) == '/Link':
                    a: Union[DictionaryObject, PdfObject] = obj['/A']
                    if type(a) is not DictionaryObject:
                        raise RuntimeError('It is not DictionaryObject.')
                    if str(a['/S']) == '/URI':
                        rect: Union[ArrayObject, PdfObject] = obj['/Rect']
                        if type(rect) is not ArrayObject:
                            raise RuntimeError('It is not ArrayObject.')
                        link_left: float = rect[0].as_numeric()
                        link_bottom: float = rect[1].as_numeric()
                        link_right: float = rect[2].as_numeric()
                        link_top: float = rect[3].as_numeric()
                        uri: str = str(a['/URI'])
                        print(f'Link\t{link_left}\t{link_bottom}'
                              f'\t{link_right}\t{link_top}'
                              f'\t{uri}')


if __name__ == '__main__':
    main()

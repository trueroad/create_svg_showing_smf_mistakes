#!/usr/bin/env python

"""
Levenshtein matching class partially compatible with difflib.SequenceMatcher.

https://gist.github.com/trueroad/341afa4ff6045fe05ae945a0697822c5

Copyright (C) 2022 Masamichi Hosoda.
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

from collections.abc import Hashable, Sequence
from typing import Any, Final, List, Optional, Tuple, cast
from warnings import warn


VERSION: Final[str] = "20220331.02"


class LevenshteinMatcher:
    """
    Levenshtein matching class.

    This class is a subset of the functionality provided
    by difflib.SequenceMatcher class and is partially compatible.
    """

    def __init__(self,
                 isjunk: Any = None,
                 a: Sequence[Hashable] = '',
                 b: Sequence[Hashable] = '',
                 autojunk: Any = None) -> None:
        """
        __init__.

        Args:
          isjunk (Any): Dummy for compatibility.
          a (Sequence[Hashable]): Sequence 1.
          b (Sequence[Hashable]): Sequence 2.
          autojunk (Any): Dummy for compatibility.
        """
        if isjunk is not None:
            warn('isjunk is NOT implemented, ignored')
        if autojunk is not None:
            warn('autojunk is NOT implemented, ignored')
        self.set_seqs(a, b)

        self.cost_insert: int = 1
        self.cost_delete: int = 1
        self.cost_replace: int = 2

    def __init_cache(self) -> None:
        """Init cache."""
        self.__dp: Optional[List[List[int]]] = None
        self.__distance: Optional[int] = None
        self.__ratio: Optional[float] = None
        self.__trace: Optional[List[Tuple[bool, int, int]]] = None
        self.__opcodes: Optional[List[Tuple[str, int, int, int, int]]] = None

    def set_seqs(self, a: Sequence[Hashable], b: Sequence[Hashable]) -> None:
        """
        Set sequences.

        Args:
          a (Sequence[Hashable]): Sequence 1.
          b (Sequence[Hashable]): Sequence 2.
        """
        self.set_seq1(a)
        self.set_seq2(b)

    def set_seq1(self, a: Sequence[Hashable]) -> None:
        """
        Set sequence 1.

        Args:
          a (Sequence[Hashable]): Sequence 1.
        """
        self.__a: Sequence[Hashable] = a
        self.__len_a: int = len(a)
        self.__hash_a: List[int] = [0] * self.__len_a
        i: int
        for i in range(self.__len_a):
            self.__hash_a[i] = hash(self.__a[i])
        self.__init_cache()

    def set_seq2(self, b: Sequence[Hashable]) -> None:
        """
        Set sequence 2.

        Args:
          b (Sequence[Hashable]): Sequence 1.
        """
        self.__b: Sequence[Hashable] = b
        self.__len_b: int = len(b)
        self.__hash_b: List[int] = [0] * self.__len_b
        j: int
        for j in range(self.__len_b):
            self.__hash_b[j] = hash(self.__b[j])
        self.__init_cache()

    def __calc_dp(self) -> None:
        """Calc DP."""
        self.__dp \
            = [[0] * (self.__len_b + 1) for _ in range(self.__len_a + 1)]

        for j in range(1, self.__len_b + 1):
            self.__dp[0][j] = j * self.cost_insert

        for i in range(1, self.__len_a + 1):
            self.__dp[i][0] = i * self.cost_delete
            for j in range(1, self.__len_b + 1):
                cost: int
                if self.__hash_a[i - 1] == self.__hash_b[j - 1]:
                    cost = 0
                else:
                    cost = self.cost_replace
                self.__dp[i][j] = min(self.__dp[i - 1][j] + self.cost_delete,
                                      self.__dp[i][j - 1] + self.cost_insert,
                                      self.__dp[i - 1][j - 1] + cost)

        self.__distance = self.__dp[self.__len_a][self.__len_b]

    def get_dp_for_debug(self) -> List[List[int]]:
        """
        Get DP for debug.

        This method does not exist in difflib.SequenceMatcher.

        Returns:
          List[Tuple[str, int, int]]: trace.
        """
        if self.__dp is None:
            self.__calc_dp()
            if self.__dp is None:
                raise RuntimeError('No DP')
        return self.__dp

    def get_levenshtein_distance(self) -> int:
        """
        Get Levenshtein distance.

        This method does not exist in difflib.SequenceMatcher.

        Returns:
          int: Levenshtein distance.
        """
        if self.__distance is None:
            self.__calc_dp()
            if self.__distance is None:
                raise RuntimeError('No distance')
        return self.__distance

    def __calc_backtrace(self) -> None:
        """Calc backtrace."""
        if self.__dp is None:
            self.__calc_dp()
            if self.__dp is None:
                raise RuntimeError('No DP')

        self.__trace = []

        i: int = self.__len_a
        j: int = self.__len_b
        while i > 0 and j > 0:
            cost: int
            if self.__hash_a[i - 1] == self.__hash_b[j - 1]:
                cost = 0
            else:
                cost = self.cost_replace

            cost_current: int = self.__dp[i][j]
            cost_delete: int = self.__dp[i - 1][j]
            cost_insert: int = self.__dp[i][j - 1]
            cost_other: int = self.__dp[i - 1][j - 1]

            if cost_current == cost_other + cost:
                # equal and replace
                self.__trace.append((cost == 0, i, j))
                i = i - 1
                j = j - 1
            elif cost_current == cost_insert + self.cost_insert:
                # insert
                self.__trace.append((False, i, j))
                j = j - 1
            elif cost_current == cost_delete + self.cost_delete:
                # delete
                self.__trace.append((False, i, j))
                i = i - 1
            else:
                raise RuntimeError('Invalid DP')

        while j > 0:
            # insert
            self.__trace.append((False, i, j))
            j = j - 1
        while i > 0:
            # delete
            self.__trace.append((False, i, j))
            i = i - 1

        self.__trace.reverse()

    def get_trace_for_debug(self) -> List[Tuple[bool, int, int]]:
        """
        Get trace for debug.

        This method does not exist in difflib.SequenceMatcher.

        Returns:
          List[Tuple[bool, int, int]]: trace.
        """
        if self.__trace is None:
            self.__calc_backtrace()
            if self.__trace is None:
                raise RuntimeError('No trace')
        return self.__trace

    def ratio(self) -> float:
        """
        Get matching ratio.

        Returns:
          float: seaquences matching ratio [0.0, 1.0].
            1.0 means they are completely the same.
            0.0 means they are completely different.
        """
        if self.__ratio is not None:
            return self.__ratio

        if self.__trace is None:
            self.__calc_backtrace()
            if self.__trace is None:
                raise RuntimeError('No trace')

        matched: int = 0
        op: Tuple[bool, int, int]
        for op in self.__trace:
            if op[0]:
                matched += 1

        self.__ratio = 2.0 * matched / (self.__len_a + self.__len_b)
        return self.__ratio

    def quick_ratio(self) -> float:
        """
        Calc quick ratio.

        This is a just dummy for compatibility with difflib.SequenceMatcher.
        """
        warn('quick_ratio() is NOT implemented, use ratio()')
        return self.ratio()

    def real_quick_ratio(self) -> float:
        """
        Calc real quick ratio.

        This is a just dummy for compatibility with difflib.SequenceMatcher.
        """
        warn('real_quick_ratio() is NOT implemented, use ratio()')
        return self.ratio()

    def __append_opcode(self, before_flag: bool,
                        begin_i: int, before_i: int,
                        begin_j: int, before_j: int) -> None:
        """Append opcode."""
        opcode: str
        if before_flag:
            opcode = 'equal'
        elif begin_i == before_i and begin_j < before_j:
            opcode = 'insert'
        elif begin_i < before_i and begin_j == before_j:
            opcode = 'delete'
        elif begin_i < before_i and begin_j < before_j:
            opcode = 'replace'
        else:
            raise RuntimeError('Invalid trace')

        cast(List[Tuple[str, int, int, int, int]],
             self.__opcodes).append((opcode,
                                     begin_i, before_i,
                                     begin_j, before_j))

    def __calc_opcodes(self) -> None:
        """Calc opcodes."""
        if self.__trace is None:
            self.__calc_backtrace()
            if self.__trace is None:
                raise RuntimeError('No trace')

        self.__opcodes = []

        before_flag: bool = self.__trace[0][0]
        before_i: int = 0
        begin_i: int = 0
        before_j: int = 0
        begin_j: int = 0
        op: Tuple[bool, int, int]
        for op in self.__trace:
            if before_flag == op[0]:
                before_i = op[1]
                before_j = op[2]
                continue
            self.__append_opcode(before_flag,
                                 begin_i, before_i, begin_j, before_j)
            before_flag = op[0]
            begin_i = before_i
            before_i = op[1]
            begin_j = before_j
            before_j = op[2]

        self.__append_opcode(before_flag,
                             begin_i, before_i, begin_j, before_j)

    def get_opcodes(self) -> List[Tuple[str, int, int, int, int]]:
        """
        Get opcodes.

        Returns:
          List[Tuple[str, int, int, int, int]]: opcodes.
        """
        if self.__opcodes is None:
            self.__calc_opcodes()
            if self.__opcodes is None:
                raise RuntimeError('No opcodes')
        return self.__opcodes


def __test_matcher(a: Sequence[Hashable], b: Sequence[Hashable]) -> None:
    """Test matcher."""
    print(f'\n\na: {a}\nb: {b}\n')

    lm: LevenshteinMatcher = LevenshteinMatcher(None, a, b)
    print(f'Levenshtein distance: {lm.get_levenshtein_distance()}')
    ratio: float = lm.ratio()
    print(f'ratio: {ratio}')
    opcodes: List[Tuple[str, int, int, int, int]] = lm.get_opcodes()
    print(f'opcodes: {opcodes}')
    """
    print(lm.get_dp_for_debug())
    print(lm.get_trace_for_debug())
    """

    """
    import difflib
    sm: difflib.SequenceMatcher[Hashable] \
        = difflib.SequenceMatcher(None, a, b, False)
    print('\ndifflib.SequenceMatcher')
    sm_ratio: float = sm.ratio()
    print(f'ratio: {sm_ratio}, ', end='')
    if ratio > sm_ratio:
        print('non optimal result')
    elif ratio < sm_ratio:
        print('*** ERROR: LevenshteinMatcher is wrong ***')
    elif ratio == sm_ratio:
        print('same as LevenshteinMatcher')
    else:
        print('*** UNKNOWN ***')
    sm_opcodes: List[Tuple[str, int, int, int, int]] = sm.get_opcodes()
    if opcodes == sm_opcodes:
        print('opcodes: same as LevenshteinMatcher')
    else:
        print(f'opcodes: {sm_opcodes}')
    """


def main() -> None:
    """Test main."""
    print('Levenshtein matching class partially compatible '
          'with difflib.SequenceMatcher.\n'
          f'{VERSION}\n\n'
          'https://gist.github.com/trueroad/'
          '341afa4ff6045fe05ae945a0697822c5\n\n'
          'Copyright (C) 2022 Masamichi Hosoda.\n'
          'All rights reserved.\n')

    # Both matching results are the same.
    __test_matcher('kitten', 'sitting')
    __test_matcher('kitten', 'aaakitten')
    __test_matcher('aaakitten', 'kitten')
    __test_matcher('abcdefg', 'abcexfg')
    __test_matcher('abcdefghi', 'abcfxghi')
    __test_matcher('abcdef', 'adxf')
    __test_matcher('aabcba', 'cacbda')

    # difflib.SequenceMatcher's matching result is not optimal.
    __test_matcher('abcabcabc',
                   'ababcbc')

    # Can be used for sequences other than str.
    __test_matcher([1, 2, 3, 4, 5, 6, 7, 8, 9, 0],
                   [10, 1, 2, 4, 5, 16, 8, 9, 0, 20])


if __name__ == '__main__':
    main()

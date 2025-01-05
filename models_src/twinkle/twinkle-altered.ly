%%#!lilypond twinkle-altered.ly -*- coding: utf-8; -*-

% https://gist.github.com/trueroad/01353cff1b7079be44e05901832dfbae
% based on
% https://gist.github.com/trueroad/851949e3eadd5cdd1e4d34ad9517454a

\version "2.22.1"

\pointAndClickOff

\header {
  title = "きらきら星変奏曲のテーマより冒頭部分を抜粋"
  subtitle = "一部をわざと改変"
  composer = "W. A. モーツァルト"
}

upper = \relative c'' {
  \clef treble
  \key c \major
  \time 2/4
  \set Score.tempoHideNote = ##t
  \tempo 4 = 120

  c4 c | g' g | a a | g2 | f4 f | e e | d8. c16 d8. e16 | c2 \bar "|."
}

lower = \relative c {
  \clef bass
  \key c \major
  \time 2/4

  c4 c'4 | e c | f c | e c | d b | c a | f g | c,2 \bar "|."
}

\score {
  \new PianoStaff
  <<
    \new Staff = "upper" \upper
    \new Staff = "lower" \lower
  >>
  \layout {}
  \midi {}
}

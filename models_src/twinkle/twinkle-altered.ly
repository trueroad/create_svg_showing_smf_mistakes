% きらきら星変奏曲のテーマより冒頭部分を抜粋
% 一部をわざと改変
%
% Based on
% https://gist.github.com/trueroad/01353cff1b7079be44e05901832dfbae

\version "2.24.3"

\include "articulate.ly"
\pointAndClickOff

upper = \relative c'' {
  \clef treble
  \key c \major
  \time 2/4
  %\set Score.tempoHideNote = ##t
  \tempo 4 = 120

  c4 c | g' g | a a | g2 | f4 f | e e | d8. c16 d8. e16 | c2 \bar "|."
}

lower = \relative c {
  \clef bass
  \key c \major
  \time 2/4

  c4 c'4 | e c | f c | e c | d b | c a | f g | c,2 \bar "|."
}

all_staff = {
  \new PianoStaff
  <<
    \new Staff = "upper" \upper
    \new Staff = "lower" \lower
  >>
}

\score
{
  \articulate
  <<
    \all_staff
  >>
  \midi {}
}
\score
{
  \all_staff
  \layout
  {
    \context
    {
      \Score
      proportionalNotationDuration = #(ly:make-moment 1/8)
    }
  }
}

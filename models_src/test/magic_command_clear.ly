% マジックコマンド画面クリア

\version "2.24.3"

\include "articulate.ly"
\pointAndClickOff

upper = \relative
{
  \clef treble
  \key c \major
  \time 4/4
  \tempo 4 = 80

  c' cis c cis |
}

lower = \relative
{
  \clef bass
  \key c \major
  \time 4/4

  R1 |
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

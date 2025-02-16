\version "2.24.4"

\include "articulate.ly"
\pointAndClickOff

upper = \relative
{
  \clef treble
  \key c \major
  \time 4/4
  \tempo 4 = 120

  c'4-. e-- g c, |
}

lower = \relative
{
  \clef bass
  \key c \major
  \time 4/4

  <c e g>4-. <c e g>-- <c e g> <c e g> |
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

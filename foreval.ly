\version "2.24.3"

\pointAndClickOff

upper = \relative
{
  \clef treble
  \key c \major
  \time 4/4
  \tempo 4 = 80

  c'4-- e-. r8 g c,4 |
}

lower = \relative
{
  \clef bass
  \key c \major
  \time 4/4

  <c g'>4-. <c e>-- <f a>8 <c e g> <c e g>4 |
}

\score
{
  \new PianoStaff
  <<
    \new Staff = "upper" \upper
    \new Staff = "lower" \lower
  >>
  \layout {}
  \midi {}
}

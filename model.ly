\version "2.24.3"

%%% INCLUDE %%%
\pointAndClickOn

upper = \relative
{
  \clef treble
  \key c \major
  \time 4/4
  \tempo 4 = 80

  c'4-. e-- g c, |
}

lower = \relative
{
  \clef bass
  \key c \major
  \time 4/4

  <c e g>4-. <c e g>-- <c e g> <c e g> |
}

\score
{
  \new PianoStaff
  <<
    \new Staff = "upper" \upper
    \new Staff = "lower" \lower
  >>
  \layout {}
  % \midi {}
}

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

all_staff = {
  \new PianoStaff
  <<
    \new Staff = "upper" \upper
    \new Staff = "lower" \lower
  >>
}

\version "2.24.4"

\include "articulate.ly"
\pointAndClickOff

\include "model.ly"

\score
{
  \articulate
  <<
    \all_staff
  >>
  \midi {}
}

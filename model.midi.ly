\version "2.24.3"

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

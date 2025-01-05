\version "2.24.3"

% \include
\pointAndClickOn

\include "model.ly"

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

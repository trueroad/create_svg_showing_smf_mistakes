\version "2.24.3"

\pointAndClickOff

upper = \relative
{
  \clef treble
  \key c \major
  \time 4/4
  \tempo 4 = 80

  c'4-- e-.
  <<
    {
      \voiceOne
      r8 g~ g r
    }
    \new Voice
    {
      \voiceTwo
      r4 c,
    }
  >>
  \oneVoice
  |
}

lower = \relative
{
  \clef bass
  \key c \major
  \time 4/4

  <c g'>4-. <c e>--
  <<
    {
      \voiceOne
      <f a>8 <c e g> ~ <c e g> r
    }
    \new Voice
    {
      \voiceTwo
      r4 <c e g>
    }
  >>
  \oneVoice
  |
}

\score
{
  \new PianoStaff
  <<
    \new Staff = "upper" \upper
    \new Staff = "lower" \lower
  >>
  \layout {}
  \midi
  {
    % MIDI チャンネルをボイスごとに割り当てる
    % https://lilypond.org/doc/v2.24/Documentation/snippets/midi
    % 同音が同チャネルで重なると自動的に note off されてしまうため、
    % チャネルを変えることで自動 note off を回避する。
    % smf_diff.py はチャネルの違いを無視するので
    % チャネルが違っても差分比較には問題ない。

    \context
    {
      \Staff
      \remove "Staff_performer"
    }
    \context
    {
      \Voice
      \consists "Staff_performer"
    }
  }
}

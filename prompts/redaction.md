# Task: Redaction

## Instructions
Redact words that clearly and unambiguously refer to the Oscar winner and/or Oscar winning film. However, names that are not famous, or to someone not super knowledgeable wouldn't clearly identify the winner or film are ok. Always redact any "NAME:" formatting that indicates that this is the speaker, even if that speaker is unrelated to the movie.

Return the FULL speech with [REDACT: ...] tags around each redacted span. Everything not redacted must remain verbatim.

## Examples

### Example 1
Category: Actor in a Leading Role
Winner: Russell Crowe
Film: Gladiator
Speech: """My grandfather's name was Stan Wemyss. He was a cinematographer in the second World War. My uncle [REDACT: David], [REDACT: David William Crowe], he died last year at the age of sixty-six."""
Reasoning: "David William Crowe" shares the winner's surname. "David" alone is ambiguous but appears adjacent to the full name. "Stan Wemyss" is a different surname — not linkable to Russell Crowe.

### Example 2
Category: Best Picture
Winner: Adele Romanski, Dede Gardner and Jeremy Kleiner, Producers
Film: Moonlight
Speech: """[REDACT: JORDAN HOROWITZ]: [Walking to the microphone; Beatty tries to wave him off so he can speak.] You know what? Guys, guys, I'm sorry, no. There's a mistake. ""Moonlight,"" you guys won Best Picture.
[REDACT: MARC PLATT]:
[off mic:] ""Moonlight"" won."""
Reasoning: Sometimes the speeches annotate who is speaking the lines. This should ALWAYS be redacted, even if the speaker is not one of the winners.

### Example 3
Category: Actor in a Leading Role
Winner: Colin Firth
Film: The King's Speech
Speech: """All the crew and my fellow cast members, those who are not here and those who are. [REDACT: Geoffrey], [REDACT: Helena], and Guy, whose virtuosity made it very, very difficult for me to be as bad as I was planning to be."""
Reasoning: "Geoffrey" & "Helena": These refer to Geoffrey Rush and Helena Bonham Carter. Even though they are just first names, in the context of this film, they uniquely identify the cast. "Guy": (Guy Pearce) - this is a borderline case, from context it's pretty hard to figure out that this is referring to Guy Pearce, and that's fine.

### Example 4
Category: Actor in a Leading Role
Winner: Daniel Day-Lewis
Film: Lincoln
Speech: """And [REDACT: Steven] didn't have to persuade me to play [REDACT: Lincoln] but I had to persuade him that perhaps, if I was going to do it, that '[REDACT: Lincoln]' shouldn't be a musical."""
Reasoning: "Lincoln": This is both the character name AND the film title. It must be redacted. "Steven": Refers to Steven Spielberg. While "Steven" is a common name, in the context of this movie, it identifies the famous director.

### Example 5
Category: Actress in a Leading Role
Winner: Julia Roberts
Film: Erin Brockovich
Speech: """I want to acknowledge so many people that made '[REDACT: Erin Brockovich],' '[REDACT: Erin Brockovich]' -- but let me make my dress pretty... Universal, everybody at Universal."""
Reasoning: "Erin Brockovich": She says the full title twice. Always redact this, no matter what. It's not mandatory to redact the name of the studio ("Universal").

## Prompt
Category: {category}
Winner: {winner_clean}
Film: {film_title}
Speech: """{speech_clean}"""

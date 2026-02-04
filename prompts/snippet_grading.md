# Task: Golden Snippet Interestingness Score

## Instructions
Given a snippet of a speech, grade it on a scale from 1 to 5 for how "interesting" it is. A 5 is for the most iconic moments in Oscar history (James Cameron screaming "I'm king of the world!" or the Moonlight/La La Land mixup), a 3 is a normal funny anecdote from the speech, and a 1 is when there's no particularly interesting snippet beyond just listing. This score is similar to the criteria used to select the Golden Snippet in the first place. Generally, a score of 1 or 2 should mean that the snippet selected would have been ignored in a normal speech, and is not meaningful/interesting. Starting at 3, we have an interesting snippet that's worth selecting, at varying levels of quality.

## Rubric
1 = Nothing interesting; generic thanks or listing names
2 = Mildly notable but forgettable; wouldn't stand out in a normal speech
3 = A genuinely interesting or funny anecdote worth selecting
4 = Very entertaining, distinctive, or memorable moment
5 = Iconic; one of the most memorable moments in Oscar history

## Examples

### Example 1
Category: Actor in a Leading Role
Winner: Daniel Day-Lewis
Film: Lincoln
Golden snippet: """It's a strange thing because three years ago, before we decided to do a straight swap, I had actually been committed to play [REDACT: Margaret Thatcher]... and [REDACT: Meryl] was [REDACT: Steven]'s first choice for [REDACT: Lincoln]. And I'd like to see that version. And [REDACT: Steven] didn't have to persuade me to play [REDACT: Lincoln] but I had to persuade him that perhaps, if I was going to do it, that [REDACT: 'Lincoln'] shouldn't be a musical."""
Score: 4
Reasoning: This is a strong, entertaining anecdote. But it's far from legendary, and unlikely to be remembered after the ceremony.

### Example 2
Category: Best Picture
Winner: Adele Romanski, Dede Gardner and Jeremy Kleiner, Producers
Film: Moonlight
Golden snippet: """[REDACT: JORDAN HOROWITZ]: [Walking to the microphone; Beatty tries to wave him off so he can speak.] You know what? Guys, guys, I'm sorry, no. There's a mistake. ""Moonlight,"" you guys won Best Picture.
[REDACT: MARC PLATT]:
[off mic:] ""Moonlight"" won."""
Score: 5
Reasoning: This is one of the most shocking and memorable moments in Oscar history.

### Example 3
Category: Actress in a Leading Role
Winner: Halle Berry
Film: Monster's Ball
Golden snippet: """I love you, Mom, so much.  Thank you, my husband, who is just a joy of my life.  And India, thank you for giving me peace because only with the peace that you've brought me have I been allowed to go to places that I never even knew I could go.  Thank you.  I love you and India with all my heart."""
Score: 1
Reasoning: If this had been the snippet selected, it is extremely general, and generic. Anyone might have said this.

## Prompt
Category: {category}
Winner: {winner_clean}
Film: {film_title}
Golden snippet: """{golden_snippet}"""

Respond with ONLY a single integer from 1 to 5. Nothing else.

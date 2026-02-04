# Task: Golden Snippet Selection

## Instructions
Identify the most interesting, distinctive, funny, unique, and/or entertaining subset of the speech. In the best case, it might be a complete anecdote, up to a paragraph long. It could be just a few sentences, if they are a self-contained funny zinger. Or it could just be the most interesting stretch of the speech, even if it isn't all on the same topic.

Return ONLY the selected snippet text. Preserve any [REDACT: ...] tags exactly as they appear in the input. You may use "..." to indicate where you skipped over less interesting lines within the snippet.

## Examples

### Example 1
Category: Actor in a Leading Role
Winner: Daniel Day-Lewis
Film: Lincoln
Speech: """I really don't know how any of this happened. I do know that I've received so much more than my fair share of good fortune in my life... It's a strange thing because three years ago, before we decided to do a straight swap, I had actually been committed to play [REDACT: Margaret Thatcher]... and [REDACT: Meryl] was [REDACT: Steven]'s first choice for [REDACT: Lincoln]. And I'd like to see that version. And [REDACT: Steven] didn't have to persuade me to play [REDACT: Lincoln] but I had to persuade him that perhaps, if I was going to do it, that [REDACT: 'Lincoln'] shouldn't be a musical. My fellow nominees, my equals, my betters, I'm so proud to have been included as one amongst you."""
Golden snippet: """It's a strange thing because three years ago, before we decided to do a straight swap, I had actually been committed to play [REDACT: Margaret Thatcher]... and [REDACT: Meryl] was [REDACT: Steven]'s first choice for [REDACT: Lincoln]. And I'd like to see that version. And [REDACT: Steven] didn't have to persuade me to play [REDACT: Lincoln] but I had to persuade him that perhaps, if I was going to do it, that [REDACT: 'Lincoln'] shouldn't be a musical."""
Reasoning: This is a strong, distinctive anecdote (even if parts have to be redacted). The sentences before and after are just filler.

### Example 2
Category: Actress in a Supporting Role
Winner: Viola Davis
Film: Fences
Speech: """Thank you to the Academy. Thank you to my producers, and to my lovely husband. I'm so grateful for this opportunity, and it was such a special experience to play this iconic role. I've always dreamed of having this opportunity. You know, there's one place that all the people with the greatest potential are gathered. One place. And that's the graveyard. People ask me all the time, "What kind of stories do you want to tell, [REDACT: Viola]?" And I say, exhume those bodies. Exhume those stories. The stories of the people who dreamed big and never saw those dreams to fruition. People who fell in love and lost. I became an artist, and thank god I did, because we are the only profession that celebrates what it means to live a life. So here's to [REDACT: August Wilson], who exhumed and exalted the ordinary people."""
Golden snippet: """You know, there's one place that all the people with the greatest potential are gathered. One place. And that's the graveyard. People ask me all the time, "What kind of stories do you want to tell, [REDACT: Viola]?" And I say, exhume those bodies. Exhume those stories. The stories of the people who dreamed big and never saw those dreams to fruition. People who fell in love and lost. I became an artist, and thank god I did, because we are the only profession that celebrates what it means to live a life."""
Reasoning: This is a distinctive, unique anecdote. The early sentences are generic thanks that can be skipped.

### Example 3
Category: Actor in a Supporting Role
Winner: George Clooney
Film: Syriana
Speech: """Wow. Wow. Alright, so I'm not winning Director. It's a funny thing about winning an Academy Award, this will always be sort of synonymous with your name from here on in. It will be: Oscar winner [REDACT: George Clooney], Sexiest Man Alive 1997, [REDACT: Batman], died today in a freak accident.... Listen, I don't quite know how you compare art. You look at these performances this year, of these actors, and unless we all did the same role—everybody put on a bat suit, we'll all try that—unless we all did the same role, I don't know how you compare it. I want to share this with all these wise people who made this movie happen. You are all amazing."""
Golden snippet: """It's a funny thing about winning an Academy Award, this will always be sort of synonymous with your name from here on in. It will be: Oscar winner [REDACT: George Clooney], Sexiest Man Alive 1997, [REDACT: Batman], died today in a freak accident.... unless we all did the same role—everybody put on a bat suit, we'll all try that—unless we all did the same role, I don't know how you compare it."""

### Example 4
Category: Actress in a Leading Role
Winner: Halle Berry
Film: Monster's Ball
Speech: """Oh my God. Oh my God. I'm sorry. This moment is so much bigger than me. This moment is for [REDACT: Dorothy Dandridge], [REDACT: Lena Horne], [REDACT: Diahann Carroll]. It's for the women that stand beside me, [REDACT: Jada Pinkett], [REDACT: Angela Bassett], [REDACT: Vivica Fox]. And it's for every nameless, faceless woman of color that now has a chance because this door tonight has been opened. Thank you. I'm so honored. I want to thank my manager, Vincent Cirrincione.  He's been with me for twelve long years and you fought every fight, and you loved me when I've been up but more importantly you've loved me when I've been down.  You have been a manager, a friend and the only father I've ever known.  Really.  And I love you very much.  I want to thank my mom who has given me the strength to fight every single day to be who I want to be and to give me the courage to dream, that this dream might be happening and possible for me.  I love you, Mom, so much.  Thank you, my husband, who is just a joy of my life.  And India, thank you for giving me peace because only with the peace that you've brought me have I been allowed to go to places that I never even knew I could go.  Thank you.  I love you and India with all my heart."""
Golden snippet: """Oh my God. Oh my God. I'm sorry. This moment is so much bigger than me. This moment is for [REDACT: Dorothy Dandridge], [REDACT: Lena Horne], [REDACT: Diahann Carroll]... And it's for every nameless, faceless woman of color that now has a chance because this door tonight has been opened."""

## Prompt
Category: {category}
Winner: {winner_clean}
Film: {film_title}
Speech: """{redacted_speech}"""

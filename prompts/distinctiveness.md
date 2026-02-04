# Task: Distinctiveness

## Instructions
Rate the following Oscar acceptance speech for distinctiveness on a scale of 1-5.

## Rubric
1 = Completely generic (just lists thank-yous, no personal content)
2 = Mostly generic with one mild personal touch
3 = Has some memorable or unique content
4 = Quite distinctive and memorable
5 = Iconic, highly unique speech

## Examples

### Example 1
Category: Actor in a Leading Role
Speech: """Thank you to the Academy. I want to thank my agent, my manager, my wife, my kids. Thank you all so much. This means the world to me. Thank you."""
Score: 1
Reasoning: Pure generic thanks, nothing memorable or specific. Could be anyone's speech for any award.

### Example 2
Category: Actress in a Supporting Role
Speech: """I want to thank the Academy. Working on this film changed my life. I grew up in a small town where nobody looked like me on screen, and to stand here today... my mother told me I was crazy to pursue acting, and Mom, I love you but I'm glad I didn't listen. Thank you to our incredible director for believing in me."""
Score: 3
Reasoning: Has a genuine personal anecdote about growing up and her mother's advice, which adds color, but the overall structure is still fairly standard acceptance speech fare.

### Example 3
Category: Actress in a Leading Role
Speech: """Sit down; you're too old to be standing. I just want to thank everybody I've ever met in my entire life. And I'm going to go home and... I'm going to have a big glass of wine. I have nothing prepared, I didn't think this would happen."""
Score: 4
Reasoning: Funny, self-deprecating, specific references to other nominees, spontaneous feel. Memorable and quotable.

## Prompt
Category: {category}
Speech: """{speech_clean}"""

Respond with ONLY a single integer from 1 to 5. Nothing else.

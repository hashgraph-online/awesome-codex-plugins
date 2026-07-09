# Examples — LinkedIn Reply Handler

## Example

> User: "Reply to this: https://www.linkedin.com/feed/update/urn:li:activity:7449018753880834048?commentUrn=urn%3Ali%3Acomment%3A%28activity%3A7449018753880834048%2C7449758545140453376%29"
>
> Skill: parses → post 7449018753880834048, comment 7449758545140453376. Fetches thread. Sees: post-author's post → Serge's comment ("moat moved to taste") → author's reply ("How are you building that conviction muscle with your team?"). Drafts R1 Answer-Their-Question variant. Shows approval card.
>
> User: "post"
>
> Skill: react APPRECIATION on the author's reply → pause 12s → post reply with parentComment set to Serge's original comment URN (the TOP level, not the author's reply).

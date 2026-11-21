> The calls below are Candor MCP tool calls. Replace placeholders such as `TRANSACTION_ID` with values from earlier responses; where an `input` names an operation instead of showing an object, `candor_schema` lists its fields.

# Goal recipes

## Revise a goal

```text
candor_get({
  "operation": "goals.get",
  "reason": "Read the goal before changing it",
  "args": {
    "goal_id": "GOAL_ID"
  }
})
candor_get({
  "operation": "goals.history",
  "reason": "See earlier versions and why they changed",
  "args": {
    "goal_id": "GOAL_ID"
  }
})
candor_write({
  "operation": "goals.update",
  "reason": "Move the date the person agreed to",
  "input": "<goals.update input object; candor_schema lists its fields>"
})
```

Every operation takes the `goal_key` wherever it takes a goal id. An update
saves a new version; say what changed so the person can correct it. Progress
facts never retarget a goal on their own: a slipping goal is a conversation,
not an automatic new date.

## Record progress by hand

Only for a `recorded` measure, or progress the records cannot show (cash at
home, an account Candor does not see):

```text
candor_write({
  "operation": "goals.progress.record",
  "reason": "Record the deposit the person made at their credit union",
  "args": {
    "goal_id": "GOAL_ID",
    "amount": "USD 250.00",
    "kind": "contribution"
  }
})
```

Check it is not already counted, cite where it came from, and re-read the
goal.

## Archive

```text
candor_write({
  "operation": "goals.archive",
  "reason": "The person dropped this goal",
  "args": {
    "goal_id": "GOAL_ID"
  }
})
```

Archiving keeps history. Save a note saying why, so it is not suggested again.

## Several goals

When goals compete for the same money, show the collision with figures and
let the person rank them; record `priority` as they say it. Parts of one
ambition use `parent_goal_id` and show under it on the dashboard.

## Goal check-in

"Am I on track?" Read `progress` for each goal: what moved since last time
(`goal.moved` in the opening), the required versus planned pace, and the
projected completion date. Lead with the one that needs attention. Show
`candor_visualize({"panel":"goals","reason":"Show the person their goals"})` when they want the picture.

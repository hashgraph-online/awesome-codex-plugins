---
name: linkedin-engagement-leads
description: "Turn the people who commented on or reacted to a LinkedIn post into a ranked lead list, with the LinkMCP connector. The list shows up to 20 people, each with the name, title, company, profile link, how the person engaged and why the person fits. Use when the user asks who engaged with a LinkedIn post: a post URL, their own latest post or a company post. Also use it when the user wants to know which of these people fit a target profile. Reads LinkedIn data only. It does not send connection requests, messages, comments or reactions."
license: MIT
compatibility: "Needs the LinkMCP connector (remote MCP server) in the AI client. Replies to comments need a paid LinkMCP plan with a connected LinkedIn account."
metadata:
  author: LinkMCP
  version: "1.0.0"
---

# LinkedIn engagement leads

Make a lead list from the people who engaged with one LinkedIn post. The user decides what to do with each person.

## Rules

- This skill only reads. Do not send connection requests or messages. Do not comment or react. Do not schedule any of these actions.
- Do not write messages to the people on the list. If the user wants to contact one person, treat it as a new task. Show the exact text, and send only after the user approves that one message.
- Do not look up email addresses or phone numbers for the people on the list.
- Keep only the data that the list needs. Save a file only when the user asks for it.
- LinkMCP lookups can use part of the monthly LinkMCP usage of the user. Ask the user before you read more pages of comments or reactions, or look up more than 20 profiles.

## Tools

This skill uses these LinkMCP tools. All of them only read: `linkedin_who_am_i`, `linkedin_get_person_posts`, `linkedin_get_company_posts`, `linkedin_get_post_comments`, `linkedin_get_post_reactions`, `linkedin_get_nested_comments`, `linkedin_bulk_get_profiles`.

Your client can show a tool name with a prefix, for example `mcp__linkmcp__linkedin_get_post_comments`. Use the tool whose name ends with the name in this skill.

## Steps

1. Make sure that the LinkMCP tools are available, for example `linkedin_get_post_comments`. If they are not available, stop and tell the user how to connect LinkMCP:
   - With the LinkMCP plugin: connect the LinkMCP connector of the plugin and sign in. In Claude, the connector is on the Connectors tab of the plugin.
   - Without the plugin: add LinkMCP as a remote MCP server with the URL `https://app.linkmcp.io/api/mcp?ref=skills` and sign in. Setup steps for each AI client: https://app.linkmcp.io/docs/quick-start
2. Find the post.
   - If the user gives a post URL, use it.
   - If the user means their own latest post, call `linkedin_who_am_i` to get the profile URL of the user. If it does not give the URL, ask the user for it. Then call `linkedin_get_person_posts` and select the newest post that the user wrote (not a repost).
   - If the user means a post of a company, call `linkedin_get_company_posts` and select the post in the same way.
   - Show the first line and the date of the post. Ask the user to confirm that it is the correct post.
3. If the user did not describe a good lead, ask for it: for example job titles, seniority, industry, region or company size. If the user does not know, rank the people by how close their work is to the topic of the post.
4. Read the comments: call `linkedin_get_post_comments` one time, with `postUrl` or `activityUrn`. One call can return many comments. If the result has a `nextCursor`, more comments exist. Ask the user before you read the next page with `cursor` set to that value.
5. Read the reactions: call `linkedin_get_post_reactions` one time, with `postUrl` or `activityUrn`. If the result has a `nextCursor`, more reactions exist. Ask the user before you read the next page with `cursor` set to that value. If the tool says that it needs a connected LinkedIn account or a paid plan, give that message to the user. Then continue with the comments only.
6. Optional: the user can ask for the replies to comments. Then call `linkedin_get_nested_comments` for each comment whose `replyCount` is above 0. Set `activityUrn` to the post and `parentCommentId` to the `commentId` of the comment. Do this for 10 comments or fewer. If the first call says that LinkedIn is not connected, skip this step.
7. Merge the people. Use the profile URL or the profile ID as the key. Remove the author of the post and the user. Remove company pages (`actorType` is "organization"). A comment is a stronger signal than a reaction. Keep the strongest signal for each person.
8. Rank the people with the data that you already have. A comment gives the headline and the comment text. A reaction gives only the name and the profile link, so do not guess the fit of a person who only reacted.
9. Call `linkedin_bulk_get_profiles` for 20 people or fewer. Take the commenters who fit best first. Then take the people who reacted, in the order that LinkMCP returned them. Use up to 10 identifiers in each call and `detail` set to "slim". Rank the people again with the title, company and location from the results.
10. Show the list in the format below.

## List format

Show a table with the people that you looked up in step 9. Put the best fit first.

| # | Name | Title | Company | Location | Engagement | Fit | Why | Profile |
|---|---|---|---|---|---|---|---|---|

- **Engagement:** "Comment: <short quote>" or "Reaction: <type>".
- **Fit:** High, Medium or Low, compared with the description of a good lead.
- **Why:** one short reason from the data. Do not guess facts.

After the table, give the counts: comments read, reactions read, people found and people in the table. Offer the same table as CSV.

## When a tool fails

- If a tool needs a connected LinkedIn account or a paid plan, it tells you. Give that message to the user. Then continue with the other steps.
- If a tool reports a limit or tells you to wait, do what it says. Do not call the tool again and again. If the wait is long, stop and show the list with the data that you have.
- If LinkMCP cannot find the post, ask the user for the exact post URL.

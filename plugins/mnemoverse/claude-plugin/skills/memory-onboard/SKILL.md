---
name: memory-onboard
description: "Seeds long-term Mnemoverse memory with a project's durable conventions and decisions, taken from its README, CLAUDE.md, AGENTS.md and contributing notes, one fact per memory and without saving what memory already holds. Use when the user starts using memory on an existing project, says \"onboard this repo\", \"learn this project\", or \"seed memory from the docs\", or when memory has nothing about a project the user works on often."
---

# Onboard a project into memory

## Check first

Look for the tools `memory_stats`, `memory_read`, `memory_list_recent` and `memory_write`. If they are missing, memory is not connected: say so in one sentence and use the bundled `setup` skill if it is installed, otherwise https://mnemoverse.com/docs/api/install-by-host.

## 1. See what is already there

- Call `memory_stats` to see the existing domains. If the project already has one, such as `project:<repository-name>`, reuse that exact spelling.
- If the project has a domain, call `memory_list_recent` with that `domain` and follow the cursor to the end to see everything stored there; otherwise call `memory_read` with the project name. Facts already in memory are not written again.

## 2. Read the project's own documents

In this order, where they exist: `README.md`, `CLAUDE.md`, `AGENTS.md`, `CONTRIBUTING.md`, and any architecture or decision records the README points to.

Take only what stays true for months:

- how to build, run and test the project, with the exact commands;
- code style and naming conventions that are written down;
- decisions with their reasons ("we use X because Y");
- where things live: the main folders and what each is for;
- who owns what, if the documents say so.

Leave out anything transient (open tasks, this week's status), anything that is only a link with no content, and any secret, key, token or connection string, even an example one.

## 3. Show the list before writing

Present the facts as a short numbered list, each with the file it came from. Write only after the user agrees, and drop the ones the user strikes out.

## 4. Write

- One `memory_write` per fact, `content` as a self-contained statement that names the project and the source file.
- Use the project's domain from step 1, or `project:<repository-name>` if there was none.
- A write can be refused when memory already holds something too close to it in the same domain. If step 1 found the same fact, count it as already known; if the fact is genuinely different, write it once more with only what is new in it, and report any fact that is still refused.

## 5. Report

Say how many facts were saved, how many were already known, and which files were read. Suggest the `memory-search` skill for using them.

---
name: principle-boundary-discipline
description: Use when wiring input validation, error handling, adapters, CLI or config parsing, or API clients. Check data at the point it enters, rely on typed values past that point, and put domain logic in framework-free functions called by a thin shell.
disable-model-invocation: true
---

# Boundary discipline

Do the defensive work (parsing, validation, error handling) where data crosses into the system. Past that point, hand typed values around and rely on them. Domain logic belongs in side-effect-free functions that a small layer of framework code invokes.

## When it applies

Wiring validation, error handling, framework adapters, CLI parsing, config loading, or API clients, and deciding where logic lives relative to framework code.

This principle moves checks to the right place. It never justifies skipping validation at a real boundary.

## What to do

1. List the boundaries the change touches: command-line arguments, config files, environment variables, network requests, responses from external APIs, reads from storage, and output from tools or models an agent calls. Each is a trust boundary where content may be malformed or hostile.
2. At each boundary, parse raw input into a domain type, reject what does not parse, and return a typed error. A webhook handler parses the JSON body into a `SignedEvent` after verifying the signature. It does not pass a raw dictionary inward.
3. Inside, pass the typed value along and propagate errors. Do not re-check what the boundary already guaranteed. A null check five calls deep on a field the parser made mandatory is noise.
4. Validate configuration when it is parsed, at startup.
5. At the public surface, expose domain concepts. Do not re-export the HTTP response type, the ORM row, or the framework's request object. Generic mechanism stays inside, and rules specific to one caller or deployment sit at the outer layer.
6. Write business logic as pure functions with no framework imports, so you can test it without starting the framework. Good candidates: parsers that turn bytes into typed state, prompt builders that turn structured state into a string, and scorers that turn state into a verdict.
7. Ask two questions of each check and each function. Is this data crossing a boundary right now? If not, the validation is redundant. Could this be a pure function the shell calls? If so, extract it.

## The failure it prevents

Scattered validation gives false confidence because nobody can say which layer is the real gate. Logic tangled with framework wiring cannot be unit tested, and leaked wire types tie the domain to one transport.

## Done when

Every guard sits at a boundary, inner code trusts its types, and the logic runs without the framework.

Related: [principle-type-system-discipline](../principle-type-system-discipline/SKILL.md), [principle-minimize-reader-load](../principle-minimize-reader-load/SKILL.md), [principle-treat-input-as-untrusted](../principle-treat-input-as-untrusted/SKILL.md).

# Gotchas

## Single-File Regression

Do not collapse the course back into one large HTML artifact. The default output is a multi-file course directory with authored assets plus a built `index.html`.

## Writing Modules Before You Know The Shape

For complex codebases, do not jump straight into lesson prose. Write module briefs first so subsystem boundaries and teaching order are explicit before drafting content.

## Turning The Course Into A File Census

A long list of filenames is not orientation. Focus on the handful of files that explain behavior, boundaries, and likely change points.

## Quoting Too Much Code

Whole-file dumps make the lesson harder to follow and are a bad public-data habit. Keep real excerpts short and only when the exact wording matters.

## Pretending Redaction Is Automatic

This skill does not guarantee that sensitive source text will be cleaned for you. If a snippet is not safe to publish, paraphrase it or leave it out.

## External Asset Drift

Avoid CDN links, remote font kits, and hosted script dependencies. The built course should still work when opened from disk without a network connection.

## Decorative Interaction

An interactive widget should help the learner test a concept, compare layers, or follow a flow. If it only adds motion, remove it.

## Expert-Only Language

If a non-technical learner needs three definitions before a paragraph makes sense, rewrite the paragraph. Plain language comes first, then formal terms.

## Implying Automatic Browser Launch

The result should be directly openable in a browser, but do not promise that the browser will launch by itself. Report the built path and leave opening behavior explicit.

## Forgetting To Rebuild

`index.html` is the assembled output. After editing course content or structure, rebuild so the final entry page matches the authored files.

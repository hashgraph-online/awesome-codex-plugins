# Worked delivery contract

This synthetic scenario demonstrates the expected artifact shape; its numbers and outcomes are example inputs, not measured customer results.

## Input

An owned interview has a transcripted moment at 02:10–02:28 explaining one inventory mistake. A stable draft guide answers how to prevent that mistake. The task is a saved draft package only.

## Expected output

Return the package-template sections: source/rights record, exact timestamps and excerpt, five-dimension moment score, guide promise/draft state, bridge copy with one action, proposed sequence, measurement and approval state draft. In standard mode record certainty_status: not-required; in worker-fleet mode retain both required checks.

## Failure case

The clip needs preceding context or the guide does not answer its natural next question. Return the failed moment/bridge score and the smallest source or guide revision needed. Do not force an 8/10 score to fill the campaign.

## Validation

Run python3 scripts/validate_package.py against the saved artifact from the skill directory, then inspect source timestamps, rights route and guide promise directly. Validator success does not create publication authority or prove a live post exists.

## Coverage and routing

Suede AI short-to-long content funnel: turns a video, clip, interview moment, talk excerpt, screen recording, or transcript into a scored, rights-checked package that bridges attention to an owned guide, X Article, LinkedIn article, newsletter, or playbook, and makes that guide the page search engines and AI answers find. Use when a clip must lead somewhere deeper, when third-party footage needs a rights route before reuse, or when an X post must pair native video with an owned Article card. NOT FOR: video editing or rendering (use suede-video), social calendars, account audits, or listening (use suede-social), writing the long-form guide from scratch (use suede-copy), paid ads (use suede-ad-creative), or publishing without exact-content and visible-identity approval.

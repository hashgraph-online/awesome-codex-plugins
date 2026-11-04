# Add-on: incident angles

Append this to every investigator's brief when the target looks defensive: null or type guards, retries, timeouts, throttling, feature flags, outbound-network guards, memory-exhaustion handling. Defensive code is often what an incident leaves behind. Take the date the defensive code first appeared from the anchor and search around it in your own source:

- **Version control:** commit messages describing an incident fix or a newly added guard, and revert-then-reapply pairs. Both are strong signals.
- **Tracker:** tickets labeled as incidents, by severity, as postmortem follow-ups, or as reliability work.
- **Long-form docs:** postmortem pages and incident reviews that name the service, the error text or the guard.
- **Team chat:** incident and severity channels in a window around the introduction date.
- **Infrastructure monitoring and error reporting:** your playbooks already cover incident records and error histories; run those steps first.
- **Analytics warehouse:** an error-classifying event that drops sharply right after the guard shipped.

Fold the results into your normal report and log these searches like any others.

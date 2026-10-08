# Product actions and events

A campaign can call the user's product for one prospect through an app connection. Inspect the actual endpoint and payload before proposing an `app_action`. Use `sendsets connection create --help` and `sendsets connection test CONNECTION_ID --json` to configure and verify it.

The product can report behavior with `sendsets events send EVENT_NAME --email PROSPECT_EMAIL --data JSON`, or through the API. Map only events the app can emit or clearly list the missing instrumentation. A `wait_for_event` step can branch or stop follow-up after a view, signup, activation, feature use, or upgrade. Make the event identity and timing explicit so a prospect cannot affect another prospect's campaign.

Clay, Firecrawl, HubSpot, and other tools are optional sources of prospects or context. Check available integrations and permissions before claiming an automated connection exists. The differentiating step is the useful action inside the customer's product, not a generic enrichment field.

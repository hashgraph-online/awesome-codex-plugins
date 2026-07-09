# CRM Integration Guide — Connection Patterns & Data Sync

How the Digital Marketing Pro plugin connects to CRMs, maps marketing data to CRM objects, and keeps records synchronized across systems.

---

## Section 1: Supported CRMs

| CRM | MCP Server | Auth Type | Read | Write | Key Objects |
|---|---|---|---|---|---|
| **Salesforce** | `mcp-salesforce` | OAuth 2.0 | Yes | Yes | Leads, Contacts, Accounts, Opportunities, Campaigns |
| **HubSpot** | `@anthropic/mcp-hubspot` | API Key / OAuth | Yes | Yes (beta) | Contacts, Companies, Deals, Tickets |
| **Zoho CRM** | `mcp-zoho-crm` | OAuth 2.0 | Yes | Yes | Leads, Contacts, Accounts, Deals, Campaigns |
| **Pipedrive** | `mcp-pipedrive` | API Token | Yes | Yes | Persons, Organizations, Deals, Activities |
| **Odoo CRM** | `mcp-odoo` | API Key + DB Name | Yes | Yes | Leads, Contacts, Opportunities, Activities, Campaigns, Invoices |
| **Freshsales** | `mcp-freshsales` | API Key | Yes | Yes | Contacts, Accounts, Deals, Tasks, Sales Sequences |
| **Monday.com CRM** | `mcp-monday-crm` | API Token / OAuth | Yes | Yes | Boards, Items, Columns, Groups, Updates |
| **Microsoft Dynamics 365** | `mcp-dynamics-365` | OAuth 2.0 | Yes | Yes | Leads, Contacts, Accounts, Opportunities, Campaigns |
| **Copper CRM** | `mcp-copper` | API Key + Email | Yes | Yes | People, Companies, Opportunities, Projects, Tasks |
| **Close CRM** | `mcp-close-crm` | API Key (Basic Auth) | Yes | Yes | Leads, Contacts, Opportunities, Activities, Sequences |
| **Keap** | `mcp-keap` | OAuth 2.0 | Yes | Yes | Contacts, Companies, Deals, Tags, Campaigns, Orders |

**Setup:** Set the relevant API key or OAuth credentials in `.env`. The MCP server configuration in `.mcp.json` handles connection routing. Each brand can use a different CRM (see Section 7: Multi-CRM Setup).

---

## Section 2: Field Mapping

How brand profile and marketing data fields map to CRM object fields across platforms.

### Contact & Company Fields

| Brand Profile / Marketing Field | Salesforce | HubSpot | Zoho | Pipedrive |
|---|---|---|---|---|
| `company_name` | Account.Name | Company.name | Account.Account_Name | Organization.name |
| `contact.email` | Lead.Email / Contact.Email | Contact.email | Lead.Email / Contact.Email | Person.email |
| `contact.phone` | Lead.Phone / Contact.Phone | Contact.phone | Lead.Phone / Contact.Phone | Person.phone |
| `contact.first_name` | Lead.FirstName | Contact.firstname | Lead.First_Name | Person.first_name |
| `contact.last_name` | Lead.LastName | Contact.lastname | Lead.Last_Name | Person.last_name |
| `contact.title` | Lead.Title | Contact.jobtitle | Lead.Designation | Person.job_title |
| `contact.source` | Lead.LeadSource | Contact.hs_lead_source | Lead.Lead_Source | Person.source |

### Deal & Campaign Fields

| Marketing Field | Salesforce | HubSpot | Zoho | Pipedrive |
|---|---|---|---|---|
| `deal_value` | Opportunity.Amount | Deal.amount | Deal.Amount | Deal.value |
| `deal_stage` | Opportunity.StageName | Deal.dealstage | Deal.Stage | Deal.stage_id |
| `deal_close_date` | Opportunity.CloseDate | Deal.closedate | Deal.Closing_Date | Deal.expected_close_date |
| `campaign_name` | Campaign.Name | (custom property) | Campaign.Campaign_Name | (custom field) |
| `campaign_status` | Campaign.Status | (custom property) | Campaign.Status | (custom field) |
| `utm_source` | Lead.UTM_Source__c (custom) | Contact.hs_analytics_source | Lead.UTM_Source (custom) | Person.utm_source (custom) |

**Note:** Fields marked "(custom)" require creating a custom field/property in the CRM before the plugin can write to them. Use `crm-sync.py --action setup-fields --crm {crm}` to auto-create required custom fields.

### Extended Platform Contact & Company Fields

| Brand Profile / Marketing Field | Odoo | Freshsales | Monday.com CRM | Dynamics 365 | Copper | Close | Keap |
|---|---|---|---|---|---|---|---|
| `company_name` | res.partner.name (company type) | Account.name | Board item (custom column) | Account.name | Company.name | Lead.display_name | Company.company_name |
| `contact.email` | res.partner.email | Contact.emails[0].value | Item email column | Contact.emailaddress1 | Person.emails[0].email | Contact.emails[0].email | Contact.email_addresses[0].email |
| `contact.phone` | res.partner.phone | Contact.phones[0].value | Item phone column | Contact.telephone1 | Person.phone_numbers[0].number | Contact.phones[0].phone | Contact.phone_numbers[0].number |
| `contact.first_name` | res.partner.name (parsed) | Contact.first_name | Item name (parsed) | Contact.firstname | Person.name (parsed) | Contact.name (parsed) | Contact.given_name |
| `contact.last_name` | res.partner.name (parsed) | Contact.last_name | Item name (parsed) | Contact.lastname | Person.name (parsed) | Contact.name (parsed) | Contact.family_name |
| `contact.title` | res.partner.function | Contact.job_title | Item text column (custom) | Contact.jobtitle | Person.title | Contact.title | Contact.job_title |
| `contact.source` | crm.lead.source_id | Contact.lead_source_id | Item status column (custom) | Lead.leadsourcecode | Person.source (custom) | Lead.source (custom) | Contact.source_type |

### Extended Platform Deal & Campaign Fields

| Marketing Field | Odoo | Freshsales | Monday.com CRM | Dynamics 365 | Copper | Close | Keap |
|---|---|---|---|---|---|---|---|
| `deal_value` | crm.lead.expected_revenue | Deal.amount | Item number column | Opportunity.estimatedvalue | Opportunity.monetary_value | Opportunity.value | Deal.deal_value |
| `deal_stage` | crm.lead.stage_id | Deal.deal_stage_id | Item status column | Opportunity.salesstagecode | Opportunity.pipeline_stage_id | Opportunity.status_id | Deal.stage.name |
| `deal_close_date` | crm.lead.date_deadline | Deal.expected_close | Item date column | Opportunity.estimatedclosedate | Opportunity.close_date | Opportunity.date_won | Deal.next_action_date |
| `campaign_name` | utm.campaign.name | (custom field) | Board name or group name | Campaign.name | (custom field) | (custom field) | Campaign.campaign_name |
| `campaign_status` | utm.campaign.stage_id | (custom field) | Item status column | Campaign.statuscode | (custom field) | (custom field) | Campaign.status |
| `utm_source` | crm.lead.source_id | Contact.utm_source (custom) | Item text column (custom) | Lead.utm_source (custom) | Person.utm_source (custom) | Lead.utm_source (custom) | Contact.utm_source (custom) |

---

## Section 3: Data Sync Patterns

### One-Way Push (Plugin to CRM)

The most common pattern. The plugin is the source of truth for marketing data and pushes to the CRM.

| Use Case | Trigger | CRM Action |
|---|---|---|
| Lead import from campaign | Campaign execution or form submission | Create Lead/Contact |
| Deal update from pipeline analysis | Pipeline review or scoring change | Update Opportunity/Deal |
| Campaign record creation | Campaign launch via `/digital-marketing-pro:launch-campaign` (or `/digital-marketing-pro:launch-ad-campaign` for paid-ads only) | Create Campaign object |
| Activity logging | Email send, ad click, webinar registration | Create Activity/Task |

```bash
python crm-sync.py --brand {slug} --action push --object lead --data '{"email": "...", "source": "q3-webinar"}'
```

### Two-Way Sync (Plugin and CRM)

Used when both systems hold authoritative data. The CRM has sales activity and deal progression; the plugin has marketing engagement and scoring.

| Direction | Data | Example |
|---|---|---|
| Plugin → CRM | Marketing score, campaign membership, content engagement | Lead score updated from 45 to 82 |
| CRM → Plugin | Deal stage changes, revenue data, sales feedback | Deal moved to "Closed Won" — attribute to campaign |

**Conflict resolution:** Last-write-wins with audit trail. Every sync operation logs: field, old value, new value, source (plugin or CRM), timestamp. Audit log at `~/.claude-marketing/brands/{slug}/crm-sync-log.json`.

### Event-Triggered Sync

Automated syncs fired by specific marketing or sales events.

| Event | Sync Action |
|---|---|
| Campaign execution | Create/update CRM Campaign record |
| Lead form submission | Create CRM Lead with UTM data |
| Lead score crosses threshold (80+) | Update CRM Lead status to "Sales-Ready", notify sales |
| Deal stage changes to "Closed Won" | Trigger attribution update in plugin |
| Email hard bounce | Update CRM Contact status to "Invalid Email" |

---

## Section 4: Deduplication Rules

Before creating any CRM record, the plugin checks for existing matches. Rules are applied in priority order:

| Priority | Method | Match Criteria | Confidence |
|---|---|---|---|
| 1 | Email match | Exact match, case-insensitive | Highest |
| 2 | Phone match | Normalized: strip spaces, dashes, parentheses, country code prefix | High |
| 3 | Company + Name | Company name exact + contact name fuzzy (Levenshtein distance ≤ 2) | Medium |
| 4 | Domain match | Extract domain from email → match to company | Company-level only |

**Always check dedup BEFORE creating records:**
```bash
python crm-sync.py --brand {slug} --action check-dedup --email "user@example.com" --phone "+1-555-0123"
```

**Merge behavior:** When a match is found, the plugin updates the existing record rather than creating a duplicate. If multiple matches are found, the highest-confidence match is used and the others are flagged for manual review.

---

## Section 5: Campaign Linking

How marketing campaigns connect to CRM campaign objects for attribution and reporting.

| CRM | Campaign Object | Lead/Contact Association | Attribution Model |
|---|---|---|---|
| **Salesforce** | Campaign | CampaignMember (links Leads/Contacts to Campaign with Status and ResponseDate) | Influence model via CampaignInfluence or custom attribution |
| **HubSpot** | Custom properties or Campaigns (Marketing Hub Professional+) | Contact timeline events, custom association | HubSpot attribution reports or custom |
| **Zoho** | Campaign | Associate Leads/Contacts via Campaign Member | Zoho Campaign analytics or custom |
| **Pipedrive** | Custom fields or Activities linked to Deals | Activity association on Deal/Person | Custom attribution via plugin |
| **Odoo CRM** | utm.campaign | Link Leads/Contacts via `campaign_id` on `crm.lead` | UTM-based attribution via source/medium/campaign fields |
| **Freshsales** | Custom field on Deal/Contact | Sales Sequence membership, custom associations | Custom attribution via plugin |
| **Monday.com CRM** | Board group or dedicated Campaign board | Item links (connect items across boards) | Custom attribution via plugin dashboards |
| **Microsoft Dynamics 365** | Campaign entity | Campaign Response links Leads/Contacts with response type and date | Built-in campaign attribution reports, custom via Power BI |
| **Copper CRM** | Custom field on Opportunity/Project | Tag or custom field association on People/Companies | Custom attribution via plugin |
| **Close CRM** | Custom field on Lead | Smart View filter + custom field tagging | Custom attribution via plugin |
| **Keap** | Campaign (visual campaign builder) | Tag-based campaign membership on Contacts | Built-in campaign reporting, tag-based attribution |

**Plugin tracking:** Every campaign execution logs a `crm_campaign_id` via:
```bash
python execution-tracker.py --action log-execution --campaign-id {id} --crm-campaign-id {crm_id}
```

This creates a bidirectional link: the plugin knows which CRM campaign corresponds to each marketing campaign, and the CRM campaign links back to the plugin's campaign ID via a custom field.

---

## Section 6: Lead Scoring Integration

The plugin's lead scoring system (defined in `skills/marketing-automation/lead-scoring.md`) generates a 0-100 marketing score. This score must be synced to the CRM for sales team visibility.

### Score Field Mapping

| CRM | Field | Type | Notes |
|---|---|---|---|
| **Salesforce** | `Lead.Marketing_Score__c` / `Contact.Marketing_Score__c` | Number (custom field) | Create via Setup > Object Manager > Fields |
| **HubSpot** | `hubspot_score` (built-in) or custom contact property | Number | Built-in scoring available in Marketing Hub Professional+ |
| **Zoho** | `Marketing_Score` (custom field) | Number | Create via Settings > Modules > Fields |
| **Pipedrive** | Custom field on Person | Number | Create via Settings > Data fields |
| **Odoo CRM** | `crm.lead.priority` or custom field `x_marketing_score` | Integer | Create via Settings > Technical > Fields or API `ir.model.fields` |
| **Freshsales** | `lead_score` (built-in) or custom contact field | Number | Built-in Freddy AI scoring available; custom field for plugin score |
| **Monday.com CRM** | Number column on Contact/Lead board | Number | Add column via board settings or API |
| **Microsoft Dynamics 365** | `lead.msdyn_marketingscore` or custom field `new_marketingscore` | Whole Number | Create via Power Apps > Tables > Lead > Columns |
| **Copper CRM** | Custom field on Person | Number | Create via Settings > Custom Fields |
| **Close CRM** | Custom field on Lead | Number | Create via Settings > Custom Fields > Lead |
| **Keap** | Custom field on Contact or Tag-based scoring | Number | Create via Settings > Custom Fields; or use tag thresholds |

### Sync Frequency

| Trigger | Action |
|---|---|
| Score change (any amount) | Queue sync — batch executes every 15 minutes |
| Score crosses a threshold boundary | Immediate sync + notification |
| Daily batch (midnight local) | Full reconciliation of all scored leads |

### Threshold Actions

| Score Range | Status | CRM Action |
|---|---|---|
| 80-100 | Sales-Ready | Update Lead status, notify assigned sales rep, create Task/Activity |
| 50-79 | Nurture | Enroll in nurture sequence, update Lead status to "Marketing Qualified" |
| 20-49 | Cold | Continue automated nurture, no sales notification |
| 0-19 | Inactive | Flag for re-engagement campaign or suppression after 90 days |

---

## Section 7: Multi-CRM Setup (Agency Pattern)

Agencies managing multiple brands can connect each brand to a different CRM.

**How it works:**
- Credential profiles (`credential-manager.py`) map each brand to its CRM and credentials
- The active CRM is determined by the brand's credential profile via the `default_crm` field
- Switching brands (via `/digital-marketing-pro:switch-brand`) automatically switches CRM context

**Credential profile structure:**
```json
{
  "brand_slug": "acme-corp",
  "default_crm": "salesforce",
  "crm_credentials": {
    "salesforce": {
      "env_prefix": "ACME_SF"
    }
  }
}
```

**Environment variables follow the pattern:** `{ENV_PREFIX}_CLIENT_ID`, `{ENV_PREFIX}_CLIENT_SECRET`, `{ENV_PREFIX}_REFRESH_TOKEN`.

**Example multi-brand setup:**

| Brand | CRM | Env Prefix | Notes |
|---|---|---|---|
| Acme Corp | Salesforce | `ACME_SF` | Enterprise CRM, full read/write |
| BetaWidget | HubSpot | `BETA_HS` | Marketing Hub Professional |
| LocalShop | Pipedrive | `LOCAL_PD` | Small business, deal-focused |
| HealthCo | Zoho CRM | `HEALTH_ZO` | HIPAA-aware configuration |
| MfgDirect | Odoo CRM | `MFG_ODOO` | Open-source, self-hosted with ERP integration |
| SaaSFlow | Freshsales | `SAAS_FS` | Built-in phone/email, Freddy AI scoring |
| CreativeHub | Monday.com CRM | `CREATIVE_MON` | Visual pipeline, Kanban-focused |
| GlobalEnterp | Dynamics 365 | `GLOBAL_DYN` | Enterprise, Microsoft 365 ecosystem |
| DesignStudio | Copper | `DESIGN_CU` | Gmail-native, Google Workspace integration |
| InsideSales | Close CRM | `INSIDE_CL` | Built-in calling/SMS, power dialer |
| CoachPro | Keap | `COACH_KP` | All-in-one with marketing automation + e-commerce |

---

## Section 8: Platform-Specific Integration Details

Detailed connection patterns, object models, and unique capabilities for each extended CRM platform.

### Odoo CRM

- **API:** XML-RPC and JSON-RPC APIs; REST API available via custom module
- **Authentication:** API key + database name + instance URL
- **Key objects:** Leads (`crm.lead`), Contacts (`res.partner`), Opportunities (`crm.lead` with `type=opportunity`), Activities (`mail.activity`), Pipeline stages, Campaigns (`utm.campaign`), Invoices (`account.move`)
- **MCP config key:** `odoo`

| Plugin Field | Odoo Field | Notes |
|---|---|---|
| `lead_name` | `name` | Lead/opportunity title |
| `email` | `email_from` | Primary email on lead |
| `phone` | `phone` | Primary phone on lead |
| `company` | `partner_name` | Company name (text field on lead) |
| `stage` | `stage_id` | Many2one relation to `crm.stage` |
| `expected_revenue` | `expected_revenue` | Monetary value |
| `probability` | `probability` | Win probability (0-100) |
| `tags` | `tag_ids` | Many2many relation to `crm.tag` |

**Unique features:**
- Open-source with full customization — self-hosted or Odoo.sh cloud
- Integrated ERP modules (inventory, accounting, HR, manufacturing) share the same database
- Custom field creation via API using `ir.model.fields`
- Automated actions and server actions for workflow triggers
- Multi-company support with inter-company rules

**Connection example:**
```bash
# .env
ODOO_URL=https://mycompany.odoo.com
ODOO_DB=mycompany
ODOO_API_KEY=your-api-key-here

# Sync command
python crm-sync.py --brand {slug} --crm odoo --action push --object lead --data '{"name": "Q3 Webinar Lead", "email_from": "user@example.com"}'
```

---

### Freshsales (Freshworks CRM)

- **API:** REST API v2
- **Authentication:** API key + domain (`yourcompany.freshsales.io`)
- **Key objects:** Contacts, Accounts, Deals, Notes, Tasks, Appointments, Sales Sequences, Activities
- **MCP config key:** `freshsales`

| Plugin Field | Freshsales Field | Notes |
|---|---|---|
| `contact_name` | `first_name` / `last_name` | Separate first/last fields |
| `email` | `emails[0].value` | Array of email objects |
| `phone` | `phones[0].value` | Array of phone objects |
| `company` | `company.name` | Nested company object |
| `deal_amount` | `amount` | Deal monetary value |
| `deal_stage` | `deal_stage_id` | ID reference to pipeline stage |
| `lead_score` | `lead_score` | Built-in scoring field |

**Unique features:**
- Built-in phone and email (Freshcaller/Freshdesk integration)
- AI lead scoring via Freddy AI — automatic behavioral and demographic scoring
- Auto-profile enrichment from public data sources
- Sales sequences for automated multi-step outreach (email + phone + wait)
- Territory management for geographic/segment-based assignment
- Built-in chat widget for website visitor capture

**Connection example:**
```bash
# .env
FRESHSALES_DOMAIN=yourcompany
FRESHSALES_API_KEY=your-api-key-here

# Sync command
python crm-sync.py --brand {slug} --crm freshsales --action push --object contact --data '{"first_name": "Jane", "last_name": "Doe", "emails": [{"value": "jane@example.com"}]}'
```

---

### Monday.com CRM

- **API:** GraphQL API v2
- **Authentication:** API token (personal or OAuth)
- **Key objects:** Boards (represent CRM pipeline), Items (represent leads/deals/contacts), Columns (fields), Groups (stages), Updates (activity log), Automations
- **MCP config key:** `monday-crm`

| Plugin Field | Monday.com Mapping | Notes |
|---|---|---|
| `item_name` | `name` | Item name (lead/deal name) |
| `stage` | Group within board | Items are organized into Groups representing stages |
| `deal_value` | Number column (custom-defined) | Column ID varies per board |
| `email` | Email column (custom-defined) | Column ID varies per board |
| `close_date` | Date column (custom-defined) | Column ID varies per board |
| `owner` | People column (custom-defined) | Assigns team member |

**Unique features:**
- Highly visual and customizable — Kanban, timeline, table, chart, and calendar views
- Native automations engine: "When status changes to X, notify Y" with 200+ automation recipes
- Integration marketplace with 250+ apps for extending functionality
- Workload management for balancing team capacity
- Dashboards with charts, numbers, and battery widgets for pipeline visualization
- Cross-board item linking for connecting contacts to deals

**Connection example:**
```bash
# .env
MONDAY_API_TOKEN=your-api-token-here

# Sync command (uses GraphQL mutations)
python crm-sync.py --brand {slug} --crm monday-crm --action push --object item --data '{"board_id": 123456, "group_id": "new_leads", "name": "Q3 Webinar Lead", "column_values": {"email": "user@example.com", "numbers": 5000}}'
```

---

### Microsoft Dynamics 365

- **API:** Dataverse Web API (OData v4); also Power Automate connectors
- **Authentication:** OAuth 2.0 (`client_id` + `client_secret` + `tenant_id`), instance URL
- **Key objects:** Leads (`lead`), Contacts (`contact`), Accounts (`account`), Opportunities (`opportunity`), Activities (`activitypointer`), Campaigns (`campaign`), Campaign Responses, Marketing Lists
- **MCP config key:** `dynamics-365`

| Plugin Field | Dynamics 365 Field | Notes |
|---|---|---|
| `lead_name` | `fullname` (or `firstname` / `lastname`) | Composite or separate fields |
| `email` | `emailaddress1` | Primary email |
| `phone` | `telephone1` | Primary phone |
| `company` | `companyname` | Company name on lead |
| `opportunity_amount` | `estimatedvalue` | Monetary (supports multi-currency) |
| `stage` | `salesstagecode` | Sales stage picklist |
| `close_date` | `estimatedclosedate` | Expected close |
| `probability` | `closeprobability` | Win probability (0-100) |

**Unique features:**
- Deep Microsoft 365 integration — Outlook (email tracking, meetings), Teams (collaboration), SharePoint (document management)
- Enterprise-grade security and compliance (SOC 2, ISO 27001, HIPAA, FedRAMP)
- Power Platform integration: Power BI (analytics), Power Automate (workflows), Power Apps (custom apps)
- AI insights via Copilot for sales recommendations and email drafting
- Customer journey orchestration for multi-channel marketing campaigns
- Multi-currency and multi-language support out of the box

**Connection example:**
```bash
# .env
DYNAMICS_INSTANCE_URL=https://yourorg.crm.dynamics.com
DYNAMICS_TENANT_ID=your-tenant-id
DYNAMICS_CLIENT_ID=your-client-id
DYNAMICS_CLIENT_SECRET=your-client-secret

# Sync command
python crm-sync.py --brand {slug} --crm dynamics-365 --action push --object lead --data '{"firstname": "Jane", "lastname": "Doe", "emailaddress1": "jane@example.com", "companyname": "Acme Corp"}'
```

---

### Copper CRM

- **API:** REST API v1
- **Authentication:** API key + user email (both required in headers)
- **Key objects:** People (contacts), Companies, Opportunities, Projects, Tasks, Activities, Custom Fields
- **MCP config key:** `copper`

| Plugin Field | Copper Field | Notes |
|---|---|---|
| `person_name` | `name` | Full name string |
| `email` | `emails[0].email` | Array of email objects |
| `phone` | `phone_numbers[0].number` | Array of phone objects |
| `company` | `company_id` | Relation to Company record |
| `opportunity_value` | `monetary_value` | Deal value in cents |
| `stage` | `pipeline_stage_id` | ID reference to pipeline stage |
| `close_date` | `close_date` | Unix timestamp |
| `status` | `status` | Open, Won, Lost, Abandoned |

**Unique features:**
- Gmail-native — lives inside the Gmail sidebar with automatic contact capture
- Automatic data entry from email interactions (no manual logging)
- Relationship intelligence surfaces interaction history and engagement
- Google Workspace deep integration: Calendar (meetings auto-logged), Drive (files attached to records), Sheets (data export)
- Project management for post-sale delivery and onboarding workflows

**Connection example:**
```bash
# .env
COPPER_API_KEY=your-api-key-here
COPPER_USER_EMAIL=user@yourcompany.com

# Sync command
python crm-sync.py --brand {slug} --crm copper --action push --object people --data '{"name": "Jane Doe", "emails": [{"email": "jane@example.com", "category": "work"}]}'
```

---

### Close CRM

- **API:** REST API v1
- **Authentication:** API key (Basic auth with API key as username, empty password)
- **Key objects:** Leads, Contacts, Opportunities, Activities (calls, emails, SMS, meetings), Tasks, Custom Fields, Smart Views, Sequences
- **MCP config key:** `close-crm`

| Plugin Field | Close Field | Notes |
|---|---|---|
| `lead_name` | `display_name` | Lead display name |
| `contact_name` | `name` | Contact full name |
| `email` | `emails[0].email` | Array of email objects |
| `phone` | `phones[0].phone` | Array of phone objects |
| `opportunity_value` | `value` | Deal value in cents |
| `stage` | `status_id` | Reference to pipeline status |
| `confidence` | `confidence` | Win confidence (0-100) |
| `close_date` | `date_won` or `date_lost` | Set on outcome |

**Unique features:**
- Built-in calling with VoIP, call recording, and voicemail drop
- Built-in SMS for text-based outreach directly from CRM
- Built-in email (send and receive within CRM — no external client needed)
- Power dialer for high-volume outbound sales teams
- Email sequences for automated multi-step follow-up
- Predictive dialer for maximizing call connect rates
- Pipeline reporting with funnel and velocity metrics
- Custom activities for tracking non-standard interactions

**Connection example:**
```bash
# .env
CLOSE_API_KEY=your-api-key-here

# Sync command
python crm-sync.py --brand {slug} --crm close-crm --action push --object lead --data '{"name": "Acme Corp", "contacts": [{"name": "Jane Doe", "emails": [{"email": "jane@example.com"}]}]}'
```

---

### Keap (formerly Infusionsoft)

- **API:** REST API v2 (newer) and XML-RPC (legacy)
- **Authentication:** OAuth 2.0 access token (or legacy API key for XML-RPC)
- **Key objects:** Contacts, Companies, Deals/Opportunities, Tasks, Notes, Tags, Campaigns (visual campaign builder), Orders, Invoices, Products, Subscriptions
- **MCP config key:** `keap`

| Plugin Field | Keap Field | Notes |
|---|---|---|
| `contact_name` | `given_name` / `family_name` | Separate first/last fields |
| `email` | `email_addresses[0].email` | Array of email objects |
| `phone` | `phone_numbers[0].number` | Array of phone objects |
| `company` | `company.company_name` | Nested company object |
| `deal_amount` | `deal_value` | Opportunity monetary value |
| `stage` | `stage.name` | Pipeline stage name |
| `tags` | `tag_ids` | Array of tag ID integers |

**Unique features:**
- Built-in marketing automation with visual campaign builder (triggers, sequences, timers, decision diamonds)
- E-commerce engine: orders, invoices, payments, products, and subscriptions managed natively
- Appointment scheduling with online booking pages
- Landing page builder for lead capture without external tools
- SMS marketing for text-based campaigns and reminders
- Referral partner program management for affiliate tracking
- Small business all-in-one platform: CRM + marketing + sales + e-commerce in a single system

**Connection example:**
```bash
# .env
KEAP_CLIENT_ID=your-client-id
KEAP_CLIENT_SECRET=your-client-secret
KEAP_ACCESS_TOKEN=your-access-token
KEAP_REFRESH_TOKEN=your-refresh-token

# Sync command
python crm-sync.py --brand {slug} --crm keap --action push --object contact --data '{"given_name": "Jane", "family_name": "Doe", "email_addresses": [{"email": "jane@example.com", "field": "EMAIL1"}]}'
```

---

## Section 9: Data Privacy

### GDPR Compliance

| Requirement | Implementation |
|---|---|
| Document legal basis for processing | Store `consent_basis` field on every CRM record (consent, legitimate interest, contract) |
| Respect data subject requests | `crm-sync.py --action dsr --type {access/delete/port} --email "..."` |
| Data retention policy | Configure max retention per brand; auto-flag records exceeding retention period |
| Data Processing Agreements | Required with every CRM vendor — verify before connecting |

### CCPA Compliance

| Requirement | Implementation |
|---|---|
| Honor opt-out requests | `crm-sync.py --action opt-out --email "..."` — suppresses across all sync operations |
| Do not sell data | Plugin never transfers CRM data to third parties |
| Disclosure on collection | Lead forms must include privacy notice linking to brand's privacy policy |

### General Security Rules

| Rule | Detail |
|---|---|
| Credential storage | CRM credentials in `.env` ONLY — never in marketing data files, campaign plans, or logs |
| Audit trail | Every CRM write operation logged with: timestamp, user/agent, action, fields modified, old/new values |
| Access logging | All CRM read operations logged with: timestamp, query, records accessed, purpose |
| Cross-border transfers | If brand operates in multiple jurisdictions, apply the most restrictive privacy rules across all CRM operations |
| Encryption | All MCP connections use TLS. No CRM data stored in plaintext intermediate files |

### Privacy by Default

When creating new CRM integrations:
1. Start with read-only access — add write permissions only when needed
2. Minimize data synced — only push fields required for the use case
3. Set retention limits at connection time
4. Enable audit logging before the first sync
5. Document the data flow in the brand's credential profile

# Staff Engineer Mode Source Index

## Source Quality Policy

Use primary sources whenever available: first-party engineering publications,
official cloud/vendor documentation, standards bodies, peer-reviewed papers, or
widely cited practitioner references that originated a named pattern. Vendor and
company engineering blogs are acceptable only as large-scale case studies or
original pattern writeups, not as unchecked marketing claims. Do not add generic
product, trust, privacy, initiative, or documentation landing pages when a
specific engineering guide, standard, paper, or implementation reference exists.
Do not add
encyclopedias, Q&A/forum threads, scraped mirrors, SEO summaries, anonymous
content farms, or unmaintained unofficial copies when a primary source exists.

Sections below are grouped by source owner: company, project, standards body,
publisher, or named author. The FAANG source-owner sections appear first
alphabetically, followed by Microsoft, then the remaining source-owner sections.
They are not grouped by skill topic.

### Amazon And AWS
- [S30] AWS Well-Architected Framework PDF: https://docs.aws.amazon.com/pdfs/wellarchitected/latest/framework/wellarchitected-framework.pdf
- [S31] AWS Well-Architected Operational Excellence Pillar PDF: https://docs.aws.amazon.com/pdfs/wellarchitected/latest/operational-excellence-pillar/wellarchitected-operational-excellence-pillar.pdf
- [S32] AWS Well-Architected Reliability Pillar PDF: https://docs.aws.amazon.com/pdfs/wellarchitected/latest/reliability-pillar/wellarchitected-reliability-pillar.pdf
- [S33] AWS Well-Architected Security Pillar PDF: https://docs.aws.amazon.com/pdfs/wellarchitected/latest/security-pillar/wellarchitected-security-pillar.pdf
- [S34] AWS Builders' Library - Timeouts, Retries, and Backoff with Jitter: https://aws.amazon.com/builders-library/timeouts-retries-and-backoff-with-jitter/
- [S35] AWS Builders' Library - Static Stability Using Availability Zones: https://aws.amazon.com/builders-library/static-stability-using-availability-zones/
- [S36] AWS Builders' Library - Using Load Shedding to Avoid Overload: https://aws.amazon.com/builders-library/using-load-shedding-to-avoid-overload/
- [S37] AWS Builders' Library - Avoiding Overload in Distributed Systems by Putting the Smaller Service in Control: https://aws.amazon.com/builders-library/avoiding-overload-in-distributed-systems-by-putting-the-smaller-service-in-control/
- [S38] AWS Builders' Library - Avoiding Insurmountable Queue Backlogs: https://aws.amazon.com/builders-library/avoiding-insurmountable-queue-backlogs/
- [S39] AWS Builders' Library - Implementing Health Checks: https://aws.amazon.com/builders-library/implementing-health-checks/
- [S40] AWS Builders' Library - Leader Election in Distributed Systems: https://aws.amazon.com/builders-library/leader-election-in-distributed-systems/
- [S41] AWS Builders' Library - Making Retries Safe with Idempotent APIs: https://aws.amazon.com/builders-library/making-retries-safe-with-idempotent-APIs/
- [S42] AWS Builders' Library - Reliability and Constant Work: https://aws.amazon.com/builders-library/reliability-and-constant-work/
- [S43] AWS Builders' Library - Workload Isolation Using Shuffle-Sharding: https://aws.amazon.com/builders-library/workload-isolation-using-shuffle-sharding/
- [S44] AWS Builders' Library - Automating Safe, Hands-Off Deployments: https://aws.amazon.com/builders-library/automating-safe-hands-off-deployments/
- [S45] AWS Architecture Blog - Disaster Recovery Strategies for Recovery in the Cloud: https://aws.amazon.com/blogs/architecture/disaster-recovery-dr-architecture-on-aws-part-i-strategies-for-recovery-in-the-cloud/
- [S46] AWS SaaS Tenant Isolation Strategies: https://d1.awsstatic.com/whitepapers/saas-tenant-isolation-strategies.pdf
- [S47] Amazon Dynamo: Amazon's Highly Available Key-value Store: https://www.allthingsdistributed.com/files/amazon-dynamo-sosp2007.pdf
- [S97] AWS Builders' Library - Avoiding Fallback in Distributed Systems: https://aws.amazon.com/builders-library/avoiding-fallback-in-distributed-systems/
- [S151] DynamoDB partition key best practices: https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/bp-partition-key-design.html
- [S182] AWS Best Practices for DDoS Resiliency: https://docs.aws.amazon.com/whitepapers/latest/aws-best-practices-ddos-resiliency/aws-best-practices-ddos-resiliency.html
- [S213] Amazon Science - How Amazon Web Services Uses Formal Methods: https://www.amazon.science/publications/how-amazon-web-services-uses-formal-methods
- [S261] Amazon EKS - Kubernetes Versions: https://docs.aws.amazon.com/eks/latest/userguide/kubernetes-versions.html
- [S284] AWS Builders' Library - Ensuring Rollback Safety During Deployments: https://aws.amazon.com/builders-library/ensuring-rollback-safety-during-deployments/
- [S285] AWS Builders' Library - Instrumenting Distributed Systems for Operational Visibility: https://aws.amazon.com/builders-library/instrumenting-distributed-systems-for-operational-visibility/
- [S286] AWS Builders' Library - Building Dashboards for Operational Visibility: https://aws.amazon.com/builders-library/building-dashboards-for-operational-visibility/
- [S287] AWS Builders' Library - Going Faster with Continuous Delivery: https://aws.amazon.com/builders-library/going-faster-with-continuous-delivery/
- [S288] AWS Builders' Library - Using Dependency Isolation to Contain Concurrency Overload: https://aws.amazon.com/builders-library/dependency-isolation/
- [S289] AWS Builders' Library - Minimizing Correlated Failures in Distributed Systems: https://aws.amazon.com/builders-library/minimizing-correlated-failures-in-distributed-systems/
- [S290] AWS Builders' Library - Caching Challenges and Strategies: https://aws.amazon.com/builders-library/caching-challenges-and-strategies/
- [S291] AWS Builders' Library - Resilience Lessons from the Lunch Rush: https://aws.amazon.com/builders-library/resilience-lessons-from-the-lunch-rush/
- [S292] AWS Builders' Library - My CI/CD Pipeline Is My Release Captain: https://aws.amazon.com/builders-library/cicd-pipeline/
- [S293] AWS Builders' Library - Fairness in Multi-Tenant Systems: https://aws.amazon.com/builders-library/fairness-in-multi-tenant-systems/
- [S294] AWS Builders' Library - Challenges with Distributed Systems: https://aws.amazon.com/builders-library/challenges-with-distributed-systems/

### Apple
- [S131] Apple Secure Coding Guide: https://developer.apple.com/library/archive/documentation/Security/Conceptual/SecureCodingGuide/
- [S132] Apple Security Research - Private Cloud Compute: https://security.apple.com/blog/private-cloud-compute/
- [S176] Apple App Store Connect - Release a version update in phases: https://developer.apple.com/help/app-store-connect/update-your-app/release-a-version-update-in-phases
- [S179] Apple MetricKit: https://developer.apple.com/documentation/metrickit
- [S210] Apple Developer - Describing Data Use in Privacy Manifests: https://developer.apple.com/documentation/bundleresources/describing-data-use-in-privacy-manifests

### Google And Firebase
- [S1] Google SRE Book - Embracing Risk: https://sre.google/sre-book/embracing-risk/
- [S2] Google SRE Book - Service Level Objectives: https://sre.google/sre-book/service-level-objectives/
- [S3] Google SRE Book - Monitoring Distributed Systems: https://sre.google/sre-book/monitoring-distributed-systems/
- [S4] Google SRE Book - Release Engineering: https://sre.google/sre-book/release-engineering/
- [S5] Google SRE Book - Addressing Cascading Failures: https://sre.google/sre-book/addressing-cascading-failures/
- [S6] Google SRE Book - Managing Incidents: https://sre.google/sre-book/managing-incidents/
- [S7] Google SRE Book - Postmortem Culture: https://sre.google/sre-book/postmortem-culture/
- [S8] Google SRE Book - Eliminating Toil: https://sre.google/sre-book/eliminating-toil/
- [S9] Google SRE Book - The Production Environment at Google, from the Viewpoint of an SRE: https://sre.google/sre-book/production-environment/
- [S10] Google SRE Workbook - Alerting on SLOs: https://sre.google/workbook/alerting-on-slos/
- [S11] Google SRE Workbook - Canarying Releases: https://sre.google/workbook/canarying-releases/
- [S12] Google SRE Workbook - Postmortem Culture: Learning from Failure: https://sre.google/workbook/postmortem-culture/
- [S13] Google - Building Secure and Reliable Systems: https://google.github.io/building-secure-and-reliable-systems/raw/toc.html
- [S14] Software Engineering at Google - Testing Overview: https://abseil.io/resources/swe-book/html/ch11.html
- [S15] Software Engineering at Google - Documentation: https://abseil.io/resources/swe-book/html/ch10.html
- [S16] Software Engineering at Google - Version Control: https://abseil.io/resources/swe-book/html/ch16.html
- [S17] Software Engineering at Google - Continuous Delivery: https://abseil.io/resources/swe-book/html/ch24.html
- [S18] Software Engineering at Google - Large-Scale Changes: https://abseil.io/resources/swe-book/html/ch22.html
- [S19] Google Engineering Practices - Code Review: https://google.github.io/eng-practices/review/
- [S20] Google Style Guides: https://google.github.io/styleguide/
- [S21] Google Cloud - Infrastructure Reliability Guide: https://docs.cloud.google.com/architecture/infra-reliability-guide
- [S23] The Tail at Scale: https://research.google/pubs/the-tail-at-scale/
- [S24] Large-scale Cluster Management at Google with Borg: https://research.google.com/pubs/archive/43438.pdf
- [S25] Dapper, a Large-Scale Distributed Systems Tracing Infrastructure: https://research.google/pubs/dapper-a-large-scale-distributed-systems-tracing-infrastructure/
- [S26] Spanner: Google's Globally-Distributed Database: https://research.google.com/archive/spanner-osdi2012.pdf
- [S27] Bigtable: A Distributed Storage System for Structured Data: https://research.google.com/archive/bigtable-osdi06.pdf
- [S28] Maglev: A Fast and Reliable Software Network Load Balancer: https://research.google.com/pubs/archive/44824.pdf
- [S60] Google Cloud Blog - Introducing Kayenta, an Open Automated Canary Analysis Tool from Google and Netflix: https://cloud.google.com/blog/products/gcp/introducing-kayenta-an-open-automated-canary-analysis-tool-from-google-and-netflix
- [S66] Google Research - Autopilot: Workload Autoscaling at Google Scale: https://research.google/pubs/autopilot-workload-autoscaling-at-google-scale/
- [S100] Google AIP-180 - Backwards Compatibility: https://google.aip.dev/180
- [S101] Google AIP-185 - Versioning: https://google.aip.dev/185
- [S133] Google BeyondCorp: https://research.google/pubs/beyondcorp-a-new-approach-to-enterprise-security/
- [S170] Google - Rules of Machine Learning: https://developers.google.com/machine-learning/guides/rules-of-ml/
- [S171] Hidden Technical Debt in Machine Learning Systems: https://papers.nips.cc/paper/5656-hidden-technical-debt-in-machine-learning-systems.pdf
- [S172] Google Research - The ML Test Score: https://research.google/pubs/the-ml-test-score-a-rubric-for-ml-production-readiness-and-technical-debt-reduction/
- [S173] Google Cloud - MLOps: Continuous delivery and automation pipelines in machine learning: https://cloud.google.com/solutions/machine-learning/mlops-continuous-delivery-and-automation-pipelines-in-machine-learning
- [S177] Google Play Console - Release app updates with staged rollouts: https://support.google.com/googleplay/android-developer/answer/6346149
- [S178] Firebase Crashlytics - Understand crash-free metrics: https://firebase.google.com/docs/crashlytics/crash-free-metrics
- [S180] web.dev - Web Vitals: https://web.dev/articles/vitals
- [S183] Google Cloud Armor Best Practices: https://docs.cloud.google.com/armor/docs/best-practices
- [S197] Google Cloud Observability - Data Processing SLIs: https://docs.cloud.google.com/stackdriver/docs/solutions/slo-monitoring/sli-metrics/data-proc-metrics
- [S199] Google SRE Workbook - Configuration Design and Best Practices: https://sre.google/workbook/configuration-design/
- [S200] Google SRE Book - Production Services Best Practices: https://sre.google/sre-book/service-best-practices/
- [S201] Software Engineering at Google - Deprecation: https://abseil.io/resources/swe-book/html/ch15.html
- [S202] Software Engineering at Google - Build Systems and Build Philosophy: https://abseil.io/resources/swe-book/html/ch18.html
- [S209] Google Cloud - Data Deletion on Google Cloud: https://cloud.google.com/docs/security/deletion
- [S267] Google Research - Overlapping Experiment Infrastructure: https://research.google.com/pubs/archive/36500.pdf
- [S268] Google Cloud - Runtime Lifecycle: https://cloud.google.com/appengine/docs/standard/lifecycle/runtime-lifecycle
- [S260] Android Developers - Test Your App's Accessibility: https://developer.android.com/guide/topics/ui/accessibility/testing

### Meta
- [S50] Meta Engineering - Move Faster, Wait Less: Improving Code Review Time at Meta: https://engineering.fb.com/2022/11/16/culture/meta-code-review-time-improving/
- [S51] Meta Engineering - Open-sourcing Facebook Infer: https://engineering.fb.com/developer-tools/open-sourcing-facebook-infer-identify-bugs-before-you-ship/
- [S52] Meta Engineering - Sapienz: Intelligent Automated Software Testing at Scale: https://engineering.fb.com/developer-tools/sapienz-intelligent-automated-software-testing-at-scale/
- [S53] Meta Engineering - TAO: The Power of the Graph: https://engineering.fb.com/2013/06/25/core-infra/tao-the-power-of-the-graph/
- [S54] Meta Engineering - Scaling Memcache at Facebook: https://engineering.fb.com/2013/04/15/core-infra/scaling-memcache-at-facebook/
- [S55] Meta Engineering - Cache Made Consistent: https://engineering.fb.com/2022/06/08/core-infra/cache-made-consistent/
- [S56] Meta Engineering - More Details About the October 4 Outage: https://engineering.fb.com/2021/10/05/networking-traffic/outage-details/
- [S58] Meta Engineering - Automating Dead Code Cleanup: https://engineering.fb.com/2023/10/24/data-infrastructure/automating-dead-code-cleanup/
- [S205] Meta Engineering - Automating Product Deprecation: https://engineering.fb.com/2023/10/17/data-infrastructure/automating-product-deprecation-meta/
- [S206] Meta Engineering - Automating Data Removal: https://engineering.fb.com/2023/10/31/data-infrastructure/automating-data-removal/
- [S207] Meta Engineering - DELF: Safeguarding Deletion Correctness: https://engineering.fb.com/2020/08/12/security/delf/
- [S208] Meta Engineering - Privacy Aware Infrastructure Purpose Limitation: https://engineering.fb.com/2024/08/27/security/privacy-aware-infrastructure-purpose-limitation-meta/
- [S211] Meta Engineering - How Meta Understands Data at Scale: https://engineering.fb.com/2025/04/28/security/how-meta-understands-data-at-scale/

### Netflix
- [S62] A Platform for Automating Chaos Experiments: https://arxiv.org/abs/1702.05849
- [S64] Netflix DGS Framework - Federation: https://netflix.github.io/dgs/federation/
- [S65] Netflix Repokid: https://github.com/Netflix/repokid
- [S212] Netflix - Automating Chaos Experiments in Production: https://arxiv.org/abs/1905.04648

### Microsoft And Azure
- [S91] Azure Well-Architected - Mission-Critical Design Principles: https://learn.microsoft.com/en-us/azure/well-architected/mission-critical/mission-critical-design-principles
- [S92] Microsoft Security Development Lifecycle: https://learn.microsoft.com/en-us/compliance/assurance/assurance-microsoft-security-development-lifecycle
- [S93] Microsoft Learn - Integrating Threat Modeling with DevOps: https://learn.microsoft.com/en-us/security/engineering/threat-modeling-with-dev-ops
- [S94] Azure Architecture Center - Retry Pattern: https://learn.microsoft.com/en-us/azure/architecture/patterns/retry
- [S95] Azure Architecture Center - Circuit Breaker Pattern: https://learn.microsoft.com/en-us/azure/architecture/patterns/circuit-breaker
- [S96] Azure Architecture Center - Bulkhead Pattern: https://learn.microsoft.com/en-us/azure/architecture/patterns/bulkhead
- [S214] Azure Well-Architected - Reliability Checklist: https://learn.microsoft.com/en-us/azure/well-architected/reliability/checklist
- [S215] Azure Well-Architected - Safe Deployment Practices: https://learn.microsoft.com/en-us/azure/well-architected/operational-excellence/safe-deployments
- [S216] Azure Well-Architected - Incident Management Process: https://learn.microsoft.com/en-us/azure/well-architected/operational-excellence/mitigation-strategy
- [S217] Azure Well-Architected - Performance Efficiency Checklist: https://learn.microsoft.com/en-us/azure/well-architected/performance-efficiency/checklist
- [S218] Azure Well-Architected - Performance Testing Strategies: https://learn.microsoft.com/en-us/azure/well-architected/performance-efficiency/performance-test
- [S219] Azure Well-Architected - Cost Optimization Tradeoffs: https://learn.microsoft.com/en-us/azure/well-architected/cost-optimization/tradeoffs
- [S220] Azure Architecture Center - Deployment Stamps Pattern: https://learn.microsoft.com/en-us/azure/architecture/patterns/deployment-stamp
- [S221] Azure Well-Architected - Availability Zones and Regions: https://learn.microsoft.com/en-us/azure/well-architected/reliability/regions-availability-zones
- [S222] Azure Architecture Center - Rate Limiting Pattern: https://learn.microsoft.com/en-us/azure/architecture/patterns/rate-limiting-pattern
- [S223] Azure Architecture Center - Queue-Based Load Leveling Pattern: https://learn.microsoft.com/en-us/azure/architecture/patterns/queue-based-load-leveling
- [S224] Microsoft DevOps - How Microsoft Develops with DevOps: https://learn.microsoft.com/en-us/devops/develop/how-microsoft-develops-devops
- [S225] Microsoft DevOps - How Microsoft Delivers Software with DevOps: https://learn.microsoft.com/en-us/devops/deliver/how-microsoft-delivers-devops
- [S226] Microsoft DevOps - How Microsoft Operates Reliable Systems with DevOps: https://learn.microsoft.com/en-us/devops/operate/how-microsoft-operates-devops
- [S227] Microsoft DevOps - Shift Testing Left with Unit Tests: https://learn.microsoft.com/en-us/devops/develop/shift-left-make-testing-fast-reliable
- [S228] Microsoft DevOps - Continuous Delivery: https://learn.microsoft.com/en-us/devops/deliver/what-is-continuous-delivery
- [S229] Microsoft Platform Engineering - Self-Service with Guardrails: https://learn.microsoft.com/en-us/platform-engineering/about/self-service
- [S230] Microsoft Cloud Adoption Framework - Azure Landing Zones: https://learn.microsoft.com/en-us/azure/cloud-adoption-framework/ready/landing-zone/
- [S231] Microsoft Entra - Configure Zero Trust to Protect Identities and Secrets: https://learn.microsoft.com/en-us/entra/fundamentals/zero-trust-protect-identities
- [S232] Microsoft Entra - Workload Identities: https://learn.microsoft.com/en-us/entra/workload-id/workload-identities-overview
- [S233] Microsoft Cloud Security Benchmark v2 Preview - DevOps Security: https://learn.microsoft.com/en-us/security/benchmark/azure/mcsb-v2-devop-security
- [S234] Microsoft Secure Future Initiative - Protect the Software Supply Chain: https://learn.microsoft.com/en-us/security/zero-trust/sfi/protect-software-supply-chain
- [S235] Azure DDoS Protection - Fundamental Best Practices: https://learn.microsoft.com/en-us/azure/ddos-protection/fundamental-best-practices
- [S236] Azure Architecture Center - API Design: https://learn.microsoft.com/en-us/azure/architecture/microservices/design/api-design
- [S237] Azure Architecture Center - Data Partitioning Strategies: https://learn.microsoft.com/en-us/azure/architecture/best-practices/data-partitioning-strategies
- [S238] Azure Architecture Center - Cache-Aside Pattern: https://learn.microsoft.com/en-us/azure/architecture/patterns/cache-aside
- [S239] Azure Architecture Center - CQRS Pattern: https://learn.microsoft.com/en-us/azure/architecture/patterns/cqrs
- [S240] Azure Architecture Center - Event Sourcing Pattern: https://learn.microsoft.com/en-us/azure/architecture/patterns/event-sourcing
- [S241] Azure Well-Architected - Data Classification: https://learn.microsoft.com/en-us/azure/well-architected/security/data-classification
- [S242] Microsoft Purview - Data Lifecycle Management: https://learn.microsoft.com/en-us/purview/data-lifecycle-management
- [S243] Azure Well-Architected - Security Checklist: https://learn.microsoft.com/en-us/azure/well-architected/security/checklist
- [S244] Azure Well-Architected - Threat Analysis Strategies: https://learn.microsoft.com/en-us/azure/architecture/framework/security/design-threat-model
- [S245] Azure Well-Architected - Build a Monitoring System: https://learn.microsoft.com/en-us/azure/well-architected/design-guides/monitoring
- [S246] Azure Reliability - Business Continuity, High Availability, and Disaster Recovery: https://learn.microsoft.com/en-us/azure/reliability/disaster-recovery-overview
- [S247] Azure Well-Architected - Reliability Testing Strategy: https://learn.microsoft.com/en-us/azure/well-architected/reliability/testing-strategy
- [S248] Azure Well-Architected - Mission-Critical Health Modeling: https://learn.microsoft.com/en-us/azure/well-architected/mission-critical/mission-critical-health-modeling
- [S249] Azure Well-Architected - Health Modeling for Workloads: https://learn.microsoft.com/en-us/azure/well-architected/design-guides/health-modeling
- [S250] Microsoft Entra - Managed Identities for Azure Resources: https://learn.microsoft.com/en-us/entra/identity/managed-identities-azure-resources/overview
- [S251] Microsoft Entra - Workload Identity Federation: https://learn.microsoft.com/en-us/entra/workload-id/workload-identity-federation
- [S252] Microsoft Platform Engineering - Platform Engineering Capability Model: https://learn.microsoft.com/en-us/platform-engineering/platform-engineering-capability-model
- [S253] Microsoft Azure AI Foundry - Planning Red Teaming for Large Language Models: https://learn.microsoft.com/en-us/azure/foundry/openai/concepts/red-teaming
- [S254] Microsoft Security Engineering - Threat Modeling AI/ML Systems and Dependencies: https://learn.microsoft.com/en-us/security/engineering/threat-modeling-aiml
- [S255] Microsoft Security Engineering - Failure Modes in Machine Learning: https://learn.microsoft.com/en-us/security/engineering/failure-modes-in-machine-learning
- [S256] Azure Well-Architected - Security Incident Response: https://learn.microsoft.com/en-us/azure/well-architected/security/incident-response
- [S257] Azure Architecture Center - Tenancy Models for a Multitenant Solution: https://learn.microsoft.com/en-us/azure/architecture/guide/multitenant/considerations/tenancy-models
- [S258] Microsoft Cloud Security Benchmark v2 Preview - Overview: https://learn.microsoft.com/en-us/security/benchmark/azure/overview
- [S272] Microsoft Research - Diagnosing Sample Ratio Mismatch in Online Controlled Experiments: https://www.microsoft.com/en-us/research/publication/diagnosing-sample-ratio-mismatch-in-online-controlled-experiments-a-taxonomy-and-rules-of-thumb-for-practitioners/

### ACM Queue
- [S190] ACM Queue - Systems Correctness Practices at AWS: https://queue.acm.org/detail.cfm?id=3712057

### ADR GitHub Organization
- [S106] ADR GitHub organization and templates: https://adr.github.io/

### Alistair Cockburn
- [S110] Alistair Cockburn - Hexagonal Architecture: https://alistair.cockburn.us/hexagonal-architecture

### Anthropic
- [S259] Anthropic Docs - Create Strong Empirical Evaluations: https://docs.anthropic.com/en/docs/test-and-evaluate/develop-tests

### Apache Cassandra
- [S154] Cassandra Data Modeling: https://cassandra.apache.org/doc/latest/cassandra/developing/data-modeling/intro.html

### Argo CD
- [S122] Argo CD Core Concepts: https://argo-cd.readthedocs.io/en/stable/core_concepts/

### AsyncAPI Initiative
- [S262] AsyncAPI Specification: https://www.asyncapi.com/docs/reference/specification/latest

### Backstage
- [S123] Backstage Software Catalog: https://backstage.io/docs/features/software-catalog/

### Brendan Gregg
- [S143] Brendan Gregg - USE Method and Flame Graphs: https://www.brendangregg.com/usemethod.html

### CA/Browser Forum
- [S263] CA/Browser Forum - Baseline Requirements for TLS Server Certificates: https://cabforum.org/working-groups/server/baseline-requirements/requirements/

### CISA
- [S72] CISA Secure by Design: https://www.cisa.gov/resources-tools/resources/secure-by-design
- [S82] CISA Zero Trust Maturity Model: https://www.cisa.gov/zero-trust-maturity-model
- [S193] CISA Known Exploited Vulnerabilities Catalog: https://www.cisa.gov/known-exploited-vulnerabilities-catalog
- [S264] CISA And Partners - Deploying AI Systems Securely: https://media.defense.gov/2024/Apr/15/2003439257/-1/-1/0/CSI-DEPLOYING-AI-SYSTEMS-SECURELY.PDF

### CloudEvents
- [S265] CloudEvents Specification: https://github.com/cloudevents/spec

### Cloudflare
- [S184] Cloudflare DDoS Protection - Proactive Defense: https://developers.cloudflare.com/ddos-protection/best-practices/proactive-defense/

### Confluent
- [S118] Confluent - Schema Registry: https://docs.confluent.io/platform/current/schema-registry/index.html

### Diataxis
- [S266] Diataxis Documentation Framework: https://diataxis.fr/

### Discord
- [S152] Discord Engineering - How Discord Stores Trillions of Messages: https://discord.com/blog/how-discord-stores-trillions-of-messages

### DORA
- [S22] DORA - Software Delivery Performance Metrics: https://dora.dev/guides/dora-metrics-four-keys/

### Envoy
- [S129] Envoy Architecture Overview: https://www.envoyproxy.io/docs/envoy/latest/intro/arch_overview/arch_overview

### Eric Evans
- [S109] Eric Evans - Domain-Driven Design Reference: https://www.domainlanguage.com/wp-content/uploads/2016/05/DDD_Reference_2015-03.pdf

### Etsy
- [S141] Etsy Debriefing Facilitation Guide: https://extfiles.etsy.com/DebriefingFacilitationGuide.pdf

### FinOps Foundation
- [S155] FinOps Usage Optimization: https://www.finops.org/framework/capabilities/workload-optimization/

### FIRST
- [S194] FIRST Exploit Prediction Scoring System: https://www.first.org/epss/

### GitHub
- [S186] GitHub Blog - gh-ost: GitHub's Online Schema Migration Tool for MySQL: https://github.blog/news-insights/company-news/gh-ost-github-s-online-migration-tool-for-mysql/
- [S189] GitHub Docs - About Secret Scanning: https://docs.github.com/en/code-security/concepts/secret-security/about-secret-scanning

### Grafana
- [S125] Grafana - Dashboard Best Practices: https://grafana.com/docs/grafana/latest/dashboards/build-dashboards/best-practices/
- [S144] Grafana - The RED Method: https://grafana.com/blog/the-red-method-how-to-instrument-your-services/

### Great Expectations
- [S198] Great Expectations - Run Validations: https://docs.greatexpectations.io/docs/core/run_validations/

### HashiCorp
- [S121] Terraform Language Documentation: https://developer.hashicorp.com/terraform/language

### Honeycomb
- [S145] Honeycomb - Observability 2.0: https://www.honeycomb.io/blog/one-key-difference-observability1dot0-2dot0

### IETF
- [S84] OAuth 2.1 Draft: https://datatracker.ietf.org/doc/html/draft-ietf-oauth-v2-1
- [S85] RFC 8446 - TLS 1.3: https://datatracker.ietf.org/doc/html/rfc8446
- [S104] RFC 9457 - Problem Details for HTTP APIs: https://www.rfc-editor.org/rfc/rfc9457.html
- [S269] RFC 7696 - Guidelines for Cryptographic Algorithm Agility: https://www.rfc-editor.org/rfc/rfc7696

### Industrial Empathy
- [S159] Industrial Empathy - Design Docs at Google: https://www.industrialempathy.com/posts/design-docs-at-google/

### Istio
- [S195] Istio Traffic Management: https://istio.io/latest/docs/concepts/traffic-management/

### Jay Kreps
- [S153] Jay Kreps - The Log: https://engineering.linkedin.com/distributed-systems/log-what-every-software-engineer-should-know-about-real-time-datas-unifying

### John D. C. Little
- [S157] Little - A Proof for the Queuing Formula L = lambda W: https://pubsonline.informs.org/doi/10.1287/opre.9.3.383

### JSON Schema
- [S270] JSON Schema Specification: https://json-schema.org/specification

### Kubernetes
- [S120] Kubernetes Components: https://kubernetes.io/docs/concepts/overview/components/
- [S196] Kubernetes Gateway API: https://kubernetes.io/docs/concepts/services-networking/gateway/
- [S271] Kubernetes Version Skew Policy: https://kubernetes.io/releases/version-skew-policy

### Martin Fowler
- [S108] Martin Fowler - What do you mean by Event-Driven?: https://martinfowler.com/articles/201701-event-driven.html
- [S111] Martin Fowler - Bounded Context: https://martinfowler.com/bliki/BoundedContext.html
- [S114] Martin Fowler - MonolithFirst: https://martinfowler.com/bliki/MonolithFirst.html
- [S115] Martin Fowler - Feature Toggles: https://martinfowler.com/articles/feature-toggles.html
- [S160] Martin Fowler - The Practical Test Pyramid: https://martinfowler.com/articles/practical-test-pyramid.html
- [S161] Martin Fowler - Circuit Breaker: https://martinfowler.com/bliki/CircuitBreaker.html
- [S162] Martin Fowler - Microservice Premium: https://martinfowler.com/bliki/MicroservicePremium.html
- [S163] Martin Fowler - CanaryRelease: https://martinfowler.com/bliki/CanaryRelease.html

### Martin Kleppmann
- [S148] Designing Data-Intensive Applications, 2nd Edition: https://www.oreilly.com/library/view/designing-data-intensive-applications/9781098119058/

### Michael Nygard
- [S191] Michael Nygard - Documenting Architecture Decisions: https://cognitect.com/blog/2011/11/15/documenting-architecture-decisions

### Microservices.io
- [S116] Microservices.io - Transactional Outbox: https://microservices.io/patterns/data/transactional-outbox.html
- [S117] Microservices.io - Saga: https://microservices.io/patterns/data/saga.html

### MITRE
- [S87] MITRE ATT&CK: https://attack.mitre.org/

### NIST
- [S70] NIST SP 800-218 - Secure Software Development Framework: https://csrc.nist.gov/pubs/sp/800/218/final
- [S81] NIST SP 800-207 - Zero Trust Architecture: https://csrc.nist.gov/pubs/sp/800/207/final
- [S86] NIST Post-Quantum Cryptography Project: https://csrc.nist.gov/projects/post-quantum-cryptography
- [S192] NIST FIPS 203 - Module-Lattice-Based Key-Encapsulation Mechanism Standard: https://csrc.nist.gov/pubs/fips/203/final
- [S203] NIST Privacy Framework 1.0: https://csrc.nist.gov/pubs/cswp/10/nist-privacy-framework-version-10/final
- [S204] NIST SP 800-53 Revision 5 - Security and Privacy Controls: https://csrc.nist.gov/pubs/sp/800/53/r5/upd1/final
- [S273] NIST SP 800-128 - Security-Focused Configuration Management: https://csrc.nist.gov/publications/detail/sp/800-128/final
- [S274] NIST AI Risk Management Framework 1.0: https://www.nist.gov/publications/artificial-intelligence-risk-management-framework-ai-rmf-10
- [S275] NIST AI 600-1 - Generative AI Profile: https://www.nist.gov/publications/artificial-intelligence-risk-management-framework-generative-artificial-intelligence
- [S276] NIST SP 800-57 Part 1 Revision 5 - Recommendation for Key Management: https://csrc.nist.gov/pubs/sp/800/57/pt1/r5/final
- [S277] NIST SP 800-131A Revision 2 - Transitioning Cryptographic Algorithms and Key Lengths: https://csrc.nist.gov/pubs/sp/800/131/a/r2/final

### OpenAI
- [S278] OpenAI API - Agent Evals: https://platform.openai.com/docs/guides/agent-evals

### OpenAPI Initiative
- [S279] OpenAPI Specification: https://spec.openapis.org/oas/

### Open Policy Agent
- [S126] Open Policy Agent Policy Language: https://www.openpolicyagent.org/docs/latest/policy-language/

### OpenSSF
- [S78] OpenSSF Scorecard: https://github.com/ossf/scorecard
- [S79] OpenSSF Open Source Project Security Baseline: https://baseline.openssf.org/
- [S280] OpenSSF - Security-Focused Guide for AI Code Assistant Instructions: https://best.openssf.org/Security-Focused-Guide-for-AI-Code-Assistant-Instructions
- [S281] OpenSSF AI/ML Security Working Group Repository: https://github.com/ossf/ai-ml-security

### OpenTelemetry
- [S89] OpenTelemetry Specification: https://opentelemetry.io/docs/specs/otel/
- [S128] OpenTelemetry Collector Configuration: https://opentelemetry.io/docs/collector/configuration/

### OWASP
- [S73] OWASP Application Security Verification Standard: https://owasp.org/www-project-application-security-verification-standard/
- [S74] OWASP Top 10: https://owasp.org/Top10/
- [S75] OWASP Cheat Sheet Series: https://cheatsheetseries.owasp.org/
- [S175] OWASP Top 10 for LLM Applications 2025: https://genai.owasp.org/resource/owasp-top-10-for-llm-applications-2025/

### PagerDuty
- [S140] PagerDuty Incident Response: https://response.pagerduty.com/

### Perfdynamics
- [S156] Universal Scalability Law: https://www.perfdynamics.com/Manifesto/USLscalability.html

### PostgreSQL
- [S187] PostgreSQL Documentation - Routine Vacuuming: https://www.postgresql.org/docs/current/routine-vacuuming.html

### Principles Of Chaos Engineering
- [S61] Principles of Chaos Engineering: https://principlesofchaos.org/

### Prometheus
- [S124] Prometheus Querying Basics: https://prometheus.io/docs/prometheus/latest/querying/basics/
- [S295] Prometheus Alerting Rules: https://prometheus.io/docs/prometheus/latest/configuration/alerting_rules/

### Richard Cook
- [S142] Richard Cook - How Complex Systems Fail: https://how.complexsystems.fail/

### Semantic Versioning
- [S282] Semantic Versioning Specification: https://semver.org/

### Shopify
- [S112] Shopify Engineering - Deconstructing the Monolith: https://shopify.engineering/deconstructing-monolith-designing-software-maximizes-developer-productivity

### Sigstore
- [S80] Sigstore Security Model: https://docs.sigstore.dev/about/security/
- [S127] Cosign Documentation: https://docs.sigstore.dev/cosign/signing/overview/

### SLSA
- [S76] SLSA Specification: https://slsa.dev/spec/
- [S77] SLSA Build Provenance Specification: https://slsa.dev/spec/v1.2/build-provenance

### SPIFFE/SPIRE
- [S83] SPIFFE Standard: https://raw.githubusercontent.com/spiffe/spiffe/main/standards/SPIFFE.md

### Stripe
- [S102] Stripe - Designing Robust and Predictable APIs with Idempotency: https://stripe.com/blog/idempotency
- [S103] Stripe - API Versioning: https://stripe.com/blog/api-versioning
- [S185] Stripe - Online Migrations at Scale: https://stripe.com/blog/online-migrations

### The Twelve-Factor App
- [S147] Twelve-Factor App - Config: https://12factor.net/config

### Trunk Based Development
- [S146] Trunk Based Development: https://trunkbaseddevelopment.com/

### Uber
- [S113] Uber Engineering - DOMA: https://www.uber.com/us/en/blog/microservice-architecture/

### Vitess
- [S188] Vitess Documentation - Managed, Online Schema Changes: https://vitess.io/docs/24.0/user-guides/schema-changes/managed-online-schema-changes/

### W3C
- [S88] W3C Trace Context: https://www.w3.org/TR/trace-context/
- [S181] W3C - Web Content Accessibility Guidelines 2.2: https://www.w3.org/TR/WCAG22/
- [S283] W3C - Accessibility Conformance Testing Rules Format: https://www.w3.org/TR/act-rules-format/

### Werner Vogels
- [S48] Werner Vogels - Eventually Consistent: https://www.allthingsdistributed.com/2008/12/eventually_consistent.html

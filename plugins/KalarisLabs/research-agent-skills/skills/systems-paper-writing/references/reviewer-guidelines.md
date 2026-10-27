# Systems Conference Reviewer Guidelines

Systems conferences (OSDI, NSDI, ASPLOS, SOSP) evaluate papers differently from ML/AI venues. Understanding these differences is critical for cross-venue submissions.

---

## Core Evaluation Criteria for Systems

| Criterion | What Reviewers Look For |
|-----------|------------------------|
| **Novelty** | New system design, not just incremental improvement |
| **Significance** | Solves important practical problem |
| **System Design** | Sound architecture, clear design decisions |
| **Implementation** | Working prototype, not just simulation |
| **Evaluation** | Real workloads, end-to-end performance |
| **Clarity** | Clear writing, reproducible |

## OSDI 2026 Reviewer Perspective

**What reviewers evaluate:**
- Topic relevance to computer systems
- Potential to impact future systems research and practices
- Interest to substantial portion of OSDI attendees
- Papers with little PC overlap are less likely accepted

**Research Track criteria:**
- Novelty, significance, clarity, relevance, correctness
- Quantified or insightful experiences in systems

**Operational Systems Track criteria:**
- Real-world deployment at meaningful scale
- Lessons that deepen understanding of existing problems
- Disproves or strengthens existing assumptions
- Novel research ideas NOT required

**New in 2026:**
- No author response period
- Conditional accept replaces revise-and-resubmit
- Target acceptance rate ≥20%
- Reviewers encouraged to down-rank padded papers

## NSDI 2027 Reviewer Perspective

**Prescreening (Introduction only):**

Reviewers check three criteria in the prescreening phase:
1. **Scope**: Subject within NSDI topics
2. **Accessibility**: Understandable by PC member
3. **Track alignment**: Meets track-specific criteria

**Track-specific review:**

| Track | Key Criterion |
|-------|---------------|
| Research | Novel idea + compelling evaluation evidence |
| Frontiers | Bold non-incremental idea (complete evaluation not required) |
| Operational | Deployment context, scale, lessons for community |

**One-shot revision:**
- Rejected papers may receive a list of issues to address
- Authors can resubmit revision at next deadline
- Same reviewers review the revision (to extent possible)

## ASPLOS 2027 Reviewer Perspective

**Rapid Review Round:**
- Reviewers read ONLY first 2 pages
- Evaluates: Does this advance Architecture, PL, or OS research?
- Majority of submissions may not advance past this stage
- Similar to Nature/Science early screening model

**Full Review criteria:**
- Advances in core ASPLOS disciplines (not just using them)
- Quality of system design and implementation
- Major Revision decision available

## SOSP 2026 Reviewer Perspective

**Core evaluation:**
- Novelty, significance, interest, clarity, relevance, correctness
- Encourages groundbreaking work in significant new directions
- Different evaluation criteria for new problems vs established areas

**Author Response:**
- Limited to: correcting factual errors + addressing reviewer questions
- NO new experiments or additional work
- Keep under 500 words

**Artifact Evaluation:**
- Optional but encouraged
- Cooperative process: authors can fix issues during evaluation
- Register within days of acceptance notification

## ML vs Systems: Key Review Differences

| Aspect | ML/AI Venues | Systems Venues |
|--------|-------------|---------------|
| **Page limit** | 7-9 pages | 12 pages |
| **Evaluation focus** | Benchmarks, ablations, metrics | End-to-end system performance, real workloads |
| **Implementation** | Code often optional | Working system expected |
| **Novelty** | New methods/insights | New system designs/approaches |
| **Reproducibility** | Checklist-based | Artifact evaluation (optional) |
| **Template** | Venue-specific `.sty` | USENIX `.sty` or ACM `acmart.cls` |
| **Review process** | Single deadline | Often dual deadlines |

## Systems-Specific Common Concerns

| Concern | How to Pre-empt |
|---------|-----------------|
| "Just an ML paper, not systems" | Emphasize system design, architecture decisions, deployment challenges |
| "Evaluation only on microbenchmarks" | Include end-to-end evaluation with real workloads |
| "No working prototype" | Build and evaluate a real system, not just simulate |
| "Deployment not realistic" | Show real-world applicability, discuss practical constraints |
| "Not relevant to systems community" | Frame contributions in systems terms, cite systems papers |
| "ASPLOS: Not advancing arch/PL/OS" | Explicitly state how work advances core disciplines |

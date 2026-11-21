# Source register and applicability

Research baseline: **1 October 2026**. Sources were discovered with Exa and web search and checked against their primary pages. This register preserves support for maintained rules; it is not a ranking benchmark. Recheck vendor instructions when a task depends on a current feature, format or limit.

## ATS product documentation

| Primary source | Supported scope and limit |
|---|---|
| Greenhouse: [Unsuccessful resume parse](https://support.greenhouse.io/hc/en-us/articles/200989175-Unsuccessful-resume-parse), [supported uploads](https://support.greenhouse.io/hc/en-us/articles/360052218132-Supported-formats-for-resumes-cover-letters-and-other-candidate-uploads) | Parsing risks include complex layout and contact placement. Accepted upload and parser limits are distinct; acceptance is not successful parsing. |
| Greenhouse: [Boolean search](https://support.greenhouse.io/hc/en-us/articles/202360199-Search-candidates-using-Boolean-queries), [Talent Matching](https://support.greenhouse.io/hc/en-us/articles/41396009937307-Talent-Matching), [auto-reject](https://support.greenhouse.io/hc/en-us/articles/360000653472-Auto-reject) | Search, optional configured matching, and rejection rules on application answers are separate functions. They do not establish a portable ATS score. |
| Lever: [Resume parsing](https://help.lever.co/s/article/Understanding-Resume-Parsing), [advanced search and rediscovery](https://help.lever.co/hc/en-us/articles/20087212721309-Using-advanced-search-and-rediscovery) | Text-based PDF and Word are among supported inputs; selectable text is a preliminary check. Parsed fields and recruiter search differ from matching or rejection. |
| Workday HiredScore: [grades](https://doc.workday.com/hiredscore/en-us/workday-hiredscore/recruiter-productivity-/concept--hiredscore-grades.html), [candidate profiles](https://doc.workday.com/hiredscore/en-us/workday-hiredscore/recruiter-productivity-/concept--candidate-profiles.html), [Fit & Gap](https://doc.workday.com/hiredscore/en-us/workday-hiredscore/recruiter-productivity-/concept--fit---gap.html) | Product-specific grades and configurable analysis exist. Do not imply every Workday employer uses HiredScore or these settings. Pages show older/inherited update metadata; do not call them new 2026 releases. |
| iCIMS: [Binary Files](https://developer-community.icims.com/applications/applicant-tracking/binary-files), [searching/reporting FAQ](https://community.icims.com/articles/FAQ/Searching-Reporting-FAQ) | Extraction and file handling have system-specific settings. One documented keyword rank uses term location/frequency; no global repetition cap follows. |
| SmartRecruiters: [Talent Matching](https://www.smartrecruiters.com/recruiting-software/talent-matching/), [June 2026 release](https://www.smartrecruiters.com/resources/article/june-2026-product-release-highlights-more-control-confidence-in-hiring-workflows/) | Product descriptions support the existence of matching, not universal accuracy. Candidate-verified experience/education can take precedence over parsed data in the documented workflow. |

No inspected primary evidence established a global two-mention rule, fourth-mention penalty, numeric outcome in every bullet, universal DOCX parsing advantage, or local 70/85% passing thresholds. Unsupported legacy percentages were removed; lack of verification is not proof that every underlying study is false.

## Writing, market and role guidance

| Primary source | Useful decision; limits |
|---|---|
| Harvard: [strong resumes](https://careerservices.fas.harvard.edu/resources/create-a-strong-resume/), [resumes and cover letters](https://careerservices.fas.harvard.edu/resources/hes-create-impactful-resumes-and-cover-letters/) | Specific, factual, audience-aware language; natural cover letters. US-facing personal-data guidance is not a rule for all English-language CVs. |
| MIT: [Resumes](https://capd.mit.edu/resources/resumes/) | Action, context and evidence; quantify when possible. Qualitative work remains valid when numbers are unavailable. Student-oriented examples do not define an executive page ceiling. |
| Oxford: [CVs](https://www.careers.ox.ac.uk/cvs) | Select relevant evidence and adapt format to the application; UK/academic guidance has its own context. English is not equivalent to US hiring. |
| Europass: [Create a CV](https://europass.europa.eu/en/create-europass-cv) | European public guidance includes a photo recommendation. This is a competing convention, not proof that every European employer requires a photo. |
| hh.ru: [Resume guide](https://hh.ru/article/kak-sostavit-rezyume), [photo and experience](https://hh.ru/article/25339), [executive resumes](https://hh.ru/article/27467), [cover letters](https://hh.ru/article/kak-napisat-soprovoditelnoe-pismo-k-rezyume-primery-i-sovety) | Platform-oriented relevance, neutral actions, optional photo and different depth for managers. Editorial advice is not an ATS benchmark. Do not generalize structured-platform fields to all Russian attachments. |
| hh.ru: [Resume creation help](https://feedback.hh.ru/knowledge-base/article/1628) | Inspect the actual form and requirements. Optional date-of-birth guidance found on Zarplata's separate help page does not establish hh.ru behavior. |
| GitLab: [Engineering management](https://handbook.gitlab.com/job-description-library/engineering/engineering-management/), [Staff scope](https://handbook.gitlab.com/handbook/engineering/careers/matrix/staff/), [Principal scope](https://handbook.gitlab.com/handbook/engineering/careers/matrix/principal/) | Employer-specific remit informs role emphasis. Titles and level equivalences vary; compare with the actual JD. |
| Monzo: [Engineering-manager expectations](https://monzo.com/blog/expectations-for-an-engineering-manager-at-monzo) | Team growth, coaching, execution and partnership provide concrete management dimensions. These are one employer's expectations. |
| McKinsey: [Recruiter guidance on resumes](https://www.mckinsey.com/careers/life-at-mckinsey/our-culture-and-communities/careers-blog/amy-r) | Explain the candidate's contribution without claiming the whole team's work. Consulting guidance does not imply every role needs a sales pitch. |

The role/voice matrix synthesizes these sources with safeguards for factual scope and attribution. It has not been tested as a callback-maximizing formula. Photo, personal details, length and section order depend on recipient instructions, relevant evidence and user preferences; language alone cannot resolve them.

## Export implementation

The source review checked these APIs through Context7 on the research-baseline date; recheck current documentation when using or debugging export tooling:

- [WeasyPrint CLI](https://doc.courtbouillon.org/weasyprint/stable/api_reference.html) and [first steps](https://doc.courtbouillon.org/weasyprint/stable/first_steps.html): actual HTML-to-PDF export; environment-specific library lookup only when needed.
- [python-docx quickstart](https://python-docx.readthedocs.io/en/latest/user/quickstart.html), [text](https://python-docx.readthedocs.io/en/latest/user/text.html) and [sections](https://python-docx.readthedocs.io/en/latest/user/sections.html): native paragraphs, headings, font and page controls for real DOCX output.

Local extraction and rendering demonstrate properties of the tested files. They do not certify a proprietary ATS or guarantee correct portal autofill.

---
name: frappe-lms
description: Frappe LMS customization guidance for courses, batches, lessons, quizzes, assessments, enrollment, progress, certificates, portals, and learning workflows. Use when work touches Frappe LMS or education/training flows.
---

Act as a Frappe LMS specialist.

Start by identifying:
- learner, instructor, evaluator, and administrator roles
- course, batch, lesson, quiz, assignment, assessment, and certificate lifecycle
- enrollment, progress tracking, grading, completion, and notification requirements
- whether the change is configuration, metadata, portal UX, reports, or code

Prefer standard LMS surfaces first:
- course/batch configuration, custom fields, workflows, web forms, notifications, reports, dashboards, and certificate templates
- portal and website customization before building a separate app

When code is required:
- preserve enrollment and permission checks for learners and instructors
- keep progress, grading, certificate issuance, and content publishing concerns separate
- avoid storing assessment answers or private learner data in weakly protected custom fields

Design learning UX around next action: continue learning, pending assessment, instructor feedback, progress, deadline, and certificate state should be obvious.

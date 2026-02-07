# Feature 13: Teacher Dashboard

## Overview

The Teacher Dashboard is the command center for educators using EduAGI. From this single interface, teachers manage their classes, upload and organize curriculum content, create and assign assessments, monitor individual student progress, receive AI-powered insights, and communicate with students and parents. It is designed to reduce administrative burden while giving teachers the tools to be more effective -- not to replace teacher judgment, but to augment it with data and AI assistance.

**Priority:** Critical (P0)
**Status:** Design Phase
**Dependencies:** Document Processing (F11), Analytics Dashboard (F12), Assessment Engine (F8), Student Memory (F5), Learning Path (F14), RAG System (F6)
**Stakeholders:** Teachers, Curriculum Coordinators, School Administrators

---

## Teacher Perspective

Ms. Rodriguez starts her day by opening the EduAGI Teacher Dashboard. She sees:

1. **Morning briefing**: "3 students are at-risk this week. Quiz 7 results are in (class avg: 76%). 5 new documents finished processing overnight."
2. She clicks into her AP Biology class and scans the student progress table. She sorts by "risk level" and sees Marcus Chen flagged. She clicks his name, reads the AI insight ("engagement dropped 35%, accuracy on Kinematics declining"), and sends him a quick encouraging message through the platform.
3. She navigates to Content Management, sees her uploaded textbook chapters are processed and tagged. She adjusts one tag from "General Biology" to "AP Biology" and publishes the content.
4. She opens Assessment Builder, creates a quick 10-question review quiz on Kinematics (the class's weakest topic), uses the AI to auto-generate 5 questions from her uploaded content, writes 5 herself, and schedules it for Friday.
5. Before leaving, she checks the AI Teaching Assistant panel: "Suggestion: 68% of students scored below 70% on mitosis questions. Consider a review session. Here is a suggested 30-minute lesson plan." She downloads the lesson plan, tweaks it, and adds it to her calendar.

Total time: 12 minutes. Without EduAGI, these tasks would take over an hour.

---

## Dashboard Layout

```
TEACHER DASHBOARD - MAIN LAYOUT
=================================

+------------------------------------------------------------------+
|  EduAGI Teacher Dashboard       Ms. Rodriguez       [Notifications]|
+------------------------------------------------------------------+
|          |                                                         |
| SIDEBAR  |  MAIN CONTENT AREA                                    |
|          |                                                         |
| [Home]   |  +--------------------------------------------------+ |
|          |  |  MORNING BRIEFING / TODAY'S OVERVIEW              | |
| [Classes]|  |                                                    | |
|  > AP Bio|  |  At-risk: 3 | New results: Quiz 7 | Processed: 5 | |
|  > Bio101|  |  Upcoming: Quiz 8 (Fri) | Unread messages: 2     | |
|  > Lab   |  +--------------------------------------------------+ |
|          |                                                         |
| [Content]|  +------------------------+-------------------------+  |
|          |  | CLASS QUICK STATS      | AT-RISK STUDENTS        |  |
| [Assess- |  |                        |                         |  |
|  ments]  |  | Students: 32           | Marcus Chen [!]         |  |
|          |  | Avg Mastery: 74%       | Jordan Williams [!]     |  |
| [Students|  | Active Today: 28       | Dana Park [!]           |  |
|  List]   |  | Engagement: 82%        |                         |  |
|          |  +------------------------+-------------------------+  |
| [Messages|                                                         |
|  /Comms] |  +--------------------------------------------------+ |
|          |  | RECENT ACTIVITY FEED                               | |
| [AI      |  |                                                    | |
|  Asst.]  |  | 10:23 - Sarah Kim completed Quiz 7 (92%)          | |
|          |  | 10:15 - Alex Torres asked AI about photosynthesis  | |
| [Reports]|  | 09:45 - Document "Ch8_Genetics.pdf" processed      | |
|          |  | 09:30 - Marcus Chen started a study session         | |
| [Settings|  |                                                    | |
|  ]       |  +--------------------------------------------------+ |
|          |                                                         |
+------------------------------------------------------------------+
```

---

## Class Management

### Create a Class

```
CLASS CREATION FLOW
====================

  +-------------------+     +-------------------+     +------------------+
  | Teacher clicks    |---->| Class Setup Form  |---->| Invite Students  |
  | "New Class"       |     |                   |     |                  |
  +-------------------+     | - Class name      |     | - Share join     |
                            | - Subject         |     |   code           |
                            | - Grade level     |     | - Upload CSV     |
                            | - School year     |     |   of student     |
                            | - Schedule        |     |   emails         |
                            | - Description     |     | - Link to LMS    |
                            +-------------------+     |   (auto-import)  |
                                                      +--------+---------+
                                                               |
                                                               v
                                                      +------------------+
                                                      | Class Active     |
                                                      | - Students join  |
                                                      | - Content linked |
                                                      | - Assessments    |
                                                      |   assigned       |
                                                      +------------------+
```

### Class Configuration

| Setting | Options | Default |
|---------|---------|---------|
| Class Name | Free text | Required |
| Subject | Dropdown (auto-populated from school config) | Required |
| Grade Level | K-12, College, Adult | Required |
| Curriculum Standard | Common Core, AP, IB, State-specific, Custom | None |
| Join Method | Join code, Email invitation, LMS sync | Join code |
| AI Difficulty | Auto-adjust, Fixed (Easy/Medium/Hard), Teacher-controlled | Auto-adjust |
| Leaderboard | Enabled (opt-in), Disabled | Disabled |
| Parent Access | Enabled, Disabled | Enabled |
| Max Students | 10-200 | 40 |

### Student Enrollment

- **Join code**: 6-character alphanumeric code, expires after set period, teacher can regenerate
- **Email invitation**: Teacher enters email list, students receive invite with account creation link
- **CSV import**: Upload CSV with columns: first_name, last_name, email, student_id
- **LMS sync**: Connect to Google Classroom, Canvas, Schoology, or Clever for automatic roster sync
- **Manual add**: Teacher searches for existing platform users and adds to class

### Class Archive and Handoff

- **Archive**: At end of term, teacher archives the class. Student data is retained but class is no longer active. Archived classes are read-only.
- **Duplicate**: Teacher can duplicate a class to create next semester's version (same content, settings, assessments -- but no students)
- **Transfer**: Teacher can transfer class ownership to another teacher (substitute teacher mode, see sub-features)
- **Co-teaching**: Multiple teachers can share a class with configurable permissions

---

## Student Monitoring

### Student List View

```
STUDENT LIST VIEW
==================

+------------------------------------------------------------------+
|  AP Biology - Period 3               [Sort By v]  [Filter v]     |
+------------------------------------------------------------------+
|                                                                    |
|  Search: [________________________]                               |
|                                                                    |
|  +------+-------------+-------+----------+-------+------+------+ |
|  |      | Name        |Mastery|Engagement| Trend | Risk |Action| |
|  +------+-------------+-------+----------+-------+------+------+ |
|  | [Av] | Sarah Kim   | 92%   | 95%      |  UP   |  --  | ...  | |
|  | [Av] | Alex Torres | 85%   | 88%      |  UP   |  --  | ...  | |
|  | [Av] | Maria Garcia| 78%   | 75%      | FLAT  |  --  | ...  | |
|  | [Av] | Priya Patel | 75%   | 80%      |  UP   |  --  | ...  | |
|  | ...  | ...         | ...   | ...      |  ...  | ...  | ...  | |
|  | [Av] | Marcus Chen | 61%   | 45%      | DOWN  | [!]  | ...  | |
|  | [Av] | Jordan Will.| 58%   | 12%      | DOWN  | [!!] | ...  | |
|  +------+-------------+-------+----------+-------+------+------+ |
|                                                                    |
|  Showing 32 students | [Select All] [Bulk Actions v]             |
|                                                                    |
+------------------------------------------------------------------+
```

- **Sort options**: Name, Mastery (asc/desc), Engagement, Risk level, Last active
- **Filter options**: Risk level, Mastery range, Engagement range, Last active (within X days), Tag
- **Bulk select**: Select multiple students for bulk actions

### Individual Student Monitoring

When a teacher clicks on a student, they see a comprehensive profile:

```
INDIVIDUAL STUDENT PROFILE (Teacher View)
===========================================

+------------------------------------------------------------------+
|  Marcus Chen            AP Biology - Period 3    [Back to Class]  |
+------------------------------------------------------------------+
|                                                                    |
|  +------------------+  +---------------------------------------+ |
|  | PHOTO / AVATAR   |  | QUICK STATS                           | |
|  |                  |  |                                       | |
|  |   [M.C.]        |  | Overall Mastery: 61%  (class avg: 74%)| |
|  |                  |  | Engagement: 45%  (class avg: 82%)     | |
|  |                  |  | Risk Level: HIGH                       | |
|  |                  |  | Last Active: 3 days ago                | |
|  |                  |  | Sessions (30d): 23  (class avg: 31)    | |
|  |                  |  | Avg Duration: 18 min (class avg: 28m)  | |
|  +------------------+  +---------------------------------------+ |
|                                                                    |
+------------------------------------------------------------------+
|                                                                    |
|  [Progress]  [Sessions]  [Assessments]  [Messages]  [Notes]      |
|                                                                    |
+------------------------------------------------------------------+
|                                                                    |
|  PROGRESS TAB (default)                                           |
|                                                                    |
|  Topic Mastery                    Engagement Timeline             |
|  +---------------------+         +------------------------+      |
|  | (Radar chart with   |         | (Calendar heatmap)     |      |
|  |  class avg overlay) |         |                        |      |
|  +---------------------+         +------------------------+      |
|                                                                    |
|  AI INSIGHTS                                                      |
|  +----------------------------------------------------------+    |
|  | "Marcus was performing well in January but has shown a    |    |
|  |  declining pattern since Feb 1. Key observations:         |    |
|  |  - Session frequency dropped from 5/week to 2/week       |    |
|  |  - Kinematics accuracy: 72% -> 45%                       |    |
|  |  - Sessions shortened from 35min to 12min avg            |    |
|  |                                                            |    |
|  |  Suggested interventions:                                  |    |
|  |  1. Personal check-in (possible external factors)         |    |
|  |  2. Assign shorter, targeted practice sets                |    |
|  |  3. Temporarily reduce AI difficulty to rebuild confidence|    |
|  |  4. Pair with study partner (Sarah Kim has similar topics)|    |
|  +----------------------------------------------------------+    |
|                                                                    |
+------------------------------------------------------------------+
|                                                                    |
|  TEACHER ACTIONS                                                  |
|                                                                    |
|  [Send Message] [Assign Custom Work] [Adjust AI Settings]        |
|  [Add Private Note] [Contact Parent] [Generate Report]            |
|                                                                    |
+------------------------------------------------------------------+
```

### At-Risk Alert System

```
AT-RISK DETECTION AND ALERT FLOW
===================================

  Student Activity Data
        |
        v
  +------------------+
  | Risk Score       |
  | Computation      |
  | (runs every      |
  |  6 hours)        |
  +--------+---------+
           |
           v
  +------------------+     NO CHANGE     +------------------+
  | Risk threshold   |------------------>| No action        |
  | crossed?         |                   +------------------+
  +--------+---------+
           | YES
           v
  +------------------+
  | Generate alert   |
  | with AI insight  |
  | and suggestions  |
  +--------+---------+
           |
           +---> In-app notification (badge on sidebar)
           |
           +---> Email to teacher (if enabled)
           |
           +---> Dashboard "At-Risk" panel updated
           |
           +---> Weekly digest (batched alerts)
```

**Alert Severity Levels:**

| Level | Criteria | Notification |
|-------|----------|-------------|
| LOW | Risk score 0.3-0.5 | Dashboard indicator only |
| MEDIUM | Risk score 0.5-0.7 | Dashboard + weekly email digest |
| HIGH | Risk score > 0.7 | Dashboard + immediate email + in-app notification |
| CRITICAL | Risk score > 0.9 or 7+ days inactive | All channels + school admin notified |

**Intervention Suggestions (AI-Generated):**
- "Send a brief encouraging message"
- "Assign a shorter, easier practice set to rebuild confidence"
- "Schedule a 1:1 check-in"
- "Adjust AI difficulty settings for this student"
- "Suggest a study partner based on complementary strengths"
- "Contact parent/guardian"
- "Refer to school counselor" (for CRITICAL level, with appropriate sensitivity)

---

## Content Management

### Content Library

```
CONTENT MANAGEMENT INTERFACE
==============================

+------------------------------------------------------------------+
|  Content Library          [Upload New] [Import from Drive]       |
+------------------------------------------------------------------+
|                                                                    |
|  [Search content...        ]  [Subject v] [Grade v] [Status v]  |
|                                                                    |
|  +------+-------------------+--------+--------+--------+------+ |
|  |      | Title             | Format | Tags   | Status | Score| |
|  +------+-------------------+--------+--------+--------+------+ |
|  | [  ] | Ch7_Mitosis.pdf   | PDF    | AP Bio | Indexed| 4.2  | |
|  |      |                   |        | Cell   |        |      | |
|  |      |                   |        | Bio    |        |      | |
|  +------+-------------------+--------+--------+--------+------+ |
|  | [  ] | Genetics_Slides   | PPTX   | AP Bio | Review | 3.8  | |
|  |      |                   |        | Genet- |        |      | |
|  |      |                   |        | ics    |        |      | |
|  +------+-------------------+--------+--------+--------+------+ |
|  | [  ] | Ecology_Video     | YT URL | Bio101 | Proc.. | --   | |
|  |      |                   |        | Ecolo- |        |      | |
|  |      |                   |        | gy     |        |      | |
|  +------+-------------------+--------+--------+--------+------+ |
|  | [  ] | Scanned_Handout   | PDF    | AP Bio | Needs  | 2.1  | |
|  |      |                   | (scan) | Mitosis| Review |      | |
|  +------+-------------------+--------+--------+--------+------+ |
|                                                                    |
|  [Select All]  [Bulk Tag]  [Bulk Assign to Class]  [Delete]     |
|                                                                    |
+------------------------------------------------------------------+
```

**Content States:**

| Status | Meaning | Teacher Action |
|--------|---------|---------------|
| Queued | Upload received, waiting for processing | Wait |
| Processing | Being extracted, chunked, embedded | Can cancel |
| Needs Review | OCR confidence low or moderation flag | Review and approve/edit |
| Ready | Processing complete, not yet published | Publish to class |
| Indexed | Published and available to RAG/students | Active content |
| Archived | Removed from active use, still stored | Can restore |
| Failed | Processing error | Retry or contact support |

**Content Actions:**
- **Preview**: View extracted text side-by-side with original document
- **Edit Tags**: Modify auto-detected subject, grade, topic tags
- **Edit Text**: Correct OCR errors or extraction issues
- **Assign to Class**: Make content available to specific classes
- **Version History**: View previous versions of the same content
- **Quality Score**: View detailed quality breakdown
- **Delete**: Remove content from the system (with confirmation)
- **Download Original**: Download the original uploaded file

### Content Organization

- **Folder-like structure**: Teachers can organize content into custom folders/collections
- **Smart collections**: Auto-generated collections based on tags (e.g., "All Mitosis content")
- **Search**: Full-text search across content titles, extracted text, and tags
- **Filter**: By format, status, quality score, date uploaded, class assignment
- **Sort**: By date, name, quality score, usage frequency

---

## Assessment Management

### Assessment Builder

```
ASSESSMENT BUILDER INTERFACE
==============================

+------------------------------------------------------------------+
|  Create New Assessment                                            |
+------------------------------------------------------------------+
|                                                                    |
|  Title: [Kinematics Review Quiz              ]                    |
|  Type:  [Quiz v]  (Quiz / Test / Homework / Practice)            |
|  Class: [AP Biology - Period 3 v]                                |
|                                                                    |
|  Settings:                                                        |
|  Time Limit:     [15] minutes  [  ] No time limit                |
|  Attempts:       [1 v]  (1 / 2 / 3 / Unlimited)                 |
|  Due Date:       [Feb 14, 2026]  [11:59 PM v]                   |
|  Randomize:      [x] Question order  [x] Answer order            |
|  Show Answers:   [After due date v]                              |
|  Weight:         [10] % of final grade                           |
|                                                                    |
+------------------------------------------------------------------+
|                                                                    |
|  QUESTIONS                                      [Add Question v] |
|                                                                    |
|  +----------------------------------------------------------+    |
|  | Q1. Multiple Choice                          [Edit] [X]  |    |
|  | What is the unit of force in the SI system?               |    |
|  | A. Joule  B. Newton (correct)  C. Watt  D. Pascal        |    |
|  | Points: 2  |  Tags: Kinematics, Units                    |    |
|  +----------------------------------------------------------+    |
|  | Q2. Short Answer                              [Edit] [X]  |    |
|  | Explain Newton's second law in your own words.            |    |
|  | Rubric: Mentions force, mass, acceleration (1pt each)     |    |
|  | Points: 3  |  Tags: Newton's Laws                        |    |
|  +----------------------------------------------------------+    |
|  | Q3-Q5: AI-Generated from "Ch3_Kinematics.pdf"            |    |
|  | [Review & Edit AI Questions]                              |    |
|  +----------------------------------------------------------+    |
|                                                                    |
|  Total: 10 questions | 25 points                                 |
|                                                                    |
|  [AI: Generate Questions]  [Import from Bank]  [Preview]         |
|  [Save Draft]  [Assign to Class]                                  |
|                                                                    |
+------------------------------------------------------------------+
```

### Question Types Supported

| Type | Description | AI Gradable? |
|------|------------|-------------|
| Multiple Choice | Single correct answer from 2-6 options | Yes (automatic) |
| Multiple Select | Multiple correct answers from options | Yes (automatic) |
| True/False | Binary choice | Yes (automatic) |
| Short Answer | 1-3 sentence text response | Yes (AI rubric evaluation) |
| Long Answer / Essay | Paragraph+ text response | Yes (AI rubric evaluation with teacher review option) |
| Fill in the Blank | Complete a sentence with missing words | Yes (automatic, with synonym tolerance) |
| Matching | Match items from two columns | Yes (automatic) |
| Ordering | Arrange items in correct sequence | Yes (automatic) |
| Numeric | Provide a numerical answer (with tolerance range) | Yes (automatic) |
| File Upload | Student uploads a file (diagram, lab report) | No (teacher graded) |

### AI Question Generation

```
AI QUESTION GENERATION FLOW
==============================

  +-------------------+     +--------------------+     +------------------+
  | Teacher selects   |---->| AI generates       |---->| Teacher reviews  |
  | source content    |     | questions based    |     | each question    |
  | (uploaded docs)   |     | on content &       |     |                  |
  |                   |     | parameters         |     | - Accept as-is   |
  | Parameters:       |     |                    |     | - Edit & accept  |
  | - # of questions  |     | - Varies question  |     | - Reject         |
  | - Difficulty      |     |   types            |     | - Regenerate     |
  | - Topics to cover |     | - Includes         |     |                  |
  | - Question types  |     |   distractors      |     +------------------+
  | - Bloom's level   |     | - Maps to rubric   |
  +-------------------+     +--------------------+
```

- Teacher specifies: number of questions, difficulty level, topic focus, question type mix, Bloom's taxonomy level (remember, understand, apply, analyze, evaluate, create)
- AI generates from uploaded curriculum content (not generic knowledge)
- Each generated question includes: correct answer, explanation, difficulty rating, topic tags, estimated time to answer
- Teacher must review before publishing (no fully automated assessment creation)

### Assessment Assignment and Results

```
ASSESSMENT LIFECYCLE
=====================

  +----------+     +-----------+     +----------+     +------------+
  | DRAFT    |---->| ASSIGNED  |---->| ACTIVE   |---->| CLOSED     |
  |          |     |           |     |          |     |            |
  | Teacher  |     | Visible   |     | Students |     | Past due   |
  | building |     | to class, |     | can      |     | date or    |
  |          |     | not yet   |     | attempt  |     | all done   |
  |          |     | startable |     |          |     |            |
  +----------+     +-----------+     +----------+     +-----+------+
                                                            |
                                                            v
                                                     +------------+
                                                     | GRADED     |
                                                     |            |
                                                     | AI grades  |
                                                     | auto parts.|
                                                     | Teacher    |
                                                     | reviews    |
                                                     | subjective |
                                                     | parts.     |
                                                     +-----+------+
                                                           |
                                                           v
                                                     +------------+
                                                     | RELEASED   |
                                                     |            |
                                                     | Students   |
                                                     | can see    |
                                                     | scores &   |
                                                     | feedback   |
                                                     +------------+
```

**Results View for Teacher:**
- Summary: average score, score distribution histogram, completion rate
- Per-question analysis: which questions had lowest accuracy (indicates class-wide misunderstanding)
- Individual student results with option to override grades
- Export: CSV of all scores, PDF of individual student reports
- AI insight: "Question 4 (on mitotic spindle formation) had only 23% accuracy. This suggests the class needs a review of this concept."

### Grade Override

- Teacher can override any AI-graded answer
- Override includes: new score and teacher comment explaining the override
- Override is logged in audit trail
- Student sees both original AI score and teacher override with comment
- Bulk override: teacher can adjust all scores for a question (e.g., "give everyone full credit on Q4 due to ambiguous wording")

---

## Communication

### Messaging System

```
MESSAGING INTERFACE
====================

+------------------------------------------------------------------+
|  Messages                        [New Message] [Bulk Message]    |
+------------------------------------------------------------------+
|                           |                                        |
|  CONVERSATIONS            |  CONVERSATION VIEW                    |
|                           |                                        |
|  Marcus Chen (2 unread)   |  Marcus Chen - AP Biology             |
|  Sarah Kim                |                                        |
|  -- Class Announcements -- |  Ms. R: Hi Marcus, I noticed you     |
|  AP Bio - Period 3        |  haven't been on in a few days.       |
|  Bio 101                  |  Everything okay?                      |
|                           |                                        |
|                           |  Marcus: Yeah, I've been busy with     |
|                           |  basketball tryouts. I'll catch up     |
|                           |  this weekend.                         |
|                           |                                        |
|                           |  Ms. R: No worries! I've assigned     |
|                           |  a short review quiz on Kinematics -  |
|                           |  it should only take 15 minutes.      |
|                           |  Let me know if you need help.        |
|                           |                                        |
|                           |  [Type a message...          ] [Send] |
|                           |                                        |
+---------------------------+----------------------------------------+
```

**Message Types:**
- **Direct message**: Teacher to individual student
- **Class announcement**: Teacher to entire class
- **AI feedback annotation**: Teacher adds a comment to an AI tutoring response ("The AI's explanation is correct, but I would add...")
- **Parent message**: Teacher to parent (separate from student messages)
- **Assessment feedback**: Contextual message attached to a specific assessment result

**Features:**
- Rich text formatting (bold, italic, lists, links)
- File attachments (images, PDFs, up to 10MB)
- Read receipts (teacher can see who read class announcements)
- Scheduled messages (compose now, send at a specific time)
- Message templates (save frequently used messages)
- Translation support (auto-translate for ESL students/parents)

---

## AI Teaching Assistant

### Capabilities

```
AI TEACHING ASSISTANT PANEL
=============================

+------------------------------------------------------------------+
|  AI Teaching Assistant                                            |
+------------------------------------------------------------------+
|                                                                    |
|  INSIGHTS & SUGGESTIONS                                           |
|                                                                    |
|  +----------------------------------------------------------+    |
|  | CLASS-WIDE INSIGHT                                        |    |
|  |                                                            |    |
|  | "68% of students scored below 70% on mitosis questions    |    |
|  |  in the last 2 weeks. The most common misconception is    |    |
|  |  confusing prophase and prometaphase. Consider a targeted |    |
|  |  review session."                                          |    |
|  |                                                            |    |
|  | [Generate Review Material] [Create Quiz on This Topic]    |    |
|  +----------------------------------------------------------+    |
|                                                                    |
|  +----------------------------------------------------------+    |
|  | LESSON PLAN SUGGESTION                                    |    |
|  |                                                            |    |
|  | Based on current class progress and upcoming curriculum:  |    |
|  |                                                            |    |
|  | Suggested next topic: Meiosis                             |    |
|  | Prerequisite check: 78% of class has mastered Mitosis     |    |
|  |   (above 70% threshold)                                   |    |
|  | Suggested lesson: 30 min lecture + 15 min practice         |    |
|  |                                                            |    |
|  | [View Full Lesson Plan] [Customize] [Dismiss]             |    |
|  +----------------------------------------------------------+    |
|                                                                    |
|  ASK THE AI ASSISTANT                                             |
|  +----------------------------------------------------------+    |
|  | [How can I help my students understand kinematics better?]|    |
|  |                                                [Ask -->]  |    |
|  +----------------------------------------------------------+    |
|                                                                    |
+------------------------------------------------------------------+
```

**AI Assistant Functions:**

| Function | Description | Input | Output |
|----------|------------|-------|--------|
| Lesson Plan Generator | Create a lesson plan for a topic | Topic, duration, class level | Structured lesson plan with activities |
| Weak Topic Identifier | Find topics where the class struggles | Class performance data | Ranked list of weak topics with evidence |
| Review Material Generator | Create review materials for weak topics | Topic, difficulty, format preference | Practice problems, summary notes, flashcards |
| Student Grouping | Suggest study groups based on complementary strengths | Class roster + mastery data | Suggested groups with rationale |
| Differentiation Advisor | Suggest how to differentiate instruction | Class mastery distribution | Tiered activity suggestions |
| Question Bank Curator | Suggest questions from the bank for assessments | Topic, difficulty, Bloom's level | Curated question set |
| Progress Narrator | Generate plain-English progress summary for a student | Student data | Narrative report suitable for parent conferences |
| Curriculum Pacer | Suggest pacing adjustments based on actual progress vs. plan | Curriculum plan + actual progress | Adjusted timeline |

### Lesson Plan Format

```
AI-GENERATED LESSON PLAN
==========================

Topic: Meiosis - Introduction
Duration: 45 minutes
Class: AP Biology - Period 3
Prerequisites: Mitosis (78% class mastery - READY)

OBJECTIVES:
- Students will be able to compare and contrast mitosis and meiosis
- Students will identify the stages of meiosis I
- Students will explain the significance of crossing over

MATERIALS:
- Uploaded content: "Ch8_Meiosis.pdf" (sections 8.1-8.3)
- AI-generated diagram comparison sheet
- Practice quiz (5 questions, auto-generated)

LESSON STRUCTURE:
1. Warm-up (5 min): Quick review quiz on mitosis (3 questions)
2. Introduction (10 min): Compare mitosis vs. meiosis using side-by-side diagram
3. Direct Instruction (15 min): Walk through meiosis I stages
4. Guided Practice (10 min): Students label meiosis diagram with AI tutor assistance
5. Exit Ticket (5 min): Short AI-graded assessment on meiosis I stages

DIFFERENTIATION:
- Advanced: Include meiosis II and nondisjunction
- On-level: Focus on meiosis I stages only
- Struggling: Provide pre-filled diagram, focus on comparing to mitosis

[Download as PDF]  [Add to Calendar]  [Edit]  [Assign Materials]
```

---

## Sub-Features

### Bulk Actions

- **Bulk message**: Send the same message to selected students
- **Bulk assign**: Assign an assessment or resource to multiple classes
- **Bulk tag**: Apply tags to multiple content items
- **Bulk grade override**: Adjust grades for multiple students on an assessment
- **Bulk export**: Export data for selected students or classes
- **Bulk archive**: Archive multiple content items or assessments

### CSV Export of Grades

- Export formats: CSV, XLSX, PDF
- Configurable columns: student name, student ID, per-assessment scores, overall grade, mastery per topic
- Compatible with: school SIS systems, Google Sheets, Excel
- Scheduled exports: automatic weekly/monthly export to teacher's email or connected Drive

### Printable Reports

- **Student progress report**: One page per student, suitable for parent-teacher conferences. Includes mastery radar chart, engagement summary, AI insights, teacher notes.
- **Class summary report**: One page, class-wide metrics, topic coverage, at-risk summary.
- **Assessment report**: Score distribution, per-question analysis, class performance summary.
- **Formatted for printing**: Clean layout, school branding, appropriate fonts and spacing.

### Calendar Integration

```
CALENDAR INTEGRATION
=====================

  +-------------------+     +------------------+
  | EduAGI Assessment |     | External Calendar|
  | Scheduler         |<--->| (Google, Outlook,|
  |                   |     |  Apple)          |
  | - Due dates       |     |                  |
  | - Scheduled       |     | Teacher sees     |
  | - Class sessions  |     | all education    |
  |   meetings        |     | events in one    |
  |                   |     | place            |
  +-------------------+     +------------------+
```

- Sync assessment due dates to teacher's calendar (Google Calendar, Outlook, Apple Calendar via CalDAV/iCal)
- Sync class meeting times
- Visual timeline of upcoming assessments and milestones within the dashboard
- Conflict detection: warn if two assessments are due the same day for the same class

### Assignment Scheduling

- Schedule assessments to become available at a future date/time
- Schedule content to be published at a specific time
- Recurring assignments: weekly practice quizzes, daily warm-up exercises
- Conditional scheduling: "Unlock Quiz 8 when Quiz 7 completion rate reaches 80%"

### Rubric Builder

```
RUBRIC BUILDER
===============

+------------------------------------------------------------------+
|  Rubric: Essay on Photosynthesis                                  |
+------------------------------------------------------------------+
|                                                                    |
|  Criteria      | Excellent(4) | Good(3)  | Fair(2)  | Poor(1)    |
|  ---------------------------------------------------------------- |
|  Content       | All key      | Most key | Some key | Missing    |
|  Accuracy      | concepts     | concepts | concepts | key        |
|                | correct      | correct  | correct  | concepts   |
|  ---------------------------------------------------------------- |
|  Scientific    | Precise      | Mostly   | Some     | Inaccurate |
|  Vocabulary    | terminology  | accurate | errors   | terminology|
|  ---------------------------------------------------------------- |
|  Organization  | Clear,       | Logical  | Some     | No clear   |
|                | logical flow | sequence | structure| structure  |
|  ---------------------------------------------------------------- |
|                                                                    |
|  [Add Criteria]  [Import Template]  [Save as Template]           |
|  [Attach to Assessment]  [Share with AI Grader]                   |
|                                                                    |
+------------------------------------------------------------------+
```

- Define criteria with performance levels and point values
- Save rubrics as templates for reuse
- Share rubric with AI grader so AI evaluates against the same criteria
- Student can view rubric before submitting (transparency)
- AI uses rubric to provide structured feedback per criterion

### Question Bank Management

- Teachers build a personal question bank organized by topic and difficulty
- AI-generated questions can be saved to the bank
- Import questions from shared school-wide bank
- Export questions in standard formats (QTI for LMS compatibility)
- Duplicate detection: warn when adding a question similar to one already in the bank
- Usage tracking: see how many times each question has been used and its discrimination index

### Class Comparison Analytics

- Compare two or more classes on the same metrics (mastery, engagement, assessment scores)
- Side-by-side visualization
- Identify: which class is furthest behind, which teaching approach works better (if same content taught differently)
- Use case: teacher with multiple sections of the same course can compare effectiveness

### Substitute Teacher Mode

```
SUBSTITUTE TEACHER HANDOFF
============================

  +-------------------+     +------------------+
  | Primary Teacher   |---->| Handoff Package  |
  | clicks "Prepare   |     |                  |
  | Sub Handoff"      |     | Includes:        |
  +-------------------+     | - Class roster   |
                            | - Current topic  |
                            | - Lesson plans   |
                            | - At-risk notes  |
                            | - Scheduled      |
                            |   assessments    |
                            | - Special needs  |
                            |   notes          |
                            +--------+---------+
                                     |
                                     v
                            +------------------+
                            | Substitute gets  |
                            | temporary access |
                            | (read-only or    |
                            |  limited write)  |
                            +------------------+
```

- Teacher generates a "handoff package" with everything a substitute needs
- Configurable access level: read-only (just view), limited (can send messages, review assignments), full (temporary full access)
- Time-limited: access expires after the set date
- Audit log: all substitute actions are logged and visible to the primary teacher

### Parent Communication Portal

- Separate from student messaging
- Teacher can share: progress reports, assessment results, general updates
- Parent can: view shared reports, send messages to teacher, set notification preferences
- Translation: auto-translate messages for non-English-speaking parents
- Privacy: teacher controls exactly what information is shared with parents
- Bulk parent updates: "Your child's class just completed the Genetics unit. Here is how they did: [individualized insert]"

---

## Role-Based API Access Design

### Role Hierarchy

```
ROLE HIERARCHY
===============

  Platform Admin
       |
       v
  School Admin
       |
       v
  Teacher -------> Co-Teacher (shared class access)
       |
       +---------> Substitute Teacher (temporary, limited)
       |
       v
  Parent (view-only, scoped to their child)
       |
       v
  Student (own data only)
```

### API Permission Matrix

```
PERMISSION MATRIX
==================

Endpoint                        Teacher   Co-Teacher  Substitute  Parent  Student
-------------------------------  --------  ----------  ----------  ------  -------
GET /classes                    Own       Shared      Temp        --      Enrolled
POST /classes                   YES       NO          NO          --      NO
PUT /classes/:id                Own       NO          NO          --      NO
DELETE /classes/:id             Own       NO          NO          --      NO

GET /students/:id               Own class  Shared cls  Temp class  Own child Own
PUT /students/:id/settings      Own class  Shared cls  NO          NO       NO

POST /content/upload            YES       YES         NO          --      NO
GET /content                    Own       Shared      Temp(view)  --      NO
PUT /content/:id                Own       Shared      NO          --      NO
DELETE /content/:id             Own       NO          NO          --      NO

POST /assessments               YES       YES         NO          --      NO
GET /assessments/:id/results    Own class  Shared cls  Temp class  --      Own
PUT /assessments/:id/grades     Own class  Shared cls  NO          --      NO

POST /messages                  YES       YES         YES(limited) YES    YES
GET /messages                   Own       Shared      Temp        Own     Own

GET /analytics/class            Own class  Shared cls  Temp class  --      --
GET /analytics/student/:id      Own class  Shared cls  Temp class  Own child Own

POST /ai-assistant/query        YES       YES         NO          --      --
GET /ai-assistant/insights      Own class  Shared cls  Temp class  --      --
```

### Authentication and Authorization

- JWT-based authentication with role claims
- API middleware checks: (1) valid token, (2) role permission, (3) resource ownership/scope
- School admin can impersonate teacher (for support purposes), with audit log
- All API calls logged with: user ID, role, endpoint, timestamp, IP address
- Rate limiting per role: teachers get higher limits than students

---

## Data Flow Between Teacher Actions and Student Experience

```
TEACHER ACTIONS -> STUDENT EXPERIENCE
========================================

  TEACHER ACTION                         STUDENT EXPERIENCE
  ==============                         ==================

  Uploads curriculum content    ---->    AI tutor gives answers grounded
  (Document Processing, F11)            in teacher's specific materials

  Creates & assigns assessment  ---->    Student sees new quiz in their
  (Assessment Builder)                   dashboard, receives notification

  Overrides AI grade            ---->    Student sees updated score with
  (Grade Override)                       teacher's comment explaining why

  Sends message                 ---->    Student receives notification,
  (Messaging)                            sees message in their inbox

  Annotates AI feedback         ---->    Student sees teacher's note
  (AI Feedback Annotation)               alongside AI tutor's response

  Adjusts AI difficulty         ---->    AI tutor adjusts question
  (Student Settings)                     difficulty for that student

  Identifies weak topic         ---->    Learning Path (F14) adjusts
  (AI Teaching Assistant)                recommendations for class

  Publishes content to class    ---->    RAG system (F6) now includes
  (Content Management)                   new material in responses

  Sets up class with            ---->    Student's dashboard shows
  curriculum standards                   progress mapped to standards
  (Class Setup)

  Generates progress report     ---->    Parent receives progress
  (Reports)                              report via parent portal
```

---

## Service Considerations

### Admin Panel Frameworks

Since the Teacher Dashboard is a role-specific view within the same application (not a separate admin tool), it should use the same frontend framework as the student-facing app. However, the following patterns are relevant:

| Approach | Pros | Cons |
|----------|------|------|
| **Same React app, role-based routing** | Single codebase, shared components, consistent UX | Larger bundle (teacher components loaded for all), more complex routing |
| **Separate teacher SPA** | Smaller bundles per role, independent deployment, optimized per audience | Code duplication, maintaining two apps, separate build pipelines |
| **Micro-frontend (module federation)** | Best of both: shared shell, independent feature modules, deploy independently | Infrastructure complexity, runtime overhead, debugging harder |

**Recommendation:** Start with **same React app, role-based routing** using code-splitting (React.lazy) to only load teacher components when a teacher is logged in. This minimizes complexity while keeping bundle sizes manageable. If the teacher dashboard grows significantly, migrate to a micro-frontend architecture.

### State Management

- Teacher dashboard has complex state: class data, student lists, content library, assessment builder, messaging
- Recommendation: Use a combination of server state management (React Query / TanStack Query for data fetching and caching) and local state (Zustand or Redux Toolkit for UI state like filters, selections, form state)
- Optimistic updates: when teacher performs an action (send message, assign quiz), update UI immediately and sync with server in background

---

## MCP Servers

| MCP Server | Purpose | How It Helps |
|------------|---------|-------------|
| **Google Drive MCP** | Cloud storage integration | Browse and import content from teacher's Google Drive directly in the dashboard |
| **Google Calendar MCP** | Calendar integration | Sync assessment due dates and class events with teacher's Google Calendar |
| **Slack / Email MCP** | Communication | Send notifications and alerts through external channels |
| **SQLite / PostgreSQL MCP** | Data access | AI Teaching Assistant queries student data directly to generate insights |
| **Memory MCP** | Student memory | Access student learning history for generating personalized insights and recommendations |
| **Fetch MCP** | External resources | AI assistant can fetch curriculum standards, teaching resources from the web |
| **Filesystem MCP** | Report generation | Generate and save PDF reports to local filesystem |

---

## Performance Requirements

| Metric | Target |
|--------|--------|
| Dashboard initial load | < 2 seconds |
| Student list rendering (40 students) | < 500ms |
| Student list rendering (200 students, class) | < 1 second |
| Content upload initiation | < 1 second to show progress |
| Assessment builder save | < 500ms |
| AI question generation (5 questions) | < 15 seconds |
| AI lesson plan generation | < 20 seconds |
| Message send | < 500ms (optimistic UI) |
| Grade override | < 500ms |
| Report generation (PDF) | < 10 seconds |
| Search across content library | < 1 second |
| Concurrent teacher sessions | 1,000+ |

---

## Accessibility Requirements

- WCAG 2.1 AA compliance throughout the dashboard
- Keyboard navigation for all interactive elements
- Screen reader compatible tables, charts, and forms
- High contrast mode
- Reduced motion mode (disable animations)
- Alt text for all data visualizations (auto-generated summaries)
- Font size adjustment
- Mobile-responsive design (teachers should be able to check alerts on phone)

---

## Open Questions

1. Should teachers be able to see AI tutoring session transcripts for their students? This would help understand student struggles but raises privacy concerns.
2. How much AI autonomy should the Teaching Assistant have? Should it be able to automatically adjust difficulty for at-risk students, or always require teacher approval?
3. Should co-teachers have equal permissions or should there be a "primary" and "secondary" teacher role?
4. How do we handle the transition between school years? Should student data carry over to their next teacher?
5. Should the question bank be shareable across the school (with appropriate permissions) or teacher-private only?
6. What is the right balance between AI-generated insights and overwhelming teachers with too much information?
7. Should assessment results feed directly into the school's official gradebook (SIS integration) or remain separate within EduAGI?

# F02: RAG Knowledge Retrieval
# EduAGI - Feature Design Document

**Feature ID:** F02
**Version:** 1.0
**Date:** February 2026
**Author:** AGI Education Team
**Status:** Design Phase
**Priority:** P0 (Critical)
**Dependencies:** ChromaDB, Embedding Model, Document Parsers, LLM (Claude)

---

## Table of Contents

1. [Feature Overview](#1-feature-overview)
2. [Detailed Workflow](#2-detailed-workflow)
3. [Sub-features and Small Touches](#3-sub-features-and-small-touches)
4. [Technical Requirements](#4-technical-requirements)
5. [Services and Alternatives](#5-services-and-alternatives)
6. [Connections and Dependencies](#6-connections-and-dependencies)
7. [Appendix](#7-appendix)

---

## 1. Feature Overview

### 1.1 What Is RAG and Why It Matters for Education

Retrieval-Augmented Generation (RAG) is a technique that grounds Large Language
Model (LLM) responses in real, verified source documents rather than relying
solely on the model's pre-trained knowledge. In an educational context, this
distinction is not merely technical -- it is pedagogically critical.

When a student asks "What caused the French Revolution?", the answer must come
from their actual curriculum materials, textbooks, and teacher-approved content.
A pure LLM might produce a plausible but inaccurate or off-syllabus answer. RAG
ensures the response is anchored in the documents the student is actually
studying from.

```
THE PROBLEM WITHOUT RAG
=======================

  Student Question                LLM (No RAG)
  +-----------------------+       +---------------------------+
  | "What is the          |       | "Mitosis is the process   |
  |  difference between   | ----> |  of cell division where   |
  |  mitosis and meiosis  |       |  DNA replicates..."       |
  |  according to our     |       |                           |
  |  textbook?"           |       | (Generic answer, may not  |
  +-----------------------+       |  match textbook content,  |
                                  |  could contain errors or  |
                                  |  outdated information)    |
                                  +---------------------------+

THE SOLUTION WITH RAG
=====================

  Student Question          Retrieve from              LLM + Context
                            Knowledge Base
  +------------------+     +------------------+     +--------------------+
  | "What is the     |     | Chunk 1: Ch.5    |     | "According to your |
  |  difference      | --> | of Biology 101   | --> |  textbook (Ch.5,   |
  |  between mitosis |     | p.134-136        |     |  p.134), mitosis   |
  |  and meiosis     |     |                  |     |  produces two      |
  |  according to    |     | Chunk 2: Teacher |     |  identical cells   |
  |  our textbook?"  |     | lecture notes    |     |  while meiosis..." |
  +------------------+     | on cell division |     |                    |
                           +------------------+     | [Source: Biology   |
                                                    |  101, p.134-136]   |
                                                    +--------------------+
```

### 1.2 Why RAG Is Critical for EduAGI

| Concern | How RAG Addresses It |
|---------|---------------------|
| **Hallucination prevention** | Responses are generated only from verified source documents, not from parametric memory |
| **Curriculum alignment** | Content retrieval is filtered by subject, grade level, and curriculum standard |
| **Source transparency** | Every claim can be traced back to a specific document, page, and paragraph |
| **Trust building** | Students and teachers can verify the AI is using approved materials |
| **Content freshness** | Knowledge base is updated independently of the LLM's training cutoff |
| **Institutional control** | Schools and teachers control exactly what content the system draws from |

### 1.3 The Student Perspective

From a student's point of view, the RAG system should be invisible. They ask
a question and get an accurate, sourced answer. What they experience:

- Answers that match what their teacher taught and what their textbook says
- Citations they can click to read the original source material
- Honest admissions when the system does not have content on a topic
- Consistent answers that do not contradict their course materials
- The ability to flag answers that seem wrong

### 1.4 Scope of This Feature

```
+-------------------------------------------------------------------+
|                  F02: RAG KNOWLEDGE RETRIEVAL                      |
+-------------------------------------------------------------------+
|                                                                    |
|  IN SCOPE                          OUT OF SCOPE                   |
|  +-----------------------------+   +----------------------------+ |
|  | Document ingestion pipeline |   | LLM fine-tuning            | |
|  | Text extraction & cleaning  |   | Real-time web search       | |
|  | Chunking & embedding        |   | Student-generated content  | |
|  | Vector storage & indexing   |   | Collaborative editing      | |
|  | Query rewriting             |   | Content authoring tools    | |
|  | Semantic search             |   | DRM / copyright management | |
|  | Re-ranking & filtering      |   | Payment / licensing        | |
|  | Context window assembly     |   +----------------------------+ |
|  | Source citation             |                                   |
|  | Confidence scoring          |                                   |
|  | Metadata tagging            |                                   |
|  | Content freshness tracking  |                                   |
|  +-----------------------------+                                   |
+-------------------------------------------------------------------+
```

---

## 2. Detailed Workflow

### 2.1 End-to-End RAG Pipeline Overview

```
+=========================================================================+
|                    COMPLETE RAG PIPELINE                                  |
+=========================================================================+
|                                                                          |
|   PHASE 1: INGESTION (Offline / Background)                             |
|   ==========================================                             |
|                                                                          |
|   [Documents]    [Extract]    [Clean]    [Chunk]    [Embed]    [Store]   |
|   PDF,DOCX  -->  Raw Text --> Cleaned --> Chunks --> Vectors --> ChromaDB|
|   PPTX,YT       + metadata   text        + meta    1536-dim   + index   |
|   Web pages                                                              |
|                                                                          |
|   PHASE 2: RETRIEVAL (Real-time / Per Query)                             |
|   ==========================================                             |
|                                                                          |
|   [Student   [Query     [Semantic  [Re-rank  [Context   [LLM        ]   |
|    Question]  Rewrite]   Search]    Filter]   Assembly]  Generation  ]   |
|   "What..." -> Expand -> k-NN   -> Score  -> Pack    -> Claude      ]   |
|               + refine   top-20    top-5     prompt     + sources    ]   |
|                                                                          |
|   PHASE 3: RESPONSE (Real-time)                                          |
|   =============================                                          |
|                                                                          |
|   [Generate]   [Cite Sources]   [Score Confidence]   [Deliver]          |
|   Answer   --> Add citations --> Calculate        --> To student        |
|   from LLM    [Doc, Page, Ch]   confidence score     with sources      |
|                                                                          |
+=========================================================================+
```

### 2.2 Document Ingestion Pipeline

The ingestion pipeline processes educational materials from multiple formats
into searchable vector embeddings. This runs as a background process triggered
by teacher uploads or scheduled batch jobs.

#### 2.2.1 Supported Document Types

| Format | Parser | Content Extracted |
|--------|--------|-------------------|
| PDF | PyPDF2 / PyMuPDF | Text, page numbers, tables |
| DOCX | python-docx | Text, headings, tables, formatting |
| PPTX | python-pptx | Slide text, speaker notes, slide numbers |
| YouTube | youtube-transcript-api | Timestamped transcripts |
| Web pages | BeautifulSoup + Trafilatura | Main content, stripped of nav/ads |
| Plain text | Built-in | Raw text content |
| Markdown | Built-in | Text with structure preserved |

#### 2.2.2 Ingestion Flow Diagram

```
  +-------------------+
  |   SOURCE DOCUMENT |
  |   (PDF, DOCX,     |
  |    PPTX, YT, Web) |
  +--------+----------+
           |
           v
  +--------+----------+
  |   FORMAT DETECTOR  |    Identify file type by extension
  |   (mime type check)|    and magic bytes
  +--------+----------+
           |
           v
  +--------+----------+
  |   DOCUMENT LOADER  |    Select appropriate parser:
  |                    |    - PyPDF2 for PDF
  |                    |    - python-docx for DOCX
  |                    |    - python-pptx for PPTX
  |                    |    - yt-dlp + whisper for YouTube
  |                    |    - trafilatura for web pages
  +--------+----------+
           |
           v
  +--------+----------+
  |   TEXT EXTRACTION  |    Extract raw text preserving:
  |                    |    - Page/slide numbers
  |                    |    - Headings & structure
  |                    |    - Table data
  |                    |    - Image alt text
  +--------+----------+
           |
           v
  +--------+----------+
  |   TEXT CLEANING    |    Remove:
  |                    |    - Headers/footers repeated per page
  |                    |    - Page numbers in body text
  |                    |    - Excessive whitespace
  |                    |    - Non-content artifacts
  |                    |    Normalize:
  |                    |    - Unicode characters
  |                    |    - Encoding issues
  +--------+----------+
           |
           v
  +--------+----------+
  |   METADATA         |    Attach metadata:
  |   EXTRACTION       |    - Title, author, date
  |                    |    - Subject, grade level
  |                    |    - Curriculum standard tags
  |                    |    - Source file path & hash
  |                    |    - Upload timestamp
  |                    |    - Uploaded by (teacher ID)
  +--------+----------+
           |
           v
  +--------+----------+
  |   DUPLICATE        |    Check content hash against
  |   DETECTION        |    existing documents. If duplicate:
  |                    |    - Skip ingestion
  |                    |    - Or update if newer version
  +--------+----------+
           |
           v
  +--------+----------+
  |   CHUNKING         |    Split text into chunks
  |   ENGINE           |    (see Section 2.4 for strategy)
  +--------+----------+
           |
           v
  +--------+----------+
  |   EMBEDDING        |    Generate vector embeddings
  |   GENERATION       |    for each chunk
  +--------+----------+
           |
           v
  +--------+----------+
  |   VECTOR STORE     |    Store in ChromaDB with
  |   (ChromaDB)       |    metadata and indexes
  +--------+----------+
           |
           v
  +--------+----------+
  |   INGESTION LOG    |    Record: document ID, chunk count,
  |   (PostgreSQL)     |    status, errors, timestamp
  +-------------------+
```

### 2.3 Text Extraction and Cleaning

Text extraction must handle the messy reality of educational documents. A
scanned PDF textbook is very different from a cleanly formatted DOCX lecture
note.

#### Extraction Rules by Format

**PDF Documents:**
- Use PyMuPDF (fitz) as primary extractor for speed and accuracy
- Fall back to PyPDF2 if PyMuPDF fails
- For scanned PDFs, use Tesseract OCR via pytesseract
- Preserve page boundaries as metadata
- Extract table of contents if present for structural context
- Attempt to preserve reading order (column detection for multi-column layouts)

**DOCX Documents:**
- Use python-docx to extract text with heading hierarchy
- Preserve heading levels (H1, H2, H3) as structural markers for chunking
- Extract tables as pipe-delimited text with header row marked
- Extract image alt text and figure captions
- Preserve numbered and bulleted list structure

**PPTX Documents:**
- Extract slide text and speaker notes separately
- Tag each chunk with slide number
- Combine slide title + bullet points + speaker notes as a single unit
- Treat each slide as a natural semantic boundary

**YouTube Transcripts:**
- Use youtube-transcript-api to fetch auto-generated or manual captions
- Group transcript segments into ~60-second windows
- Attach timestamp metadata to each chunk for "jump to" functionality
- Prefer manually uploaded captions over auto-generated ones

**Web Pages:**
- Use trafilatura for main content extraction (strips navigation, ads, sidebars)
- Preserve heading structure
- Extract publication date and author when available
- Store original URL for citation purposes

#### Cleaning Pipeline

```
  Raw Text
     |
     v
  [1. Normalize Unicode]  --> NFC normalization, fix encoding
     |
     v
  [2. Remove Artifacts ]  --> Page numbers in body, repeated headers,
     |                        watermarks, "Page X of Y" patterns
     v
  [3. Fix Whitespace   ]  --> Collapse multiple newlines, normalize
     |                        tabs to spaces, trim lines
     v
  [4. Repair Hyphens   ]  --> Rejoin words broken across lines
     |                        ("photo-\nsynthesis" -> "photosynthesis")
     v
  [5. Normalize Quotes ]  --> Smart quotes to straight quotes,
     |                        curly apostrophes to standard
     v
  [6. Detect Language  ]  --> Tag content language for multi-lingual
     |                        support filtering
     v
  Clean Text + Language Tag
```

### 2.4 Chunking Strategy

Chunking is the most consequential design decision in a RAG system. Chunks
that are too large waste context window space. Chunks that are too small lose
meaning. The goal is chunks that represent a single coherent idea or concept.

#### Strategy: Hierarchical Semantic Chunking

EduAGI uses a three-tier chunking approach rather than a single fixed-size
split.

```
  TIER 1: STRUCTURAL BOUNDARIES (Primary splits)
  ================================================
  Split on natural document structure:
  - Chapter boundaries
  - Section headings (H1, H2)
  - Slide boundaries (PPTX)
  - Major topic shifts

  TIER 2: SEMANTIC BOUNDARIES (Secondary splits)
  ================================================
  Within structural sections, split on:
  - Paragraph boundaries
  - Subsection headings (H3, H4)
  - After complete "thought units" (definition + explanation)
  - Before/after examples or worked problems

  TIER 3: SIZE-BASED FALLBACK (Safety net)
  ================================================
  If a chunk exceeds max size after structural/semantic splits:
  - Split at sentence boundaries
  - Target: 512 tokens per chunk
  - Overlap: 64 tokens (12.5%)
  - Never split mid-sentence
```

#### Chunk Size Configuration

| Parameter | Value | Rationale |
|-----------|-------|-----------|
| Target chunk size | 512 tokens | Balances specificity with context |
| Maximum chunk size | 768 tokens | Hard ceiling to prevent oversized chunks |
| Minimum chunk size | 64 tokens | Discard fragments below this threshold |
| Overlap size | 64 tokens | Preserves context across chunk boundaries |
| Overlap strategy | Sliding window | Repeat last N tokens at start of next chunk |

#### Why 512 Tokens

- Small enough that each chunk typically covers one concept
- Large enough to include a definition plus a brief explanation
- Allows packing 5-8 chunks into a typical context window alongside system prompt and conversation history
- Empirically shown to perform well for educational Q&A tasks
- Matches well with embedding model context windows (most support 512+ tokens)

#### Chunk Metadata

Every chunk carries the following metadata:

```
{
  "chunk_id":            "uuid",
  "document_id":         "uuid of parent document",
  "document_title":      "Biology 101 Textbook",
  "source_file":         "biology_101_ch5.pdf",
  "page_numbers":        [134, 135],
  "slide_number":        null,
  "section_heading":     "5.3 Mitosis vs Meiosis",
  "chapter":             "Chapter 5: Cell Division",
  "chunk_index":         12,
  "total_chunks":        187,
  "subject":             "Biology",
  "grade_level":         "10",
  "curriculum_standard": "NGSS-LS1-4",
  "topic_tags":          ["cell division", "mitosis", "meiosis"],
  "content_type":        "textbook",
  "language":            "en",
  "uploaded_by":         "teacher_uuid",
  "upload_timestamp":    "2026-01-15T10:30:00Z",
  "content_hash":        "sha256:abc123...",
  "freshness_date":      "2025-08-01",
  "token_count":         487
}
```

### 2.5 Embedding Generation

Embeddings convert text chunks into dense vector representations that capture
semantic meaning. Two chunks about the same concept will have similar vectors,
enabling semantic search.

```
  +------------------+     +-------------------+     +------------------+
  |   Text Chunk     |     |   Embedding Model |     |   Vector         |
  |                  |     |                   |     |   (1536-dim)     |
  |  "Mitosis is the | --> | text-embedding-   | --> |  [0.023, -0.041, |
  |   process of     |     | 3-small           |     |   0.187, 0.002,  |
  |   cell division  |     | (OpenAI)          |     |   ..., -0.156]   |
  |   that results   |     |                   |     |                  |
  |   in two         |     +-------------------+     +------------------+
  |   genetically    |
  |   identical      |           Batch processing:
  |   daughter       |           - Up to 2048 chunks per API call
  |   cells..."      |           - Retry with exponential backoff
  +------------------+           - Cache embeddings to avoid re-computation
```

#### Embedding Configuration

| Setting | Value |
|---------|-------|
| Model (primary) | text-embedding-3-small (OpenAI) |
| Dimensions | 1536 |
| Batch size | 512 chunks per API call |
| Rate limiting | 3000 RPM (OpenAI tier) |
| Caching | Store embeddings alongside chunks; recompute only on content change |
| Normalization | L2 normalization applied before storage |

### 2.6 Indexing by Subject, Grade Level, Topic, and Curriculum Standard

ChromaDB supports metadata filtering, which allows narrowing search results
before the vector similarity search runs. This is critical for educational
content where a biology answer should never pull from a history textbook.

#### Collection Design

```
  ChromaDB Instance
  +---------------------------------------------------------------+
  |                                                                |
  |  Collection: "educational_content"                             |
  |  +---------------------------------------------------------+  |
  |  |                                                          |  |
  |  |  Every chunk is stored with metadata that enables        |  |
  |  |  filtering by any combination of:                        |  |
  |  |                                                          |  |
  |  |  subject:              "Biology", "Math", "History"...   |  |
  |  |  grade_level:          "9", "10", "11", "AP"...          |  |
  |  |  curriculum_standard:  "CCSS.MATH.8.EE", "NGSS-LS1"...  |  |
  |  |  content_type:         "textbook", "lecture", "notes"... |  |
  |  |  uploaded_by:          teacher UUID (for prioritization) |  |
  |  |  language:             "en", "es", "fr"...               |  |
  |  |                                                          |  |
  |  +---------------------------------------------------------+  |
  |                                                                |
  |  Collection: "assessment_content"                              |
  |  +---------------------------------------------------------+  |
  |  |  Separate collection for test banks, rubrics, answer     |  |
  |  |  keys -- isolated so students cannot retrieve these      |  |
  |  |  through normal tutoring queries.                        |  |
  |  +---------------------------------------------------------+  |
  |                                                                |
  +---------------------------------------------------------------+
```

#### Why a Single Collection with Metadata Filtering (Not Per-Subject Collections)

- Avoids collection proliferation (hundreds of subject/grade combos)
- ChromaDB handles metadata filtering efficiently with WHERE clauses
- Cross-subject queries still work (e.g., "How does math apply to physics?")
- Simpler index maintenance and backup strategy
- A separate assessment collection exists only for access control reasons

### 2.7 Query Rewriting

Students often ask questions that are vague, colloquial, or too short for
effective retrieval. Query rewriting expands and clarifies the student's
question before sending it to the vector search engine.

```
  Student's Original Question
  +--------------------------------------------+
  | "i dont get photosynthesis"                |
  +---------------------+----------------------+
                        |
                        v
  +---------------------+----------------------+
  |              QUERY REWRITER (LLM)          |
  |                                            |
  |  Input: student question + context         |
  |                                            |
  |  Context used:                             |
  |  - Current subject: Biology                |
  |  - Current topic: Plant Biology            |
  |  - Grade level: 10th grade                 |
  |  - Recent conversation: discussed          |
  |    chloroplasts in last 3 messages         |
  |                                            |
  |  Rewrites to 2-3 search queries:          |
  +---------------------+----------------------+
                        |
                        v
  +---------------------------------------------+
  | Query 1: "photosynthesis process explanation |
  |           light reactions dark reactions"     |
  |                                              |
  | Query 2: "how do plants convert sunlight     |
  |           to energy chloroplast"             |
  |                                              |
  | Query 3: "photosynthesis equation inputs     |
  |           outputs grade 10 biology"          |
  +---------------------------------------------+
```

#### Query Rewriting Rules

1. **Expand abbreviations and slang**: "dont get" becomes a proper question
2. **Add subject context**: Include current subject and topic keywords
3. **Generate multiple query variants**: 2-3 queries that capture different angles of the same question
4. **Include grade-appropriate terminology**: Adjust vocabulary to match the student's level
5. **Incorporate conversation context**: If the student was just discussing chloroplasts, include that in the expanded query
6. **Preserve specificity**: If the student asked about a specific page or chapter, keep that reference

#### Lightweight Query Rewriting (Cost Optimization)

Full LLM-based rewriting adds latency and cost. For simple, well-formed
questions, a rule-based fast path is used:

```
  Student Question
       |
       v
  [Is question well-formed?]
       |          |
      YES         NO
       |          |
       v          v
  [Rule-based]  [LLM-based
   expansion]    rewrite]
       |          |
       v          v
  Add subject   Full rewrite
  + grade       with context
  keywords      expansion
       |          |
       +----+-----+
            |
            v
     Search Queries
```

### 2.8 Semantic Search Flow

Once queries are prepared, the semantic search finds the most relevant chunks
from the knowledge base.

```
  Rewritten Queries (2-3 variants)
       |
       v
  +----+-----------------------------+
  |   EMBEDDING                      |
  |   Convert queries to vectors     |
  |   using same model as ingestion  |
  +----+-----------------------------+
       |
       v
  +----+-----------------------------+
  |   METADATA PRE-FILTER            |
  |                                  |
  |   WHERE:                         |
  |     subject = "Biology"          |
  |     AND grade_level IN (10, AP)  |
  |     AND language = "en"          |
  |                                  |
  |   This narrows the search space  |
  |   BEFORE vector similarity runs  |
  +----+-----------------------------+
       |
       v
  +----+-----------------------------+
  |   VECTOR SIMILARITY SEARCH       |
  |                                  |
  |   For EACH query variant:        |
  |     Find top-k nearest neighbors |
  |     k = 10 per query             |
  |     Distance metric: cosine      |
  |                                  |
  |   Total candidates: up to 30     |
  |   (10 per query x 3 queries)     |
  +----+-----------------------------+
       |
       v
  +----+-----------------------------+
  |   DEDUPLICATION                  |
  |                                  |
  |   Remove duplicate chunks that   |
  |   appear across multiple query   |
  |   variant results                |
  |                                  |
  |   Keep the instance with the     |
  |   highest similarity score       |
  +----+-----------------------------+
       |
       v
  Candidate Pool (15-25 unique chunks)
```

### 2.9 Re-ranking Results

Raw vector similarity scores are a good starting point but insufficient for
educational use. The re-ranker applies multiple weighted signals to produce
a final relevance score.

```
  Candidate Pool (15-25 chunks)
       |
       v
  +----+------------------------------+
  |   RE-RANKING PIPELINE             |
  |                                   |
  |   For each chunk, compute:        |
  |                                   |
  |   Score = w1 * semantic_sim       |
  |         + w2 * grade_match        |
  |         + w3 * curriculum_match   |
  |         + w4 * source_priority    |
  |         + w5 * freshness          |
  |         + w6 * content_type_pref  |
  |                                   |
  |   Weights:                        |
  |   w1 = 0.40  (semantic relevance) |
  |   w2 = 0.15  (grade level match)  |
  |   w3 = 0.15  (curriculum match)   |
  |   w4 = 0.15  (source priority)    |
  |   w5 = 0.10  (content freshness)  |
  |   w6 = 0.05  (content type pref)  |
  +----+------------------------------+
       |
       v
  +----+------------------------------+
  |   SCORING DETAILS                 |
  |                                   |
  |   semantic_sim:                   |
  |     Raw cosine similarity (0-1)   |
  |                                   |
  |   grade_match:                    |
  |     1.0 = exact grade match       |
  |     0.7 = +/- 1 grade level      |
  |     0.3 = +/- 2 grade levels     |
  |     0.0 = 3+ grades away         |
  |                                   |
  |   curriculum_match:               |
  |     1.0 = same curriculum std     |
  |     0.5 = same subject area       |
  |     0.0 = no curriculum tag       |
  |                                   |
  |   source_priority:                |
  |     1.0 = teacher-uploaded for    |
  |           this specific class     |
  |     0.7 = teacher-uploaded        |
  |           (general)               |
  |     0.5 = official textbook       |
  |     0.3 = supplementary material  |
  |     0.1 = web-scraped content     |
  |                                   |
  |   freshness:                      |
  |     1.0 = less than 6 months old  |
  |     0.7 = 6-12 months old         |
  |     0.4 = 1-3 years old           |
  |     0.1 = 3+ years old            |
  |                                   |
  |   content_type_pref:              |
  |     Based on student's learning   |
  |     style preference              |
  +----+------------------------------+
       |
       v
  Sort by final score descending
  Select top 5 chunks
       |
       v
  Final Retrieved Context (5 chunks)
```

### 2.10 Context Window Assembly

The retrieved chunks must be packed into the LLM prompt alongside the system
prompt, conversation history, and student profile. Context window budget
management is essential.

```
  CONTEXT WINDOW BUDGET (Claude 3 Opus: 200k tokens)
  ===================================================

  Typical allocation for a tutoring response:

  +-----------------------------------------------+
  |  System Prompt + Student Profile    ~800 tokens|
  +-----------------------------------------------+
  |  Teaching Guidelines & Rules        ~400 tokens|
  +-----------------------------------------------+
  |  RAG Context Block                             |
  |  +------------------------------------------+  |
  |  | RETRIEVED KNOWLEDGE:                     |  |
  |  |                                          |  |
  |  | [Source 1: Biology 101, Ch.5, p.134]     |  |
  |  | "Mitosis is the process of cell..."      |  |
  |  |                                          |  |
  |  | [Source 2: Teacher Notes, Slide 12]      |  |
  |  | "Key differences between mitosis..."     |  |
  |  |                                          |  |
  |  | [Source 3: Biology 101, Ch.5, p.136]     |  |
  |  | "Meiosis, unlike mitosis, produces..."   |  |
  |  |                                          |  |
  |  | [Source 4: AP Bio Study Guide, p.45]     |  |
  |  | "A comparison table of mitosis vs..."    |  |
  |  |                                          |  |
  |  | [Source 5: Lecture Recording, 23:15]      |  |
  |  | "Now let me explain why meiosis is..."   |  |
  |  +------------------------------------------+  |
  |  RAG block total:               ~2500 tokens   |
  +-----------------------------------------------+
  |  Conversation History (last 10)  ~2000 tokens  |
  +-----------------------------------------------+
  |  Student's Current Question       ~100 tokens  |
  +-----------------------------------------------+
  |  Reserved for Response           ~4000 tokens  |
  +-----------------------------------------------+
  |  TOTAL USED:                     ~9800 tokens  |
  +-----------------------------------------------+

  Note: This conservative allocation uses <5% of the
  200k window. The budget allows scaling up for complex
  multi-hop questions that need more retrieved context.
```

#### Context Assembly Rules

1. **Source attribution in context**: Each chunk is prefixed with its source information so the LLM can cite it
2. **Ordering**: Chunks are ordered by re-ranking score (most relevant first)
3. **Deduplication in assembly**: If two chunks have >80% text overlap, keep only the higher-scored one
4. **Budget enforcement**: If total RAG context exceeds the budget, truncate lower-ranked chunks
5. **Separation markers**: Use clear delimiters between chunks so the LLM can distinguish sources

### 2.11 Source Citation in Responses

The LLM is instructed to cite sources inline using a consistent format that
the frontend can render as clickable links.

```
  LLM Response (as delivered to the student):
  ============================================

  Mitosis and meiosis are both forms of cell division, but they
  serve different purposes. **Mitosis** produces two genetically
  identical daughter cells and is used for growth and repair
  [Source: Biology 101, Ch.5, p.134]. **Meiosis**, on the other
  hand, produces four genetically unique cells and is essential
  for sexual reproduction [Source: Biology 101, Ch.5, p.136].

  Your teacher also highlighted that the key difference is in
  the number of division stages -- mitosis has one division while
  meiosis has two [Source: Lecture Notes, Slide 12].

  ---
  Sources used:
  1. Biology 101 Textbook, Chapter 5, pages 134-136
  2. Teacher Lecture Notes, Slide 12
  3. AP Biology Study Guide, page 45
```

#### Citation Format

Citations follow a structured format that the frontend parses:

```
  [Source: {document_title}, {location_descriptor}]

  Examples:
  [Source: Biology 101, Ch.5, p.134]
  [Source: Teacher Notes, Slide 12]
  [Source: Khan Academy Video, 23:15]
  [Source: AP Study Guide, Section 3.2]
```

### 2.12 Confidence Scoring

Every RAG-grounded response receives a confidence score that helps the system
and the student gauge reliability.

```
  CONFIDENCE SCORE CALCULATION
  ============================

  confidence = weighted_average(
      retrieval_confidence,    weight = 0.40
      source_quality,          weight = 0.30
      answer_grounding,        weight = 0.30
  )

  retrieval_confidence:
  +------+--------------------------------------------+
  | 1.0  | Top chunk cosine similarity > 0.90         |
  | 0.8  | Top chunk cosine similarity 0.80-0.90      |
  | 0.5  | Top chunk cosine similarity 0.65-0.80      |
  | 0.2  | Top chunk cosine similarity < 0.65         |
  | 0.0  | No relevant chunks found                   |
  +------+--------------------------------------------+

  source_quality:
  +------+--------------------------------------------+
  | 1.0  | Teacher-uploaded, curriculum-aligned        |
  | 0.8  | Official textbook                          |
  | 0.5  | Supplementary educational material          |
  | 0.3  | Web content from reputable source           |
  | 0.1  | Unverified or low-quality source            |
  +------+--------------------------------------------+

  answer_grounding:
  +------+--------------------------------------------+
  | 1.0  | Response fully supported by retrieved text  |
  | 0.7  | Response mostly supported, minor inference  |
  | 0.4  | Response partially supported                |
  | 0.1  | Response mostly from LLM general knowledge  |
  +------+--------------------------------------------+

  CONFIDENCE THRESHOLDS AND ACTIONS:
  +-------------+------------------------------------------+
  | >= 0.80     | High confidence. Deliver normally.        |
  | 0.60 - 0.79 | Medium confidence. Add disclaimer:        |
  |             | "Based on available materials..."         |
  | 0.40 - 0.59 | Low confidence. Warn student:             |
  |             | "I found limited info on this. You may    |
  |             |  want to check with your teacher."        |
  | < 0.40      | Very low confidence. Knowledge gap:       |
  |             | "I don't have reliable content on this    |
  |             |  topic yet. Let me know if you'd like     |
  |             |  me to flag this for your teacher."       |
  +-------------+------------------------------------------+
```

---

## 3. Sub-features and Small Touches

### 3.1 "Where Did You Learn That?" -- Source Viewer

Students can click on any citation in a response to see the original source
material. This builds trust and enables deeper learning.

```
  Student View (Chat Interface)
  +-------------------------------------------------------------+
  |                                                              |
  |  EduAGI: Mitosis produces two identical daughter cells       |
  |  [Source: Biology 101, Ch.5, p.134]  <-- clickable          |
  |                                                              |
  +-------------------------------------------------------------+
          |
          | (student clicks citation)
          v
  +-------------------------------------------------------------+
  |  SOURCE VIEWER (Modal / Side Panel)                         |
  |                                                              |
  |  Document: Biology 101 Textbook                              |
  |  Chapter:  5 - Cell Division                                 |
  |  Pages:    134-135                                           |
  |                                                              |
  |  +-------------------------------------------------------+  |
  |  | "Mitosis is the process by which a single cell        |  |
  |  | divides to produce two genetically identical daughter  |  |
  |  | cells. The process occurs in four main stages:        |  |
  |  | prophase, metaphase, anaphase, and telophase.         |  |
  |  | During mitosis, the chromosomes are replicated and    |  |
  |  | distributed equally..."                               |  |
  |  |                                                       |  |
  |  | [HIGHLIGHTED: the specific passage the AI used]       |  |
  |  +-------------------------------------------------------+  |
  |                                                              |
  |  [Read Full Chapter]    [Download PDF]   [Close]            |
  +-------------------------------------------------------------+
```

#### Implementation Notes

- The source viewer retrieves the full chunk (not just the preview) from ChromaDB
- If the original document is accessible, a "Read Full Chapter" link opens it at the relevant page
- The specific text passage used is highlighted within the broader chunk context
- Teacher-uploaded documents require access control checks before displaying

### 3.2 Multi-hop Retrieval

Some questions require synthesizing information from multiple sources. For
example: "How did the economic conditions that caused the French Revolution
compare to the conditions before the American Revolution?"

This requires retrieving content about both revolutions and synthesizing.

```
  Complex Student Question
  "How did economic conditions in France before the
   Revolution compare to colonial America?"
       |
       v
  +----+------------------------------+
  |   QUESTION DECOMPOSITION (LLM)    |
  |                                   |
  |   Sub-question 1:                 |
  |   "Economic conditions in France  |
  |    before French Revolution"      |
  |                                   |
  |   Sub-question 2:                 |
  |   "Economic conditions in         |
  |    colonial America before        |
  |    American Revolution"           |
  |                                   |
  |   Sub-question 3:                 |
  |   "Comparison frameworks for      |
  |    revolutionary economic causes" |
  +----+------------------------------+
       |
       v
  [Run retrieval for EACH sub-question]
       |
       +----------+-----------+
       |          |           |
       v          v           v
  [Chunks A]  [Chunks B]  [Chunks C]
  French Rev  Amer. Rev   Comparison
  economics   economics   frameworks
       |          |           |
       +----------+-----------+
       |
       v
  [Merge and re-rank all chunks]
  [Remove duplicates]
  [Select top 8 chunks across all sub-questions]
       |
       v
  [Assemble context with source groupings]
       |
       v
  [LLM generates comparative answer with
   citations from both topic areas]
```

#### When Multi-hop Triggers

Multi-hop retrieval activates when the question decomposition LLM detects:
- Comparison questions ("compare", "contrast", "difference between")
- Cause-effect chains spanning topics ("how did X lead to Y")
- Questions referencing multiple subjects or time periods
- Questions requiring both factual recall and application

### 3.3 Curriculum Alignment Tagging

Every ingested document can be tagged with one or more curriculum standards.
This enables precise filtering and helps teachers verify coverage.

#### Supported Curriculum Frameworks

| Framework | Region | Subjects | Example Code |
|-----------|--------|----------|--------------|
| Common Core State Standards (CCSS) | USA | Math, ELA | CCSS.MATH.8.EE.A.1 |
| Next Generation Science Standards (NGSS) | USA | Science | NGSS-LS1-4 |
| International Baccalaureate (IB) | Global | All | IB.BIO.2.1 |
| Advanced Placement (AP) | USA | All | AP.BIO.LO.3.1 |
| National Curriculum (UK) | UK | All | UK.KS4.SCI.B4 |
| Australian Curriculum | Australia | All | ACSSU176 |
| Custom / Institutional | Any | Any | INST.{code} |

#### Auto-tagging Flow

When a teacher uploads a document without specifying curriculum tags, the
system attempts to auto-detect them:

```
  Uploaded Document (no curriculum tags)
       |
       v
  [Extract key concepts from document]
       |
       v
  [Match concepts against curriculum
   standard database using semantic
   similarity on standard descriptions]
       |
       v
  [Propose top 3-5 matching standards]
       |
       v
  [Present to teacher for confirmation]
       |
       +-------+--------+
       |                |
       v                v
  [Teacher         [Teacher
   confirms]        edits/corrects]
       |                |
       +-------+--------+
               |
               v
  [Store confirmed curriculum tags
   with document metadata]
```

### 3.4 Auto-detection of Outdated Content

Educational content becomes outdated. A 2019 chemistry textbook might have
different IUPAC naming conventions than a 2025 edition. The system tracks
content freshness and flags potential issues.

```
  FRESHNESS MONITORING
  ====================

  Triggers for outdated content review:

  1. AGE-BASED:
     Documents older than the configured freshness threshold
     (default: 3 years for STEM, 5 years for humanities)
     are flagged for teacher review.

  2. CONFLICT DETECTION:
     When two chunks from different sources contradict each
     other on the same topic, the system flags both for review
     and prefers the newer source in retrieval.

  3. TEACHER-INITIATED:
     Teachers can mark specific documents as "superseded" or
     "archived" which removes them from active retrieval.

  4. EXTERNAL SIGNAL:
     When curriculum standards are updated, documents tagged
     with old standard codes are flagged for review.
```

### 3.5 Student Flagging of Incorrect Information

Students can flag any response they believe is incorrect. This creates a
feedback loop that improves content quality over time.

```
  Student sees potentially wrong information
       |
       v
  [Clicks flag icon on response]
       |
       v
  +--------------------------------------+
  |  FLAG SUBMISSION FORM                |
  |                                      |
  |  What seems wrong?                   |
  |  ( ) Factually incorrect             |
  |  ( ) Contradicts what teacher said   |
  |  ( ) Contradicts textbook            |
  |  ( ) Outdated information            |
  |  ( ) Other                           |
  |                                      |
  |  Optional details: [____________]    |
  |                                      |
  |  [Submit Flag]                       |
  +--------------------------------------+
       |
       v
  [Flag stored in PostgreSQL with:]
  - Response ID and content
  - Source chunks that were used
  - Student's reason and details
  - Timestamp
       |
       v
  [Teacher receives notification in dashboard]
       |
       v
  [Teacher reviews and either:]
  - Confirms content is correct (dismiss flag)
  - Updates/removes the source document
  - Adds a correction note to the content
```

### 3.6 "Read More" Links

When a response is based on a larger document, the student can access the
full source for deeper study.

#### Read More Behavior

| Source Type | Read More Action |
|-------------|-----------------|
| Uploaded PDF | Open PDF viewer at relevant page |
| Uploaded DOCX | Render document section in viewer |
| PPTX | Show the relevant slide(s) |
| YouTube video | Link to video at timestamp |
| Web page | Link to original URL |
| Teacher notes | Show full note in reader view |

### 3.7 Knowledge Gap Detection

When the system cannot find relevant content for a student's question, it
should honestly say so rather than hallucinate.

```
  Retrieval returns low confidence (< 0.40)
       |
       v
  +--------------------------------------+
  |  KNOWLEDGE GAP RESPONSE              |
  |                                      |
  |  "I don't have reliable study        |
  |   materials on [topic] in my         |
  |   knowledge base yet.                |
  |                                      |
  |   Here is what I can do:             |
  |   1. I can try to explain based on   |
  |      my general knowledge (but I     |
  |      cannot cite specific sources)   |
  |   2. I can flag this topic for your  |
  |      teacher to add materials        |
  |   3. I can suggest related topics    |
  |      I do have content for           |
  |                                      |
  |   What would you prefer?"            |
  +--------------------------------------+
       |
       v
  [If student chooses option 2:]
  Store knowledge gap request in PostgreSQL
  Notify teacher via dashboard
  Teacher sees: "3 students asked about [topic]
  but no content was available"
```

### 3.8 Teacher-uploaded Content Prioritization

Content uploaded by a student's own teacher for their specific class should
always rank higher than generic content. The re-ranking system (Section 2.9)
handles this through the source_priority weight.

#### Priority Hierarchy

```
  HIGHEST PRIORITY
  +-------------------------------------------------+
  |  1. Teacher-uploaded for THIS specific class     |
  |     (teacher_id matches AND class_id matches)    |
  +-------------------------------------------------+
  |  2. Teacher-uploaded for this subject generally   |
  |     (teacher_id matches, no class restriction)   |
  +-------------------------------------------------+
  |  3. Institution-approved textbook content         |
  |     (admin-uploaded, curriculum-aligned)          |
  +-------------------------------------------------+
  |  4. Supplementary educational material            |
  |     (educational publishers, curated sources)     |
  +-------------------------------------------------+
  |  5. Web-sourced educational content               |
  |     (scraped from reputable educational sites)    |
  +-------------------------------------------------+
  LOWEST PRIORITY
```

### 3.9 Duplicate Content Detection

When the same content is uploaded multiple times (e.g., multiple teachers
uploading the same textbook chapter), the system should detect and handle
duplicates.

```
  New Document Arrives for Ingestion
       |
       v
  [Compute content hash (SHA-256 of cleaned text)]
       |
       v
  [Check hash against existing documents]
       |
       +----------+----------+
       |                     |
  [No match]            [Match found]
       |                     |
       v                     v
  [Proceed with         [DUPLICATE HANDLING]
   normal ingestion]         |
                             +--------+--------+
                             |                 |
                        [Same uploader]   [Different uploader]
                             |                 |
                             v                 v
                        [Skip -- notify  [Link to existing
                         "already        document. Add new
                         uploaded"]      uploader as co-owner.
                                         No re-ingestion needed.]
```

#### Near-duplicate Detection

For documents that are similar but not identical (e.g., different editions
of the same textbook), the system uses a secondary check:

- Compute SimHash of the cleaned text
- If SimHash similarity > 85%, flag as potential near-duplicate
- Present to the teacher/admin for manual resolution

### 3.10 Content Freshness Scoring

Every document receives a freshness score that decays over time. This score
feeds into the re-ranking pipeline (Section 2.9).

```
  Freshness Score Decay Curve:

  Score
  1.0 |****
      |    ****
  0.8 |        ****
      |            ***
  0.6 |               ***
      |                  ***
  0.4 |                     ***
      |                        ***
  0.2 |                           ****
      |                               *****
  0.0 +---+---+---+---+---+---+---+---+-----> Age
      0   6   12  18  24  30  36  42  48 months

  Decay function: score = max(0, 1.0 - (age_months / 48))
  Floor: 0.05 (never fully zero -- old content may still be relevant)

  Subject-specific adjustments:
  - STEM subjects:  Faster decay (score / 48 months)
  - Humanities:     Slower decay (score / 72 months)
  - Mathematics:    Very slow decay (score / 120 months)
  - Current events: Rapid decay (score / 6 months)
```

---

## 4. Technical Requirements

### 4.1 Vector Database: ChromaDB Configuration

ChromaDB is the primary vector database for EduAGI, chosen for its Python-
native API, simplicity, and zero-configuration startup.

#### ChromaDB Setup

```
  Deployment Options:

  DEVELOPMENT:
  +----------------------------------+
  | ChromaDB (in-process)            |
  | PersistentClient                 |
  | Storage: ./data/chroma/          |
  | No separate server needed        |
  +----------------------------------+

  PRODUCTION:
  +----------------------------------+
  | ChromaDB Server (Docker)         |
  | HttpClient connection            |
  | Host: chromadb:8000              |
  | Persistent volume mounted        |
  | Backed by: DuckDB + Parquet      |
  +----------------------------------+
```

#### Collection Configuration

```
  Collection: "educational_content"
  +-----------------------------------------+
  | Embedding function: OpenAI              |
  | Distance metric: cosine                 |
  | HNSW parameters:                        |
  |   space:            "cosine"            |
  |   construction_ef:  200                 |
  |   search_ef:        100                 |
  |   M:                16                  |
  | Max elements:       1,000,000           |
  +-----------------------------------------+

  Collection: "assessment_content"
  +-----------------------------------------+
  | Same configuration as above             |
  | Access restricted to Assessment Agent   |
  | and teacher-role users only             |
  +-----------------------------------------+
```

#### HNSW Parameter Rationale

| Parameter | Value | Why |
|-----------|-------|-----|
| construction_ef | 200 | Higher = better index quality, slower build. Ingestion is background so speed is less critical. |
| search_ef | 100 | Balances search accuracy with latency. At 100, recall is >95% while keeping search under 50ms. |
| M | 16 | Number of connections per element. 16 is the standard default offering good recall/memory tradeoff. |

### 4.2 Embedding Models

#### Primary: OpenAI text-embedding-3-small

| Property | Value |
|----------|-------|
| Dimensions | 1536 |
| Max input tokens | 8191 |
| Cost | $0.02 / 1M tokens |
| Performance (MTEB) | 62.3% average |
| Latency | ~100ms per batch of 100 |

#### Why text-embedding-3-small Over ada-002

- 5x cheaper than ada-002
- Higher benchmark performance (62.3% vs 61.0% on MTEB)
- Same 1536 dimensions (drop-in replacement)
- Supports optional dimension reduction (e.g., 512-dim for cost savings)
- Native Matryoshka representation support

#### Fallback: Open-source Alternative

For institutions that cannot send data to OpenAI:

| Property | BAAI/bge-large-en-v1.5 |
|----------|------------------------|
| Dimensions | 1024 |
| Max input tokens | 512 |
| Cost | Free (self-hosted) |
| Performance (MTEB) | 64.2% average |
| Hosting | Runs on a single GPU or CPU |
| Latency | ~200ms per batch of 100 (GPU) |

### 4.3 Document Parsers

| Format | Primary Parser | Fallback | Notes |
|--------|---------------|----------|-------|
| PDF | PyMuPDF (fitz) | PyPDF2 | PyMuPDF is faster and handles complex layouts better |
| PDF (scanned) | pytesseract + pdf2image | -- | OCR pipeline for image-based PDFs |
| DOCX | python-docx | docx2txt | python-docx preserves structure; docx2txt is simpler |
| PPTX | python-pptx | -- | Extracts slide text, speaker notes, and shapes |
| YouTube | youtube-transcript-api | yt-dlp + whisper | Prefer existing captions; fall back to audio transcription |
| Web pages | trafilatura | BeautifulSoup | trafilatura is purpose-built for content extraction |
| Plain text | Built-in | -- | Direct ingestion with paragraph-based chunking |
| Markdown | Built-in | -- | Parse headings as structural boundaries |
| EPUB | ebooklib | -- | For digital textbooks in EPUB format |

### 4.4 MCP Servers

EduAGI integrates with Model Context Protocol (MCP) servers for extended
capabilities.

#### Filesystem MCP Server

```
  Purpose: Allow the LLM agents to read and navigate
           uploaded educational documents stored on the
           server filesystem or object storage.

  Configuration:
  +-----------------------------------------------+
  | Server: @modelcontextprotocol/server-filesystem|
  | Root:   /data/documents/                       |
  | Access: Read-only                              |
  | Scope:  Only the documents/ directory tree     |
  |                                                |
  | Capabilities:                                  |
  | - List documents in a directory                |
  | - Read document contents                       |
  | - Search document filenames                    |
  +-----------------------------------------------+

  Use cases:
  - Tutor Agent needs to look up a specific table
    or figure that was not fully captured in chunks
  - Content Agent needs to verify full document context
  - Assessment Agent reads answer keys from protected
    document directory
```

#### Web Scraping MCP Server (Future)

```
  Purpose: Fetch content from educational websites
           when the knowledge base lacks coverage.

  Configuration:
  +-----------------------------------------------+
  | Server: Custom web-fetch MCP                   |
  | Allowed domains:                               |
  |   - khanacademy.org                            |
  |   - wikipedia.org                              |
  |   - openstax.org                               |
  |   - purplemath.com                             |
  |   - bbc.co.uk/bitesize                         |
  | Blocked: all other domains                     |
  | Rate limit: 10 requests per minute             |
  |                                                |
  | Capabilities:                                  |
  | - Fetch and extract web page content           |
  | - Convert to clean text                        |
  | - Auto-ingest into knowledge base with         |
  |   low priority source tag                      |
  +-----------------------------------------------+

  Note: This is a Phase 2+ feature. MVP relies
  entirely on pre-ingested content.
```

### 4.5 Chunk Size Optimization Testing Strategy

The chunking parameters (Section 2.4) should be validated empirically. The
testing strategy:

```
  CHUNK SIZE OPTIMIZATION PROTOCOL
  =================================

  Step 1: Create a test dataset
  - 50 educational documents across 5 subjects
  - 200 student questions with known correct answers
  - Each answer traceable to specific document passages

  Step 2: Test matrix
  +----------+----------+----------+----------+
  | Chunk    | Overlap  | Top-k    | Metric   |
  | size     | size     | retrieved| (Recall) |
  +----------+----------+----------+----------+
  | 256 tok  | 32 tok   | 3, 5, 10 | Recall@k |
  | 512 tok  | 64 tok   | 3, 5, 10 | Recall@k |
  | 768 tok  | 96 tok   | 3, 5, 10 | Recall@k |
  | 1024 tok | 128 tok  | 3, 5, 10 | Recall@k |
  +----------+----------+----------+----------+

  Step 3: Evaluation metrics
  - Recall@k: Does the correct passage appear in top-k?
  - Precision@k: What fraction of retrieved chunks are relevant?
  - Answer quality: LLM answer quality with each configuration
  - Latency: End-to-end retrieval time

  Step 4: Select configuration that maximizes Recall@5
          while keeping latency under 500ms

  Expected outcome: 512 tokens with 64-token overlap
  is the sweet spot for educational content, but this
  must be validated with real curriculum materials.
```

### 4.6 Metadata Schema Design

The metadata schema is the backbone of filtered retrieval. It must be
consistent across all document types while remaining flexible.

#### Required Metadata Fields (All Documents)

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| document_id | UUID | Yes | Unique identifier for parent document |
| chunk_id | UUID | Yes | Unique identifier for this chunk |
| document_title | string | Yes | Human-readable document name |
| subject | string | Yes | Primary subject area |
| grade_level | string | Yes | Target grade level or range |
| content_type | string | Yes | "textbook", "lecture", "notes", "web", "video" |
| language | string | Yes | ISO 639-1 language code |
| upload_timestamp | ISO datetime | Yes | When the document was ingested |
| content_hash | string | Yes | SHA-256 hash of chunk content |

#### Optional Metadata Fields

| Field | Type | Description |
|-------|------|-------------|
| curriculum_standard | string | Curriculum alignment code (CCSS, NGSS, etc.) |
| topic_tags | list of strings | Specific topic tags for fine-grained filtering |
| chapter | string | Chapter or section identifier |
| page_numbers | list of ints | Page numbers in source document |
| slide_number | int | Slide number for PPTX sources |
| video_timestamp | string | Timestamp for video/audio sources |
| uploaded_by | UUID | Teacher or admin who uploaded |
| class_id | UUID | Specific class this content is assigned to |
| freshness_date | ISO date | Publication or last-verified date |
| source_url | string | Original URL for web-sourced content |
| source_priority | float | Pre-computed priority score (0.0-1.0) |
| is_archived | boolean | Whether this content has been superseded |

### 4.7 Index Maintenance

#### Re-indexing Strategy

```
  RE-INDEXING TRIGGERS
  ====================

  1. DOCUMENT UPDATE:
     When a teacher uploads a new version of an existing document:
     - Delete all chunks from old version (by document_id)
     - Re-ingest the new version
     - Update the document record in PostgreSQL

  2. EMBEDDING MODEL CHANGE:
     When switching embedding models (e.g., ada-002 to text-embedding-3-small):
     - Full re-index required
     - Run as background batch job
     - Strategy: build new collection in parallel, swap atomically

  3. SCHEDULED MAINTENANCE:
     Monthly job that:
     - Removes chunks from deleted/archived documents
     - Recalculates freshness scores
     - Updates content hashes
     - Compacts ChromaDB storage

  4. ON-DEMAND:
     Admin can trigger full or partial re-index from dashboard
```

#### Garbage Collection

```
  GARBAGE COLLECTION FLOW
  =======================

  Monthly scheduled job:

  [1. Query PostgreSQL for documents marked as deleted or archived]
       |
       v
  [2. Collect their document_ids]
       |
       v
  [3. Delete all chunks in ChromaDB WHERE document_id IN (deleted_ids)]
       |
       v
  [4. Verify deletion count matches expected count]
       |
       v
  [5. Log results and any discrepancies]
       |
       v
  [6. Run ChromaDB compaction if supported]
```

---

## 5. Services and Alternatives

### 5.1 Vector Database Comparison

#### Primary: ChromaDB

| Aspect | Details |
|--------|---------|
| Why chosen | Python-native, zero-config, open source, embedded mode for dev |
| Strengths | Simple API, metadata filtering, easy local dev, active community |
| Weaknesses | Less battle-tested at scale, limited distributed mode |
| Cost | Free (open source), self-hosted |
| Scale limit | ~5M vectors on single node (sufficient for MVP) |

#### Alternative 1: Pinecone

| Aspect | Details |
|--------|---------|
| Strengths | Fully managed, highly scalable, fast, reliable SLA |
| Weaknesses | Vendor lock-in, cost at scale, data leaves your infrastructure |
| Cost | $70/month (starter) to $500+/month (production) |
| When to consider | When scaling beyond 5M vectors or needing 99.99% uptime SLA |
| Migration path | ChromaDB metadata schema maps cleanly to Pinecone namespaces |

#### Alternative 2: Weaviate

| Aspect | Details |
|--------|---------|
| Strengths | Built-in hybrid search (BM25 + vector), GraphQL API, multi-modal |
| Weaknesses | Heavier operational burden, more complex setup |
| Cost | Free (open source) or managed cloud ($25+/month) |
| When to consider | When hybrid search becomes critical or when multi-modal vectors (images) are needed |

#### Alternative 3: Qdrant

| Aspect | Details |
|--------|---------|
| Strengths | Rust-based (fast), excellent filtering, payload indexing |
| Weaknesses | Smaller community than Pinecone/Weaviate, newer |
| Cost | Free (open source) or managed cloud |
| When to consider | When query filtering performance is the bottleneck |

#### Alternative 4: pgvector

| Aspect | Details |
|--------|---------|
| Strengths | Runs inside existing PostgreSQL (no new infra), SQL interface |
| Weaknesses | Slower than purpose-built vector DBs, limited ANN algorithms |
| Cost | Free (PostgreSQL extension) |
| When to consider | When simplifying infrastructure is more important than search speed, or for small deployments |

#### Decision Matrix

```
  Criteria (1-5)       Chroma  Pine   Weav   Qdrant  pgvec
  +-----------------+--------+------+------+--------+------+
  | Ease of setup   |   5    |  4   |  3   |   4    |  5   |
  | Python API      |   5    |  4   |  3   |   4    |  3   |
  | Scale (10M+)    |   2    |  5   |  4   |   4    |  2   |
  | Metadata filter  |   4    |  4   |  5   |   5    |  4   |
  | Hybrid search   |   2    |  3   |  5   |   4    |  3   |
  | Self-hostable   |   5    |  1   |  5   |   5    |  5   |
  | Cost            |   5    |  2   |  4   |   5    |  5   |
  | Community       |   4    |  5   |  4   |   3    |  4   |
  +-----------------+--------+------+------+--------+------+
  | TOTAL           |  32    | 28   | 33   |  34    | 31   |
  +-----------------+--------+------+------+--------+------+

  Decision: ChromaDB for MVP (simplicity, zero-config).
  Migration path: Qdrant or Weaviate for production scale.
```

### 5.2 Embedding Model Comparison

#### Primary: OpenAI text-embedding-3-small

| Aspect | Details |
|--------|---------|
| Why chosen | Best cost/performance ratio, high quality, simple API |
| Dimensions | 1536 (configurable down to 256) |
| Cost | $0.02 / 1M tokens |
| MTEB score | 62.3% |

#### Alternative 1: OpenAI text-embedding-3-large

| Aspect | Details |
|--------|---------|
| Strengths | Higher accuracy (64.6% MTEB), 3072 dimensions |
| Weaknesses | 6.5x more expensive, double the storage for vectors |
| Cost | $0.13 / 1M tokens |
| When to consider | When retrieval accuracy is critical and budget allows |

#### Alternative 2: Cohere embed-v3

| Aspect | Details |
|--------|---------|
| Strengths | Built-in search/classification modes, multi-lingual, compression |
| Weaknesses | Separate API dependency, less ecosystem integration |
| Cost | $0.10 / 1M tokens |
| When to consider | When multi-lingual support is a primary concern |

#### Alternative 3: Voyage AI voyage-2

| Aspect | Details |
|--------|---------|
| Strengths | Highest quality on code/legal/financial, good retrieval quality |
| Weaknesses | Newer company, smaller community |
| Cost | $0.10 / 1M tokens |
| When to consider | When embedding technical or domain-specific content |

#### Alternative 4: BAAI/bge-large-en-v1.5 (Open Source)

| Aspect | Details |
|--------|---------|
| Strengths | Free, self-hosted, no data leaves infrastructure, good quality |
| Weaknesses | Requires GPU hosting, 512-token limit, maintenance overhead |
| Cost | Free (compute costs for hosting) |
| When to consider | When data privacy requirements prevent using external APIs |

### 5.3 Document Parsing Comparison

#### Primary: Custom Parsers (PyPDF + python-docx + python-pptx)

| Aspect | Details |
|--------|---------|
| Why chosen | Fine-grained control, lightweight, no external dependencies |
| Strengths | Each parser optimized for its format, metadata extraction control |
| Weaknesses | More code to maintain, must handle edge cases per format |

#### Alternative 1: LangChain Document Loaders

| Aspect | Details |
|--------|---------|
| Strengths | Unified API, many format loaders, community-maintained |
| Weaknesses | Less control over extraction details, extra abstraction layer |
| When to consider | When development speed is prioritized over fine-grained control |

#### Alternative 2: Unstructured.io

| Aspect | Details |
|--------|---------|
| Strengths | Best-in-class extraction, handles messy documents, OCR built-in |
| Weaknesses | Heavy dependency, some features require API key, complex setup |
| When to consider | When dealing with many scanned PDFs or complex document layouts |

#### Alternative 3: LlamaParse (LlamaIndex)

| Aspect | Details |
|--------|---------|
| Strengths | LLM-powered parsing, excellent table extraction, layout understanding |
| Weaknesses | API-based (data leaves infrastructure), cost per page, latency |
| When to consider | When documents have complex tables, charts, or mixed layouts |

### 5.4 Search Strategy Comparison

#### Primary: Pure Semantic Search (Vector Similarity)

| Aspect | Details |
|--------|---------|
| Why chosen | Captures meaning, not just keywords; matches student language to textbook language |
| Strengths | Handles synonyms, paraphrases, and conceptual queries naturally |
| Weaknesses | Can miss exact keyword matches; "fuzzy" relevance |

#### Alternative 1: Hybrid Search (BM25 + Semantic)

```
  HOW HYBRID SEARCH WORKS
  ========================

  Student Query: "What is Newton's second law F=ma?"

  BM25 (keyword):
  - Excels at finding exact match "F=ma" and "Newton's second law"
  - Misses: "force equals mass times acceleration" (no keyword match)

  Semantic (vector):
  - Finds: "force equals mass times acceleration"
  - May rank generic physics content too high

  Hybrid (combined):
  - Finds BOTH exact matches AND semantic matches
  - Re-ranks using Reciprocal Rank Fusion (RRF)

  Score_hybrid = (1 / (k + rank_bm25)) + (1 / (k + rank_semantic))
  where k = 60 (standard RRF constant)
```

| Aspect | Details |
|--------|---------|
| Strengths | Best of both worlds; handles formulas, names, and concepts |
| Weaknesses | Requires maintaining both a BM25 index and vector index |
| When to consider | When retrieval quality on keyword-heavy queries (formulas, names, dates) needs improvement |
| Migration path | Add BM25 index (Elasticsearch or SQLite FTS) alongside ChromaDB |

#### Alternative 2: ColBERT (Contextualized Late Interaction)

| Aspect | Details |
|--------|---------|
| Strengths | Token-level matching, excellent precision, strong on long documents |
| Weaknesses | Higher storage cost (vector per token), more complex infrastructure |
| When to consider | When retrieval precision must be maximized regardless of cost |

#### Alternative 3: Re-ranking with Cross-encoder

| Aspect | Details |
|--------|---------|
| Strengths | Much higher accuracy than bi-encoder similarity alone |
| Weaknesses | Slower (must score each candidate pair), adds latency |
| When to consider | As a second-stage re-ranker on top of vector search results |

---

## 6. Connections and Dependencies

### 6.1 System Integration Map

```
  +===================================================================+
  |               HOW RAG CONNECTS TO THE REST OF EDUAGI               |
  +===================================================================+
  |                                                                    |
  |                    +------------------+                            |
  |                    |   TEACHER/ADMIN  |                            |
  |                    |   Content Upload |                            |
  |                    +--------+---------+                            |
  |                             |                                      |
  |                             | (uploads PDF, DOCX, etc.)            |
  |                             v                                      |
  |  +--------------------------------------------------------------+ |
  |  |                RAG KNOWLEDGE SYSTEM (F02)                     | |
  |  |                                                               | |
  |  |  +-----------+  +----------+  +----------+  +-------------+  | |
  |  |  | Ingestion |  | ChromaDB |  | Retrieval|  | Re-ranking  |  | |
  |  |  | Pipeline  |->| Vector   |->| Engine   |->| + Citation  |  | |
  |  |  |           |  | Store    |  |          |  |             |  | |
  |  |  +-----------+  +----------+  +----------+  +------+------+  | |
  |  +--------------------------------------------------------------+ |
  |         ^                                              |           |
  |         |                                              |           |
  |         | triggers ingestion                           | provides  |
  |         |                                              | grounded  |
  |         |                                              | context   |
  |   +-----+-------+                              +------v------+    |
  |   |  Content     |                              |             |    |
  |   |  Upload API  |                              |  TUTOR      |    |
  |   |  (REST)      |                              |  AGENT      |    |
  |   +-----+--------+                              |             |    |
  |         ^                                        | Uses RAG    |    |
  |         |                                        | context to  |    |
  |  +------+-------+                               | generate    |    |
  |  |   CONTENT    |                               | accurate    |    |
  |  |   AGENT      |                               | responses   |    |
  |  |              |                               +------+------+    |
  |  | Generates    |                                      |           |
  |  | study guides |                                      v           |
  |  | and lesson   |                              +-------------+     |
  |  | plans from   |                              |  STUDENT    |     |
  |  | RAG content  |                              |  (Chat UI)  |     |
  |  +--------------+                              +------+------+     |
  |                                                       |            |
  |                                                       | asks       |
  |                                                       | questions  |
  |  +-------------+                                      |            |
  |  | ASSESSMENT  |<-------------------------------------+            |
  |  | AGENT       |  (uses RAG to generate curriculum-aligned         |
  |  |             |   questions and verify answer correctness)        |
  |  +-------------+                                                   |
  |                                                                    |
  +====================================================================+
```

### 6.2 How RAG Feeds into the Tutor Agent

The Tutor Agent is the primary consumer of RAG-retrieved content. Every
tutoring response follows this flow:

```
  Student asks a question in chat
       |
       v
  [Tutor Agent receives question]
       |
       v
  [Tutor Agent calls RAG Retrieval Service]
       |
       +--> Query: student's question
       +--> Filters: {
       |      subject: context.current_subject,
       |      grade_level: student.grade_level,
       |      class_id: student.class_id (optional)
       |    }
       +--> k: 5 (number of chunks to retrieve)
       |
       v
  [RAG returns: {
     context: "combined text of top 5 chunks",
     sources: [{title, page, chunk_id}, ...],
     confidence: 0.85
  }]
       |
       v
  [Tutor Agent builds prompt:]
       |
       |  System prompt (teaching style, student profile)
       |  + RAG context block (retrieved chunks with source tags)
       |  + Conversation history (last 10 messages)
       |  + Instructions: "Cite sources. If unsure, say so."
       |  + Student's question
       |
       v
  [LLM generates response with inline citations]
       |
       v
  [Tutor Agent returns response to student]
  [Includes: text, sources list, confidence score]
```

### 6.3 How RAG Feeds into the Assessment Agent

The Assessment Agent uses RAG differently -- not for answering student
questions but for generating curriculum-aligned assessments and verifying
student answers.

```
  USE CASE 1: QUESTION GENERATION
  ================================

  Teacher requests: "Generate a quiz on Chapter 5: Cell Division"
       |
       v
  [Assessment Agent calls RAG with:]
       Query: "Cell division mitosis meiosis chapter 5"
       Filters: {subject: "Biology", content_type: "textbook"}
       k: 15 (more chunks needed for comprehensive question generation)
       |
       v
  [RAG returns key concepts from Chapter 5]
       |
       v
  [Assessment Agent generates questions GROUNDED in actual content]
  [Each question can be traced to a specific chunk/page]

  USE CASE 2: ANSWER VERIFICATION
  ================================

  Student submits: "Mitosis produces four daughter cells"
       |
       v
  [Assessment Agent calls RAG with:]
       Query: "How many daughter cells does mitosis produce"
       Collection: "assessment_content" (includes answer keys)
       k: 3
       |
       v
  [RAG returns: "Mitosis produces TWO identical daughter cells"]
       |
       v
  [Assessment Agent: "Incorrect. Mitosis produces two identical
   daughter cells, not four. You may be confusing this with meiosis,
   which produces four cells. See Biology 101, p.134."]
```

### 6.4 How Teacher Content Upload Triggers RAG Ingestion

```
  TEACHER CONTENT UPLOAD FLOW
  ============================

  Teacher Dashboard
  +-------------------------------------------+
  | Upload Materials                           |
  |                                            |
  | File: [biology_ch5.pdf]          [Browse]  |
  |                                            |
  | Subject:     [Biology        v]            |
  | Grade Level: [10th Grade     v]            |
  | Class:       [Period 3 Bio   v]            |
  | Curriculum:  [NGSS-LS1-4     v]            |
  | Tags:        [cell division, mitosis]      |
  |                                            |
  | [Upload and Process]                       |
  +---------------------+---------------------+
                        |
                        v
  [Content Upload API receives file + metadata]
                        |
                        v
  [File stored in Object Storage (S3/MinIO)]
                        |
                        v
  [Document record created in PostgreSQL]
  [Status: "processing"]
                        |
                        v
  [Ingestion job queued in task queue (Celery/Redis)]
                        |
                        v
  [Background worker picks up job]
                        |
                        v
  [INGESTION PIPELINE RUNS (Section 2.2)]
  [Extract -> Clean -> Chunk -> Embed -> Store]
                        |
                        v
  [Document status updated to "ready"]
  [Teacher notified: "Your document has been
   processed. 47 knowledge chunks created."]
                        |
                        v
  [Content immediately available for
   RAG retrieval by students in this class]
```

### 6.5 Complete Data Flow Diagram

```
  +=================================================================+
  |                    COMPLETE DATA FLOW                             |
  +=================================================================+
  |                                                                  |
  |  INGESTION FLOW (Background, Async)                              |
  |  ==================================                              |
  |                                                                  |
  |  [Teacher] --upload--> [REST API] --store--> [Object Storage]   |
  |                            |                                     |
  |                            +--queue--> [Task Queue (Redis)]     |
  |                                            |                     |
  |                                            v                     |
  |                                   [Ingestion Worker]            |
  |                                            |                     |
  |                            +-------+-------+-------+             |
  |                            |       |       |       |             |
  |                            v       v       v       v             |
  |                         [Parse] [Clean] [Chunk] [Embed]         |
  |                                                    |             |
  |                                                    v             |
  |                                              [ChromaDB]         |
  |                                              (vectors +         |
  |                                               metadata)         |
  |                                                                  |
  |  RETRIEVAL FLOW (Real-time, Sync)                                |
  |  ================================                                |
  |                                                                  |
  |  [Student] --question--> [WebSocket/REST API]                   |
  |                               |                                  |
  |                               v                                  |
  |                      [Orchestrator]                              |
  |                               |                                  |
  |                    +----------+----------+                       |
  |                    |                     |                        |
  |                    v                     v                        |
  |             [Memory Agent]        [RAG Retriever]                |
  |             (student context)          |                          |
  |                    |           +-------+-------+                 |
  |                    |           |       |       |                 |
  |                    |           v       v       v                 |
  |                    |        [Query] [Search] [Re-rank]          |
  |                    |        Rewrite  ChromaDB  Results           |
  |                    |                              |               |
  |                    +----------+-------------------+              |
  |                               |                                  |
  |                               v                                  |
  |                      [Tutor/Assessment Agent]                   |
  |                      (LLM with RAG context)                     |
  |                               |                                  |
  |                               v                                  |
  |                      [Response + Citations]                     |
  |                               |                                  |
  |                               v                                  |
  |                         [Student UI]                             |
  |                    (text + source links)                         |
  |                                                                  |
  |  FEEDBACK FLOW (Async)                                           |
  |  =====================                                           |
  |                                                                  |
  |  [Student] --flags incorrect info--> [PostgreSQL]               |
  |                                           |                      |
  |                                           v                      |
  |                                    [Teacher Dashboard]          |
  |                                           |                      |
  |                                           v                      |
  |                                    [Content Update]             |
  |                                    (re-ingestion if needed)     |
  |                                                                  |
  +=================================================================+
```

### 6.6 Dependency Map

```
  F02: RAG Knowledge Retrieval
       |
       | depends on:
       |
       +---> ChromaDB (vector storage)
       |       |
       |       +---> Must be running before any retrieval
       |       +---> Initialized in Phase 1, Sprint 3
       |
       +---> Embedding Model API (OpenAI)
       |       |
       |       +---> Required for both ingestion and query
       |       +---> OPENAI_API_KEY must be configured
       |
       +---> PostgreSQL
       |       |
       |       +---> Document records, ingestion logs, student flags
       |       +---> Shared with Memory Agent and all other features
       |
       +---> Redis
       |       |
       |       +---> Task queue for background ingestion jobs
       |       +---> Cache for frequent query results
       |
       +---> Object Storage (S3/MinIO)
       |       |
       |       +---> Source document file storage
       |       +---> Referenced by "Read More" links
       |
       | depended on by:
       |
       +---> Tutor Agent (F01) -- primary consumer
       +---> Assessment Agent (F04) -- question gen + grading
       +---> Content Agent -- lesson plan generation
       +---> Analytics Agent -- content coverage reports
```

---

## 7. Appendix

### 7.1 Glossary

| Term | Definition |
|------|-----------|
| **RAG** | Retrieval-Augmented Generation. A technique that retrieves relevant documents and includes them in the LLM prompt to ground responses in factual content. |
| **Chunk** | A segment of a document, typically 256-1024 tokens, that represents a single unit of information for embedding and retrieval. |
| **Embedding** | A dense vector representation of text that captures semantic meaning. Similar texts have similar embeddings. |
| **Vector database** | A database optimized for storing and searching dense vector embeddings using approximate nearest neighbor algorithms. |
| **Cosine similarity** | A measure of similarity between two vectors, ranging from -1 (opposite) to 1 (identical). Used to find semantically similar text. |
| **HNSW** | Hierarchical Navigable Small World. An algorithm for approximate nearest neighbor search used by ChromaDB and other vector databases. |
| **BM25** | Best Matching 25. A keyword-based ranking function used in traditional information retrieval. |
| **Re-ranking** | A second-stage scoring process that refines initial retrieval results using additional signals beyond vector similarity. |
| **Context window** | The maximum number of tokens an LLM can process in a single prompt. Determines how much retrieved content can be included. |
| **Multi-hop retrieval** | Retrieving information from multiple sources to answer a complex question that spans multiple topics. |
| **Matryoshka embeddings** | Embeddings that can be truncated to fewer dimensions while preserving quality, enabling cost/accuracy tradeoffs. |

### 7.2 Configuration Reference

```
  # RAG Configuration (config/rag.yaml)

  ingestion:
    chunk_size_tokens: 512
    chunk_overlap_tokens: 64
    max_chunk_size_tokens: 768
    min_chunk_size_tokens: 64
    batch_size: 100
    supported_formats:
      - pdf
      - docx
      - pptx
      - txt
      - md
      - epub

  embedding:
    model: "text-embedding-3-small"
    dimensions: 1536
    batch_size: 512
    max_retries: 3
    retry_delay_seconds: 2

  retrieval:
    default_top_k: 5
    max_top_k: 20
    query_rewrite_enabled: true
    multi_hop_enabled: true
    multi_hop_max_sub_queries: 3

  reranking:
    semantic_weight: 0.40
    grade_match_weight: 0.15
    curriculum_match_weight: 0.15
    source_priority_weight: 0.15
    freshness_weight: 0.10
    content_type_weight: 0.05

  chromadb:
    host: "localhost"
    port: 8000
    collection_name: "educational_content"
    assessment_collection: "assessment_content"
    hnsw_construction_ef: 200
    hnsw_search_ef: 100
    hnsw_M: 16
    distance_metric: "cosine"

  confidence:
    high_threshold: 0.80
    medium_threshold: 0.60
    low_threshold: 0.40

  freshness:
    stem_decay_months: 48
    humanities_decay_months: 72
    math_decay_months: 120
    current_events_decay_months: 6
    floor_score: 0.05

  maintenance:
    garbage_collection_schedule: "monthly"
    freshness_recalculation_schedule: "weekly"
    full_reindex_on_model_change: true
```

### 7.3 Performance Targets

| Metric | Target | Notes |
|--------|--------|-------|
| Ingestion throughput | 100 pages/minute | Background processing |
| Query-to-retrieval latency | < 300ms | Vector search + re-ranking |
| End-to-end RAG response | < 2 seconds | Including LLM generation |
| Retrieval Recall@5 | > 90% | Correct passage in top 5 results |
| Retrieval Precision@5 | > 70% | Fraction of top 5 that are relevant |
| Knowledge base capacity | 1M+ chunks | Sufficient for large institution |
| Concurrent retrieval queries | 100/second | Peak load handling |

### 7.4 Error Handling

| Error Scenario | Handling Strategy |
|---------------|-------------------|
| ChromaDB unreachable | Retry 3x with backoff, then fall back to LLM general knowledge with disclaimer |
| Embedding API rate limited | Queue and retry with exponential backoff; cache embeddings aggressively |
| Document parsing failure | Log error, notify uploader, skip document, continue with remaining |
| Empty retrieval results | Trigger knowledge gap response (Section 3.7) |
| Ingestion timeout | Retry the job; if repeated failure, flag document for manual review |
| Metadata missing/invalid | Use defaults where possible; require subject and grade_level as mandatory |

---

*Document Version History*

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | Feb 2026 | AGI Education Team | Initial feature design |

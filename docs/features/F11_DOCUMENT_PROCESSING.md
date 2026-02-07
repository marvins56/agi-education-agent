# Feature 11: Document Upload & Processing

## Overview

Teachers upload curriculum content -- PDFs, slide decks, textbook chapters, YouTube lectures, web articles -- and the system processes it into structured, indexed knowledge that powers the RAG-based tutoring engine. This is the primary content ingestion pipeline for EduAGI. Without it, the AI tutor has nothing domain-specific to teach from.

**Priority:** Critical (P0)
**Status:** Design Phase
**Dependencies:** RAG System (F6), Teacher Dashboard (F13), Storage Infrastructure
**Stakeholders:** Teachers, Curriculum Coordinators, System Administrators

---

## Student & Teacher Perspective

### Teacher's Experience

Ms. Rodriguez teaches AP Biology. She has 47 PDF chapters, 12 PowerPoint presentations, 6 YouTube lecture links, and a Google Drive folder with worksheets. She logs into EduAGI, navigates to Content Management, drags her files into the upload zone, pastes her YouTube URLs, and connects her Google Drive. She watches real-time progress bars as each document is processed. The system auto-detects "Biology > AP Biology > Cell Biology > Mitosis" as tags. She adjusts one tag, previews the extracted text for a scanned handout (the OCR caught everything), and clicks "Publish to Class." Within minutes, her students can ask the AI tutor questions grounded in her exact curriculum.

### Student's Experience

Marcus asks the AI tutor: "Explain the phases of mitosis using the diagrams from chapter 7." The tutor responds with an explanation that references a specific diagram Ms. Rodriguez uploaded, because the document processing pipeline extracted that diagram, generated an AI description of it, and indexed it alongside the surrounding text. Marcus never interacts with the upload system directly -- he just benefits from richer, curriculum-aligned answers.

---

## Upload Flow

### Entry Points

```
+------------------------------------------------------------------+
|                    CONTENT UPLOAD INTERFACE                        |
+------------------------------------------------------------------+
|                                                                    |
|  +------------------+  +------------------+  +------------------+ |
|  |   DRAG & DROP    |  |   FILE BROWSER   |  |   URL IMPORT     | |
|  |                  |  |                  |  |                  | |
|  |  Drop files or   |  |  Browse local    |  |  Paste YouTube,  | |
|  |  folders here    |  |  filesystem      |  |  web URLs, or    | |
|  |                  |  |                  |  |  article links   | |
|  +------------------+  +------------------+  +------------------+ |
|                                                                    |
|  +------------------+  +------------------+  +------------------+ |
|  |  GOOGLE DRIVE    |  |  ONEDRIVE        |  |  BULK CSV        | |
|  |                  |  |                  |  |                  | |
|  |  Connect & pick  |  |  Connect & pick  |  |  Upload CSV of   | |
|  |  files/folders   |  |  files/folders   |  |  URLs to process | |
|  +------------------+  +------------------+  +------------------+ |
|                                                                    |
+------------------------------------------------------------------+
```

### Drag-and-Drop Upload

- Accept single files, multiple files, and entire folder structures
- Preserve folder hierarchy as organizational metadata
- Show file type icons and size estimates before upload begins
- Validate file types client-side before initiating transfer
- Support resume on interrupted uploads via chunked upload protocol (tus.io)
- Maximum file size: 200MB per file, 2GB per batch
- Maximum files per batch: 500

### URL Import

- YouTube links: extract transcript via YouTube Data API, download thumbnail
- Web URLs: fetch page content via headless browser, extract main article text
- Google Scholar links: extract paper metadata and content
- Wikipedia links: extract structured article content with section headings
- Validation: check URL is reachable, detect paywalled content, warn on ephemeral content

### Cloud Drive Import

- Google Drive: OAuth2 connection, folder browser, selective sync
- OneDrive: OAuth2 connection, folder browser, selective sync
- Maintain sync link: optionally re-process when source file changes
- Show storage quota impact before confirming import

---

## Supported Formats

| Format | Extension(s) | Processing Method | Notes |
|--------|-------------|-------------------|-------|
| PDF (digital) | .pdf | Text extraction + layout analysis | Preserves headings, lists, tables |
| PDF (scanned) | .pdf | OCR pipeline | Detects scanned vs digital automatically |
| Word | .docx, .doc | XML parsing / LibreOffice conversion | Extracts images, tables, formatting |
| PowerPoint | .pptx, .ppt | Slide-by-slide extraction | Speaker notes included, images described |
| Plain Text | .txt | Direct ingestion | Minimal processing needed |
| Markdown | .md | Parse to AST then extract | Preserves structure natively |
| EPUB | .epub | Unzip + HTML parsing | Chapter-aware extraction |
| HTML | .html, .htm | DOM parsing + boilerplate removal | Uses readability algorithm |
| Rich Text | .rtf | Convert via LibreOffice | Formatting preserved |
| CSV/Excel | .csv, .xlsx | Table-aware extraction | Each sheet processed separately |
| Images | .png, .jpg, .webp | OCR + image description | For photographed worksheets |
| YouTube | URL | Transcript API + audio fallback | Timestamped segments |
| Web Page | URL | Headless fetch + readability | Main content extraction |
| LaTeX | .tex | Parse to structured text | Math equations preserved as LaTeX |

---

## Processing Pipeline

### High-Level Flow

```
                         DOCUMENT UPLOAD & PROCESSING PIPELINE
                         =====================================

  +-----------+     +-------------+     +----------------+     +---------------+
  |  TEACHER  |---->|   UPLOAD    |---->|   VALIDATION   |---->|   ROUTING     |
  |  UPLOADS  |     |   SERVICE   |     |   & QUEUING    |     |   ENGINE      |
  +-----------+     +-------------+     +----------------+     +---------------+
                          |                    |                       |
                          v                    v                       |
                    +-----------+      +---------------+              |
                    |  STORAGE  |      |  VIRUS SCAN   |              |
                    |  (Raw)    |      |  + MODERATION |              |
                    +-----------+      +---------------+              |
                                                                      |
                    +--------------------------------------------------+
                    |                    |                    |
                    v                    v                    v
            +-------------+    +--------------+    +-----------------+
            |   TEXT       |    |   MEDIA      |    |   URL           |
            |   PIPELINE   |    |   PIPELINE   |    |   PIPELINE      |
            |              |    |              |    |                 |
            | PDF, DOCX,   |    | Images,      |    | YouTube, Web   |
            | PPTX, TXT,   |    | Diagrams,    |    | Articles,      |
            | MD, EPUB     |    | Scanned docs |    | Scholar        |
            +------+-------+    +------+-------+    +--------+-------+
                   |                   |                      |
                   v                   v                      v
            +-------------+    +--------------+    +-----------------+
            | Text        |    | OCR Engine   |    | Content Fetcher |
            | Extraction  |    | + Image      |    | + Transcript    |
            |             |    | Description  |    | Extractor       |
            +------+------+    +------+-------+    +--------+-------+
                   |                   |                      |
                   +-------------------+----------------------+
                                       |
                                       v
                            +---------------------+
                            |   CHUNKING ENGINE   |
                            |                     |
                            | - Semantic chunking |
                            | - Sliding window    |
                            | - Section-aware     |
                            +----------+----------+
                                       |
                                       v
                            +---------------------+
                            |   ENRICHMENT        |
                            |                     |
                            | - Auto-tagging      |
                            | - Quality scoring   |
                            | - Entity extraction |
                            | - Summary gen       |
                            +----------+----------+
                                       |
                                       v
                            +---------------------+
                            |   EMBEDDING &       |
                            |   INDEXING           |
                            |                     |
                            | - Vector embeddings |
                            | - Full-text index   |
                            | - Metadata index    |
                            +----------+----------+
                                       |
                                       v
                            +---------------------+
                            |   RAG SYSTEM        |
                            |   (Feature 6)       |
                            |                     |
                            | Ready for student   |
                            | queries             |
                            +---------------------+
```

### Stage 1: Upload & Validation

1. **Client-side validation**: File type check, size check, duplicate name detection
2. **Chunked upload**: Files uploaded in 5MB chunks via tus protocol for reliability
3. **Server-side validation**: MIME type verification (not just extension), magic byte check
4. **Virus scanning**: ClamAV scan on raw file before any processing
5. **Content moderation pre-check**: Flag suspicious filenames, check against known harmful content hashes
6. **Queue entry**: File metadata written to processing queue with priority (teacher-initiated = high, background sync = low)

### Stage 2: Routing

The routing engine inspects the file type and dispatches to the appropriate processing pipeline:

```
ROUTING DECISION TREE
=====================

File received
  |
  +-- Is it a URL?
  |     |
  |     +-- YouTube URL? ---------> YouTube Pipeline
  |     +-- Web URL? -------------> Web Scraping Pipeline
  |     +-- Google Scholar URL? --> Scholar Pipeline
  |
  +-- Is it an image file?
  |     |
  |     +-- Yes ------------------> OCR + Image Description Pipeline
  |
  +-- Is it a PDF?
  |     |
  |     +-- Contains selectable text? --> Text PDF Pipeline
  |     +-- No selectable text? -------> Scanned PDF Pipeline (OCR)
  |     +-- Mixed? --------------------> Hybrid Pipeline
  |
  +-- Is it DOCX/PPTX/EPUB?
  |     |
  |     +-- Yes ------------------> Structured Document Pipeline
  |
  +-- Is it TXT/MD/LaTeX?
  |     |
  |     +-- Yes ------------------> Plain Text Pipeline
  |
  +-- Is it CSV/XLSX?
        |
        +-- Yes ------------------> Tabular Data Pipeline
```

### Stage 3: Text Extraction

**For PDFs (digital):**
- Extract text with positional information (bounding boxes)
- Detect and preserve document structure: headings, paragraphs, lists, footnotes
- Extract embedded images and their captions
- Detect and extract tables with row/column structure
- Preserve reading order (multi-column layouts handled)
- Extract metadata: title, author, creation date, page count

**For DOCX:**
- Parse XML structure for headings, paragraphs, lists, tables
- Extract embedded images with alt-text
- Preserve formatting hierarchy (Heading 1 > Heading 2 > Body)
- Handle track changes (use accepted version)
- Extract comments as annotation metadata

**For PPTX:**
- Process slide-by-slide: title, bullet points, speaker notes
- Extract images and diagrams from each slide
- Preserve slide ordering and section grouping
- Extract chart data when possible
- Create per-slide and full-presentation text representations

**For YouTube:**
- Attempt official transcript via YouTube Data API v3
- Fallback: audio extraction + Whisper transcription
- Segment transcript by natural topic breaks (not just timestamps)
- Extract video metadata: title, description, channel, duration, chapter markers
- Download and store thumbnail for reference

### Stage 4: OCR Pipeline (for Scanned Documents)

```
SCANNED DOCUMENT OCR FLOW
==========================

  +----------------+     +------------------+     +----------------+
  | Scanned Page   |---->| Pre-processing   |---->| OCR Engine     |
  | (Image)        |     |                  |     |                |
  +----------------+     | - Deskew         |     | - Character    |
                         | - Denoise        |     |   recognition  |
                         | - Binarize       |     | - Layout       |
                         | - Contrast       |     |   analysis     |
                         |   enhancement    |     | - Table detect |
                         +------------------+     +-------+--------+
                                                          |
                                                          v
                                                  +----------------+
                                                  | Post-process   |
                                                  |                |
                                                  | - Spell check  |
                                                  | - Confidence   |
                                                  |   scoring      |
                                                  | - Layout       |
                                                  |   reconstruction|
                                                  +----------------+
```

- Pre-process images: deskew, denoise, adaptive binarization, contrast enhancement
- Run OCR with confidence scores per word
- Flag low-confidence regions for teacher review
- Reconstruct document layout from OCR bounding boxes
- Handle multi-language documents (detect language per region)

### Stage 5: Image & Diagram Extraction

- Extract embedded images from documents
- For each image, generate an AI description using a vision model (GPT-4V, Claude Vision, or similar)
- Detect diagram types: flowchart, graph, table, photograph, illustration, chart
- For charts: attempt to extract underlying data
- For diagrams: generate structured text description of relationships
- Store both the raw image and its text description for RAG indexing
- Link images to their surrounding text context

### Stage 6: Table Extraction

- Detect tables in PDFs via layout analysis
- Detect tables in images via OCR + structure recognition
- Extract to structured format (rows, columns, headers, merged cells)
- Generate natural language summary of table contents
- Store both structured data and natural language representation
- Handle complex tables: merged cells, nested headers, spanning rows

### Stage 7: Chunking

```
CHUNKING STRATEGY
=================

Document Text
     |
     v
+-----------------------+
| Structure-Aware Split |  <-- First: split by headings, sections, chapters
+-----------+-----------+
            |
            v
+-----------------------+
| Semantic Chunking     |  <-- Within sections: split at semantic boundaries
+-----------+-----------+     (paragraph breaks, topic shifts)
            |
            v
+-----------------------+
| Size Enforcement      |  <-- Ensure chunks are 200-800 tokens
+-----------+-----------+     (split large, merge small)
            |
            v
+-----------------------+
| Overlap Addition      |  <-- Add 50-token overlap between consecutive chunks
+-----------+-----------+
            |
            v
+-----------------------+
| Metadata Attachment   |  <-- Attach: source doc, page number, section title,
+-----------------------+     heading hierarchy, position in document
```

- **Section-aware chunking**: Respect document structure. Never split mid-sentence, prefer splitting at paragraph or section boundaries
- **Semantic chunking**: Use embedding similarity to detect topic shifts within sections
- **Sliding window overlap**: 50-token overlap between consecutive chunks ensures context continuity
- **Target chunk size**: 200-800 tokens (configurable per content type)
- **Metadata per chunk**: Source document ID, page number(s), section heading hierarchy, position index, preceding/following chunk IDs

### Stage 8: Enrichment

**Auto-Tagging:**
- Use LLM to classify each document by: subject area, grade level, specific topic(s), difficulty level, content type (lecture, worksheet, reference, practice problems)
- Cross-reference with curriculum standards databases (Common Core, AP, IB, state standards)
- Detect prerequisite topics mentioned in the content
- Extract key terms and concepts for a document-level glossary

**Content Quality Scoring:**
- Readability score (Flesch-Kincaid, appropriate for detected grade level?)
- Completeness score (does it cover the tagged topic adequately?)
- OCR confidence score (for scanned documents)
- Extraction quality score (did we preserve structure accurately?)
- Flag: needs teacher review if any score falls below threshold

**Entity Extraction:**
- Key terms and definitions
- Named entities (people, places, scientific terms, historical events)
- Mathematical formulas and equations
- Cross-references to other documents or external resources

### Stage 9: Embedding & Indexing

- Generate vector embeddings for each chunk using the project's embedding model
- Store embeddings in the vector database (used by RAG system, Feature 6)
- Create full-text search index entries for keyword search
- Index metadata for filtered search (by subject, grade, topic, teacher, date)
- Create document-level summary embedding for coarse-grained retrieval

---

## Content Moderation

### Moderation Pipeline

```
CONTENT MODERATION FLOW
========================

  Uploaded Content
        |
        v
  +------------------+     PASS     +-------------------+
  | Hash Check       |------------>| Text Moderation    |
  | (Known harmful   |             | (LLM classifier)   |
  |  content DB)     |             |                    |
  +--------+---------+             | - Inappropriate    |
           |                       | - Violent          |
           | FLAGGED               | - Hate speech      |
           v                       | - Age-inappropriate|
  +------------------+             +--------+-----------+
  | REJECT &         |                      |
  | NOTIFY ADMIN     |              PASS    |  FLAGGED
  +------------------+                |     |
                                      v     v
                              +-----------+  +------------------+
                              | PROCEED   |  | QUARANTINE       |
                              | to next   |  | + NOTIFY TEACHER |
                              | stage     |  | & ADMIN          |
                              +-----------+  +------------------+
```

- **Stage 1 - Hash check**: Compare file hash against databases of known harmful content (PhotoDNA, CSAM hash databases)
- **Stage 2 - Text moderation**: Run extracted text through moderation classifier. Flag content that is violent, sexually explicit, contains hate speech, or is age-inappropriate for the tagged grade level
- **Stage 3 - Image moderation**: Run extracted images through image safety classifier
- **Quarantine**: Flagged content is not indexed. Teacher is notified with explanation. Admin can review and override
- **Appeals**: Teacher can request admin review of false positives
- **Audit log**: All moderation decisions logged for compliance

---

## Progress Tracking

### Real-Time Processing Status

Teachers see a detailed progress view for each uploaded document:

```
PROCESSING STATUS DISPLAY
==========================

+------------------------------------------------------------------+
|  Cell_Biology_Chapter7.pdf                                        |
|                                                                    |
|  [=============================>          ] 72%                    |
|                                                                    |
|  Step 1: Upload              [COMPLETE]     00:03                 |
|  Step 2: Virus Scan          [COMPLETE]     00:01                 |
|  Step 3: Text Extraction     [COMPLETE]     00:12                 |
|  Step 4: Image Extraction    [COMPLETE]     00:08                 |
|  Step 5: Table Extraction    [COMPLETE]     00:05                 |
|  Step 6: OCR (3 pages)       [IN PROGRESS]  00:15 (est. 00:06)   |
|  Step 7: Chunking            [PENDING]      --                    |
|  Step 8: Auto-Tagging        [PENDING]      --                    |
|  Step 9: Embedding           [PENDING]      --                    |
|  Step 10: Indexing            [PENDING]      --                    |
|                                                                    |
|  Extracted: 42 pages, 3 tables, 7 images, 3 scanned pages        |
|  Auto-detected: Biology > Cell Biology > Mitosis (Grade 11)      |
|                                                                    |
|  [ Preview Extracted Text ]  [ Cancel Processing ]                |
+------------------------------------------------------------------+
```

- WebSocket-based real-time updates (no polling)
- Per-file progress with estimated time remaining
- Aggregate batch progress ("Processing 47 files: 31 complete, 2 in progress, 14 queued")
- Email/notification when batch processing completes
- Error reporting: if a file fails, show specific error and suggest resolution

---

## Sub-Features

### Preview Before Indexing

- After text extraction and before embedding/indexing, teacher can preview all extracted content
- Side-by-side view: original document on left, extracted text on right
- Highlight OCR confidence issues (low-confidence words shown in yellow)
- Teacher can approve, edit, or reject before content enters the RAG system
- Batch approve option for large uploads

### Edit Extracted Text

- Rich text editor for correcting OCR errors or extraction artifacts
- Inline diff view showing changes from original extraction
- Spell-check and grammar check on extracted text
- Changes are versioned (can revert to original extraction)
- Per-chunk editing: teachers can fix specific sections without re-processing entire document

### Manual Tag Override

- Auto-detected tags shown as editable pills/chips
- Teacher can add, remove, or modify any tag
- Suggest related tags as teacher types
- Save custom tag presets for repeated use ("All my AP Bio Chapter uploads get these tags")
- Override persists through re-processing (if document is updated)

### Version History

- Every re-upload or edit creates a new version
- Diff view between versions (what changed in the extracted content)
- RAG system uses latest version by default
- Teacher can pin a specific version as the "active" version
- Old versions retained for 1 year, then archived

### Bulk Import from Google Drive / OneDrive

```
CLOUD DRIVE IMPORT FLOW
========================

  +-------------------+     +------------------+     +------------------+
  | Teacher clicks    |---->| OAuth2 Flow      |---->| Folder Browser   |
  | "Import from      |     | (one-time auth)  |     | (tree view of    |
  | Google Drive"     |     |                  |     |  drive contents) |
  +-------------------+     +------------------+     +--------+---------+
                                                              |
                                                              v
                                                     +-----------------+
                                                     | Teacher selects |
                                                     | files/folders   |
                                                     +--------+--------+
                                                              |
                                                              v
                                                     +-----------------+
                                                     | Preview:        |
                                                     | - 23 files      |
                                                     | - 145 MB total  |
                                                     | - 2 unsupported |
                                                     |   (skipped)     |
                                                     +--------+--------+
                                                              |
                                                              v
                                                     +-----------------+
                                                     | Download &      |
                                                     | enter standard  |
                                                     | processing      |
                                                     | pipeline        |
                                                     +-----------------+
```

- Folder structure preserved as organizational tags
- Option for continuous sync (re-process when source changes)
- Shared drive support (school-wide resource folders)
- Selective sync: choose specific folders, file types, or date ranges

### Content Quality Scoring

Each processed document receives a quality score:

| Dimension | Scoring Criteria | Weight |
|-----------|-----------------|--------|
| Extraction Fidelity | OCR confidence, structure preservation, completeness | 30% |
| Readability | Grade-appropriate language, Flesch-Kincaid score | 20% |
| Topic Coverage | How thoroughly it covers the tagged topic(s) | 20% |
| Curriculum Alignment | Match to curriculum standards for the class | 15% |
| Freshness | How recent/current the content is | 10% |
| Accessibility | Alt-text for images, clear structure, no jargon without definition | 5% |

- Score displayed as a 1-5 star rating with breakdown available on click
- Documents below 2 stars flagged for teacher review
- Aggregate scores per topic show "content gap" areas (topics with low coverage or low quality)

---

## Service Comparison: Document Parsing

### Unstructured.io

| Aspect | Details |
|--------|---------|
| **Approach** | Open-source library with hosted API option |
| **Pros** | Broad format support, active community, partitioning strategies, good table extraction, self-hostable |
| **Cons** | Can be slow on large PDFs, API costs at scale, some formats need additional dependencies |
| **Best For** | General-purpose document processing where format variety is high |
| **Cost** | Free (self-hosted), $0.01-0.05 per page (hosted API) |

### LlamaParse

| Aspect | Details |
|--------|---------|
| **Approach** | LLM-powered document parsing from LlamaIndex |
| **Pros** | Excellent at understanding document structure, good with complex layouts, multimodal parsing, great table handling |
| **Cons** | Requires API calls (cost), slower than rule-based parsers, relatively new |
| **Best For** | Complex documents with mixed content types, academic papers, textbooks |
| **Cost** | ~$0.003 per page (API) |

### Apache Tika

| Aspect | Details |
|--------|---------|
| **Approach** | Java-based content detection and extraction framework |
| **Pros** | Extremely broad format support (1000+ types), battle-tested, self-hosted, metadata extraction |
| **Cons** | Java dependency, less sophisticated structure preservation, basic table extraction |
| **Best For** | High-volume processing where format detection matters most |
| **Cost** | Free (open-source, self-hosted) |

### Custom Parsers (per format)

| Aspect | Details |
|--------|---------|
| **Approach** | Use best-of-breed library per format (PyMuPDF for PDF, python-docx for DOCX, etc.) |
| **Pros** | Maximum control, optimized per format, no vendor dependency |
| **Cons** | Significant development effort, must maintain each parser, format edge cases |
| **Best For** | When specific formats dominate and you need precise control |
| **Cost** | Development time only |

### Recommendation

Use a **hybrid approach**:
- **LlamaParse** for complex documents (textbooks, academic papers, scanned content) where structural understanding matters most
- **Unstructured.io** as the general-purpose fallback for standard formats
- **Custom parsers** for YouTube transcripts and web URL fetching (these are not traditional document parsing)
- **Apache Tika** for format detection and metadata extraction as a pre-processing step

---

## Service Comparison: OCR

### Tesseract OCR

| Aspect | Details |
|--------|---------|
| **Pros** | Free, open-source, self-hosted, supports 100+ languages, active development |
| **Cons** | Lower accuracy than cloud services on degraded scans, requires pre-processing for best results |
| **Accuracy** | ~85-95% on clean scans, ~70-85% on degraded |
| **Cost** | Free |
| **Latency** | Moderate (1-3 sec/page depending on hardware) |

### Google Cloud Vision OCR

| Aspect | Details |
|--------|---------|
| **Pros** | High accuracy, handwriting recognition, layout detection, 200+ languages |
| **Cons** | Cloud dependency, per-request cost, data leaves your infrastructure |
| **Accuracy** | ~95-99% on clean scans, ~85-95% on degraded |
| **Cost** | $1.50 per 1000 pages |
| **Latency** | ~1-2 sec/page |

### AWS Textract

| Aspect | Details |
|--------|---------|
| **Pros** | Excellent table and form extraction, key-value pair detection, query-based extraction |
| **Cons** | AWS lock-in, higher cost, data leaves your infrastructure |
| **Accuracy** | ~95-99%, especially strong on structured documents |
| **Cost** | $1.50 per 1000 pages (text), $15 per 1000 pages (tables/forms) |
| **Latency** | ~2-5 sec/page |

### Azure Document Intelligence (formerly Form Recognizer)

| Aspect | Details |
|--------|---------|
| **Pros** | Pre-built models for common document types, excellent layout analysis, custom model training |
| **Cons** | Azure lock-in, complex pricing tiers, data leaves your infrastructure |
| **Accuracy** | ~95-99%, best-in-class for structured forms |
| **Cost** | $1.00 per 1000 pages (read), $10 per 1000 pages (layout) |
| **Latency** | ~1-3 sec/page |

### Recommendation

Use a **tiered approach**:
1. **Tesseract** as the default (free, self-hosted, good enough for most clean scans)
2. **Google Cloud Vision** or **Azure Document Intelligence** as a fallback when Tesseract confidence is below 85%
3. **AWS Textract** specifically for documents detected as forms or heavy-table content

---

## Service Comparison: Object Storage

### Amazon S3

| Aspect | Details |
|--------|---------|
| **Pros** | Industry standard, massive ecosystem, lifecycle policies, versioning, cross-region replication |
| **Cons** | Egress costs, complex pricing, vendor lock-in |
| **Cost** | ~$0.023/GB/month storage, $0.09/GB egress |
| **Best For** | Production systems already on AWS |

### MinIO

| Aspect | Details |
|--------|---------|
| **Pros** | S3-compatible API, self-hosted, no egress costs, fast, Kubernetes-native |
| **Cons** | Must manage infrastructure, no global CDN built-in |
| **Cost** | Free (open-source), infrastructure costs only |
| **Best For** | Self-hosted deployments, data sovereignty requirements, development environments |

### Cloudflare R2

| Aspect | Details |
|--------|---------|
| **Pros** | Zero egress costs, S3-compatible API, global distribution, simple pricing |
| **Cons** | Newer service, smaller ecosystem, no lifecycle policies (yet) |
| **Cost** | $0.015/GB/month storage, $0.00/GB egress |
| **Best For** | Cost-sensitive deployments with high download volume |

### Google Cloud Storage

| Aspect | Details |
|--------|---------|
| **Pros** | Tight integration with Google AI services, strong IAM, multi-regional options |
| **Cons** | Egress costs, vendor lock-in to GCP |
| **Cost** | ~$0.020/GB/month storage, $0.12/GB egress |
| **Best For** | Production systems already on GCP |

### Recommendation

**MinIO** for development and self-hosted deployments. **Cloudflare R2** for production (zero egress costs are significant when serving document previews to teachers and content to the processing pipeline). Use S3-compatible API throughout so the storage backend can be swapped without code changes.

---

## MCP Servers

The following Model Context Protocol servers could assist with document processing:

| MCP Server | Purpose | How It Helps |
|------------|---------|-------------|
| **Filesystem MCP** | Local file access | Allow the AI to read and process uploaded files directly from local storage |
| **Google Drive MCP** | Google Drive integration | Browse, search, and download files from connected Google Drive accounts |
| **Fetch MCP** | URL content retrieval | Fetch and process web URLs, articles, and online resources for the URL import pipeline |
| **Memory MCP** | Persistent knowledge storage | Store processing metadata, document relationships, and extraction results |
| **Brave Search MCP** | Web search | Find additional context for uploaded content, verify facts, find related resources |
| **Puppeteer MCP** | Headless browser | Render JavaScript-heavy web pages for content extraction from dynamic URLs |
| **SQLite MCP** | Database operations | Query and manage the document metadata database, processing queue, and tag indexes |

---

## Data Model

### Document Record

```
Document {
  id:                 UUID
  teacher_id:         UUID (FK -> User)
  class_ids:          UUID[] (FK -> Class, many-to-many)

  // Source
  original_filename:  String
  source_type:        Enum (upload, google_drive, onedrive, url, youtube)
  source_url:         String? (for URL/cloud imports)
  storage_key:        String (path in object storage)
  file_size_bytes:    Integer
  mime_type:          String

  // Processing
  status:             Enum (queued, processing, review, indexed, failed, quarantined)
  processing_stage:   String (current stage name)
  processing_progress: Float (0.0 - 1.0)
  processing_started: Timestamp?
  processing_completed: Timestamp?
  error_message:      String?

  // Extracted Content
  extracted_text:     Text (full extracted text, stored separately)
  page_count:         Integer
  image_count:        Integer
  table_count:        Integer
  chunk_count:        Integer

  // Tags & Classification
  auto_tags:          JSON { subject, grade_level, topics[], difficulty, content_type }
  manual_tags:        JSON (teacher overrides)
  effective_tags:     JSON (computed: manual overrides auto)
  curriculum_standards: String[] (matched standard IDs)

  // Quality
  quality_score:      Float (0.0 - 5.0)
  quality_breakdown:  JSON { extraction_fidelity, readability, coverage, alignment, freshness, accessibility }
  ocr_confidence:     Float? (average OCR confidence, if applicable)
  moderation_status:  Enum (passed, flagged, rejected, override_approved)

  // Versioning
  version:            Integer
  previous_version_id: UUID?

  // Timestamps
  created_at:         Timestamp
  updated_at:         Timestamp
}
```

### Chunk Record

```
Chunk {
  id:                 UUID
  document_id:        UUID (FK -> Document)

  // Content
  text:               Text
  token_count:        Integer

  // Position
  chunk_index:        Integer (order within document)
  page_numbers:       Integer[] (source pages)
  section_heading:    String? (nearest heading)
  heading_hierarchy:  String[] (e.g., ["Chapter 7", "Mitosis", "Prophase"])

  // Relationships
  previous_chunk_id:  UUID?
  next_chunk_id:      UUID?

  // Embedding
  embedding_vector:   Float[] (stored in vector DB)
  embedding_model:    String (model used)

  // Metadata
  has_table:          Boolean
  has_image:          Boolean
  image_descriptions: String[]

  created_at:         Timestamp
}
```

---

## Connections to Other Features

```
FEATURE CONNECTIONS
====================

  +-------------------+
  | F13: Teacher      |<---- Teacher initiates uploads,
  | Dashboard         |      manages content, reviews
  +--------+----------+      extracted text, overrides tags
           |
           v
  +-------------------+
  | F11: Document     |
  | Processing        |
  | (THIS FEATURE)    |
  +--------+----------+
           |
           +----------------+-----------------+
           |                |                 |
           v                v                 v
  +--------------+  +---------------+  +--------------+
  | F6: RAG      |  | F12: Analytics|  | F14: Learning|
  | System       |  | Dashboard     |  | Path         |
  |              |  |               |  |              |
  | Chunks &     |  | Content       |  | Topics from  |
  | embeddings   |  | coverage      |  | auto-tags    |
  | power AI     |  | metrics,      |  | inform       |
  | responses    |  | upload stats  |  | prerequisite |
  +--------------+  +---------------+  | graph        |
                                       +--------------+
```

- **Teacher Dashboard (F13)**: Primary UI surface for initiating and managing uploads. Upload status, content library, and tag management all live within the teacher dashboard.
- **RAG System (F6)**: Direct consumer of processed chunks and embeddings. The entire purpose of document processing is to feed high-quality, structured content into the RAG pipeline.
- **Analytics Dashboard (F12)**: Receives content coverage metrics (which topics have strong/weak content coverage), upload volume statistics, and processing success rates.
- **Learning Path (F14)**: Auto-detected topics and curriculum standard mappings from document processing feed into the prerequisite graph and topic inventory that the learning path engine uses.

---

## Error Handling

| Error Scenario | Detection | Response |
|---------------|-----------|----------|
| Corrupt file | Parser throws exception | Notify teacher, suggest re-upload, log error |
| Unsupported format | MIME type check fails | Immediate client-side rejection with supported format list |
| Password-protected PDF | Parser detects encryption | Prompt teacher for password or skip |
| Very large file (>200MB) | Size check | Reject with suggestion to split or compress |
| OCR failure (unreadable scan) | OCR confidence < 50% | Flag for teacher review, suggest better scan |
| Extraction produces empty text | Post-extraction check | Alert teacher, offer manual text entry |
| Processing timeout (>30 min) | Queue monitor | Retry once, then alert teacher with partial results |
| Storage full | Storage quota check | Alert admin, pause processing queue |
| Moderation flag | Moderation pipeline | Quarantine content, notify teacher and admin |
| Duplicate content | Content hash comparison | Warn teacher, offer to link existing or re-process |

---

## Performance Requirements

| Metric | Target |
|--------|--------|
| Upload speed | Limited by user's connection; server accepts at network speed |
| Processing time (10-page PDF, digital) | < 30 seconds |
| Processing time (10-page PDF, scanned) | < 2 minutes |
| Processing time (1-hour YouTube video) | < 5 minutes |
| Processing time (web URL) | < 15 seconds |
| Concurrent processing jobs | 50+ (horizontally scalable workers) |
| Queue wait time (95th percentile) | < 5 minutes |
| Storage retrieval latency | < 100ms for metadata, < 500ms for full document |
| Maximum documents per teacher | 10,000 |
| Maximum total storage per school | 500 GB (configurable) |

---

## Security Considerations

- All uploaded files scanned for malware before processing
- Files stored encrypted at rest (AES-256)
- Files transmitted encrypted in transit (TLS 1.3)
- Temporary processing files cleaned up within 1 hour of processing completion
- Access control: only the uploading teacher and school admins can view/manage uploaded documents
- Students never see raw documents -- only AI-generated responses grounded in document content
- Audit log of all uploads, deletions, and access events
- FERPA compliance: student data never stored in document processing pipeline (documents are curriculum content, not student data)
- GDPR: right to deletion -- deleting a document removes all chunks, embeddings, and cached content

---

## Open Questions

1. Should we support real-time collaborative editing of extracted text (like Google Docs) or is a simpler edit-and-save sufficient for v1?
2. How do we handle copyright-protected textbook content? Should we add a copyright acknowledgment step to the upload flow?
3. Should cloud drive sync be one-way (import only) or two-way (push corrections back to Drive)?
4. What is the retention policy for raw uploaded files after processing? Keep forever, or archive/delete after a configurable period?
5. Should students be able to suggest documents for their teacher to upload ("I found this helpful resource")?

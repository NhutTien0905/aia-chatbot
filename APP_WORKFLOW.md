# App Workflow — Secure Multi-Modal Insurance Assistant

Tài liệu mô tả chi tiết cách hoạt động của ứng dụng từ đầu đến cuối.

---

## Tổng quan kiến trúc

```
┌──────────────────────────────────────────────────────────────┐
│                   Frontend (Next.js 14)                        │
│  • Upload UI (drag & drop)                                    │
│  • Chat Interface (streaming SSE)                             │
│  • Session management (localStorage)                          │
│  • Theme (dark/light, persist)                                │
│  • Chat history (persist localStorage)                        │
└────────────────────────┬─────────────────────────────────────┘
                         │  REST API + SSE
┌────────────────────────▼─────────────────────────────────────┐
│                   Backend (FastAPI)                            │
│  • Document ingestion pipeline                                │
│  • Hybrid search (Semantic + BM25 + Rerank)                   │
│  • LLM answer generation (streaming)                          │
│  • Session isolation (per-session ChromaDB collection)         │
└────────────────────────┬─────────────────────────────────────┘
                         │
┌────────────────────────▼─────────────────────────────────────┐
│              ChromaDB (Vector Database)                        │
│  • Per-session collections                                    │
│  • Cosine similarity                                          │
│  • Persistent storage on disk                                 │
└──────────────────────────────────────────────────────────────┘
```

---

## 1. Session Management

### Frontend
- Khi user mở app lần đầu → gọi `POST /api/session/create` → nhận UUID
- Lưu session ID vào `localStorage` với TTL 24 giờ
- Mỗi request gửi session ID qua header `X-Session-ID`
- Khi refresh page → đọc session từ localStorage → gọi `GET /api/session/{id}/info` để restore danh sách files
- Chat history lưu trong `localStorage` theo key `chat_history_{session_id}`

### Backend
- Mỗi session có 1 ChromaDB collection riêng: `s_{session_id}`
- Session isolation: User A không thể truy cập data của User B
- Session ID validate bằng UUID regex pattern

---

## 2. Document Upload Pipeline

### Flow tổng quan

```
User chọn file (max 2 files, max 5MB mỗi file)
        │
        ▼
Frontend validate (type, size) → gửi POST /api/upload (multipart)
        │
        ▼
Backend validate (extension, content-type, size)
        │
        ▼
Sanitize filename (chống path traversal)
        │
        ▼
process_document() — orchestrator chính
        │
        ├── Step 1: Extract text
        ├── Step 2: Chunk text
        ├── Step 3: Summarize (token optimization)
        └── Step 4: Embed + Index vào ChromaDB
```

### 2.1. Validation

**Frontend** (`FileUpload.tsx`):
- Allowed types: PDF, DOCX, PNG, JPG/JPEG
- Max size: 5MB per file
- Max files: 2 per upload

**Backend** (`ingestion.py` → `validate_file()`):
- Check file extension: `.pdf`, `.docx`, `.png`, `.jpg`, `.jpeg`
- Check MIME content-type
- Check size ≤ 5MB
- Sanitize filename: remove path separators, control chars, leading dots, limit 255 chars

### 2.2. Text Extraction (Step 1)

| Format | Parser | Thư viện | Output |
|--------|--------|----------|--------|
| PDF | `utils/pdf_parser.py` | PyMuPDF (fitz) | 1 entry per page (max 20 pages) |
| DOCX | `utils/docx_parser.py` | python-docx | 1 entry per section |
| Image | `utils/image_parser.py` | EasyOCR + Pillow | 1 entry (toàn bộ OCR text) |

#### PDF Parser
```python
# Mở PDF từ bytes
doc = fitz.open(stream=file_bytes, filetype="pdf")

# Duyệt từng page (max 20)
for page_num in range(min(len(doc), 20)):
    text = page.get_text("text")
    # → {text, metadata: {filename, page_number, upload_date, source_type: "pdf"}}
```

#### DOCX Parser
```python
# Đọc document
doc = Document(io.BytesIO(file_bytes))

# Gom paragraphs thành sections:
# - Cắt khi gặp Heading style
# - Hoặc cắt khi đủ 10 paragraphs
# → {text, metadata: {filename, section_number, paragraph_range, upload_date, source_type: "docx"}}
```

#### Image Parser (OCR)
```python
# Lazy load EasyOCR reader (English + Vietnamese, CPU mode)
reader = easyocr.Reader(["en", "vi"], gpu=False)

# Mở ảnh → convert RGB → numpy array
image = Image.open(io.BytesIO(file_bytes)).convert("RGB")
img_array = np.array(image)

# Chạy OCR
results = reader.readtext(img_array, detail=1)
full_text = "\n".join([result[1] for result in results])
# → {text, metadata: {filename, page_number: 1, upload_date, source_type: "image"}}
```

### 2.3. Text Chunking (Step 2)

**File**: `services/chunking.py`

**Tham số**:
- `chunk_size`: 500 characters
- `chunk_overlap`: 50 characters

**Thuật toán** — Recursive Character Splitter:
1. Nếu text ≤ 500 chars → trả nguyên (1 chunk)
2. Thử split theo separator ưu tiên: `\n\n` → `\n` → `. ` → `! ` → `? ` → `; `
3. Gom các parts cho đến khi vượt 500 chars → tạo chunk mới
4. Nếu 1 part > 500 chars → recursive split với separator tiếp theo
5. Nếu hết separator → force split theo chunk_size với overlap

**Output**: Mỗi chunk giữ nguyên metadata gốc + thêm `chunk_index`

**Ví dụ**: 1 PDF 10 pages, mỗi page ~2000 chars → ~4 chunks/page → ~40 chunks total

### 2.4. Summarization — Token Optimization (Step 3)

**File**: `services/summarizer.py`

**Logic**:
- Chunks ≤ 1500 chars → giữ nguyên (không summarize)
- Chunks > 1500 chars → gọi LLM để tóm tắt

**LLM Call**:
```
Model: Azure OpenAI (cùng model với chat)
Temperature: 0.0
Max tokens: 500
Prompt: "Summarize concisely, preserve all key facts, numbers, dates, names, policy details"
```

**Kết quả**:
- Text gốc được thay bằng summary (để embedding ngắn hơn, tiết kiệm token)
- `original_text[:500]` lưu trong metadata cho citation tooltip
- Flag `is_summarized: True` trong metadata
- Retry 2 lần với exponential backoff, nếu fail → dùng text gốc

### 2.5. Embedding + Indexing (Step 4)

**File**: `services/vectorstore.py`

**Embedding**:
- Model: Azure OpenAI `text-embedding-3-small`
- Batch size: 20 texts per API call
- Retry: 3 lần với exponential backoff

**ChromaDB Storage**:
- Collection name: `s_{session_id}` (UUID với `-` → `_`)
- Distance metric: cosine similarity
- Mỗi chunk lưu: `id`, `embedding`, `document` (text), `metadata`
- ID format: `{session_id}_{index}_{filename}`

---

## 3. Chat / Query Pipeline

### Flow tổng quan

```
User gửi câu hỏi
        │
        ▼
POST /api/chat (JSON: question, session_id, selected_files)
        │
        ▼
Validate (session_id, sanitize query)
        │
        ▼
Hybrid Search
  ├── Semantic Search (ChromaDB, top-10)
  ├── BM25 Search (in-memory, top-10)
  ├── Reciprocal Rank Fusion (merge)
  └── Cohere Rerank v4 (top-5)
        │
        ▼
Build context prompt (5 chunks with [Source N] labels)
        │
        ▼
LLM Generate (streaming, SSE)
        │
        ▼
Frontend render (token-by-token + citations)
```

### 3.1. Hybrid Search (`services/retrieval.py`)

**Bước 1 — Build BM25 index**:
- Lấy tất cả documents từ ChromaDB collection của session
- Build BM25Okapi index in-memory (tokenize: lowercase + word boundary regex)

**Bước 2 — Semantic Search** (ChromaDB):
- Embed query bằng `text-embedding-3-small`
- Query ChromaDB với cosine similarity, top-10 results
- Nếu có `selected_files` → filter metadata `filename` (where clause)

**Bước 3 — BM25 Search**:
- Tokenize query
- Score tất cả documents, lấy top-10 (score > 0)
- Filter theo `selected_files` nếu có

**Bước 4 — Reciprocal Rank Fusion (RRF)**:
```
score(doc) = Σ 1/(k + rank + 1)    với k = 60
```
- Merge 2 ranked lists (semantic + BM25)
- Sort theo fused score, lấy top-10 candidates

**Bước 5 — Reranking** (Cohere Rerank v4):
- Gửi 10 candidates + query tới Cohere Rerank API (Azure AI)
- Nhận lại top-5 documents sorted by relevance_score
- Fallback: nếu reranker fail → dùng RRF scores, lấy top-5

### 3.2. LLM Answer Generation (`services/llm.py`)

**Context Building**:
```
[Source 1: filename.pdf, Page 3]
<chunk text>

---

[Source 2: filename.pdf, Page 5]
<chunk text>

...
```

**System Prompt** (rules):
1. Chỉ trả lời dựa trên context
2. Nếu không có thông tin → nói "I don't have enough information..."
3. Không hallucinate
4. Cite bằng [1], [2], [3]... mapping với Source numbers
5. Trả lời cùng ngôn ngữ với câu hỏi (EN/VI)
6. Có thể dùng **bold** để nhấn mạnh

**LLM Config**:
- Model: Azure OpenAI (configurable, e.g. GPT-4o)
- Temperature: 0.1 (low creativity, high accuracy)
- Max tokens: 2000
- Streaming: Yes (token-by-token)

### 3.3. Streaming Response (`routers/chat.py`)

**Protocol**: Server-Sent Events (SSE)

**Event types**:
```
data: {"type": "citations", "data": [...]}     ← Gửi citations trước
data: {"type": "token", "data": "word"}        ← Từng token
data: {"type": "hide_citations"}               ← Ẩn citations nếu "I don't know"
data: {"type": "error", "data": "msg"}         ← Lỗi
data: {"type": "done"}                         ← Kết thúc
```

**"I Don't Know" Detection**:
- Sau khi stream xong, check nếu response < 200 chars VÀ chứa IDK phrase
- Nếu đúng → gửi `hide_citations` event → frontend ẩn citations

### 3.4. Frontend Rendering (`ChatInterface.tsx`)

- Nhận SSE events qua `ReadableStream`
- `citations` event → lưu citations array
- `token` event → append vào message content, re-render
- `hide_citations` event → clear citations (LLM không tìm thấy answer)
- `done` event → finalize message

**Citation Display** (`MessageBubble.tsx`):
- Inline: `[1]`, `[2]`... render thành badge tròn xanh với hover tooltip
- Tooltip (portal): hiển thị filename, page, section + source text preview (250 chars)
- Sources list: deduplicate theo file+page, gộp indices (e.g. "1,4")

---

## 4. Document Management

### Delete Document
```
DELETE /api/session/{session_id}/document/{filename}
```
- Tìm tất cả chunks có metadata `filename` match
- Xóa khỏi ChromaDB collection
- Frontend cập nhật UI (remove from list, deselect)

### Delete Session
```
DELETE /api/session/{session_id}
```
- Xóa toàn bộ ChromaDB collection của session

### Session Info
```
GET /api/session/{session_id}/info
```
- Đọc tất cả metadatas từ collection
- Group by filename → trả về danh sách files + num_chunks

---

## 5. Security

| Layer | Measure |
|-------|---------|
| Session | UUID validation (regex), per-session collection isolation |
| Filename | Sanitize: remove path separators, control chars, limit length |
| Query | Sanitize: remove null bytes, trim, limit 2000 chars |
| CORS | Chỉ allow frontend origin (configurable) |
| File | Validate extension + MIME type + size |
| API Keys | Không expose trong response, đọc từ .env |

---

## 6. Frontend State Management

| State | Storage | Lifetime |
|-------|---------|----------|
| Session ID | localStorage | 24 giờ (TTL) |
| Theme (dark/light) | localStorage | Vĩnh viễn |
| Chat history | localStorage (per session) | Cho đến khi clear session |
| Uploaded files | React state + restore từ API | Per page load |
| Selected files | React state | Per page load (auto-select on upload) |

---

## 7. Performance Optimizations

| Optimization | Detail |
|-------------|--------|
| Batch embedding | 20 texts per API call (giảm round trips) |
| Retry + backoff | Exponential backoff cho API calls (embedding, LLM, reranker) |
| Lazy OCR loading | EasyOCR reader chỉ load khi cần (lần đầu dùng) |
| In-memory BM25 | Không cần external service, rebuild mỗi query |
| Streaming SSE | User thấy response ngay, không đợi full generation |
| Summarization | Chunks dài được tóm tắt → embedding ngắn hơn, retrieval tốt hơn |
| ChromaDB persist | Data không mất khi restart server |

---

## 8. Error Handling

| Scenario | Handling |
|----------|----------|
| Upload fail | Trả status "error" per file, không block files khác |
| OCR no text | Trả error "No text could be extracted" |
| Embedding API fail | Retry 3 lần, sau đó raise error |
| Reranker fail | Fallback về RRF scores (graceful degradation) |
| LLM fail | Stream error event → frontend hiển thị error message |
| Summarizer fail | Dùng text gốc (không summarize) |
| Invalid session | HTTP 400 "Invalid session ID format" |
| File too large | HTTP 400 với message cụ thể |

---

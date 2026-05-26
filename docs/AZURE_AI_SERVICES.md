# Giải thích lựa chọn Azure AI Services

## Tổng quan

Dự án sử dụng 3 dịch vụ AI từ Azure để xây dựng pipeline RAG (Retrieval-Augmented Generation) hoàn chỉnh:

| Thành phần | Model | Endpoint |
|---|---|---|
| LLM (sinh câu trả lời) | GPT-5.4 Mini | Azure OpenAI Service |
| Embedding (vector hóa văn bản) | text-embedding-3-large | Azure OpenAI Service |
| Reranker (xếp hạng lại kết quả) | Cohere Rerank v4.0 Fast | Azure AI Services |

---

## 1. LLM — Azure OpenAI GPT-5.4 Mini

### Vai trò trong hệ thống
- Nhận context từ các document chunks đã được retrieve và sinh câu trả lời cho người dùng.
- Hỗ trợ streaming response để cải thiện trải nghiệm người dùng (không phải chờ toàn bộ response).
- Tuân thủ system prompt nghiêm ngặt: chỉ trả lời dựa trên context, trích dẫn nguồn, và từ chối trả lời khi không có thông tin.

### Tại sao chọn Azure OpenAI?

1. **Bảo mật dữ liệu (Data Privacy):** Azure OpenAI cam kết không sử dụng dữ liệu khách hàng để train model. Với domain bảo hiểm chứa thông tin nhạy cảm, đây là yêu cầu bắt buộc.

2. **Enterprise-grade SLA:** Azure cung cấp SLA 99.9% uptime, phù hợp cho ứng dụng production trong ngành bảo hiểm.

3. **Content filtering tích hợp:** Azure OpenAI có hệ thống content safety tự động, giảm rủi ro sinh nội dung không phù hợp.

4. **Regional deployment:** Có thể deploy model ở region gần (Southeast Asia), giảm latency cho người dùng Việt Nam.

5. **Tương thích OpenAI SDK:** Sử dụng cùng SDK `openai` Python, dễ dàng migrate hoặc switch provider nếu cần.

### Tại sao chọn GPT-5.4 Mini thay vì model lớn hơn?

- **Chi phí thấp hơn đáng kể** so với GPT-4o hay GPT-5 full, phù hợp cho use case Q&A với context đã được cung cấp sẵn.
- **Tốc độ response nhanh hơn**, cải thiện trải nghiệm streaming.
- **Đủ năng lực** cho task trích xuất thông tin và trả lời câu hỏi từ context có sẵn — không cần reasoning phức tạp.
- **Hỗ trợ song ngữ Anh-Việt** tốt.

---

## 2. Embedding — Azure OpenAI text-embedding-3-large

### Vai trò trong hệ thống
- Chuyển đổi document chunks và câu hỏi người dùng thành vector để lưu vào ChromaDB.
- Phục vụ semantic search: tìm các chunks có ý nghĩa tương đồng với câu hỏi.

### Tại sao chọn text-embedding-3-large?

1. **Accuracy cao nhất trong dòng embedding-3:** `text-embedding-3-large` đạt MTEB score cao hơn variant small (64.6 vs 62.3), đặc biệt quan trọng khi cần phân biệt chính xác giữa các điều khoản bảo hiểm có nội dung tương tự nhau.

2. **Multilingual quality vượt trội:** Vector 3072 dimensions encode được nhiều semantic nuance hơn, cải thiện đáng kể retrieval accuracy cho tiếng Việt — ngôn ngữ có cấu trúc khác biệt so với tiếng Anh.

3. **Matryoshka Representation Learning:** Hỗ trợ truncate vector dimension (ví dụ xuống 1536 hoặc 256) mà vẫn giữ được phần lớn accuracy, cho phép tối ưu storage sau này nếu cần.

4. **Phù hợp với domain bảo hiểm:** Tài liệu bảo hiểm chứa nhiều thuật ngữ chuyên ngành và các điều khoản có ngữ nghĩa gần nhau. Model lớn hơn phân biệt tốt hơn giữa các khái niệm tương tự (ví dụ: "bồi thường thiệt hại" vs "bồi thường trách nhiệm dân sự").

5. **Cùng endpoint Azure OpenAI:** Không cần setup thêm service riêng, giảm complexity trong infrastructure.

### Tại sao không dùng text-embedding-3-small?

- Với domain bảo hiểm, độ chính xác retrieval quan trọng hơn tiết kiệm chi phí — một chunk sai có thể dẫn đến câu trả lời sai về quyền lợi khách hàng.
- Lượng document nhỏ (max 2 files, 20 pages/file) nên chi phí embedding không đáng kể dù dùng model lớn.
- ChromaDB local xử lý tốt vector 3072 dimensions với dataset size này.

---

## 3. Reranker — Cohere Rerank v4.0 Fast (via Azure AI)

### Vai trò trong hệ thống
- Nhận danh sách candidates từ hybrid search (semantic + BM25 qua Reciprocal Rank Fusion).
- Đánh giá lại relevance của từng candidate so với query gốc.
- Trả về top-K kết quả chính xác nhất để đưa vào LLM context.

### Tại sao cần Reranker?

1. **Cải thiện precision đáng kể:** Embedding search tốt ở recall (tìm được nhiều kết quả liên quan) nhưng không phải lúc nào cũng xếp hạng chính xác. Reranker sử dụng cross-encoder architecture, xem xét query và document cùng lúc, cho relevance score chính xác hơn nhiều.

2. **Bù đắp hạn chế của hybrid search:** RRF (Reciprocal Rank Fusion) kết hợp BM25 + semantic search nhưng chỉ dựa trên rank position. Reranker đánh giá semantic relevance thực sự của từng document.

3. **Giảm noise trong LLM context:** Ít chunks không liên quan = câu trả lời chính xác hơn + ít hallucination hơn + tiết kiệm token.

### Tại sao chọn Cohere Rerank v4.0 Fast?

1. **State-of-the-art performance:** Cohere Rerank v4 là một trong những reranker tốt nhất hiện tại, vượt trội trên các benchmark retrieval.

2. **Variant "Fast":** Tối ưu cho latency thấp, phù hợp với real-time chat application. Trade-off nhỏ về accuracy so với variant full nhưng nhanh hơn đáng kể.

3. **Multilingual:** Hỗ trợ tốt tiếng Việt, quan trọng cho use case bảo hiểm tại Việt Nam.

4. **Deploy trên Azure AI:** Tận dụng cùng hạ tầng Azure, đơn giản hóa networking, billing, và compliance.

5. **Graceful fallback:** Nếu reranker service gặp lỗi, hệ thống tự động fallback về kết quả RRF mà không crash.

---

## Pipeline tổng thể

```
User Query
    │
    ▼
┌─────────────────────────────────────────┐
│         RETRIEVAL (Hybrid Search)        │
│                                          │
│  ┌──────────────┐  ┌──────────────────┐ │
│  │ Semantic      │  │ BM25 (Keyword)   │ │
│  │ (Embedding)   │  │                  │ │
│  └──────┬───────┘  └────────┬─────────┘ │
│         │                    │           │
│         ▼                    ▼           │
│     ┌────────────────────────────┐       │
│     │  Reciprocal Rank Fusion    │       │
│     └─────────────┬──────────────┘       │
│                   │                      │
│                   ▼                      │
│     ┌────────────────────────────┐       │
│     │  Cohere Rerank v4 Fast     │       │
│     │  (Cross-encoder reranking) │       │
│     └─────────────┬──────────────┘       │
│                   │                      │
└───────────────────┼──────────────────────┘
                    │
                    ▼ Top-K chunks
┌─────────────────────────────────────────┐
│         GENERATION (LLM)                 │
│                                          │
│  GPT-5.4 Mini + System Prompt            │
│  → Answer with citations [1], [2]...     │
│  → Streaming response                    │
└─────────────────────────────────────────┘
```

---

## Cấu hình Environment Variables

```env
# Azure OpenAI (LLM + Embedding)
AZURE_OPENAI_ENDPOINT=https://<resource-name>.openai.azure.com/openai/v1
AZURE_OPENAI_API_KEY=<your-api-key>
AZURE_OPENAI_DEPLOYMENT=gpt-5.4-mini
AZURE_OPENAI_EMBEDDING_DEPLOYMENT=text-embedding-3-large

# Reranker (Cohere via Azure AI)
RERANKER_ENDPOINT=https://<resource-name>.services.ai.azure.com/providers/cohere/v2/rerank
RERANKER_API_KEY=<your-reranker-api-key>
RERANKER_MODEL=Cohere-rerank-v4.0-fast
```

---

## Kết luận

Việc chọn Azure AI Services cho cả 3 thành phần (LLM, Embedding, Reranker) mang lại:

1. **Unified platform:** Quản lý tập trung trên Azure Portal, đơn giản hóa monitoring và billing.
2. **Data compliance:** Đáp ứng yêu cầu bảo mật dữ liệu ngành bảo hiểm.
3. **Optimized pipeline:** Mỗi model được chọn phù hợp với vai trò cụ thể — không over-engineer, không under-spec.
4. **Graceful degradation:** Hệ thống có fallback ở mỗi layer (reranker fail → dùng RRF scores, embedding fail → retry with backoff).

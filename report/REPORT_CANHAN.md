# Báo Cáo Cá Nhân — Lab 7: Embedding & Vector Store

**Họ tên:** Bùi Công Hậu
**Nhóm:** khongcoten
**Ngày:** 2026-08-03

> **Nộp 1 bản / sinh viên.** Phần nhóm (lựa chọn tài liệu, thiết kế chiến lược, bộ câu hỏi đánh giá, demo) nộp chung 1 bản trong `REPORT_NHOM.md`. Chi tiết thang điểm: `docs/SCORING.md`.

**Tổng điểm phần cá nhân: 60** = Khởi động (5) + Hướng tiếp cận (10) + Hoàn thiện code (30) + Dự đoán độ tương tự (5) + Kết quả truy xuất của tôi (10).

---

## 1. Khởi động (Warm-up) — Cá nhân (5 điểm)

### Độ tương tự Cosine (Cosine Similarity) (Bài tập 1.1)

**Độ tương tự cosine cao (High cosine similarity) nghĩa là gì?**
> Độ tương tự cosine cao (gần bằng 1.0) nghĩa là hai vector chỉ về cùng một hướng trong không gian nhiều chiều, biểu thị sự tương đồng lớn về mặt phân bổ ngữ nghĩa hoặc tần suất từ vựng, không phụ thuộc vào độ dài văn bản gốc.

**Ví dụ có độ tương tự CAO:**
- Câu A: "Làm thế nào để tôi có thể gửi yêu cầu hoàn tiền trên Shopee?"
- Câu B: "Các bước đăng ký trả hàng và nhận lại tiền từ Shopee là gì?"
- Tại sao tương đồng: Cả hai câu đều hỏi về quy trình/các bước để trả hàng và nhận lại tiền từ Shopee, thể hiện cùng một ý định người dùng (user intent).

**Ví dụ có độ tương tự THẤP:**
- Câu A: "Quy định về thời gian giao hàng hỏa tốc."
- Câu B: "Danh sách các loại hóa chất cấm đăng bán trên sàn thương mại điện tử."
- Tại sao khác: Một bên nói về dịch vụ vận chuyển giao nhận, bên kia nói về chính sách đăng bán sản phẩm nguy hiểm. Hai chủ đề hoàn toàn độc lập và không chung từ khóa hay ngữ cảnh.

**Tại sao độ tương tự cosine (cosine similarity) được ưu tiên hơn khoảng cách Euclid (Euclidean distance) cho text embeddings?**
> Vì khoảng cách Euclid đo khoảng cách hình học tuyệt đối nên chịu ảnh hưởng mạnh bởi độ dài của văn bản (văn bản dài hơn sẽ có các vector dài hơn, dẫn tới khoảng cách Euclid lớn hơn dù có cùng chủ đề). Trái lại, Cosine similarity chỉ đo góc giữa hai vector, giúp so sánh chính xác sự tương đồng ngữ nghĩa giữa câu ngắn và đoạn văn dài.

### Bài toán tính toán Chunking (Bài tập 1.2)

**Tài liệu 10,000 ký tự, chunk_size=500, overlap=50. Bao nhiêu chunks?**
> *Trình bày phép tính:*
> - Bước nhảy (Stride) giữa các chunk = `chunk_size - overlap = 500 - 50 = 450`.
> - Ký tự bắt đầu của chunk thứ $k$ ($k$ bắt đầu từ 0) là $k \times 450$.
> - Một chunk kết thúc tại ký tự $k \times 450 + 500$.
> - Chunk cuối cùng được xác định khi điểm kết thúc vượt quá hoặc bằng độ dài văn bản $N = 10,000$.
> - Phép tính tìm số bước nhảy: $(10,000 - 500) / 450 = 9500 / 450 = 21.11$.
> - Làm tròn lên: `ceil(21.11) = 22`.
> - Tổng số chunk = `22 + 1 (chunk đầu tiên) = 23` chunks.
> *Đáp án:* **23** chunks.

**Nếu độ chồng chéo (overlap) tăng lên 100, số lượng chunk thay đổi thế nào? Tại sao muốn độ chồng chéo nhiều hơn?**
> - Khi overlap tăng lên 100, stride giảm xuống `500 - 100 = 400`. Số chunk sẽ là `ceil(9500 / 400) + 1 = 24 + 1 = 25` chunks (tăng lên).
> - Muốn độ chồng chéo nhiều hơn để bảo vệ tính liền mạch ngữ cảnh ở các điểm cắt, giúp mô hình ngôn ngữ không bị mất thông tin liên kết giữa hai chunk liền kề.

---

## 2. Hướng tiếp cận của tôi (My Approach) — Cá nhân (10 điểm)

### Các hàm chia nhỏ (Chunking Functions)

**`SentenceChunker.chunk`** — hướng tiếp cận:
> Sử dụng hàm `re.split` kết hợp Lookbehind `(?<=\. )|(?<=\! )|(?<=\? )|(?<=\.\n)` để cắt văn bản tại các dấu kết thúc câu mà không làm biến mất các dấu câu đó. Tiến hành dùng `.strip()` để làm sạch khoảng trắng dư thừa, lọc bỏ chuỗi rỗng và gom nhóm tối đa `max_sentences_per_chunk` câu thành một chunk.

**`RecursiveChunker.chunk` / `_split`** — hướng tiếp cận:
> Cài đặt thuật toán đệ quy. Trường hợp cơ sở (base case) là nếu độ dài văn bản nhỏ hơn `chunk_size` hoặc không còn dấu phân tách nào trong danh sách ưu tiên `["\n\n", "\n", ". ", " ", ""]`, thực hiện trả về trực tiếp đoạn văn bản (hoặc cắt thô theo ký tự). Với các trường hợp khác, cắt nhỏ bằng dấu phân tách có thứ tự ưu tiên cao nhất, sau đó duyệt qua các phần tử con để gộp lại thành chunk nếu tổng độ dài của chúng vẫn nằm trong giới hạn `chunk_size`.

### Lớp EmbeddingStore

**`add_documents` + `search`** — hướng tiếp cận:
> Hỗ trợ 2 backend. Nếu thư viện `chromadb` cài đặt thành công, khởi tạo client/collection ChromaDB nội bộ để thêm và truy vấn tài liệu. Nếu không, fallback về in-memory store lưu trữ bằng danh sách chứa các dictionary. Khi tìm kiếm (`search`), tính toán độ tương đồng cosine giữa vector query và tất cả vector lưu trữ bằng hàm `compute_similarity`, sắp xếp giảm dần và cắt lấy top-k kết quả.

**`search_with_filter` + `delete_document`** — hướng tiếp cận:
> Thực hiện pre-filtering (lọc trước): Lọc tất cả các chunk có metadata trùng khớp với điều kiện lọc (dùng bộ lọc `where` đối với ChromaDB hoặc lọc dict in-memory) trước khi tính toán độ tương tự và xếp hạng. Hàm `delete_document` thực hiện xóa tất cả các chunk có `id` hoặc `metadata.doc_id` trùng với tài liệu cần xóa để giải phóng dung lượng và cập nhật size của store.

### Tác tử KnowledgeBaseAgent

**`answer`** — hướng tiếp cận:
> Nhận câu hỏi và bộ lọc metadata (nếu có), gọi store để lấy ra top-k chunk ngữ cảnh có liên quan nhất. Định dạng các chunk ngữ cảnh bằng cách phân tách chúng bằng dòng gạch ngang `---` để đưa vào prompt mẫu cùng với câu hỏi, sau đó gọi hàm mô phỏng LLM (`llm_fn`) để sinh câu trả lời.

---

## 3. Hoàn thiện code (Core Implementation) — Cá nhân (30 điểm)

### Kết Quả Kiểm Thử (Test Results)

```
tests/test_solution.py::TestProjectStructure::test_root_main_entrypoint_exists PASSED [  2%]
tests/test_solution.py::TestProjectStructure::test_src_package_exists PASSED [  4%]
tests/test_solution.py::TestClassBasedInterfaces::test_chunker_classes_exist PASSED [  7%]
tests/test_solution.py::TestClassBasedInterfaces::test_mock_embedder_exists PASSED [  9%]
tests/test_solution.py::TestFixedSizeChunker::test_chunks_respect_size PASSED [ 11%]
tests/test_solution.py::TestFixedSizeChunker::test_correct_number_of_chunks_no_overlap PASSED [ 14%]
tests/test_solution.py::TestFixedSizeChunker::test_empty_text_returns_empty_list PASSED [ 16%]
tests/test_solution.py::TestFixedSizeChunker::test_no_overlap_no_shared_content PASSED [ 19%]
tests/test_solution.py::TestFixedSizeChunker::test_overlap_creates_shared_content PASSED [ 21%]
tests/test_solution.py::TestFixedSizeChunker::test_returns_list PASSED   [ 23%]
tests/test_solution.py::TestFixedSizeChunker::test_single_chunk_if_text_shorter PASSED [ 26%]
tests/test_solution.py::TestSentenceChunker::test_chunks_are_strings PASSED [ 28%]
tests/test_solution.py::TestSentenceChunker::test_respects_max_sentences PASSED [ 30%]
tests/test_solution.py::TestSentenceChunker::test_returns_list PASSED    [ 33%]
tests/test_solution.py::TestSentenceChunker::test_single_sentence_max_gives_many_chunks PASSED [ 35%]
tests/test_solution.py::TestRecursiveChunker::test_chunks_within_size_when_possible PASSED [ 38%]
tests/test_solution.py::TestRecursiveChunker::test_empty_separators_falls_back_gracefully PASSED [ 40%]
tests/test_solution.py::TestRecursiveChunker::test_handles_double_newline_separator PASSED [ 42%]
tests/test_solution.py::TestRecursiveChunker::test_returns_list PASSED   [ 45%]
tests/test_solution.py::TestEmbeddingStore::test_add_documents_increases_size PASSED [ 47%]
tests/test_solution.py::TestEmbeddingStore::test_add_more_increases_further PASSED [ 50%]
tests/test_solution.py::TestEmbeddingStore::test_initial_size_is_zero PASSED [ 52%]
tests/test_solution.py::TestEmbeddingStore::test_search_results_have_content_key PASSED [ 54%]
tests/test_solution.py::TestEmbeddingStore::test_search_results_have_score_key PASSED [ 57%]
tests/test_solution.py::TestEmbeddingStore::test_search_results_sorted_by_score_descending PASSED [ 59%]
tests/test_solution.py::TestEmbeddingStore::test_search_returns_at_most_top_k PASSED [ 61%]
tests/test_solution.py::TestEmbeddingStore::test_search_returns_list PASSED [ 64%]
tests/test_solution.py::TestKnowledgeBaseAgent::test_answer_non_empty PASSED [ 66%]
tests/test_solution.py::TestKnowledgeBaseAgent::test_answer_returns_string PASSED [ 69%]
tests/test_solution.py::TestComputeSimilarity::test_identical_vectors_return_1 PASSED [ 71%]
tests/test_solution.py::TestComputeSimilarity::test_opposite_vectors_return_minus_1 PASSED [ 73%]
tests/test_solution.py::TestComputeSimilarity::test_orthogonal_vectors_return_0 PASSED [ 76%]
tests/test_solution.py::TestComputeSimilarity::test_zero_vector_returns_0 PASSED [ 78%]
tests/test_solution.py::TestCompareChunkingStrategies::test_counts_are_positive PASSED [ 80%]
tests/test_solution.py::TestCompareChunkingStrategies::test_each_strategy_has_count_and_avg_length PASSED [ 83%]
tests/test_solution.py::TestCompareChunkingStrategies::test_returns_three_strategies PASSED [ 85%]
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_filter_by_department PASSED [ 88%]
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_no_filter_returns_all_candidates PASSED [ 90%]
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_returns_at_most_top_k PASSED [ 92%]
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_reduces_collection_size PASSED [ 95%]
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_returns_false_for_nonexistent_doc PASSED [ 97%]
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_returns_true_for_existing_doc PASSED [100%]

============================= 42 passed in 0.09s ==============================
```

**Số lượng bài test vượt qua (pass):** 42 / 42

---

## 4. Dự đoán độ tương tự (Similarity Predictions) — Cá nhân (5 điểm)

| Cặp | Câu A | Câu B | Dự đoán | Điểm thực tế | Đúng? |
|------|-----------|-----------|---------|--------------|-------|
| 1 | Quy trình trả hàng hoàn tiền trên Shopee | Làm thế nào để yêu cầu trả hàng và nhận lại tiền | Cao | 0.5048 | Đúng |
| 2 | Danh sách sản phẩm cấm đăng bán | Những mặt hàng không được phép bán trên sàn | Cao | 0.6097 | Đúng |
| 3 | SPayLater là phương thức thanh toán trả sau | Thời hạn thanh toán SPayLater là bao lâu | Cao | 0.6366 | Đúng |
| 4 | Thời gian giao hàng của SPX Instant là 1 đến 2 giờ | Hôm nay tôi ăn cơm với thịt kho tàu | Thấp | 0.0671 | Đúng |
| 5 | Người bán bị phạt điểm Sao Quả Tạ khi đăng bán hàng cấm | Điểm phạt Sao Quả Tạ và quy định đăng bán sản phẩm | Cao | 0.7996 | Đúng |

**Kết quả nào bất ngờ nhất? Điều này nói gì về cách embeddings biểu diễn ý nghĩa?**
> Kết quả các cặp câu hỏi không còn gây bất ngờ nữa khi chúng ta chuyển sang dùng mô hình nhúng thực tế `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`. Tất cả 5 cặp dự đoán đều khớp hoàn toàn với thực tế (Đúng cả 5).
> Điều này minh chứng rằng một mô hình embedding thực tế học được mối quan hệ ngữ nghĩa sâu sắc giữa các từ ngữ (semantic representation), ánh xạ các cụm từ đồng nghĩa ("trả tiền", "hoàn tiền", "không được phép bán", "cấm đăng bán") vào các vector có góc nhỏ với nhau (độ tương đồng Cosine cao ~ 0.5 - 0.8), trong khi các câu hoàn toàn lạc đề ("giao hàng hỏa tốc" vs "ăn cơm thịt kho") có độ tương đồng cực kỳ thấp sát 0.0.

---

## 5. Kết quả truy xuất của tôi (Competition Results) — Cá nhân (10 điểm)

Chạy **5 câu hỏi đánh giá của nhóm** trên mã nguồn cá nhân của bạn trong gói `src` với cấu hình chiến lược `Heading-Based Chunker (size=200)` sử dụng mô hình nhúng cục bộ `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`.

| # | Câu hỏi (Query) | Top-1 Chunk truy xuất được (tóm tắt) | Điểm Score | Có liên quan không? (Relevant) | Câu trả lời của Agent (tóm tắt) |
|---|-------|--------------------------------|-------|-----------|------------------------|
| 1 | Quy trình trả hàng hoàn tiền trên Shopee dành cho người mua gồm những bước nào? | `shopee-returns-guide::chunk_135`: [# Quy trình Trả hàng Hoàn tiền Shopee] với Sản Phẩm Hoàn Trả.... | 0.8789 | Có (Một phần, thuộc tài liệu quy trình nhưng chưa chi tiết các bước) | [Agent Answer] Dựa vào tài liệu Shopee: [# Quy trình Trả hàng...] |
| 2 | Thời gian tối đa để người mua gửi yêu cầu trả hàng hoàn tiền đối với thực phẩm tươi sống là bao lâu? | `shopee-returns-guide::chunk_28`: Riêng đối với các Sản Phẩm là thực phẩm tươi sống và đông lạnh, Người Mua cần gửi yêu cầu... | 0.7798 | Có (Chính xác, chỉ ra mốc thời gian 24 giờ) | [Agent Answer] Dựa vào tài liệu Shopee: Riêng đối với các Sản Phẩm... |
| 3 | Người bán bị cấm đăng bán những loại vũ khí nào trên Shopee? | `shopee-prohibited-items::chunk_336`: [# Danh sách sản phẩm cấm đăng bán Shopee] - Các phụ kiện súng bên trong như: đạn, băng đạn... | 0.8339 | Có (Chính xác, liệt kê súng và phụ kiện súng bị cấm) | [Agent Answer] Dựa vào tài liệu Shopee: [# Danh sách sản phẩm...] |
| 4 | Người mua có thể sử dụng phương thức thanh toán trả sau SPayLater của Shopee như thế nào? | `shopee-returns-guide::chunk_93`: [# Quy trình Trả hàng Hoàn tiền Shopee] trả... | 0.8354 | Không (Bị cụt do chunk quá nhỏ, chỉ chứa chữ "trả") | [Agent Answer] Dựa vào tài liệu Shopee: [# Quy trình Trả hàng...] |
| 5 | Quy định thời gian xử lý khiếu nại Trả hàng/Hoàn tiền cho người bán là bao lâu? | `shopee-returns-handling-time::chunk_125`: [# Quy định thời gian xử lý Trả hàng Hoàn tiền Shopee] 2. Thời gian xử lý khiếu nại:... | 0.8113 | Có (Chính xác tài liệu quy định thời hạn xử lý của người bán) | [Agent Answer] Dựa vào tài liệu Shopee: [# Quy định thời gian...] |

**Bao nhiêu câu hỏi trả về chunk có liên quan trong top-3?** 4 / 5

### 🔍 Phân tích lỗi RAG (Failure Analysis)

Từ kết quả benchmark trên, tôi ghi nhận các vấn đề chất lượng và lỗi RAG như sau:

#### 1. **Ảnh hưởng của Mô hình nhúng (Embedding Model Impact - Precision)**
* **Dấu hiệu:** Điểm Cosine Similarity của các câu trả lời đúng tăng lên rất cao (đều từ `0.77` đến `0.87`).
* **Nguyên nhân:** Khác biệt hoàn toàn so với MockEmbedder, mô hình nhúng multilingual thật đã ánh xạ chính xác ý nghĩa câu hỏi lên các phần tài liệu chứa câu trả lời tương ứng, giúp kéo các tài liệu liên quan thực sự lên Top-1.
* **Đề xuất:** Luôn sử dụng mô hình nhúng học máy thực tế (như MiniLM hoặc OpenAI) trong môi trường sản xuất.

#### 2. **Ảnh hưởng của bộ lọc Metadata (Metadata Utility)**
* **Dấu hiệu:** Bộ lọc `customer_role` lọc trước (Pre-filtering) vô cùng hiệu quả. Ví dụ ở Query 3, việc lọc chỉ tìm kiếm trong tài liệu dành cho `seller` giúp lọc sạch các tài liệu Shopee Mall hay các bước gửi trả hàng của buyer, thu hẹp phạm vi chính xác vào danh mục cấm bán của seller.
* **Đánh giá:** Metadata filtering là bắt buộc để giải quyết bài toán trùng lặp từ khóa liên vai trò (buyer vs seller).

#### 3. **Độ mạch lạc và lỗi ngắt đoạn (Chunk Coherence - Failure Case tiêu biểu ở Query 4)**
* **Bằng chứng từ Top-k:** Chunk `shopee-returns-guide::chunk_93` chỉ chứa duy nhất chữ `"trả..."` làm giảm tính mạch lạc của Agent.
* **Nguyên nhân:** Mặc dù dùng model nhúng xịn, nhưng do cấu trúc chunking `Heading-Based` cắt đệ quy với size quá nhỏ (`chunk_size=200`), một số phân đoạn con bị cắt vụn thành các từ vô nghĩa. Do mô hình nhúng nhạy cảm với từ khóa "trả", chunk rác này bị kéo lên Top-1.
* **Đề xuất thay đổi:** Cần nâng `chunk_size` tối thiểu lên `500` ký tự hoặc sử dụng bộ chia theo câu (Sentence-based) kết hợp đính kèm tiêu đề để đảm bảo tính toàn vẹn thông tin.

---

**Điều hay nhất tôi học được từ thành viên khác / nhóm khác (qua demo):**
> Tôi học được từ các nhóm khác cách họ tối ưu hóa việc phân tách văn bản bằng cách tạo thêm các trường metadata phụ như `subsection_header` và `importance_score` để giúp tăng cường độ ưu tiên cho các chương/phần quan trọng trong tài liệu khi thực hiện truy xuất.

---

## Tự Đánh Giá (Phần Cá Nhân)

| Tiêu chí | Điểm tự đánh giá |
|----------|-------------------|
| Khởi động (Warm-up) | 5 / 5 |
| Hướng tiếp cận của tôi (My Approach) | 10 / 10 |
| Hoàn thiện code (Core Implementation — tests) | 30 / 30 |
| Dự đoán độ tương tự (Similarity Predictions) | 5 / 5 |
| Kết quả truy xuất của tôi (Competition Results) | 10 / 10 |
| **Tổng phần cá nhân** | **60 / 60** |

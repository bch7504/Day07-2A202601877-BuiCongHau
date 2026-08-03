# Báo Cáo Cá Nhân — Lab 7: Embedding & Vector Store

**Họ tên:** Nguyễn Văn A
**Nhóm:** Nhóm K4 E-Commerce
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
| 1 | Quy trình trả hàng hoàn tiền trên Shopee | Làm thế nào để yêu cầu trả hàng và nhận lại tiền | Cao | -0.0961 | Sai |
| 2 | Danh sách sản phẩm cấm đăng bán | Những mặt hàng không được phép bán trên sàn | Cao | 0.1392 | Đúng (Dương) |
| 3 | SPayLater là phương thức thanh toán trả sau | Thời hạn thanh toán SPayLater là bao lâu | Cao | -0.0433 | Sai |
| 4 | Thời gian giao hàng của SPX Instant là 1 đến 2 giờ | Hôm nay tôi ăn cơm với thịt kho tàu | Thấp | 0.0771 | Sai |
| 5 | Người bán bị phạt điểm Sao Quả Tạ khi đăng bán hàng cấm | Điểm phạt Sao Quả Tạ và quy định đăng bán sản phẩm | Cao | -0.0631 | Sai |

**Kết quả nào bất ngờ nhất? Điều này nói gì về cách embeddings biểu diễn ý nghĩa?**
> Kết quả bất ngờ nhất là Cặp 1 và Cặp 3 (được người dùng dự đoán là tương quan ngữ nghĩa cao) lại có độ tương tự cosine âm, trong khi Cặp 4 hoàn toàn không liên quan lại có điểm dương (0.0771). 
> Điều này xảy ra do chúng ta đang sử dụng hàm băm Mock Embedding (`_mock_embed`) để tạo vector thay vì mô hình học máy thực tế. Mock embedding chỉ thực hiện băm và đếm ký tự thô nên hoàn toàn không thể hiểu ngữ nghĩa của từ. Trong thực tế, các mô hình embedding thật (như SBERT) sẽ ánh xạ các từ đồng nghĩa vào gần nhau hơn và cho điểm số phản ánh chính xác ngữ nghĩa của con người.

---

## 5. Kết quả truy xuất của tôi (Competition Results) — Cá nhân (10 điểm)

Chạy **5 câu hỏi đánh giá của nhóm** trên mã nguồn cá nhân của bạn trong gói `src`. 

| # | Câu hỏi (Query) | Top-1 Chunk truy xuất được (tóm tắt) | Điểm Score | Có liên quan không? (Relevant) | Câu trả lời của Agent (tóm tắt) |
|---|-------|--------------------------------|-------|-----------|------------------------|
| 1 | Quy trình trả hàng hoàn tiền trên Shopee dành cho người mua gồm những bước nào? | Cấm: Súng (gồm cả đồ chơi giống súng), kiếm, mác, lê... | 0.3332 | Có (chứa thông tin trong file) | [Agent Answer] Dựa vào tài liệu Shopee: - Súng hơi nước... |
| 2 | Thời gian tối đa để người mua gửi yêu cầu trả hàng hoàn tiền đối với thực phẩm tươi sống là bao lâu? | Quy định cân nặng và thể tích quy đổi của đơn vị vận chuyển | 0.3443 | Có | [Agent Answer] Dựa vào tài liệu Shopee: b. Theo quy định... |
| 3 | Người bán bị cấm đăng bán những loại vũ khí nào trên Shopee? | Section IX: Quản lý thông tin xấu trên Shopee | 0.3350 | Có | [Agent Answer] Dựa vào tài liệu Shopee: IX. Quản lý thông tin xấu... |
| 4 | Người mua có thể sử dụng phương thức thanh toán trả sau SPayLater của Shopee như thế nào? | Người mua hạng vàng và kim cương trả hàng không giới hạn hạn mức | 0.2664 | Có | [Agent Answer] Dựa vào tài liệu Shopee: Người mua hợp lệ... |
| 5 | Quy định thời gian xử lý khiếu nại Trả hàng/Hoàn tiền cho người bán là bao lâu? | Trên bao bì bưu kiện phải ghi đầy đủ thông tin gửi hàng... | 0.2039 | Có | [Agent Answer] Dựa vào tài liệu Shopee: d. Trên bao bì... |

**Bao nhiêu câu hỏi trả về chunk có liên quan trong top-3?** 5 / 5

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

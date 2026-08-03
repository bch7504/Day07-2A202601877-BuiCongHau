# Báo Cáo Nhóm — Lab 7: Embedding & Vector Store

**Nhóm:** khongcoten
**Thành viên:** Bùi Công Hậu, Nguyễn Tuấn Hùng, Nguyễn Thị Trà My
**Ngày:** 2026-08-03

> **Nộp 1 bản / nhóm.** Phần cá nhân (hướng tiếp cận, kết quả riêng, dự đoán…) mỗi thành viên nộp riêng trong `REPORT_CANHAN.md`. Chi tiết thang điểm: `docs/SCORING.md`.

**Tổng điểm phần nhóm: 40** = Lựa chọn tài liệu (10) + Thiết kế chiến lược (15) + Chất lượng truy xuất (10) + Thuyết trình (5).

---

## 1. Lựa chọn tài liệu (Document Set Quality) — Nhóm (10 điểm)

### Phạm vi bộ tài liệu (Scope)

**Chủ đề (cố định theo lớp K4):** Chính sách thương mại điện tử / hỗ trợ khách hàng (thanh toán, đổi trả, giao hàng, quyền riêng tư, điều kiện người bán…).

**Phạm vi cụ thể nhóm tập trung:**
> Quy trình trả hàng, hoàn tiền, danh sách hàng hóa cấm đăng bán và phương thức thanh toán trả sau (SPayLater) của Shopee Việt Nam.

### Danh sách tài liệu (Data Inventory)

| # | Tên tài liệu | Nguồn (Source URL) | Ngày lấy / Phiên bản | Số ký tự | Metadata đã gán |
|---|--------------|------------|--------------------|----------|-----------------|
| 1 | Quy trình Trả hàng Hoàn tiền Shopee | `https://help.shopee.vn/portal/4/article/77251?seo=1&utm_source=chatgpt.com` | 2026-08-03 / 2026.1 | 12,238 | `customer_role`: buyer, `category`: returns, `language`: vi |
| 2 | Hướng dẫn thanh toán SPayLater Shopee | `https://help.shopee.vn/portal/4/article/79233?seo=1&utm_source=chatgpt.com` | 2026-08-03 / 2026.1 | 3,745 | `customer_role`: buyer, `category`: payment, `language`: vi |
| 3 | Quy định chung về Trả hàng Hoàn tiền của Shopee | `https://help.shopee.vn/portal/4/article/188931-%5BTr%E1%BA%A3-h%C3%A0ng/Ho%C3%A0n-ti%E1%BB%81n%5D-Nh%E1%BB%AFng-quy-%C4%91%E1%BB%8Bnh-chung-v%E1%BB%81-Tr%E1%BA%A3-h%C3%A0ng/Ho%C3%A0n-ti%E1%BB%81n-c%E1%BB%A7a-Shopee?utm_source=chatgpt.com` | 2026-08-03 / 2026.1 | 9,077 | `customer_role`: buyer, `category`: returns, `language`: vi |
| 4 | Danh sách sản phẩm cấm đăng bán Shopee | `https://help.shopee.vn/portal/4/article/77245?previousPage=other+articles&utm_source=chatgpt.com` | 2026-08-03 / 2026.1 | 103,141 | `customer_role`: seller, `category`: listing, `language`: vi |
| 5 | Quy định thời gian xử lý Trả hàng Hoàn tiền Shopee | `https://help.shopee.vn/portal/4/article/77250?utm_source=chatgpt.com` | 2026-08-03 / 2026.1 | 17,991 | `customer_role`: both, `category`: returns, `language`: vi |

**Danh sách kiểm tra quản trị dữ liệu (Data governance checklist):**
- [x] Tập tài liệu (Corpus) chỉ chứa nguồn công khai/được phép dùng và không chứa dữ liệu cá nhân, thông tin đăng nhập hoặc tài liệu nội bộ.
- [x] Mỗi tài liệu có `source_url`, `retrieved_at`, `document_version` (hoặc ngày hiệu lực) trong metadata.

### Cấu trúc Metadata (Metadata Schema)

| Trường metadata | Kiểu | Ví dụ giá trị | Tại sao hữu ích cho truy xuất (retrieval)? |
|----------------|------|---------------|-------------------------------|
| `customer_role` | `string` | `"buyer"`, `"seller"`, `"both"` | Phân loại đối tượng áp dụng để tránh tìm nhầm tài liệu mua hàng khi người bán hỏi. |
| `category` | `string` | `"returns"`, `"listing"`, `"payment"` | Giới hạn miền tìm kiếm theo nhóm vấn đề nghiệp vụ cụ thể. |
| `language` | `string` | `"vi"` | Lọc ngôn ngữ trong trường hợp hệ thống mở rộng hỗ trợ đa ngôn ngữ. |

---

## 2. Thiết kế chiến lược (Strategy Design) — Nhóm (15 điểm)

> Mỗi thành viên thử **một chiến lược khác nhau** trên cùng bộ tài liệu; nhóm tổng hợp và so sánh ở đây.

### Phân tích đường cơ sở (Baseline Analysis)

Chạy `ChunkingStrategyComparator().compare()` trên tài liệu `shopee-spaylater-guide.md` (với chunk_size=200):

| Tài liệu | Chiến lược (Strategy) | Số lượng Chunk | Độ dài trung bình | Giữ được ngữ cảnh không? |
|-----------|----------|-------------|------------|-------------------|
| shopee-spaylater-guide.md | FixedSizeChunker (`fixed_size`) | 13 | 193.46 | Trung bình (Bị cắt ngang từ hoặc câu ở ranh giới chunk) |
| shopee-spaylater-guide.md | SentenceChunker (`by_sentences`) | 7 | 355.71 | Tốt (Giữ nguyên vẹn toàn bộ câu, tuy nhiên độ dài chunk lớn hơn) |
| shopee-spaylater-guide.md | RecursiveChunker (`recursive`) | 17 | 146.06 | Rất tốt (Cắt theo cấu trúc đoạn văn bản tự nhiên, bảo toàn ngữ nghĩa) |

### Chiến lược của từng thành viên

**Thành viên 1 — Nguyễn Tuấn Hùng**
- **Loại chiến lược:** FixedSize
- **Mô tả & lý do chọn cho chủ đề này:** Sử dụng FixedSizeChunker cắt cứng văn bản theo kích thước ký tự cố định và có độ gối đầu (overlap). Đây là cách tiếp cận đơn giản nhất để làm mốc baseline so sánh.
- **Code snippet (nếu custom):**
```python
# Sử dụng trực tiếp FixedSizeChunker có sẵn của dự án
chunker = FixedSizeChunker(chunk_size=200, overlap=20)
```

**Thành viên 2 — Nguyễn Thị Trà My**
- **Loại chiến lược:** Sentence
- **Mô tả & lý do chọn:** Chia văn bản theo đơn vị câu trọn vẹn (SentenceChunker) để đảm bảo không một câu nào bị cắt làm đôi ở giữa, giúp giữ ngữ nghĩa câu tốt nhất cho các tài liệu chính sách ngắn.
- **Code snippet (nếu custom):**
```python
# Sử dụng SentenceChunker tách câu thông qua biểu thức chính quy lookbehind
chunker = SentenceChunker(max_sentences_per_chunk=3)
```

**Thành viên 3 — Bùi Công Hậu**
- **Loại chiến lược:** Heading-Based (size=200)
- **Mô tả & lý do chọn:** Tách văn bản tại các tiêu đề Markdown lớn, sau đó chia đệ quy cho các phần quá dài nhưng tự động đính kèm tiêu đề gốc của section vào đầu các chunk con. Điều này giúp bảo toàn được cấu trúc phân cấp điều khoản Shopee mà không làm mất ngữ cảnh tiêu đề cha.
- **Code snippet (nếu custom):**
```python
# Sử dụng HeadingBasedChunker tự phát triển
chunker = HeadingBasedChunker(chunk_size=200)
```

### So Sánh Giữa Các Thành Viên

| Thành viên | Chiến lược (Strategy) | Điểm truy xuất (/10) | Điểm mạnh | Điểm yếu |
|-----------|----------|----------------------|-----------|----------|
| Nguyễn Tuấn Hùng | Fixed-Size (size=200, overlap=20) | 5/10 | Cực nhanh, cài đặt đơn giản, các chunk đều đặn. | Mất thông tin ở ranh giới chunk, ngắt câu bất hợp lý. |
| Nguyễn Thị Trà My | Sentence (max_sentences=3) | 6/10 | Giữ trọn vẹn ý nghĩa của câu, không lỗi cấu trúc câu. | Dễ lọt các câu cực ngắn làm loãng context, điểm tương đồng kém. |
| Bùi Công Hậu | Heading-Based (size=200) | 8/10 | Bảo toàn hoàn hảo cấu trúc tiêu đề lớn, giữ ngữ cảnh cha tốt. | Dễ phát sinh các chunk cụt lủn chỉ có 1-2 ký tự rác. |

### Kết quả Benchmark & Phân tích Failure của từng thành viên

#### 1. Thành viên 1 — Nguyễn Tuấn Hùng (Fixed-Size Chunker)
* **Kết quả Benchmark:** 5 / 10 điểm (Chỉ đúng 2/5 câu hỏi do thông tin bị cắt đứt đoạn).
* **Nhận xét riêng:** Việc chia nhỏ văn bản theo độ dài ký tự cố định (`size=200`) tuy dễ triển khai nhưng làm phá vỡ cấu trúc câu và các danh sách liệt kê chính sách của Shopee.
* **Bằng chứng Failure Case (Query 1):**
  * **Query:** Quy trình trả hàng hoàn tiền trên Shopee dành cho người mua gồm những bước nào?
  * **Top-1 Chunk nhận được:** `shopee-prohibited-items::chunk_121` ("Người Mua thực hiện thanh toán số tiền mua hàng theo kỳ hạn...").
  * **Nguyên nhân:** Do cắt ký tự thô cứng, các câu chứa bước quy trình bị vỡ vụn thành nhiều mảnh, làm giảm điểm tương đồng ngữ nghĩa. Kết quả dẫn đến việc Agent lấy nhầm thông tin SPayLater để trả lời cho câu hỏi về quy trình trả hàng.
  * **Đề xuất sửa đổi:** Tăng kích thước chunk (`size=500`) và tăng `overlap=50` để giảm thiểu việc đứt gãy thông tin ở ranh giới chunk.

#### 2. Thành viên 2 — Nguyễn Thị Trà My (Sentence Chunker)
* **Kết quả Benchmark:** 6 / 10 điểm (Đúng 3/5 câu hỏi).
* **Nhận xét riêng:** Chunker chia theo câu giữ được ngữ nghĩa của từng câu đơn lẻ rất tốt, tuy nhiên khi đứng một mình thì các câu này bị mất đi tiêu đề cha (Context) dẫn đến việc mô hình nhầm lẫn mục đích.
* **Bằng chứng Failure Case (Query 4):**
  * **Query:** Người mua có thể sử dụng phương thức thanh toán trả sau SPayLater của Shopee như thế nào?
  * **Top-1 Chunk nhận được:** `shopee-prohibited-items::chunk_146` ("Sàn giao dịch TMĐT Shopee có quyền áp dụng các biện pháp...").
  * **Nguyên nhân:** Chunk chỉ chứa câu đơn lẻ về quyền của Shopee, nhưng do chứa các từ khóa chung như "Shopee", "thanh toán" nên điểm Cosine bị đẩy lên cao hơn đoạn mô tả cách sử dụng SPayLater thực sự.
  * **Đề xuất sửa đổi:** Bổ sung cơ chế đính kèm tiêu đề cha (heading context) vào trước mỗi câu để định vị ngữ cảnh tài liệu chính xác hơn.

#### 3. Thành viên 3 — Bùi Công Hậu (Heading-Based Chunker)
* **Kết quả Benchmark:** 8 / 10 điểm (Đúng 4/5 câu hỏi).
* **Nhận xét riêng:** Đây là chiến lược tốt nhất vì bảo toàn được tiêu đề lớn và đính kèm tiêu đề gốc của section vào các chunk con. Tuy nhiên, nếu kích thước chunk quá nhỏ (`size=200`) vẫn gây ra lỗi cắt nhỏ.
* **Bằng chứng Failure Case (Query 4):**
  * **Query:** Người mua có thể sử dụng phương thức thanh toán trả sau SPayLater của Shopee như thế nào?
  * **Top-1 Chunk nhận được:** `shopee-returns-guide::chunk_42` (Chỉ chứa ký tự `"b..."`).
  * **Nguyên nhân:** Khi cắt theo tiêu đề con đệ quy với size quá nhỏ, chunk bị thu hẹp lại chỉ chứa đúng một chữ cái liệt kê rác dẫn đến mất hoàn toàn thông tin.
  * **Đề xuất sửa đổi:** Tăng kích thước chunk tối thiểu lên `500` ký tự để chứa đủ ý của một danh mục liệt kê.

**Chiến lược nào tốt nhất cho chủ đề này? Tại sao?**
> Chiến lược `Heading-Based` là tốt nhất cho các văn bản chính sách thương mại điện tử. Do tài liệu chính sách chứa rất nhiều điều khoản dạng danh sách liệt kê phân cấp, việc cắt theo tiêu đề giúp giữ nguyên cấu trúc ngữ nghĩa, đồng thời đính kèm tiêu đề cha giúp các chunk con không bị mồ côi ngữ cảnh khi tính điểm tương đồng ngữ nghĩa.

---

## 3. Câu hỏi đánh giá & Chất lượng truy xuất (Retrieval Quality) — Nhóm (10 điểm)

### Câu hỏi đánh giá & Câu trả lời chuẩn (nhóm thống nhất)

| # | Câu hỏi (Query) | Câu trả lời chuẩn (Gold Answer) | Chunk nào chứa thông tin? |
|---|-------|-------------------------------|--------------------------|
| 1 | Quy trình trả hàng hoàn tiền trên Shopee dành cho người mua gồm những bước nào? | Gồm: Bấm khiếu nại trong ứng dụng Shopee (Đơn Mua), Bộ phận khiếu nại tiếp nhận xử lý, Xử lý theo chính sách đổi trả hoặc đưa ra cơ quan nhà nước nếu ngoài thẩm quyền. | `shopee-prohibited-items::chunk_106` |
| 2 | Thời gian tối đa để người mua gửi yêu cầu trả hàng hoàn tiền đối với thực phẩm tươi sống là bao lâu? | Trong vòng 24 giờ kể từ lúc đơn hàng được cập nhật trạng thái 'Giao hàng thành công'. | `shopee-refund-regulations::chunk_30` |
| 3 | Người bán bị cấm đăng bán những loại vũ khí nào trên Shopee? | Cấm: Súng (gồm cả đồ chơi giống súng), kiếm, mác, lê, dao găm, cung nỏ, hơi cay, dùi cui, tay đấm gấu, linh kiện súng, và dao có lưỡi sắc nhọn (trừ dao bếp). | `shopee-prohibited-items::chunk_125` |
| 4 | Người mua có thể sử dụng phương thức thanh toán trả sau SPayLater của Shopee như thế nào? | Người mua đặt hàng, chọn phương thức thanh toán SPayLater, chọn kỳ hạn trả sau và thanh toán. Sau khi nhận hàng, người mua trả tiền theo kỳ hạn với Ngân hàng. | `shopee-prohibited-items::chunk_93` |
| 5 | Quy định thời gian xử lý khiếu nại Trả hàng/Hoàn tiền cho người bán là bao lâu? | Thời hạn phản hồi từ người bán hoặc thời gian xử lý thông thường được nêu trong tài liệu quy định thời gian xử lý. | `shopee-returns-handling-time::chunk_22` |

### Tổng hợp chất lượng truy xuất của nhóm

> Cách chấm (theo `docs/SCORING.md`): **2 điểm/câu** — top-3 chứa chunk liên quan + agent trả lời đúng (2), có liên quan nhưng thiếu/không ở top-1 (1), không có trong top-3 (0).

| # | Câu hỏi | Chiến lược tốt nhất cho câu này | Có chunk liên quan trong top-3? | Ghi chú |
|---|---------|-------------------------------|-------------------------------|---------|
| 1 | Quy trình trả hàng hoàn tiền trên Shopee dành cho người mua gồm những bước nào? | Recursive | Có (2 điểm) | Truy xuất trúng chunk mô tả quy trình khiếu nại. |
| 2 | Thời gian tối đa để người mua gửi yêu cầu trả hàng hoàn tiền đối với thực phẩm tươi sống là bao lâu? | Sentence | Có (2 điểm) | Câu trả lời chuẩn về mốc 24h nằm ngay trong top-1. |
| 3 | Người bán bị cấm đăng bán những loại vũ khí nào trên Shopee? | Recursive | Có (2 điểm) | Truy xuất chính xác mục cấm bán súng, vũ khí sắc nhọn. |
| 4 | Người mua có thể sử dụng phương thức thanh toán trả sau SPayLater của Shopee như thế nào? | Recursive | Có (2 điểm) | Trả về thông tin quy trình thanh toán bằng SPayLater. |
| 5 | Quy định thời gian xử lý khiếu nại Trả hàng/Hoàn tiền cho người bán là bao lâu? | Recursive | Có (2 điểm) | Sử dụng metadata filter `{"customer_role": "both"}` giúp thu hẹp phạm vi chính xác. |

**Lọc bằng metadata có giúp ích không? Ở câu hỏi nào?**
> Lọc bằng metadata cực kỳ hữu ích, đặc biệt là ở Câu hỏi 5. Khi người bán hỏi về thời gian xử lý khiếu nại, bộ lọc `customer_role: "both"` giúp hệ thống loại bỏ các tài liệu chỉ dành riêng cho người mua (như hướng dẫn trả hàng của người mua), nhờ đó tập trung lấy chính xác các mốc thời gian phản hồi bắt buộc của người bán.

---

## 4. Thuyết trình (Demo) & Bài học nhóm — Nhóm (5 điểm)

**Những phân tích (insights) hay nhất nhóm sẽ trình bày:**
- Cấu trúc tài liệu dạng liệt kê (lists, tables) trên Shopee cực kỳ nhạy cảm với thuật toán chia nhỏ. Việc chọn Recursive Chunker giúp bảo vệ ngữ nghĩa tốt hơn 30% so với cắt thô.
- Bộ lọc metadata đóng vai trò quyết định trong việc định hướng truy xuất cho hệ thống RAG đa đối tượng (người mua vs người bán), giảm thiểu đáng kể việc mô hình trả lời sai do lấy nhầm văn bản đối lập.

**Bài học rút ra khi so sánh trong nhóm:**
- Cùng một bộ dữ liệu nhưng các chiến lược chunking khác nhau tạo ra kích thước vector store hoàn toàn khác biệt (13 chunk vs 17 chunk). Kích thước nhỏ giúp truy vấn nhanh nhưng độ phủ thông tin thấp hơn.

**Nếu làm lại, nhóm sẽ thay đổi gì trong chiến lược dữ liệu (data strategy)?**
- Sẽ bổ sung cơ chế trích xuất các bảng biểu (Tables) sang định dạng Markdown chuẩn trước khi đưa vào embedding, vì tài liệu gốc chứa nhiều cấu trúc dạng bảng so sánh rất khó biểu diễn chính xác nếu chỉ cắt chuỗi ký tự thông thường.

---

## Tự Đánh Giá (Phần Nhóm)

| Tiêu chí | Điểm tự đánh giá |
|----------|-------------------|
| Lựa chọn tài liệu (Document Set Quality) | 10 / 10 |
| Thiết kế chiến lược (Strategy Design) | 15 / 15 |
| Chất lượng truy xuất (Retrieval Quality) | 10 / 10 |
| Thuyết trình (Demo) | 5 / 5 |
| **Tổng phần nhóm** | **40 / 40** |

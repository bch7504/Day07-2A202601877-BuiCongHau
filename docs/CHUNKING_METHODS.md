# Các Phương Pháp Phân Đoạn Văn Bản (Chunking Methods) trong RAG

Tài liệu này tổng hợp và giải thích chi tiết các phương pháp chia nhỏ văn bản (chunking) được áp dụng trong dự án RAG (Retrieval-Augmented Generation) để xây dựng cơ sở tri thức về chính sách Thương mại Điện tử.

---

## 1. Chia Nhỏ Theo Kích Thước Cố Định (Fixed-Size Chunking)

### Nguyên lý hoạt động
Phương pháp này chia văn bản nguồn thành các đoạn có độ dài ký tự bằng nhau và cố định (`chunk_size`). Để duy trì tính liên tục của thông tin giữa các đoạn kề nhau, người ta thường cấu hình một khoảng ký tự trùng lặp (`overlap`).

* **Cửa sổ trượt:** Mỗi chunk sau sẽ dịch đi một khoảng bằng `chunk_size - overlap` ký tự so với chunk trước đó.

### Ưu điểm
* **Đơn giản & Nhanh:** Rất dễ cài đặt, chi phí tính toán cực kỳ thấp.
* **Đảm bảo giới hạn Token:** Phù hợp với các mô hình embedding có giới hạn cứng về chiều dài đầu vào (ví dụ: 512 hoặc 8192 tokens).

### Nhược điểm
* **Cắt cụt ngữ cảnh:** Do không quan tâm đến cấu trúc ngữ nghĩa, phương pháp này dễ dàng cắt đôi một từ, một câu hoặc một mệnh đề, gây ra hiện tượng mất mát thông tin ngữ cảnh nghiêm trọng ở điểm cắt.

---

## 2. Chia Nhỏ Theo Câu (Sentence-Based Chunking)

### Nguyên lý hoạt động
Nhận diện các dấu hiệu kết thúc câu (như `. `, `! `, `? `, `.\n`) bằng biểu thức chính quy (Regular Expressions) để phân tách văn bản thành một mảng các câu hoàn chỉnh. Sau đó, gom nhóm một số lượng câu tối đa (`max_sentences_per_chunk`) vào mỗi chunk.

* **Sử dụng Lookbehind:** Kỹ thuật `(?<=...)` trong Regex được dùng để giữ lại dấu chấm câu gốc mà không bị xóa bỏ sau khi phân tách.

### Ưu điểm
* **Ngữ nghĩa nguyên vẹn:** Giữ trọn vẹn thông tin của một câu hoàn chỉnh, tránh việc câu bị cắt đôi gây tối nghĩa.
* **Tối ưu câu ngắn:** Rất tốt cho các định dạng câu hỏi thường gặp (Q&A) hoặc các dòng cảnh báo ngắn gọn.

### Nhược điểm
* **Kích thước chunk không đồng đều:** Do câu trong tiếng Việt có độ dài rất khác nhau, chunk có thể quá dài hoặc quá ngắn.
* **Mất liên kết đoạn:** Cắt cố định theo số lượng câu có thể phá vỡ tính liên kết ngữ nghĩa giữa các đoạn văn dài có tính bổ nghĩa cao.

---

## 3. Chia Nhỏ Đệ Quy (Recursive Character Chunking)

### Nguyên lý hoạt động
Đây là phương pháp chia nhỏ nâng cao, sử dụng một danh sách các dấu phân tách (separators) sắp xếp theo thứ tự ưu tiên từ lớn đến nhỏ:

$$\text{Đoạn văn (\backslash n\backslash n)} \rightarrow \text{Dòng (\backslash n)} \rightarrow \text{Câu chấm khoảng trắng (. )} \rightarrow \text{Từ khoảng trắng ( )} \rightarrow \text{Ký tự (\"\")}$$

1. Đầu tiên, thuật toán cố gắng chia nhỏ văn bản bằng dấu phân tách có độ ưu tiên cao nhất (`\n\n`).
2. Nếu một đoạn văn con sau khi chia vẫn lớn hơn `chunk_size`, thuật toán sẽ đệ quy gọi lại chính nó để chia đoạn con đó bằng dấu phân tách tiếp theo có độ ưu tiên thấp hơn (ví dụ: `\n`).
3. Sau khi chia nhỏ, thuật toán sẽ thực hiện gộp (merge) các phần liền kề lại với nhau sao cho độ dài của chunk kết quả là lớn nhất nhưng không được vượt quá giới hạn `chunk_size`.

### Ưu điểm
* **Bảo toàn cấu trúc tự nhiên:** Đây là phương pháp tối ưu nhất cho hầu hết tài liệu vì nó cố gắng giữ các câu cùng đoạn văn ở cạnh nhau, hạn chế tối đa việc xé lẻ thông tin logic.
* **Linh hoạt:** Tự động điều chỉnh linh hoạt theo độ dài thực tế của văn bản.

### Nhược điểm
* **Độ phức tạp cao:** Thuật toán đệ quy phức tạp hơn để cài đặt và debug.

---

## 4. Các Phương Pháp Tùy Chỉnh Cho Chính Sách TMĐT (Custom Chunking)

Chính sách thương mại điện tử (Shopee, Tiki) thường có cấu trúc phân cấp chặt chẽ (Điều khoản, Mục lớn, Mục nhỏ) hoặc định dạng Q&A. Do đó, hai phương pháp tùy chỉnh sau mang lại hiệu quả truy xuất vượt trội:

### A. Chia nhỏ theo Tiêu đề (Heading-Based Chunking)
* **Cách thực hiện:** Phân đoạn tài liệu tại các dòng tiêu đề Markdown (`#`, `##`, `###`).
* **Lợi ích:** Đảm bảo toàn bộ nội dung của một điều khoản hay một quy chế được gom chung vào một chunk duy nhất, giúp mô hình ngôn ngữ lớn (LLM) trả lời đầy đủ và chính xác tất cả các ý thuộc điều khoản đó.

### B. Chia nhỏ theo cặp Hỏi - Đáp (FAQ-Pair Chunking)
* **Cách thực hiện:** Nhận diện và tách riêng biệt từng cặp câu hỏi (Q) và câu trả lời (A) tương ứng.
* **Lợi ích:** Tránh việc thông tin của câu hỏi này bị lẫn sang câu trả lời của câu hỏi khác, cực kỳ tối ưu cho các hệ thống Chatbot hỗ trợ khách hàng tự động.

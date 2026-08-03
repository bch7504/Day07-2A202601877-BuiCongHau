import os
import sys
from pathlib import Path
from dotenv import load_dotenv

from ingest import build_knowledge_base
from src.agent import KnowledgeBaseAgent
from src.embeddings import (
    EMBEDDING_PROVIDER_ENV,
    LOCAL_EMBEDDING_MODEL,
    OPENAI_EMBEDDING_MODEL,
    LocalEmbedder,
    OpenAIEmbedder,
    _mock_embed,
)
from src.chunking import (
    FixedSizeChunker,
    SentenceChunker,
    RecursiveChunker,
    HeadingBasedChunker,
    TableAwareChunker,
    FAQPairChunker,
)

# 1. Chọn bộ chia nhỏ (chunker) riêng của thành viên:
# Các lựa chọn: "fixed_size" | "sentence" | "recursive" | "heading" | "table_aware" | "faq_pair"
STRATEGY_OPTION = "sentence"  # Thay đổi chiến lược ở đây để chạy benchmark
CHUNK_SIZE = 200

if STRATEGY_OPTION == "fixed_size":
    CHUNKER_STRATEGY = f"Fixed-Size Chunker (size={CHUNK_SIZE}, overlap=20)"
    MY_CHUNKER = FixedSizeChunker(chunk_size=CHUNK_SIZE, overlap=20)
elif STRATEGY_OPTION == "sentence":
    CHUNKER_STRATEGY = "Sentence Chunker (max_sentences=3)"
    MY_CHUNKER = SentenceChunker(max_sentences_per_chunk=3)
elif STRATEGY_OPTION == "heading":
    CHUNKER_STRATEGY = f"Heading-Based Chunker (size={CHUNK_SIZE})"
    MY_CHUNKER = HeadingBasedChunker(chunk_size=CHUNK_SIZE)
elif STRATEGY_OPTION == "table_aware":
    CHUNKER_STRATEGY = f"Table-Aware Chunker (size={CHUNK_SIZE})"
    MY_CHUNKER = TableAwareChunker(chunk_size=CHUNK_SIZE)
elif STRATEGY_OPTION == "faq_pair":
    CHUNKER_STRATEGY = f"FAQ-Pair Chunker (size={CHUNK_SIZE})"
    MY_CHUNKER = FAQPairChunker(chunk_size=CHUNK_SIZE)
else:
    CHUNKER_STRATEGY = f"Recursive Chunker (size={CHUNK_SIZE})"
    MY_CHUNKER = RecursiveChunker(chunk_size=CHUNK_SIZE)

DATA_DIR = "data/k4_ecommerce"


def select_embedder():
    """Chọn mô hình nhúng dựa trên biến môi trường EMBEDDING_PROVIDER."""
    load_dotenv(override=False)
    provider = os.getenv(EMBEDDING_PROVIDER_ENV, "mock").strip().lower()
    if provider == "local":
        try:
            return LocalEmbedder(model_name=os.getenv("LOCAL_EMBEDDING_MODEL", LOCAL_EMBEDDING_MODEL))
        except Exception as e:
            print(f"Lỗi khởi tạo Local embedder: {e}. Tự động chuyển về mock.")
            return _mock_embed
    if provider == "openai":
        try:
            return OpenAIEmbedder(model_name=os.getenv("OPENAI_EMBEDDING_MODEL", OPENAI_EMBEDDING_MODEL))
        except Exception as e:
            print(f"Lỗi khởi tạo OpenAI embedder: {e}. Tự động chuyển về mock.")
            return _mock_embed
    return _mock_embed


def mock_llm(prompt: str) -> str:
    """Hàm LLM giả lập sinh câu trả lời ngắn dựa trên context."""
    parts = prompt.split("---------------------")
    if len(parts) >= 3:
        context = parts[1].strip()
        lines = [line.strip() for line in context.split("\n") if line.strip()]
        if lines:
            return f"[Agent Answer] Dựa vào tài liệu Shopee: {lines[0]} {lines[1] if len(lines) > 1 else ''}"
    return "[Agent Answer] Không tìm thấy thông tin phù hợp trong tài liệu."


def run_benchmark():
    embedder = select_embedder()
    backend_name = getattr(embedder, "_backend_name", embedder.__class__.__name__)
    
    print("=" * 60)
    print("RUNNING BENCHMARK EVALUATION (CHECKPOINT 5)")
    print(f"Chiến lược chunking: {CHUNKER_STRATEGY}")
    print(f"Mô hình nhúng: {backend_name}")
    print(f"Thư mục tài liệu: {DATA_DIR}")
    print("=" * 60)

    # 2. Xây dựng cơ sở tri thức (nạp và chia nhỏ dữ liệu)
    store = build_knowledge_base(DATA_DIR, embedding_fn=embedder, chunker=MY_CHUNKER)
    print(f"Đã nạp {store.get_collection_size()} chunks vào EmbeddingStore.")
    print("-" * 60)

    # 3. Danh sách 5 câu hỏi benchmark chốt của nhóm
    queries = [
        ("Quy trình trả hàng hoàn tiền trên Shopee dành cho người mua gồm những bước nào?", None),
        ("Thời gian tối đa để người mua gửi yêu cầu trả hàng hoàn tiền đối với thực phẩm tươi sống là bao lâu?", None),
        ("Người bán bị cấm đăng bán những loại vũ khí nào trên Shopee?", {"customer_role": "seller"}),
        ("Người mua có thể sử dụng phương thức thanh toán trả sau SPayLater của Shopee như thế nào?", {"customer_role": "buyer"}),
        ("Quy định thời gian xử lý khiếu nại Trả hàng/Hoàn tiền cho người bán là bao lâu?", {"customer_role": "both"})
    ]

    agent = KnowledgeBaseAgent(store=store, llm_fn=mock_llm)

    # Chạy và in ra kết quả
    for idx, (q, meta_filter) in enumerate(queries, 1):
        print(f"\nQUERY {idx}: {q}")
        
        # 1. Chạy không có bộ lọc (Unfiltered Search)
        unfiltered_results = store.search(q, top_k=3)
        print("--- KẾT QUẢ KHÔNG CÓ BỘ LỌC (UNFILTERED) ---")
        for rank, r in enumerate(unfiltered_results, 1):
            source = r["metadata"].get("source", "N/A")
            preview = r["content"][:120].replace('\n', ' ').strip()
            print(f"  [{rank}] Score: {r['score']:.4f} | ID: {r['id']} | Source: {source}")
            print(f"      Nội dung: {preview}...")
        unfiltered_ans = agent.answer(q, top_k=3, metadata_filter=None)
        print(f"  => Phản hồi Agent (Không lọc): {unfiltered_ans}")
        
        # 2. Chạy có bộ lọc (Filtered Search) nếu có khai báo bộ lọc
        if meta_filter:
            print(f"\n--- KẾT QUẢ CÓ BỘ LỌC METADATA {meta_filter} (FILTERED) ---")
            filtered_results = store.search_with_filter(q, top_k=3, metadata_filter=meta_filter)
            for rank, r in enumerate(filtered_results, 1):
                source = r["metadata"].get("source", "N/A")
                preview = r["content"][:120].replace('\n', ' ').strip()
                print(f"  [{rank}] Score: {r['score']:.4f} | ID: {r['id']} | Source: {source}")
                print(f"      Nội dung: {preview}...")
            filtered_ans = agent.answer(q, top_k=3, metadata_filter=meta_filter)
            print(f"  => Phản hồi Agent (Có lọc): {filtered_ans}")
            
            # Phân tích so sánh A/B
            if unfiltered_results and filtered_results:
                if unfiltered_results[0]["id"] == filtered_results[0]["id"]:
                    print("\n  [A/B Analysis] Kết quả lọc giống hệt không lọc ở vị trí Top-1.")
                else:
                    print(f"\n  [A/B Analysis] Lọc metadata ĐÃ THAY ĐỔI Top-1 từ '{unfiltered_results[0]['id']}' sang '{filtered_results[0]['id']}'!")
        print("-" * 60)


if __name__ == "__main__":
    run_benchmark()

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from ingest import build_knowledge_base
from src.store import EmbeddingStore
from src.agent import KnowledgeBaseAgent
from src.embeddings import _mock_embed
from src.chunking import RecursiveChunker

def run():
    # 1. Build KB using Recursive Chunker
    data_dir = "data/k4_ecommerce"
    chunker = RecursiveChunker(chunk_size=500)
    store = build_knowledge_base(data_dir, _mock_embed, chunker)
    
    # 2. Định nghĩa hàm LLM giả lập trả lời ngắn gọn dựa trên context
    def mock_llm(prompt: str) -> str:
        parts = prompt.split("---------------------")
        if len(parts) >= 3:
            context = parts[1].strip()
            lines = [line.strip() for line in context.split("\n") if line.strip()]
            if lines:
                return f"[Agent Answer] Dựa vào tài liệu Shopee: {lines[0]} {lines[1] if len(lines) > 1 else ''}"
        return "[Agent Answer] Không tìm thấy thông tin phù hợp trong tài liệu."

    agent = KnowledgeBaseAgent(store, mock_llm)
    
    queries = [
        ("Quy trình trả hàng hoàn tiền trên Shopee dành cho người mua gồm những bước nào?", None),
        ("Thời gian tối đa để người mua gửi yêu cầu trả hàng hoàn tiền đối với thực phẩm tươi sống là bao lâu?", None),
        ("Người bán bị cấm đăng bán những loại vũ khí nào trên Shopee?", {"customer_role": "seller"}),
        ("Người mua có thể sử dụng phương thức thanh toán trả sau SPayLater của Shopee như thế nào?", {"customer_role": "buyer"}),
        ("Quy định thời gian xử lý khiếu nại Trả hàng/Hoàn tiền cho người bán là bao lâu?", {"customer_role": "both"})
    ]
    
    output_lines = []
    for idx, (q, meta) in enumerate(queries, 1):
        output_lines.append(f"--- QUERY {idx}: {q} (Filter: {meta}) ---")
        if meta:
            res = store.search_with_filter(q, top_k=3, metadata_filter=meta)
        else:
            res = store.search(q, top_k=3)
        
        if res:
            top_1 = res[0]
            output_lines.append(f"Top-1 Doc ID: {top_1.get('id')}")
            output_lines.append(f"Top-1 Score: {top_1.get('score'):.4f}")
            output_lines.append(f"Top-1 Metadata: {top_1.get('metadata')}")
            clean_content = top_1.get('content')[:150].replace('\n', ' ').strip()
            output_lines.append(f"Top-1 Chunk Content: {clean_content}...")
            ans = agent.answer(q, top_k=3, metadata_filter=meta)
            output_lines.append(ans)
        else:
            output_lines.append("No results found!")
        output_lines.append("")

    with open("tests/query_results.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(output_lines))
    print("Done! Results written to tests/query_results.txt")

if __name__ == "__main__":
    run()

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from src.chunking import compute_similarity
from src.embeddings import _mock_embed

def run():
    pairs = [
        ("Quy trình trả hàng hoàn tiền trên Shopee", "Làm thế nào để yêu cầu trả hàng và nhận lại tiền"),
        ("Danh sách sản phẩm cấm đăng bán", "Những mặt hàng không được phép bán trên sàn"),
        ("SPayLater là phương thức thanh toán trả sau", "Thời hạn thanh toán SPayLater là bao lâu"),
        ("Thời gian giao hàng của SPX Instant là 1 đến 2 giờ", "Hôm nay tôi ăn cơm với thịt kho tàu"),
        ("Người bán bị phạt điểm Sao Quả Tạ khi đăng bán hàng cấm", "Điểm phạt Sao Quả Tạ và quy định đăng bán sản phẩm")
    ]
    
    output_lines = []
    for idx, (a, b) in enumerate(pairs, 1):
        v_a = _mock_embed(a)
        v_b = _mock_embed(b)
        score = compute_similarity(v_a, v_b)
        output_lines.append(f"Pair {idx}:")
        output_lines.append(f"  A: {a}")
        output_lines.append(f"  B: {b}")
        output_lines.append(f"  Actual Cosine Similarity: {score:.4f}")
        output_lines.append("")
        
    with open("tests/similarity_results.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(output_lines))
    print("Done! Similarity results written to tests/similarity_results.txt")

if __name__ == "__main__":
    run()

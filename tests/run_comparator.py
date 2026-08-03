import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from src.chunking import ChunkingStrategyComparator

def run():
    file_path = Path("data/k4_ecommerce/shopee-spaylater-guide.md")
    text = file_path.read_text(encoding="utf-8")
    
    # Loại bỏ front matter
    if text.startswith("---"):
        parts = text.split("---", 2)
        if len(parts) >= 3:
            text = parts[2].strip()
            
    res = ChunkingStrategyComparator().compare(text, chunk_size=200)
    
    output_lines = []
    for strat, stats in res.items():
        output_lines.append(f"Strategy: {strat}")
        output_lines.append(f"  Count: {stats['count']}")
        output_lines.append(f"  Avg Length: {stats['avg_length']:.2f}")
        output_lines.append("")
        
    with open("tests/comparator_results.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(output_lines))
    print("Done! Comparator results written to tests/comparator_results.txt")

if __name__ == "__main__":
    run()

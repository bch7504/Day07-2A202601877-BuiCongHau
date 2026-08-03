from __future__ import annotations

import math
import re


class FixedSizeChunker:
    """
    Split text into fixed-size chunks with optional overlap.

    Rules:
        - Each chunk is at most chunk_size characters long.
        - Consecutive chunks share overlap characters.
        - The last chunk contains whatever remains.
        - If text is shorter than chunk_size, return [text].
    """

    def __init__(self, chunk_size: int = 500, overlap: int = 50) -> None:
        self.chunk_size = chunk_size
        self.overlap = overlap

    def chunk(self, text: str) -> list[str]:
        if not text:
            return []
        if len(text) <= self.chunk_size:
            return [text]

        step = self.chunk_size - self.overlap
        chunks: list[str] = []
        for start in range(0, len(text), step):
            chunk = text[start : start + self.chunk_size]
            chunks.append(chunk)
            if start + self.chunk_size >= len(text):
                break
        return chunks


class SentenceChunker:
    """
    Split text into chunks of at most max_sentences_per_chunk sentences.

    Sentence detection: split on ". ", "! ", "? " or ".\n".
    Strip extra whitespace from each chunk.
    """

    def __init__(self, max_sentences_per_chunk: int = 3) -> None:
        self.max_sentences_per_chunk = max(1, max_sentences_per_chunk)

    def chunk(self, text: str) -> list[str]:
        if not text:
            return []
        # Tách các câu dựa trên lookbehind giữ lại dấu kết thúc câu và khoảng trắng
        sentences = re.split(r"(?<=\. )|(?<=\! )|(?<=\? )|(?<=\.\n)", text)
        sentences = [s.strip() for s in sentences if s.strip()]

        chunks = []
        for i in range(0, len(sentences), self.max_sentences_per_chunk):
            group = sentences[i : i + self.max_sentences_per_chunk]
            chunks.append(" ".join(group))
        return chunks


class RecursiveChunker:
    """
    Recursively split text using separators in priority order.

    Default separator priority:
        ["\n\n", "\n", ". ", " ", ""]
    """

    DEFAULT_SEPARATORS = ["\n\n", "\n", ". ", " ", ""]

    def __init__(self, separators: list[str] | None = None, chunk_size: int = 500) -> None:
        self.separators = self.DEFAULT_SEPARATORS if separators is None else list(separators)
        self.chunk_size = chunk_size

    def chunk(self, text: str) -> list[str]:
        if not text:
            return []
        return self._split(text, self.separators)

    def _split(self, current_text: str, remaining_separators: list[str]) -> list[str]:
        if len(current_text) <= self.chunk_size:
            return [current_text]

        if not remaining_separators:
            chunks = []
            for i in range(0, len(current_text), self.chunk_size):
                chunks.append(current_text[i : i + self.chunk_size])
            return chunks

        separator = remaining_separators[0]
        next_separators = remaining_separators[1:]

        if separator == "":
            splits = list(current_text)
        else:
            splits = current_text.split(separator)

        chunks = []
        current_chunk = []
        current_len = 0

        for part in splits:
            if len(part) > self.chunk_size:
                if current_chunk:
                    chunks.append(separator.join(current_chunk))
                    current_chunk = []
                    current_len = 0
                sub_chunks = self._split(part, next_separators)
                chunks.extend(sub_chunks)
            else:
                sep_len = len(separator) if current_chunk else 0
                if current_len + len(part) + sep_len <= self.chunk_size:
                    current_chunk.append(part)
                    current_len += len(part) + sep_len
                else:
                    if current_chunk:
                        chunks.append(separator.join(current_chunk))
                    current_chunk = [part]
                    current_len = len(part)

        if current_chunk:
            chunks.append(separator.join(current_chunk))

        return chunks


class HeadingBasedChunker:
    """
    Split text by Markdown headings (# , ## , ### ).
    If a section is larger than chunk_size, fallback to RecursiveChunker but
    prepend the section heading to each sub-chunk to preserve context.
    """

    def __init__(self, chunk_size: int = 500) -> None:
        self.chunk_size = chunk_size
        self.fallback_chunker = RecursiveChunker(chunk_size=chunk_size)

    def chunk(self, text: str) -> list[str]:
        if not text:
            return []
        # Split by headings, keeping the heading header in each part
        parts = re.split(r"(?=\n#+\s)", "\n" + text)
        chunks = []
        for part in parts:
            part = part.strip()
            if not part:
                continue

            # Extract heading title if it starts with #
            heading_match = re.match(r"^(#+\s+[^\n]+)", part)
            heading_prefix = ""
            if heading_match:
                heading_prefix = f"[{heading_match.group(1).strip()}] "

            if len(part) <= self.chunk_size:
                chunks.append(part)
            else:
                # Split sub-parts but prepend heading prefix to keep context
                sub_parts = self.fallback_chunker.chunk(part)
                for sub in sub_parts:
                    sub = sub.strip()
                    if not sub:
                        continue
                    # Avoid doubling prefix if sub-chunk already has it
                    if heading_prefix and not sub.startswith("[#"):
                        candidate = heading_prefix + sub
                        if len(candidate) <= self.chunk_size:
                            chunks.append(candidate)
                        else:
                            chunks.append(sub)
                    else:
                        chunks.append(sub)
        return chunks


class TableAwareChunker:
    """
    Identify Markdown tables and keep them intact as a single chunk.
    Non-table segments are chunked using RecursiveChunker.
    """

    def __init__(self, chunk_size: int = 500) -> None:
        self.chunk_size = chunk_size
        self.fallback_chunker = RecursiveChunker(chunk_size=chunk_size)

    def chunk(self, text: str) -> list[str]:
        if not text:
            return []
        # Regex to find Markdown tables
        table_pattern = r"(\n\|[^\n]+\n\|[\s\-\:|]+\n(?:\|[^\n]+\n?)+)"
        parts = re.split(table_pattern, text)
        chunks = []
        for part in parts:
            if not part.strip():
                continue
            # If it is a table (starts with |)
            if part.strip().startswith("|"):
                chunks.append(part.strip())
            else:
                chunks.extend(self.fallback_chunker.chunk(part))
        return chunks


class FAQPairChunker:
    """
    Split text into FAQ (Question/Answer) pairs.
    Identifies patterns like Q: / A: or Hỏi: / Đáp: or Câu hỏi: / Trả lời:.
    """

    def __init__(self, chunk_size: int = 500) -> None:
        self.chunk_size = chunk_size
        self.fallback_chunker = RecursiveChunker(chunk_size=chunk_size)

    def chunk(self, text: str) -> list[str]:
        if not text:
            return []
        # Regex to split on question starts: e.g. "Q:", "Hỏi:", "Câu hỏi:"
        q_patterns = r"(?i)\n(?:Q|Hỏi|Câu hỏi|Câu\s+\d+)\s*:"
        parts = re.split(q_patterns, "\n" + text)
        chunks = []
        first_part = parts[0].strip()
        if first_part and not re.match(q_patterns, first_part):
            # Non-FAQ preamble
            chunks.extend(self.fallback_chunker.chunk(first_part))
            parts = parts[1:]

        matches = re.findall(q_patterns, "\n" + text)
        for i, part in enumerate(parts):
            part = part.strip()
            if not part:
                continue
            prefix = matches[i].strip() if i < len(matches) else "Hỏi:"
            faq_block = f"{prefix} {part}"
            if len(faq_block) <= self.chunk_size:
                chunks.append(faq_block)
            else:
                chunks.extend(self.fallback_chunker.chunk(faq_block))
        return chunks


def _dot(a: list[float], b: list[float]) -> float:
    return sum(x * y for x, y in zip(a, b))


def compute_similarity(vec_a: list[float], vec_b: list[float]) -> float:
    """
    Compute cosine similarity between two vectors.

    cosine_similarity = dot(a, b) / (||a|| * ||b||)

    Returns 0.0 if either vector has zero magnitude.
    """
    if not vec_a or not vec_b:
        return 0.0
    dot_prod = _dot(vec_a, vec_b)
    mag_a = math.sqrt(_dot(vec_a, vec_a))
    mag_b = math.sqrt(_dot(vec_b, vec_b))
    if mag_a == 0.0 or mag_b == 0.0:
        return 0.0
    return dot_prod / (mag_a * mag_b)


class ChunkingStrategyComparator:
    """Run all built-in chunking strategies and compare their results."""

    def compare(self, text: str, chunk_size: int = 200) -> dict:
        fixed_chunker = FixedSizeChunker(chunk_size=chunk_size, overlap=0)
        fixed_chunks = fixed_chunker.chunk(text)

        sentence_chunker = SentenceChunker(max_sentences_per_chunk=3)
        sentence_chunks = sentence_chunker.chunk(text)

        recursive_chunker = RecursiveChunker(chunk_size=chunk_size)
        recursive_chunks = recursive_chunker.chunk(text)

        def get_stats(chunks):
            count = len(chunks)
            avg_len = sum(len(c) for c in chunks) / count if count > 0 else 0.0
            return {
                "count": count,
                "avg_length": avg_len,
                "chunks": chunks,
            }

        return {
            "fixed_size": get_stats(fixed_chunks),
            "by_sentences": get_stats(sentence_chunks),
            "recursive": get_stats(recursive_chunks),
        }

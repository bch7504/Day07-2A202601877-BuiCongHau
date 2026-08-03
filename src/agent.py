from typing import Callable

from .store import EmbeddingStore


class KnowledgeBaseAgent:
    """
    An agent that answers questions using a vector knowledge base.

    Retrieval-augmented generation (RAG) pattern:
        1. Retrieve top-k relevant chunks from the store.
        2. Build a prompt with the chunks as context.
        3. Call the LLM to generate an answer.
    """

    def __init__(self, store: EmbeddingStore, llm_fn: Callable[[str], str]) -> None:
        self._store = store
        self._llm_fn = llm_fn

    def answer(
        self,
        question: str,
        top_k: int = 3,
        metadata_filter: dict | None = None,
    ) -> str:
        """
        Answer a question by retrieving relevant documents, building a context prompt,
        and calling the LLM function.
        """
        if metadata_filter:
            results = self._store.search_with_filter(question, top_k=top_k, metadata_filter=metadata_filter)
        else:
            results = self._store.search(question, top_k=top_k)

        # Trích xuất nội dung từ các kết quả truy vấn
        context_parts = [r["content"] for r in results]
        context = "\n---\n".join(context_parts)

        # Xây dựng prompt RAG chuẩn
        prompt = (
            f"Context information:\n"
            f"---------------------\n"
            f"{context}\n"
            f"---------------------\n"
            f"Based on the context above, answer the question: {question}\n"
        )

        return self._llm_fn(prompt)

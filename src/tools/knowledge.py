"""
Knowledge base tool — RAG search over support articles.

Uses FAISS vector store with LangChain. Articles are loaded from
markdown files in data/knowledge/ and embedded at startup.
"""

from __future__ import annotations

from pathlib import Path

from langchain_core.tools import tool
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document

from src.utils.llm import get_embeddings
from src.utils.config import KNOWLEDGE_DIR, VECTORSTORE_DIR


_vectorstore: FAISS | None = None


def _load_articles() -> list[Document]:
    """Load all markdown files from the knowledge directory."""
    docs = []
    knowledge_path = Path(KNOWLEDGE_DIR)

    if not knowledge_path.exists():
        return docs

    for md_file in knowledge_path.glob("*.md"):
        content = md_file.read_text(encoding="utf-8")
        docs.append(Document(
            page_content=content,
            metadata={"source": md_file.name},
        ))

    return docs


def init_knowledge_base() -> FAISS:
    """Build or load the FAISS vector store from support articles."""
    global _vectorstore

    index_path = Path(VECTORSTORE_DIR) / "index.faiss"

    # Try loading existing index
    if index_path.exists():
        _vectorstore = FAISS.load_local(
            str(VECTORSTORE_DIR),
            get_embeddings(),
            allow_dangerous_deserialization=True,
        )
        print(f"[Knowledge] Loaded existing index ({_vectorstore.index.ntotal} vectors)")
        return _vectorstore

    # Build new index from articles
    docs = _load_articles()
    if not docs:
        # Create a minimal index with a placeholder
        docs = [Document(page_content="No knowledge base articles found.", metadata={"source": "placeholder"})]

    _vectorstore = FAISS.from_documents(docs, get_embeddings())
    VECTORSTORE_DIR.mkdir(parents=True, exist_ok=True)
    _vectorstore.save_local(str(VECTORSTORE_DIR))
    print(f"[Knowledge] Built new index ({len(docs)} articles)")
    return _vectorstore


def get_vectorstore() -> FAISS:
    """Return the initialised vector store."""
    global _vectorstore
    if _vectorstore is None:
        init_knowledge_base()
    return _vectorstore


@tool
def search_knowledge_base(query: str) -> str:
    """Search the support knowledge base for articles relevant to the customer's issue. Returns the most relevant article content."""
    vs = get_vectorstore()
    results = vs.similarity_search(query, k=3)

    if not results:
        return "No relevant articles found in the knowledge base."

    output = []
    for i, doc in enumerate(results, 1):
        source = doc.metadata.get("source", "unknown")
        output.append(f"--- Article {i} (source: {source}) ---\n{doc.page_content}\n")

    return "\n".join(output)

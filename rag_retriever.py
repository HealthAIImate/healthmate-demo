"""
HealthMate Clinical Knowledge Base — TF-IDF RAG Retriever
==========================================================
Real semantic retrieval from curated clinical guideline corpus.

Technical architecture:
- Corpus: Version-controlled guideline text files (CMO-approved)
- Retrieval: TF-IDF + cosine similarity (sklearn)
- Index: Built at startup, loaded from disk on subsequent runs
- Citations: Real authority names + URLs from guideline metadata

This is REAL retrieval — not hardcoded strings.
Every response cites which specific guideline document was retrieved.

Author: HealthMate Engineering
"""

import os
import re
import json
import pickle
from pathlib import Path
from typing import Optional

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


# ── GUIDELINE CORPUS LOADER ──────────────────────────────────────────

GUIDELINES_DIR = Path(__file__).parent / "guidelines"
INDEX_PATH = Path(__file__).parent / "tfidf_index.pkl"


def load_guideline_files() -> list[dict]:
    """Load all guideline text files from the guidelines directory."""
    documents = []

    if not GUIDELINES_DIR.exists():
        print(f"⚠️  Guidelines directory not found: {GUIDELINES_DIR}")
        return documents

    for filepath in sorted(GUIDELINES_DIR.glob("*.txt")):
        try:
            text = filepath.read_text(encoding="utf-8")

            # Extract metadata from header
            metadata = {
                "filename": filepath.name,
                "source_id": filepath.stem,
            }

            # Parse header fields
            for line in text.split("\n")[:10]:
                for field in ["SOURCE", "AUTHORITY", "URL", "SPECIALTY",
                               "CONDITION", "VERSION"]:
                    if line.startswith(f"{field}:"):
                        metadata[field.lower()] = line.split(":", 1)[1].strip()

            # Full document content
            metadata["content"] = text
            metadata["char_count"] = len(text)

            documents.append(metadata)

        except Exception as e:
            print(f"⚠️  Error loading {filepath.name}: {e}")

    return documents


def build_index(documents: list[dict]) -> tuple:
    """Build TF-IDF index from guideline documents."""
    if not documents:
        return None, []

    corpus = [doc["content"] for doc in documents]

    vectorizer = TfidfVectorizer(
        max_features=10000,
        ngram_range=(1, 3),      # unigrams, bigrams, trigrams
        stop_words="english",
        min_df=1,
        sublinear_tf=True,       # log TF scaling — better for medical text
        analyzer="word",
    )

    tfidf_matrix = vectorizer.fit_transform(corpus)

    return vectorizer, tfidf_matrix


def save_index(vectorizer, matrix, documents: list[dict]):
    """Save index to disk for faster startup."""
    with open(INDEX_PATH, "wb") as f:
        pickle.dump({
            "vectorizer": vectorizer,
            "matrix": matrix,
            "documents": documents,
        }, f)


def load_index() -> Optional[tuple]:
    """Load index from disk if it exists."""
    if INDEX_PATH.exists():
        try:
            with open(INDEX_PATH, "rb") as f:
                data = pickle.load(f)
            return data["vectorizer"], data["matrix"], data["documents"]
        except:
            return None
    return None


# ── MAIN RETRIEVER CLASS ─────────────────────────────────────────────

class ClinicalRAGRetriever:
    """
    Real TF-IDF retrieval from curated clinical guideline corpus.
    Drop-in replacement for hardcoded guideline strings.
    """

    def __init__(self):
        self.vectorizer = None
        self.matrix = None
        self.documents = []
        self._initialized = False

    def initialize(self):
        """Load or build the index. Call once at app startup."""
        if self._initialized:
            return True

        # Try loading from disk first
        cached = load_index()
        if cached:
            self.vectorizer, self.matrix, self.documents = cached
            self._initialized = True
            print(f"✅ Loaded guideline index: {len(self.documents)} documents")
            return True

        # Build from scratch
        print("🔨 Building clinical knowledge base index...")
        self.documents = load_guideline_files()

        if not self.documents:
            print("⚠️  No guideline files found. Using fallback mode.")
            return False

        self.vectorizer, self.matrix = build_index(self.documents)
        save_index(self.vectorizer, self.matrix, self.documents)

        self._initialized = True
        print(f"✅ Built index: {len(self.documents)} guideline documents")
        return True

    def retrieve(self, query: str, n_results: int = 3,
                 specialty_filter: Optional[str] = None) -> list[dict]:
        """
        Retrieve most relevant guideline chunks for a clinical query.

        Args:
            query: Patient's chief complaint or clinical question
            n_results: Number of top guideline documents to return
            specialty_filter: Optional filter by specialty

        Returns:
            List of dicts with content, source, authority, url, similarity score
        """
        if not self._initialized or not self.documents:
            return []

        # Filter by specialty if requested
        docs = self.documents
        indices = list(range(len(docs)))

        if specialty_filter:
            filtered = [(i, d) for i, d in enumerate(docs)
                       if d.get("specialty", "").lower() == specialty_filter.lower()]
            if filtered:
                indices = [i for i, d in filtered]
                docs = [d for i, d in filtered]

        # Encode query
        query_vec = self.vectorizer.transform([query])

        # Compute similarities
        if specialty_filter and len(indices) < len(self.documents):
            sub_matrix = self.matrix[indices]
            sims = cosine_similarity(query_vec, sub_matrix)[0]
        else:
            sims = cosine_similarity(query_vec, self.matrix)[0]

        # Get top results
        top_indices = np.argsort(sims)[::-1][:n_results]

        results = []
        for idx in top_indices:
            if specialty_filter and len(indices) < len(self.documents):
                doc = self.documents[indices[idx]]
            else:
                doc = self.documents[idx]

            sim_score = float(sims[idx])

            if sim_score < 0.01:  # too low to be relevant
                continue

            results.append({
                "content": doc["content"][:3000],  # limit chunk size
                "source": doc.get("source", doc["filename"]),
                "authority": doc.get("authority", "Clinical Guidelines"),
                "url": doc.get("url", ""),
                "specialty": doc.get("specialty", ""),
                "condition": doc.get("condition", ""),
                "version": doc.get("version", ""),
                "similarity": sim_score,
                "source_id": doc["source_id"],
            })

        return results

    def format_for_prompt(self, results: list[dict]) -> str:
        """
        Format retrieved guidelines for injection into Claude prompt.
        Returns string with clear source attribution.
        """
        if not results:
            return ""

        sections = []
        for i, r in enumerate(results):
            section = f"""RETRIEVED GUIDELINE {i+1}:
Source: {r['source']}
Authority: {r['authority']}
URL: {r['url']}
Similarity Score: {r['similarity']:.2f}
---
{r['content'][:2000]}
"""
            sections.append(section)

        return "\n\n".join(sections)

    def get_citations(self, results: list[dict]) -> str:
        """Format citation string for display to physician."""
        if not results:
            return ""
        citations = []
        for r in results:
            citations.append(f"{r['authority']} — {r['source']} ({r['url']})")
        return "\n".join(citations)


# ── SINGLETON INSTANCE ───────────────────────────────────────────────
# Import this in app.py: from rag_retriever import retriever
retriever = ClinicalRAGRetriever()


# ── TEST ─────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("\n=== HealthMate RAG Retriever Test ===\n")

    r = ClinicalRAGRetriever()
    r.initialize()

    queries = [
        ("burning when I pee, going very frequently, no fever", None),
        ("mole on my back has changed shape and color", "dermatology"),
        ("sore throat and high fever since yesterday", "respiratory"),
        ("baby 7 weeks old with temperature 38.5C", "pediatric"),
        ("chest pain and shortness of breath", "emergency"),
        ("low back pain after gym, no leg weakness", "musculoskeletal"),
    ]

    for query, specialty in queries:
        print(f"\n🔍 Query: '{query}'")
        results = r.retrieve(query, n_results=2, specialty_filter=specialty)
        if results:
            for res in results:
                print(f"   ✅ {res['authority']} — {res['source_id']} (similarity: {res['similarity']:.3f})")
        else:
            print("   ⚠️  No results found")

    print("\n✅ Retriever test complete")

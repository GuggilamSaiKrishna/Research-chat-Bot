import json
import re
from pathlib import Path

import chromadb
from langchain_chroma import Chroma
from langchain_google_genai import GoogleGenerativeAIEmbeddings

from config import CHROMA_DIR, FACULTY_JSON, get_google_api_key
from tools.load_data import ensure_chroma_loaded


def get_db() -> Chroma | None:
    try:
        ensure_chroma_loaded()
        api_key = get_google_api_key()
        if not api_key:
            return None
        embeddings = GoogleGenerativeAIEmbeddings(
            model="gemini-embedding-001",
            google_api_key=api_key,
        )
        client = chromadb.PersistentClient(path=CHROMA_DIR)
        return Chroma(
            client=client,
            collection_name="langchain",
            embedding_function=embeddings,
        )
    except Exception as e:
        print(f"Warning: Could not connect to Chroma DB: {e}")
        return None


def _calculate_similarity(score: float) -> float:
    cos_sim = max(0.0, 1.0 - (score / 2.0))
    return round(cos_sim * 100, 2)


def fallback_retrieve_faculty(query: str, k: int = 5):
    if not Path(FACULTY_JSON).exists():
        return []

    with open(FACULTY_JSON, "r", encoding="utf-8") as f:
        faculty = json.load(f)

    query_tokens = set(re.findall(r"\w+", query.lower()))
    clean_query = query.strip().lower()

    scored = []
    for prof in faculty:
        name = prof.get("name", "Unknown")
        department = prof.get("department", "N/A")
        mobile = prof.get("mobile_number") or prof.get("mobile") or "N/A"
        research_areas = prof.get("research_areas", [])
        publications = prof.get("publications", [])

        # STRICT: Only match faculty who have publications
        if not publications:
            continue

        full_profile = f"""Name: {name}
Department: {department}
Mobile Number: {mobile}
Research Areas: {', '.join(research_areas)}
Publications: {', '.join(publications)}"""

        pub_text = " ".join(publications).lower()
        pub_tokens = set(re.findall(r"\w+", pub_text))

        # Check exact match in publications
        is_exact_pub = any(clean_query == pub.lower() or clean_query in pub.lower() for pub in publications)

        if is_exact_pub:
            pub_score = 100.0
        elif query_tokens and pub_tokens:
            common_pub = query_tokens.intersection(pub_tokens)
            pub_score = round(min(95.0, (len(common_pub) / len(query_tokens)) * 90.0), 2) if common_pub else 0.0
        else:
            pub_score = 0.0

        if pub_score > 0:
            scored.append({
                "name": name,
                "department": department,
                "mobile_number": str(mobile),
                "research_areas": ", ".join(research_areas),
                "publications": ", ".join(publications),
                "score": pub_score,
                "content": full_profile,
            })

    scored.sort(key=lambda x: x["score"], reverse=True)
    return scored[:k] if k else scored


def retrieve_faculty(query: str, k: int = 5):
    try:
        db = get_db()
        if db is None:
            return fallback_retrieve_faculty(query, k=k)

        total = db._collection.count()
        if total == 0:
            return fallback_retrieve_faculty(query, k=k)

        # Retrieve matching publication documents
        fetch_k = min(total, (k * 2) if k else total)
        results = db.similarity_search_with_score(query, k=fetch_k or total)
        clean_query = query.strip().lower()

        matches_dict = {}

        for doc, score in results:
            similarity = _calculate_similarity(score)
            name = doc.metadata.get("name", "Unknown")
            publications_text = doc.metadata.get("publications", "").strip()

            # Strictly require publications
            if not publications_text or publications_text == "N/A":
                continue

            # Exact keyword match in publications boost
            if clean_query and clean_query in publications_text.lower():
                similarity = 100.0

            if name not in matches_dict or similarity > matches_dict[name]["score"]:
                matches_dict[name] = {
                    "name": name,
                    "department": doc.metadata.get("department", "N/A"),
                    "mobile_number": doc.metadata.get("mobile_number", "N/A"),
                    "research_areas": doc.metadata.get("research_areas", "N/A"),
                    "publications": publications_text,
                    "score": similarity,
                    "content": doc.metadata.get("full_profile") or doc.page_content,
                }

        matches = list(matches_dict.values())
        matches.sort(key=lambda match: match["score"], reverse=True)
        if matches:
            return matches[:k] if k else matches
        return fallback_retrieve_faculty(query, k=k)

    except Exception as e:
        print(f"Vector retrieval exception ({e}), falling back to direct search.")
        return fallback_retrieve_faculty(query, k=k)


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

        full_profile = f"""Name: {name}
Department: {department}
Mobile Number: {mobile}
Research Areas: {', '.join(research_areas)}
Publications: {', '.join(publications)}"""

        pub_text = " ".join(publications).lower()
        area_text = " ".join(research_areas).lower()

        pub_tokens = set(re.findall(r"\w+", pub_text))
        area_tokens = set(re.findall(r"\w+", area_text))

        # Check exact matches
        is_exact_pub = any(clean_query == pub.lower() or clean_query in pub.lower() for pub in publications)
        is_exact_area = any(clean_query == area.lower() or clean_query in area.lower() for area in research_areas)

        if is_exact_pub:
            pub_score = 100.0
        elif query_tokens and pub_tokens:
            common_pub = query_tokens.intersection(pub_tokens)
            pub_score = round(min(95.0, (len(common_pub) / len(query_tokens)) * 90.0), 2) if common_pub else 0.0
        else:
            pub_score = 0.0

        if is_exact_area:
            area_score = 100.0
        elif query_tokens and area_tokens:
            common_area = query_tokens.intersection(area_tokens)
            area_score = round(min(95.0, (len(common_area) / len(query_tokens)) * 90.0), 2) if common_area else 0.0
        else:
            area_score = 0.0

        # Hierarchical scoring: Publications first (70%), Research Areas second (30%)
        if pub_score > 0:
            final_score = round((0.70 * pub_score) + (0.30 * area_score), 2)
        elif area_score > 0:
            # Scaled score when only general research areas match without publications
            final_score = round(0.50 * area_score, 2)
        else:
            final_score = 0.0

        if final_score > 0:
            scored.append({
                "name": name,
                "department": department,
                "mobile_number": str(mobile),
                "research_areas": ", ".join(research_areas),
                "publications": ", ".join(publications),
                "pub_score": pub_score,
                "area_score": area_score,
                "score": final_score,
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

        # Retrieve all candidate documents to compute multi-field scores
        results = db.similarity_search_with_score(query, k=total)
        clean_query = query.strip().lower()

        faculty_records = {}

        for doc, score in results:
            similarity = _calculate_similarity(score)
            name = doc.metadata.get("name", "Unknown")
            doc_type = doc.metadata.get("doc_type", "general")

            if name not in faculty_records:
                faculty_records[name] = {
                    "name": name,
                    "department": doc.metadata.get("department", "N/A"),
                    "mobile_number": doc.metadata.get("mobile_number", "N/A"),
                    "research_areas": doc.metadata.get("research_areas", ""),
                    "publications": doc.metadata.get("publications", ""),
                    "full_profile": doc.metadata.get("full_profile") or doc.page_content,
                    "pub_sim": 0.0,
                    "area_sim": 0.0,
                    "has_publications": bool(doc.metadata.get("publications")),
                }

            if doc_type == "publication":
                faculty_records[name]["pub_sim"] = max(
                    faculty_records[name]["pub_sim"], similarity
                )
            elif doc_type == "research_area":
                faculty_records[name]["area_sim"] = max(
                    faculty_records[name]["area_sim"], similarity
                )
            else:
                faculty_records[name]["area_sim"] = max(
                    faculty_records[name]["area_sim"], similarity
                )

        # Compute final hierarchical match score
        matches = []
        for record in faculty_records.values():
            pub_sim = record["pub_sim"]
            area_sim = record["area_sim"]
            pub_text = record["publications"].lower()
            area_text = record["research_areas"].lower()

            # Exact keyword boost
            if clean_query and clean_query in pub_text:
                pub_sim = 100.0
            if clean_query and clean_query in area_text:
                area_sim = 100.0

            if pub_sim > 0:
                # Publications primary (70%), Research Areas secondary (30%)
                final_score = round((0.70 * pub_sim) + (0.30 * area_sim), 2)
            elif area_sim > 0:
                # Scaled score for research areas without publications
                final_score = round(0.50 * area_sim, 2)
            else:
                final_score = 0.0

            if final_score > 0:
                matches.append({
                    "name": record["name"],
                    "department": record["department"],
                    "mobile_number": record["mobile_number"],
                    "research_areas": record["research_areas"],
                    "publications": record["publications"],
                    "pub_score": pub_sim,
                    "area_score": area_sim,
                    "score": final_score,
                    "content": record["full_profile"],
                })

        matches.sort(key=lambda match: match["score"], reverse=True)
        if matches:
            return matches[:k] if k else matches
        return fallback_retrieve_faculty(query, k=k)

    except Exception as e:
        print(f"Vector retrieval exception ({e}), falling back to direct search.")
        return fallback_retrieve_faculty(query, k=k)


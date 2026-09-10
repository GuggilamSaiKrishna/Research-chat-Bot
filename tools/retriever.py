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
    # Filter out basic stop words for token matching
    stop_words = {"for", "in", "and", "the", "of", "to", "a", "with", "on", "using", "by", "an"}
    significant_query_tokens = {t for t in query_tokens if t not in stop_words and len(t) > 1}
    if not significant_query_tokens:
        significant_query_tokens = query_tokens

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

        matching_pubs_scored = []
        for pub in publications:
            pub_lower = pub.lower()
            pub_tokens = set(re.findall(r"\w+", pub_lower))

            if clean_query and (clean_query == pub_lower or clean_query in pub_lower):
                pub_score = 100.0
            elif significant_query_tokens and pub_tokens:
                common = significant_query_tokens.intersection(pub_tokens)
                if common:
                    pub_score = round(min(95.0, (len(common) / len(significant_query_tokens)) * 90.0), 2)
                else:
                    pub_score = 0.0
            else:
                pub_score = 0.0

            if pub_score > 0:
                matching_pubs_scored.append((pub, pub_score))

        # Check match against research areas if no direct pub title match
        research_text = " ".join(research_areas).lower()
        research_tokens = set(re.findall(r"\w+", research_text))
        area_common = significant_query_tokens.intersection(research_tokens) if significant_query_tokens else set()

        if matching_pubs_scored:
            matching_pubs_scored.sort(key=lambda x: x[1], reverse=True)
            matched_pubs = [p[0] for p in matching_pubs_scored[:2]]
            best_score = matching_pubs_scored[0][1]
        elif area_common:
            # Query matches research area: pick top relevant publications that overlap with research/query tokens
            pub_scores = []
            for pub in publications:
                p_tokens = set(re.findall(r"\w+", pub.lower()))
                overlap = len(p_tokens.intersection(research_tokens.union(significant_query_tokens)))
                pub_scores.append((pub, overlap))
            pub_scores.sort(key=lambda x: x[1], reverse=True)
            matched_pubs = [p[0] for p in pub_scores[:2]]  # Top 2 relevant
            best_score = round(min(85.0, (len(area_common) / len(significant_query_tokens)) * 80.0), 2) if significant_query_tokens else 70.0
        else:
            continue

        full_profile = f"""Name: {name}
Department: {department}
Mobile Number: {mobile}
Research Areas: {', '.join(research_areas)}
Matching Publications: {', '.join(matched_pubs)}"""

        scored.append({
            "name": name,
            "department": department,
            "mobile_number": str(mobile),
            "research_areas": ", ".join(research_areas),
            "publications": ", ".join(matched_pubs),
            "matching_publications": matched_pubs,
            "score": best_score,
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
        fetch_k = min(total, max(30, (k * 6) if k else total))
        results = db.similarity_search_with_score(query, k=fetch_k)
        clean_query = query.strip().lower()

        stop_words = {"for", "in", "and", "the", "of", "to", "a", "with", "on", "using", "by", "an"}
        query_tokens = set(re.findall(r"\w+", clean_query))
        significant_tokens = {t for t in query_tokens if t not in stop_words and len(t) > 1}

        # Broad domain vs specific query detection
        broad_terms = ["healthcare", "health", "medical", "clinical"]
        is_broad_healthcare = any(term in clean_query for term in broad_terms)

        matches_dict = {}

        for doc, score in results:
            similarity = _calculate_similarity(score)
            name = doc.metadata.get("name", "Unknown")
            department = doc.metadata.get("department", "N/A")
            mobile = doc.metadata.get("mobile_number", "N/A")
            research_areas = doc.metadata.get("research_areas", "N/A")

            pub = doc.metadata.get("publication")
            if not pub:
                pubs_text = doc.metadata.get("publications", "").strip()
                if not pubs_text or pubs_text == "N/A":
                    continue
                pub_list = [p.strip() for p in pubs_text.split(",") if p.strip()]
            else:
                pub_list = [pub.strip()]

            for p in pub_list:
                p_lower = p.lower()
                p_tokens = set(re.findall(r"\w+", p_lower))
                token_overlap = len(significant_tokens.intersection(p_tokens)) if significant_tokens else 0

                is_exact = bool(clean_query and clean_query in p_lower)
                has_domain_match = is_broad_healthcare and any(w in p_lower for w in ["health", "medical", "disease", "patient", "cancer", "carcinoma", "seizure", "epileptic", "heart", "lung", "brain", "clinical", "eeg", "diabetic", "tumor"])

                # Exclude agricultural plant papers for healthcare queries
                if is_broad_healthcare and any(ag in p_lower for ag in ["apple plants", "crop", "farming", "agriculture", "plant"]):
                    continue

                # STRICT RULE: Publication MUST directly match query tokens, query substring, or broad domain
                if not (is_exact or token_overlap > 0 or has_domain_match):
                    # Hide non-matching publication completely
                    continue

                # Score matching publication
                p_sim = similarity
                if is_exact:
                    p_sim = 100.0
                elif token_overlap > 0:
                    p_sim = max(p_sim, 80.0 + (token_overlap * 5.0))
                else:
                    p_sim = max(p_sim, 75.0)

                if name not in matches_dict:
                    matches_dict[name] = {
                        "name": name,
                        "department": department,
                        "mobile_number": mobile,
                        "research_areas": research_areas,
                        "matching_pubs_dict": {},
                        "score": p_sim,
                        "full_profile": doc.metadata.get("full_profile", ""),
                    }

                current_dict = matches_dict[name]["matching_pubs_dict"]
                if p not in current_dict or p_sim > current_dict[p]:
                    current_dict[p] = p_sim

                if p_sim > matches_dict[name]["score"]:
                    matches_dict[name]["score"] = p_sim

        formatted_matches = []
        for name, data in matches_dict.items():
            if not data["matching_pubs_dict"]:
                continue

            # Sort matching publications by score
            sorted_pubs = sorted(data["matching_pubs_dict"].items(), key=lambda x: x[1], reverse=True)
            filtered_pubs = [p[0] for p in sorted_pubs]

            pubs_str = ", ".join(filtered_pubs)

            full_profile = f"""Name: {name}
Department: {data['department']}
Mobile Number: {data['mobile_number']}
Research Areas: {data['research_areas']}
Matching Publications: {pubs_str}"""

            formatted_matches.append({
                "name": name,
                "department": data["department"],
                "mobile_number": str(data["mobile_number"]),
                "research_areas": data["research_areas"],
                "publications": pubs_str,
                "matching_publications": filtered_pubs,
                "score": data["score"],
                "content": full_profile,
            })

        formatted_matches.sort(key=lambda match: match["score"], reverse=True)
        if formatted_matches:
            return formatted_matches[:k] if k else formatted_matches
        return fallback_retrieve_faculty(query, k=k)

    except Exception as e:
        print(f"Vector retrieval exception ({e}), falling back to direct search.")
        return fallback_retrieve_faculty(query, k=k)


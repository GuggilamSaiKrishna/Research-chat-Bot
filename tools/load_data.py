import hashlib
import json
import shutil
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_google_genai import GoogleGenerativeAIEmbeddings

from config import CHROMA_DIR, FACULTY_JSON, get_google_api_key

HASH_FILE = Path(CHROMA_DIR) / ".data_hash"


def _get_data_hash() -> str:
    if not Path(FACULTY_JSON).exists():
        return ""
    with open(FACULTY_JSON, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def _build_documents():
    if not Path(FACULTY_JSON).exists():
        return []

    with open(FACULTY_JSON, "r", encoding="utf-8") as f:
        faculty = json.load(f)

    documents = []
    for prof in faculty:
        name = prof.get("name", "Unknown").strip()
        department = prof.get("department", "N/A").strip()
        mobile = prof.get("mobile_number") or prof.get("mobile") or "N/A"
        research_areas = prof.get("research_areas", [])
        publications = prof.get("publications", [])

        # Strictly index only faculty who have publications
        if not publications:
            continue

        full_profile = f"""Name: {name}
Department: {department}
Mobile Number: {mobile}
Research Areas: {', '.join(research_areas)}
Publications: {', '.join(publications)}"""

        pub_text = f"Faculty: {name}. Publications: {'; '.join(publications)}"

        documents.append(
            Document(
                page_content=pub_text,
                metadata={
                    "name": name,
                    "department": department,
                    "mobile_number": str(mobile).strip(),
                    "research_areas": ", ".join(research_areas),
                    "publications": ", ".join(publications),
                    "full_profile": full_profile,
                },
            )
        )

    return documents



def chroma_is_ready() -> bool:
    return chroma_is_up_to_date()


def chroma_is_up_to_date() -> bool:
    if not Path(CHROMA_DIR).exists() or not HASH_FILE.exists():
        return False

    stored_hash = HASH_FILE.read_text(encoding="utf-8").strip()
    if stored_hash != _get_data_hash():
        return False

    try:
        embeddings = GoogleGenerativeAIEmbeddings(
            model="gemini-embedding-001",
            google_api_key=get_google_api_key(),
        )
        import chromadb
        client = chromadb.PersistentClient(path=CHROMA_DIR)
        db = Chroma(client=client, collection_name="langchain", embedding_function=embeddings)
        return db._collection.count() > 0
    except Exception:
        return False


def load_faculty_data(rebuild: bool = False) -> bool:
    current_hash = _get_data_hash()

    if not rebuild and chroma_is_up_to_date():
        return False

    Path(CHROMA_DIR).mkdir(parents=True, exist_ok=True)

    documents = _build_documents()
    if documents:
        try:
            embeddings = GoogleGenerativeAIEmbeddings(
                model="gemini-embedding-001",
                google_api_key=get_google_api_key(),
            )
            import chromadb

            client = chromadb.PersistentClient(path=CHROMA_DIR)
            try:
                client.delete_collection("langchain")
            except Exception:
                pass

            Chroma.from_documents(
                documents=documents,
                embedding=embeddings,
                client=client,
                collection_name="langchain",
            )
            HASH_FILE.write_text(current_hash, encoding="utf-8")
            return True
        except Exception as e:
            print(f"Warning: Chroma vector DB loading failed ({e}). Fallback search will be used.")
            return False

    return True


def ensure_chroma_loaded(force: bool = False) -> bool:
    try:
        return load_faculty_data(rebuild=force)
    except Exception as e:
        print(f"Warning: ensure_chroma_loaded error: {e}")
        return False


if __name__ == "__main__":
    reloaded = load_faculty_data(rebuild=True)
    print("Faculty profiles process completed!")

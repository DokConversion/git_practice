"""
RAG Query: Relevante Chunks aus der Mastermind-Wissensdatenbank abrufen.

Wird von allen Agenten vor jeder Aufgabe aufgerufen, um Marcs
proprietäres Insider-Wissen in den Prompt zu injizieren.

Verwendung:
    from knowledge_base.query import hole_wissen
    kontext = hole_wissen("Best practices Meta Ads Health Nische", n=3)
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from config_colitis import KB_PATH

_collection = None  # Lazy-init Cache


def _get_collection():
    global _collection
    if _collection is not None:
        return _collection

    try:
        import chromadb
        from chromadb.utils import embedding_functions
    except ImportError:
        return None

    kb_path = Path(KB_PATH)
    if not kb_path.exists():
        return None

    client = chromadb.PersistentClient(path=str(kb_path))
    try:
        ef = embedding_functions.DefaultEmbeddingFunction()
        _collection = client.get_collection(
            name="mastermind_wissen",
            embedding_function=ef
        )
        return _collection
    except Exception:
        return None


def hole_wissen(frage: str, n: int = 3, kategorie: str = None) -> str:
    """
    Sucht die n relevantesten Wissens-Chunks für eine Frage.

    Args:
        frage: Suchanfrage (z.B. "Wie baue ich einen Tiny Offer Funnel?")
        n: Anzahl der Chunks (Standard: 3)
        kategorie: Optional filtern nach 'media_buying', 'funnels', 'offers'

    Returns:
        Formatierter String mit relevanten Wissens-Ausschnitten,
        oder leerer String wenn keine Datenbank vorhanden.
    """
    collection = _get_collection()

    if collection is None or collection.count() == 0:
        return ""  # Kein Wissen → Agent arbeitet ohne RAG-Kontext

    where = {"kategorie": kategorie} if kategorie else None

    try:
        results = collection.query(
            query_texts=[frage],
            n_results=min(n, collection.count()),
            where=where
        )
    except Exception as e:
        return ""

    docs      = results.get("documents", [[]])[0]
    metadaten = results.get("metadatas", [[]])[0]

    if not docs:
        return ""

    teile = ["=== RELEVANTES INSIDER-WISSEN (aus Mastermind-Unterlagen) ==="]
    for i, (doc, meta) in enumerate(zip(docs, metadaten), 1):
        quelle = f"{meta.get('kategorie', '?')}/{meta.get('datei', '?')}"
        teile.append(f"\n[Quelle {i}: {quelle}]\n{doc.strip()}")
    teile.append("=" * 60)

    return "\n".join(teile)


def wissen_verfuegbar() -> bool:
    """Prüft ob die Wissensdatenbank befüllt ist."""
    collection = _get_collection()
    return collection is not None and collection.count() > 0


def wissen_stats() -> dict:
    """Gibt Statistiken über die Wissensdatenbank zurück."""
    collection = _get_collection()
    if collection is None:
        return {"status": "nicht initialisiert", "chunks": 0}

    count = collection.count()
    return {
        "status": "aktiv" if count > 0 else "leer",
        "chunks": count,
        "hinweis": "" if count > 0
                   else "Bitte Mastermind-Dokumente in knowledge_base/docs/ ablegen und ingest.py ausführen"
    }


if __name__ == "__main__":
    print("[KB] Status:", wissen_stats())
    if wissen_verfuegbar():
        test = hole_wissen("Meta Ads Strategie Health Nische", n=2)
        print(test)

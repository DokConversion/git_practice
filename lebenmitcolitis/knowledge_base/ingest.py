"""
RAG Ingestion: Mastermind-Dokumente in ChromaDB laden.

Einmalig ausführen wenn neue Dokumente in knowledge_base/docs/ abgelegt werden:
    python knowledge_base/ingest.py

Unterstützte Formate: PDF, DOCX, TXT, MD
Audio (MP3/MP4) → erst mit Whisper transkribieren, dann als TXT ablegen.

Verzeichnisstruktur:
    knowledge_base/docs/media_buying/   ← Meta/Google Ads Strategien
    knowledge_base/docs/funnels/        ← Funnel-Frameworks, Copy-Systeme
    knowledge_base/docs/offers/         ← Offer-Creation, Pricing, Upsells
"""

import os
import sys
import hashlib
from pathlib import Path

# Projektpfad hinzufügen
sys.path.insert(0, str(Path(__file__).parent.parent))
from config_colitis import KB_PATH, KB_DOCS_PATH, KB_CHUNK_SIZE, KB_CHUNK_OVERLAP

try:
    import chromadb
    from chromadb.utils import embedding_functions
except ImportError:
    print("[FEHLER] chromadb nicht installiert. Bitte: pip install chromadb")
    sys.exit(1)

try:
    import PyPDF2
except ImportError:
    PyPDF2 = None

try:
    import docx
except ImportError:
    docx = None


def lade_txt(pfad: Path) -> str:
    return pfad.read_text(encoding="utf-8", errors="ignore")


def lade_pdf(pfad: Path) -> str:
    if PyPDF2 is None:
        print(f"  [SKIP] PyPDF2 nicht installiert → {pfad.name}")
        return ""
    text = []
    with open(pfad, "rb") as f:
        reader = PyPDF2.PdfReader(f)
        for page in reader.pages:
            text.append(page.extract_text() or "")
    return "\n".join(text)


def lade_docx(pfad: Path) -> str:
    if docx is None:
        print(f"  [SKIP] python-docx nicht installiert → {pfad.name}")
        return ""
    doc = docx.Document(str(pfad))
    return "\n".join(p.text for p in doc.paragraphs if p.text.strip())


def lade_dokument(pfad: Path) -> str:
    suffix = pfad.suffix.lower()
    if suffix in (".txt", ".md"):
        return lade_txt(pfad)
    elif suffix == ".pdf":
        return lade_pdf(pfad)
    elif suffix == ".docx":
        return lade_docx(pfad)
    else:
        return ""


def chunk_text(text: str, chunk_size: int = KB_CHUNK_SIZE,
               overlap: int = KB_CHUNK_OVERLAP) -> list[str]:
    """Teilt langen Text in überlappende Chunks auf."""
    words = text.split()
    chunks = []
    i = 0
    while i < len(words):
        chunk = " ".join(words[i: i + chunk_size])
        if chunk.strip():
            chunks.append(chunk)
        i += chunk_size - overlap
    return chunks


def kategorie_aus_pfad(pfad: Path) -> str:
    """Leitet Kategorie aus Unterverzeichnis ab."""
    parts = pfad.parts
    docs_idx = next((i for i, p in enumerate(parts) if p == "docs"), None)
    if docs_idx is not None and docs_idx + 1 < len(parts):
        return parts[docs_idx + 1]
    return "allgemein"


def datei_hash(pfad: Path) -> str:
    return hashlib.md5(pfad.read_bytes()).hexdigest()


def ingest_alle_dokumente(force: bool = False):
    """
    Liest alle Dokumente aus KB_DOCS_PATH ein und speichert Chunks in ChromaDB.
    force=True: Alle Dokumente neu einlesen (auch bereits verarbeitete).
    """
    docs_path = Path(KB_DOCS_PATH)
    if not docs_path.exists():
        docs_path.mkdir(parents=True)
        print(f"[KB] Verzeichnis erstellt: {docs_path}")
        print("[KB] Bitte Mastermind-Dokumente in folgende Ordner ablegen:")
        print("     knowledge_base/docs/media_buying/  ← Meta/Google Ads Strategien")
        print("     knowledge_base/docs/funnels/       ← Funnel-Frameworks")
        print("     knowledge_base/docs/offers/        ← Offer & Pricing Strategien")
        return

    # ChromaDB Client initialisieren
    client = chromadb.PersistentClient(path=KB_PATH)

    # Embedding-Funktion: Standard SentenceTransformer (lokal, kostenlos)
    ef = embedding_functions.DefaultEmbeddingFunction()
    collection = client.get_or_create_collection(
        name="mastermind_wissen",
        embedding_function=ef,
        metadata={"hnsw:space": "cosine"}
    )

    # Hash-Tracking (um doppelte Ingestion zu vermeiden)
    hash_file = Path(KB_PATH) / "processed_hashes.txt"
    processed = set()
    if hash_file.exists() and not force:
        processed = set(hash_file.read_text().splitlines())

    neue_chunks = 0
    neue_dateien = 0

    alle_dateien = list(docs_path.rglob("*"))
    dokument_dateien = [f for f in alle_dateien
                        if f.is_file() and f.suffix.lower() in (".txt", ".md", ".pdf", ".docx")]

    if not dokument_dateien:
        print("[KB] Keine Dokumente gefunden. Bitte Dateien in knowledge_base/docs/ ablegen.")
        return

    for pfad in dokument_dateien:
        h = datei_hash(pfad)
        if h in processed:
            print(f"  [SKIP] Bereits verarbeitet: {pfad.name}")
            continue

        print(f"  [LESE] {pfad.relative_to(docs_path.parent)}")
        text = lade_dokument(pfad)
        if not text.strip():
            print(f"  [LEER] Kein Text extrahiert aus: {pfad.name}")
            continue

        chunks = chunk_text(text)
        kategorie = kategorie_aus_pfad(pfad)

        ids       = [f"{h}_{i}" for i in range(len(chunks))]
        metadaten = [{"datei": pfad.name, "kategorie": kategorie,
                      "chunk_nr": i, "gesamt_chunks": len(chunks)}
                     for i in range(len(chunks))]

        # In Batches von 100 einfügen
        batch = 100
        for start in range(0, len(chunks), batch):
            collection.upsert(
                documents=chunks[start:start + batch],
                ids=ids[start:start + batch],
                metadatas=metadaten[start:start + batch]
            )

        processed.add(h)
        neue_chunks += len(chunks)
        neue_dateien += 1
        print(f"  [OK]   {len(chunks)} Chunks aus '{pfad.name}' (Kategorie: {kategorie})")

    # Hashes speichern
    Path(KB_PATH).mkdir(parents=True, exist_ok=True)
    hash_file.write_text("\n".join(processed))

    print(f"\n[KB] Fertig: {neue_dateien} neue Dateien, {neue_chunks} neue Chunks")
    print(f"[KB] Gesamt in DB: {collection.count()} Chunks")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Mastermind-Dokumente in ChromaDB laden")
    parser.add_argument("--force", action="store_true",
                        help="Alle Dokumente neu einlesen (ignoriert Cache)")
    args = parser.parse_args()
    ingest_alle_dokumente(force=args.force)

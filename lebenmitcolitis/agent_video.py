"""
Video Production Agent
Generiert kurze Video-Ads (15-30 Sek) via Google Gemini Veo 2.
Nutzt UGC-Scripts aus dem Creative Director Agent.
Output: MP4-Dateien → direkt upload-ready für Meta/Google.
"""

import base64
import json
import sys
import time
from datetime import datetime
from pathlib import Path

import httpx

sys.path.insert(0, str(Path(__file__).parent))
from config_colitis import (
    GOOGLE_AI_API_KEY, VEO_MODEL,
    PROJECT_NAME, VIDEO_OUTPUT_DIR, REPORTS_DIR
)
from db_colitis import init_db


# ─── Veo 2 API ───────────────────────────────────────────────────────────────────

VEO_API_BASE = "https://generativelanguage.googleapis.com/v1beta"


def starte_video_generierung(prompt: str,
                              dauer_sekunden: int = 8,
                              format: str = "9:16") -> str | None:
    """
    Startet Video-Generierung via Veo 2 (asynchron).
    Gibt Operation-Name zurück für Status-Polling.
    """
    if not GOOGLE_AI_API_KEY:
        print("  [Veo2] GOOGLE_AI_API_KEY fehlt")
        return None

    aspect_map = {"9:16": "portrait", "1:1": "square", "16:9": "landscape"}
    aspect = aspect_map.get(format, "portrait")

    url = f"{VEO_API_BASE}/models/{VEO_MODEL}:generateVideos?key={GOOGLE_AI_API_KEY}"

    payload = {
        "prompt": {"text": prompt},
        "generateVideoConfig": {
            "durationSeconds": dauer_sekunden,
            "aspectRatio": aspect,
            "numberOfVideos": 1,
            "fps": 24,
        },
    }

    try:
        with httpx.Client(timeout=30) as client:
            resp = client.post(url, json=payload)
            resp.raise_for_status()
            data = resp.json()
            operation_name = data.get("name", "")
            print(f"  [Veo2] Generierung gestartet: {operation_name[:50]}...")
            return operation_name
    except Exception as e:
        print(f"  [Veo2] Start-Fehler: {e}")
        return None


def prüfe_video_status(operation_name: str,
                        max_wartesekunden: int = 300) -> bytes | None:
    """
    Pollt den Status der Video-Generierung.
    Gibt Video-Bytes zurück wenn fertig, None bei Fehler.
    """
    if not operation_name or not GOOGLE_AI_API_KEY:
        return None

    url = f"{VEO_API_BASE}/{operation_name}?key={GOOGLE_AI_API_KEY}"
    warte_intervall = 10  # Sekunden zwischen Polls
    wartezeit = 0

    print(f"  [Veo2] Warte auf Fertigstellung (max {max_wartesekunden}s)...")

    while wartezeit < max_wartesekunden:
        time.sleep(warte_intervall)
        wartezeit += warte_intervall

        try:
            with httpx.Client(timeout=20) as client:
                resp = client.get(url)
                resp.raise_for_status()
                data = resp.json()

                if data.get("done"):
                    # Video fertig
                    antwort = data.get("response", {})
                    videos = antwort.get("generatedVideos", [])
                    if videos:
                        video_uri = videos[0].get("video", {}).get("uri", "")
                        if video_uri:
                            # Video herunterladen
                            with httpx.Client(timeout=60) as dl_client:
                                video_resp = dl_client.get(
                                    f"{video_uri}&key={GOOGLE_AI_API_KEY}"
                                )
                                print(f"  [Veo2] Video fertig nach {wartezeit}s ✓")
                                return video_resp.content

                    print(f"  [Veo2] Fertig aber kein Video in Response")
                    return None

                print(f"  [Veo2] Noch in Bearbeitung... ({wartezeit}s)")

        except Exception as e:
            print(f"  [Veo2] Poll-Fehler: {e}")

    print(f"  [Veo2] Timeout nach {max_wartesekunden}s")
    return None


def generiere_video(prompt: str,
                     dauer: int = 8,
                     format: str = "9:16") -> bytes | None:
    """Komplett-Wrapper: Starten + Warten + Video zurückgeben."""
    operation = starte_video_generierung(prompt, dauer, format)
    if not operation:
        return None
    return prüfe_video_status(operation)


def speichere_video(video_bytes: bytes, dateiname: str) -> str:
    Path(VIDEO_OUTPUT_DIR).mkdir(parents=True, exist_ok=True)
    pfad = f"{VIDEO_OUTPUT_DIR}/{dateiname}"
    Path(pfad).write_bytes(video_bytes)
    return pfad


# ─── Video Prompts aus UGC Scripts ──────────────────────────────────────────────

def lade_aktuelle_scripts() -> list[dict]:
    """Lädt UGC Scripts vom heutigen Tag (aus Creative Director Output)."""
    datum = datetime.now().strftime("%Y-%m-%d")
    creative_pfad = Path(f"output/creatives/creative_output_{datum}.json")

    if creative_pfad.exists():
        data = json.loads(creative_pfad.read_text(encoding="utf-8"))
        return data.get("ugc_scripts", [])

    # Fallback: Gestern
    gestern = datetime.now().strftime("%Y-%m-%d")
    for i in range(1, 8):
        from datetime import timedelta
        d = (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d")
        pfad = Path(f"output/creatives/creative_output_{d}.json")
        if pfad.exists():
            data = json.loads(pfad.read_text(encoding="utf-8"))
            return data.get("ugc_scripts", [])

    return []


def script_zu_veo_prompt(script: dict) -> str:
    """Konvertiert UGC Script in Veo 2 optimierten Prompt."""
    hook     = script.get("hook", "")
    problem  = script.get("problem", "")
    loesung  = script.get("loesung", "")
    visuell  = script.get("visuelle_anweisungen", "")
    stil     = script.get("style", "direkt-kamera")

    # Veo 2 braucht englische Prompts
    base = (
        f"Short vertical video ad (9:16), authentic documentary style, "
        f"real German woman in her 30s-45s, natural lighting, handheld camera feel. "
    )

    if stil == "direkt-kamera":
        base += f"Person speaking directly to camera in German. "
    elif stil == "text-overlay":
        base += f"Cinematic B-roll footage with text overlays. "

    base += (
        f"Scene: {visuell} "
        f"Emotional context: {problem} "
        f"Tone: empathetic, warm, authentic. "
        f"NOT staged, NOT stock-photo style. "
        f"Mobile-optimized vertical format. Soft natural color grading."
    )

    return base[:500]  # Veo hat Prompt-Limit


# ─── Hauptfunktion ──────────────────────────────────────────────────────────────

def run(max_videos: int = 2) -> dict:
    """
    Führt den Video Production Agent aus.
    max_videos: Wie viele Videos generieren (Kostenkontrolle).
    """
    print(f"\n{'='*60}")
    print(f"[Video Agent] Start — {datetime.now().strftime('%d.%m.%Y %H:%M')}")
    print(f"{'='*60}")

    if not GOOGLE_AI_API_KEY:
        print("[Video] GOOGLE_AI_API_KEY fehlt — keine Videos möglich")
        print("  → Bitte GOOGLE_AI_API_KEY in .env setzen (Google AI Studio)")
        return {"videos": [], "fehler": "Kein API Key"}

    scripts = lade_aktuelle_scripts()
    if not scripts:
        print("[Video] Keine UGC Scripts gefunden — zuerst agent_creative.py ausführen")
        return {"videos": [], "fehler": "Keine Scripts"}

    datum = datetime.now().strftime("%Y-%m-%d")
    generierte_videos = []

    for i, script in enumerate(scripts[:max_videos]):
        nr    = script.get("nr", i + 1)
        stil  = script.get("style", "direkt-kamera")
        dauer_str = script.get("dauer", "20 Sek")
        dauer_sek = min(int(dauer_str.split()[0]), 30) if dauer_str[0].isdigit() else 15

        print(f"\n[Video] Generiere Video {nr}/{max_videos}: {dauer_str} — {stil}")
        print(f"  Hook: {script.get('hook', '')[:60]}...")

        veo_prompt = script_zu_veo_prompt(script)

        video_bytes = generiere_video(
            prompt=veo_prompt,
            dauer=min(dauer_sek, 8),  # Veo2 max 8s per Generation
            format="9:16"
        )

        if video_bytes:
            dateiname = f"video_ad_{datum}_{nr}_{stil}.mp4"
            pfad = speichere_video(video_bytes, dateiname)
            generierte_videos.append({
                "nr": nr,
                "pfad": pfad,
                "script": script,
                "dauer": dauer_str,
                "format": "9:16",
                "plattform": "meta_reels|google",
            })
            print(f"  ✓ Video gespeichert: {pfad}")
        else:
            print(f"  ✗ Video {nr} fehlgeschlagen")

    # Report
    Path(REPORTS_DIR).mkdir(parents=True, exist_ok=True)
    output = {"datum": datum, "videos": generierte_videos}
    json_pfad = f"{REPORTS_DIR}/video_output_{datum}.json"
    Path(json_pfad).write_text(json.dumps(output, ensure_ascii=False, indent=2),
                                encoding="utf-8")

    print(f"\n[Video] {len(generierte_videos)}/{max_videos} Videos erfolgreich generiert")
    for v in generierte_videos:
        print(f"  → {v['pfad']}")

    return output


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Video Production Agent — Veo 2")
    parser.add_argument("--max", type=int, default=2,
                        help="Maximale Anzahl Videos (Standard: 2)")
    args = parser.parse_args()

    init_db()
    run(max_videos=args.max)

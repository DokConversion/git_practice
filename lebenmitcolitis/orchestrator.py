"""
Orchestrator — Täglicher Gesamt-Runner für lebenmitcolitis.de
Läuft lokal auf deinem MacBook via Cron/Launchd.

Tägliche Reihenfolge:
1. Media Buying Intel (Perplexity Briefing)
2. Research Agent (Pain/Gain aus Reddit etc.)
3. Ad Copy Agent (Meta + Google Ads)
4. Creative Director (Bilder + UGC Scripts)
5. Video Agent (Veo 2 Videos — optional)
6. Analytics Agent (KPI Report + Telegram)

Manuell ausführen:     python orchestrator.py
Nur bestimmte Steps:   python orchestrator.py --steps research,ads
Trockenlauf:           python orchestrator.py --dry-run

MacBook Setup (automatisch täglich um 7:00 Uhr):
    python orchestrator.py --setup-cron
"""

import argparse
import asyncio
import sys
import traceback
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from config_colitis import PROJECT_NAME, REPORTS_DIR
from db_colitis import init_db, get_stats


# ─── Schritt-Definitionen ────────────────────────────────────────────────────────

ALLE_SCHRITTE = [
    "mediabuy",
    "research",
    "ads",
    "funnel",
    "creative",
    "video",
    "analytics",
]

# Standard täglich (ohne funnel+video — die laufen wöchentlich)
DAILY_SCHRITTE = ["mediabuy", "research", "ads", "creative", "analytics"]
WEEKLY_SCHRITTE = ["funnel", "video"]  # Nur montags


# ─── Runner Funktionen ───────────────────────────────────────────────────────────

def run_mediabuy(force: bool = False):
    from agent_mediabuy_intel import run
    return run(force=force)


async def run_research(dry_run: bool = False):
    from agent_research import run
    return await run(dry_run=dry_run)


def run_ads(dry_run: bool = False):
    from agent_ads import run
    return run(dry_run=dry_run)


def run_funnel(dry_run: bool = False):
    from agent_funnel import run
    return run(dry_run=dry_run)


def run_creative(generiere_bilder: bool = True):
    from agent_creative import run
    return run(generiere_bilder=generiere_bilder)


def run_video(max_videos: int = 2):
    from agent_video import run
    return run(max_videos=max_videos)


def run_analytics():
    from agent_analytics import run
    return run()


# ─── Haupt-Orchestrierung ────────────────────────────────────────────────────────

async def orchestriere(schritte: list[str],
                        dry_run: bool = False,
                        force_mediabuy: bool = False) -> dict:
    """Führt alle angegebenen Schritte aus und sammelt Ergebnisse."""

    start_time = datetime.now()
    print(f"\n{'='*65}")
    print(f"  {PROJECT_NAME} — AI Marketing Orchestrator")
    print(f"  Start: {start_time.strftime('%d.%m.%Y %H:%M:%S')}")
    print(f"  Schritte: {', '.join(schritte)}")
    print(f"  Dry-Run: {'Ja' if dry_run else 'Nein'}")
    print(f"{'='*65}")

    ergebnisse = {}
    fehler = {}

    for schritt in schritte:
        print(f"\n▶ Schritt: {schritt.upper()}")

        try:
            if schritt == "mediabuy":
                ergebnisse["mediabuy"] = run_mediabuy(force=force_mediabuy)

            elif schritt == "research":
                ergebnisse["research"] = await run_research(dry_run=dry_run)

            elif schritt == "ads":
                ergebnisse["ads"] = run_ads(dry_run=dry_run)

            elif schritt == "funnel":
                ergebnisse["funnel"] = run_funnel(dry_run=dry_run)

            elif schritt == "creative":
                # Bilder nur generieren wenn Nicht-Dry-Run und API Key vorhanden
                from config_colitis import GOOGLE_AI_API_KEY
                generiere = not dry_run and bool(GOOGLE_AI_API_KEY)
                ergebnisse["creative"] = run_creative(generiere_bilder=generiere)

            elif schritt == "video":
                if not dry_run:
                    ergebnisse["video"] = run_video(max_videos=2)
                else:
                    print("  [SKIP] Video-Generierung im Dry-Run deaktiviert")

            elif schritt == "analytics":
                ergebnisse["analytics"] = run_analytics()

            print(f"  ✓ {schritt.upper()} abgeschlossen")

        except Exception as e:
            fehler[schritt] = str(e)
            print(f"  ✗ {schritt.upper()} FEHLER: {e}")
            traceback.print_exc()

    # Abschluss-Report
    dauer = (datetime.now() - start_time).seconds
    print(f"\n{'='*65}")
    print(f"  Fertig in {dauer}s")
    print(f"  Erfolgreich: {len(ergebnisse)} | Fehler: {len(fehler)}")
    if fehler:
        print(f"  Fehler in: {', '.join(fehler.keys())}")

    stats = get_stats()
    print(f"\n  📊 Datenbank Status:")
    for tabelle, anzahl in stats.items():
        print(f"     {tabelle}: {anzahl} Einträge")
    print(f"{'='*65}\n")

    return {"ergebnisse": ergebnisse, "fehler": fehler, "dauer_sek": dauer}


# ─── macOS Cron Setup ────────────────────────────────────────────────────────────

def setup_macos_cron():
    """
    Richtet einen Cron-Job ein der den Orchestrator täglich um 7:00 Uhr startet.
    Läuft vollständig lokal auf dem MacBook.
    """
    import subprocess
    import shutil

    python_pfad = shutil.which("python3") or sys.executable
    script_pfad = Path(__file__).absolute()

    # Cron Eintrag prüfen/erstellen
    cron_zeile = f"0 7 * * * cd {script_pfad.parent} && {python_pfad} {script_pfad} --daily >> {script_pfad.parent}/logs/cron.log 2>&1"

    try:
        # Aktuelle Crontab laden
        result = subprocess.run(["crontab", "-l"], capture_output=True, text=True)
        aktuelle_crontab = result.stdout if result.returncode == 0 else ""

        if "orchestrator.py" in aktuelle_crontab:
            print("[Setup] Cron-Job bereits eingerichtet:")
            for zeile in aktuelle_crontab.splitlines():
                if "orchestrator.py" in zeile:
                    print(f"  {zeile}")
            return

        # Neue Crontab mit unserem Job
        neue_crontab = aktuelle_crontab.rstrip() + f"\n{cron_zeile}\n"

        # Logs-Verzeichnis erstellen
        (script_pfad.parent / "logs").mkdir(exist_ok=True)

        # Crontab schreiben
        proc = subprocess.run(["crontab", "-"], input=neue_crontab, text=True, capture_output=True)
        if proc.returncode == 0:
            print("[Setup] ✓ Cron-Job eingerichtet!")
            print(f"  Täglich um 07:00 Uhr: {script_pfad.name}")
            print(f"  Log: {script_pfad.parent}/logs/cron.log")
            print(f"\n  Cron-Zeile: {cron_zeile}")
        else:
            print(f"[Setup] Crontab Fehler: {proc.stderr}")

    except Exception as e:
        print(f"[Setup] Fehler: {e}")
        print(f"\nManuelle Einrichtung — führe aus:")
        print(f"  crontab -e")
        print(f"  Dann einfügen: {cron_zeile}")


def setup_launchd():
    """
    Alternative zu Cron: macOS LaunchAgent (zuverlässiger auf neueren macOS).
    Erstellt plist-Datei für automatischen Start.
    """
    import getpass

    script_pfad = Path(__file__).absolute()
    log_dir     = script_pfad.parent / "logs"
    log_dir.mkdir(exist_ok=True)

    python_pfad = sys.executable
    benutzer    = getpass.getuser()

    plist_inhalt = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
  "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>de.lebenmitcolitis.orchestrator</string>
    <key>ProgramArguments</key>
    <array>
        <string>{python_pfad}</string>
        <string>{script_pfad}</string>
        <string>--daily</string>
    </array>
    <key>StartCalendarInterval</key>
    <dict>
        <key>Hour</key>
        <integer>7</integer>
        <key>Minute</key>
        <integer>0</integer>
    </dict>
    <key>WorkingDirectory</key>
    <string>{script_pfad.parent}</string>
    <key>StandardOutPath</key>
    <string>{log_dir}/orchestrator.log</string>
    <key>StandardErrorPath</key>
    <string>{log_dir}/orchestrator_error.log</string>
    <key>EnvironmentVariables</key>
    <dict>
        <key>PATH</key>
        <string>{Path(python_pfad).parent}:/usr/local/bin:/usr/bin:/bin</string>
    </dict>
</dict>
</plist>"""

    plist_pfad = Path.home() / "Library/LaunchAgents/de.lebenmitcolitis.orchestrator.plist"
    plist_pfad.write_text(plist_inhalt, encoding="utf-8")

    print(f"[Setup] ✓ LaunchAgent plist erstellt: {plist_pfad}")
    print(f"\nAktivieren mit:")
    print(f"  launchctl load {plist_pfad}")
    print(f"\nDeaktivieren mit:")
    print(f"  launchctl unload {plist_pfad}")
    print(f"\nManuell testen:")
    print(f"  launchctl start de.lebenmitcolitis.orchestrator")


# ─── CLI ────────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description=f"{PROJECT_NAME} — AI Marketing Orchestrator"
    )

    parser.add_argument(
        "--steps", type=str,
        help=f"Komma-getrennte Schritte: {','.join(ALLE_SCHRITTE)}"
    )
    parser.add_argument(
        "--daily", action="store_true",
        help="Standard Tages-Lauf (mediabuy, research, ads, creative, analytics)"
    )
    parser.add_argument(
        "--weekly", action="store_true",
        help="Wochen-Lauf (funnel, video) — empfohlen montags"
    )
    parser.add_argument(
        "--full", action="store_true",
        help="Alle Schritte ausführen"
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Nur Output, keine API-Calls zu Ads, keine DB-Writes"
    )
    parser.add_argument(
        "--force-mediabuy", action="store_true",
        help="Media Buying Briefing auch wenn heute schon erstellt"
    )
    parser.add_argument(
        "--setup-cron", action="store_true",
        help="Cron-Job auf diesem Mac einrichten (täglich 07:00)"
    )
    parser.add_argument(
        "--setup-launchd", action="store_true",
        help="macOS LaunchAgent einrichten (zuverlässiger als Cron)"
    )
    parser.add_argument(
        "--stats", action="store_true",
        help="Datenbank-Statistiken anzeigen"
    )

    args = parser.parse_args()

    # Setup-Befehle
    if args.setup_cron:
        setup_macos_cron()
        return

    if args.setup_launchd:
        setup_launchd()
        return

    if args.stats:
        init_db()
        stats = get_stats()
        print(f"\n📊 {PROJECT_NAME} — Datenbank Status")
        print("─" * 40)
        for tabelle, anzahl in stats.items():
            print(f"  {tabelle:<30} {anzahl:>5} Einträge")
        return

    # Schritte bestimmen
    if args.steps:
        schritte = [s.strip() for s in args.steps.split(",")]
        ungültig = [s for s in schritte if s not in ALLE_SCHRITTE]
        if ungültig:
            print(f"Ungültige Schritte: {ungültig}")
            print(f"Verfügbar: {ALLE_SCHRITTE}")
            sys.exit(1)
    elif args.full:
        schritte = ALLE_SCHRITTE
    elif args.weekly:
        schritte = WEEKLY_SCHRITTE
    elif args.daily:
        schritte = DAILY_SCHRITTE
        # Montags auch Weekly-Schritte
        if datetime.now().weekday() == 0:  # Montag
            schritte = DAILY_SCHRITTE + WEEKLY_SCHRITTE
    else:
        # Default: Tages-Lauf
        schritte = DAILY_SCHRITTE

    # DB initialisieren
    init_db()

    # Starten
    asyncio.run(orchestriere(
        schritte=schritte,
        dry_run=args.dry_run,
        force_mediabuy=args.force_mediabuy
    ))


if __name__ == "__main__":
    main()

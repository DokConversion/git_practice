# Setup Guide — lebenmitcolitis.de AI Marketing System

Läuft vollständig lokal auf deinem MacBook. Kein Server, kein Hosting.

## 1. Einmaliger Setup (ca. 15 Minuten)

```bash
# In den Projektordner wechseln
cd lebenmitcolitis

# Python Dependencies installieren
pip install -r requirements.txt

# Playwright Browser installieren (für Web-Scraping)
playwright install chromium

# .env Datei aus Template erstellen
cp .env.example .env
# Dann .env öffnen und deine API Keys eintragen (siehe unten)

# Datenbank initialisieren
python db_colitis.py

# Testen ob alles läuft
python orchestrator.py --stats
```

## 2. API Keys beschaffen (Priorität)

### Sofort nötig (ohne diese läuft nichts):
| Key | Wo holen | Kosten |
|-----|----------|--------|
| `ANTHROPIC_API_KEY` | console.anthropic.com | Pay-per-Use (~€5/Monat zu Beginn) |
| `TELEGRAM_BOT_TOKEN` | @BotFather auf Telegram | Kostenlos |
| `TELEGRAM_CHAT_ID` | @userinfobot auf Telegram | Kostenlos |

### Für erste Ergebnisse (Woche 1):
| Key | Wo holen | Kosten |
|-----|----------|--------|
| `GOOGLE_AI_API_KEY` | aistudio.google.com | Kostenlos (mit Limits) |
| `PERPLEXITY_API_KEY` | perplexity.ai/settings/api | ~$20/Monat |

### Für Skalierung (ab Live-Gang):
| Key | Wo holen |
|-----|----------|
| `META_ACCESS_TOKEN` | Meta Business Manager → System Users |
| `META_AD_ACCOUNT_ID` | Meta Ads Manager (act_XXXXXXXXX) |
| `GOOGLE_ADS_*` | Google Ads API Konsole |
| `BREVO_API_KEY` | app.brevo.com |

## 3. Mastermind-Wissen einlesen (einmalig)

Deine Marketing-Unterlagen aus Masterminds in folgende Ordner ablegen:
```
knowledge_base/docs/
├── media_buying/   ← Meta/Google Ads Strategien, Kurse
├── funnels/        ← Funnel-Frameworks, Copy-Systeme
└── offers/         ← Offer-Creation, Pricing, Upsell-Strategien
```

Dann einlesen:
```bash
python knowledge_base/ingest.py
```

Formate: PDF, DOCX, TXT, MD
Audio: Erst mit Whisper transkribieren, dann als .txt ablegen

## 4. Ersten Lauf starten

```bash
# Erster Test-Lauf (kein API-Spend, zeigt nur Output)
python orchestrator.py --dry-run

# Echter erster Lauf
python orchestrator.py --daily
```

## 5. Automatischer täglicher Start einrichten

```bash
# macOS LaunchAgent (empfohlen — zuverlässiger als Cron)
python orchestrator.py --setup-launchd

# LaunchAgent aktivieren
launchctl load ~/Library/LaunchAgents/de.lebenmitcolitis.orchestrator.plist
```

Der Orchestrator startet jetzt täglich um **07:00 Uhr** automatisch.
Marc bekommt den KPI-Report per **Telegram**.

## 6. Wöchentliche Aufgaben (1,5h/Woche)

| Tag | Aufgabe | Zeit |
|-----|---------|------|
| Täglich | Telegram Report lesen | 2 Min |
| Montag | Budget-Entscheidung (skalieren/stoppen) | 10 Min |
| Mittwoch | Ad Outputs reviewen in `output/ads/` | 20 Min |
| Freitag | Creatives in `output/creatives/` ansehen | 15 Min |

## 7. Output-Verzeichnisse

```
output/
├── ads/            ← CSV-Dateien für Meta/Google Bulk-Upload
├── creatives/      ← Generierte Bilder (JPG) + Video-Scripts
├── videos/         ← Generierte MP4-Ads (Veo 2)
├── funnel/         ← Landing Page Copy, Email-Sequenzen
└── reports/        ← Tägl. KPI Reports, Ad Reports, Research Briefs
```

## 8. Häufige Befehle

```bash
# Statistiken anzeigen
python orchestrator.py --stats

# Nur Research ausführen
python orchestrator.py --steps research

# Nur Ads generieren
python orchestrator.py --steps ads

# Nur Analytics-Report
python orchestrator.py --steps analytics

# Funnel-Copy neu generieren (z.B. nach A/B Test)
python orchestrator.py --steps funnel

# Alle Schritte
python orchestrator.py --full

# Logs ansehen
tail -f logs/cron.log
```

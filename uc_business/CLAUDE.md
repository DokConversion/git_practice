# UC Business — Projekt-Kontext für Claude

## Was ist dieses Projekt?

Ein vollautomatisiertes digitales Marketing-Business rund um **Colitis Ulcerosa (CU)** 
im deutschsprachigen Markt (DACH). Anonymes Business — kein persönliches Branding, kein Gesicht.

**Marktchance:** Geringer Google Ads-Wettbewerb bei CU-Keywords bestätigt.

## Produkte

| Produkt | Typ | Preis | Status |
|---------|-----|-------|--------|
| UC Starter-Guide | PDF, Lead-Magnet | kostenlos | Konzept |
| UC Ernährungs-Kompass | PDF-Guide | €37 | In Entwicklung |
| UC Selbsthilfe-System | 8-Wochen Video-Kurs | €247 | Geplant |

## Bestehende Website

- **URL:** https://lebenmitcolitis.de/
- **Status:** Vorhanden aber kritisch überarbeitungsbedürftig
- **Hauptprobleme:**
  - Template-Text im Footer (Java-Template-Überbleibsel)
  - "Your Logo" Platzhalter
  - Design zu feminin (50% Zielgruppe ausgeschlossen)
  - "7-Tage-Plan" trivialiert chronische Erkrankung
  - Awareness-Mismatch für Cold Traffic

## Technische Infrastruktur

- **Google Ads:** ✓ Vorhanden
- **Meta Business:** ✓ Vorhanden
- **Email-Marketing-Tool:** ✓ Vorhanden (Provider noch zu konfigurieren in .env)
- **Produkt-Plattform:** ✓ Vorhanden (Provider noch zu konfigurieren in .env)

## System-Agenten

| Agent | Datei | Zweck |
|-------|-------|-------|
| CEO/CMO | orchestrator.py | Täglicher Koordinations-Loop |
| Data Analyst | data_analyst.py | KPI-Analyse, Anomalien, Empfehlungen |
| Brand Agent | brand_agent.py | Marke, Audit, Messaging |
| Psychology Expert | psychology_expert.py | Limbic, Spiral, Schwartz, Awareness |
| Google Ads | google_ads_agent.py | Kampagnen, Keywords, Bidding |
| Meta Ads | facebook_ads_agent.py | Targeting, Creative-Rotation |
| Creative | creative_agent.py | Copy, Ad-Texte, Varianten |
| Email | email_agent.py | Sequenzen, Segmentierung |
| Groups Intel | groups_intel_agent.py | FB-Gruppen-Insights |
| Tracking | tracking.py | GA4, UTM, KPI-Dashboard |
| Products | products.py | Auslieferung, Katalog |

## Psychologische Frameworks (in psychology_expert.py)

1. **Limbic Map:** Primär Gleichgewicht + Harmoniser + Hedonist
2. **Awareness (Schwartz):** Cold Traffic = Stufe 2 (Problem Aware)
3. **Spiral Dynamics:** Orange (35%) + Blau (30%) + Grün (25%)
4. **Schwartz-Werte:** Selbstbestimmung, Sicherheit, Wohlbefinden

## Compliance-Regeln (immer beachten)

- KEINE Heilsversprechen ("heilt", "kuriert", "eliminiert")
- KEINE medizinischen Claims ohne Einschränkung
- Erlaubt: "kann unterstützen", "Erfahrungen zeigen", "von Betroffenen erprobt"
- DSGVO: Double-Opt-In, Cookie-Banner, Datenschutzerklärung
- Immer: "Ersetzt keine ärztliche Beratung"

## Zielgruppen-Segmente

1. **Akut Betroffen** (Schub) — Gleichgewicht/Sicherheit, Awareness 2
2. **Remission-Suchend** — Balance/Stabilität, Awareness 3
3. **Neudiagnostiziert** — Orientierung/Community, Awareness 2
4. **Selbstoptimierer** — Stimulanz/Dominanz, Awareness 4

## Kern-Insights der Zielgruppe

**Fears (Kauftreiber):**
- Kontrollverlust über den eigenen Körper
- Soziale Isolation durch Erkrankung
- Nächster Schub kommt überraschend

**Desires (Kaufversprechen):**
- Normalen Alltag: essen, reisen, spontan sein
- Kontrolle und Vorhersehbarkeit
- Verstehen warum der Körper so reagiert

## Wichtige Entscheidungen

- Marke anonym → Trust durch Community-Konzept, nicht Einzelperson
- Design inklusiv → nicht feminin-dominant (blaugrün + sand statt lachs/beige)
- "7-Tage-Plan" → umbenennen in "4-Wochen-Framework" o.ä.
- Primärer Funnel: Ad → Opt-in (kostenlos) → Sales Page → Upsell
- Dry-Run-Modus standard — `--live` für echte API-Calls

## Wissensdateien

- `knowledge/psychology_framework.md` — Alle Psycho-Frameworks ausgearbeitet
- `knowledge/brand_brief.md` — Brand-Strategie, Audit lebenmitcolitis.de, Rewrites
- `knowledge/brand_audit_latest.json` — Letzter Brand-Audit (generiert)
- `knowledge/psych_profile_uc.json` — Psycho-Profil (generiert)

## Schnellstart

```bash
cp .env.example .env && nano .env          # API Keys eintragen
pip install -r requirements.txt
python run.py --psychology                 # Psycho-Profil ausgeben
python run.py --brand --audit             # Brand-Audit starten
python run.py --analyst --dry-run         # KPI-Analyse (Simulation)
python run.py --daily --dry-run           # Tages-Pipeline simulieren
python run.py --daily --live              # Live-Betrieb starten
```

#!/bin/bash
# ─────────────────────────────────────────────────────────────
#  Performance Dashboard – Starten
#  Ausführen: bash start.sh
# ─────────────────────────────────────────────────────────────
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

if [ ! -d ".venv" ]; then
  echo "❌ Setup noch nicht durchgeführt. Bitte zuerst: bash setup.sh"
  exit 1
fi

echo "📊 Dashboard wird gestartet…"
echo "   → http://localhost:8501"
echo "   → Beenden: Ctrl+C"
echo ""

# Browser nach kurzer Verzögerung öffnen
(sleep 2 && open "http://localhost:8501") &

.venv/bin/streamlit run app.py

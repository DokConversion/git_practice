#!/bin/bash
# ─────────────────────────────────────────────────────────────
#  Performance Dashboard – Einmaliges Setup (macOS)
#  Ausführen: bash setup.sh
# ─────────────────────────────────────────────────────────────
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo ""
echo "📊 Performance Dashboard – Setup"
echo "================================="

# ── 1. Python prüfen ──────────────────────────────────────────
if ! command -v python3 &>/dev/null; then
  echo ""
  echo "❌ Python 3 nicht gefunden."
  echo "   Bitte installieren: https://www.python.org/downloads/"
  exit 1
fi

PYTHON_VERSION=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
echo "✅ Python $PYTHON_VERSION gefunden"

# ── 2. Virtuelle Umgebung ────────────────────────────────────
if [ ! -d ".venv" ]; then
  echo "⚙️  Erstelle virtuelle Umgebung (.venv)…"
  python3 -m venv .venv
fi
echo "✅ Virtuelle Umgebung bereit"

# ── 3. Dependencies installieren ────────────────────────────
echo "📦 Installiere Abhängigkeiten…"
.venv/bin/pip install --quiet --upgrade pip
.venv/bin/pip install --quiet -r requirements.txt
echo "✅ Abhängigkeiten installiert"

# ── 4. .env erstellen ────────────────────────────────────────
if [ ! -f ".env" ]; then
  echo "🔑 Generiere Verschlüsselungs-Key…"
  MASTER_KEY=$(.venv/bin/python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())")
  echo "DASHBOARD_MASTER_KEY=$MASTER_KEY" > .env
  echo "✅ .env erstellt (Key gesichert)"
else
  echo "✅ .env bereits vorhanden"
fi

# ── 5. Streamlit-Konfiguration ───────────────────────────────
mkdir -p .streamlit
if [ ! -f ".streamlit/config.toml" ]; then
  cat > .streamlit/config.toml <<'TOML'
[server]
headless = true
port = 8501

[browser]
gatherUsageStats = false

[theme]
base = "dark"
primaryColor = "#89b4fa"
backgroundColor = "#1e1e2e"
secondaryBackgroundColor = "#313244"
textColor = "#cdd6f4"
TOML
  echo "✅ Streamlit-Konfiguration erstellt"
fi

# ── Fertig ────────────────────────────────────────────────────
echo ""
echo "✅ Setup abgeschlossen!"
echo ""
echo "▶  Dashboard starten:"
echo "   bash start.sh"
echo ""
echo "   oder Doppelklick auf: Start Dashboard.command"
echo ""

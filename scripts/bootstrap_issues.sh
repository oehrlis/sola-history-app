#!/usr/bin/env bash
#
# Erzeugt Issues aus project_issues.txt via GitHub CLI (gh issue create).
#
# Nutzung:
#   cd sola-history-app
#   chmod +x scripts/bootstrap_issues.sh
#   GITHUB_REPO=oehrlis/sola-history-app ./scripts/bootstrap_issues.sh
#
# Voraussetzung:
#   - gh CLI installiert: https://cli.github.com/
#   - gh auth login (oder GH_TOKEN / GITHUB_TOKEN gesetzt)

set -euo pipefail

ISSUES_FILE="scripts/project_issues.txt"

REPO="${GITHUB_REPO:-}"
if [[ -z "$REPO" ]]; then
  echo "Bitte die Umgebungsvariable GITHUB_REPO setzen, z.B.:"
  echo "  GITHUB_REPO=oehrlis/sola-history-app ./scripts/bootstrap_issues.sh"
  exit 1
fi

if ! command -v gh >/dev/null 2>&1; then
  echo "ERROR: 'gh' CLI nicht gefunden. Bitte GitHub CLI installieren."
  exit 1
fi

if [[ ! -f "$ISSUES_FILE" ]]; then
  echo "ERROR: Issues-Datei nicht gefunden: $ISSUES_FILE"
  exit 1
fi

echo "Erzeuge Issues in Repo: $REPO"
echo "Quelle: $ISSUES_FILE"
echo

while IFS= read -r line; do
  # Kommentare und leere Zeilen überspringen
  [[ -z "$line" ]] && continue
  [[ "$line" =~ ^# ]] && continue

  # Zerlegen: Titel | Beschreibung | Labels
  IFS='|' read -r raw_title raw_body raw_labels <<< "$line"

  # Whitespace trimmen
  title="$(echo "$raw_title" | xargs)"
  body="$(echo "$raw_body" | xargs)"
  labels="$(echo "$raw_labels" | xargs)"

  if [[ -z "$title" ]]; then
    echo "Überspringe Zeile ohne Titel: $line"
    continue
  fi

  echo "→ Erzeuge Issue: '$title' (Labels: $labels)"

  # gh issue create
  gh issue create \
    --repo "$REPO" \
    --title "$title" \
    --body "$body" \
    $( [[ -n "$labels" ]] && echo --label "$labels" )

done < "$ISSUES_FILE"

echo
echo "Fertig. Die Issues sind jetzt im Repo $REPO."
echo "Du kannst sie im GitHub Project über 'Add item → Add from repository' hinzufügen."

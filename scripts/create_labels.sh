#!/usr/bin/env bash
# Usage: GITHUB_TOKEN=xxx ./create_labels.sh owner repo

OWNER="$1"
REPO="$2"

if [ -z "$OWNER" ] || [ -z "$REPO" ]; then
  echo "Usage: $0 <owner> <repo>"
  exit 1
fi

api() {
  curl -s -H "Authorization: token ${GITHUB_TOKEN}" \
       -H "Accept: application/vnd.github+json" \
       https://api.github.com/repos/${OWNER}/${REPO}/labels \
       -d "$1"
}

create_label() {
  local name="$1"
  local color="$2"
  local desc="$3"
  api "$(jq -n --arg n "$name" --arg c "$color" --arg d "$desc" '{name:$n,color:$c,description:$d}')"
}

create_label "infra"     "f1e05a" "OCI / infrastructure / networking"
create_label "app"       "1d76db" "Application / Streamlit"
create_label "data"      "0e8a16" "Data model / pipeline"
create_label "docker"    "586069" "Docker & container"
create_label "docs"      "5319e7" "Documentation"
create_label "security"  "b60205" "Security / auth / secrets"
create_label "ci/cd"     "0fb3d2" "Automation / GitHub Actions"
create_label "planning"  "fbca04" "Race planning features"
create_label "ui/ux"     "cc317c" "User interface / experience"
create_label "admin"     "a295d6" "Admin tools & overrides"
create_label "bug"       "d73a4a" "Bug"
create_label "enhancement" "a2eeef" "Feature / enhancement"
create_label "task"      "cfd3d7" "General task"
create_label "blocked"   "e11d21" "Blocked task"

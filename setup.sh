#!/bin/bash
# cowork-skills setup script
# Syncs skills from this repo to your ~/.claude/skills/ directory
# Run this on any machine after cloning the repo

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILLS_SOURCE="$SCRIPT_DIR/skills"
SKILLS_TARGET="$HOME/.claude/skills"

echo "========================================="
echo "  Cowork Skills — Setup & Sync"
echo "========================================="
echo ""
echo "Source: $SKILLS_SOURCE"
echo "Target: $SKILLS_TARGET"
echo ""

# Create target directory
mkdir -p "$SKILLS_TARGET"

# Sync each skill
for skill_dir in "$SKILLS_SOURCE"/*/; do
    skill_name=$(basename "$skill_dir")
    echo "  Installing skill: $skill_name"
    mkdir -p "$SKILLS_TARGET/$skill_name"
    cp -r "$skill_dir"* "$SKILLS_TARGET/$skill_name/"
done

echo ""
echo "Skills installed to $SKILLS_TARGET:"
ls -1 "$SKILLS_TARGET"
echo ""
echo "Done! Skills are now available in all Claude Code sessions."
echo "Background skills (design-system, document-designer) auto-load."
echo "User skills: type /canva-designer to invoke."
echo ""
echo "To update: git pull && ./setup.sh"

#!/bin/bash

# Git Pre-Commit Hook: Runs E2E validation pipeline before allowing commits
# This hook is installed via: bash scripts/install-git-hooks.sh
# To bypass: git commit --no-verify (not recommended!)

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
BOLD='\033[1m'
NC='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo -e "${BLUE}${BOLD}Pre-Commit: Running end-to-end validation pipeline...${NC}"
echo -e "${BLUE}(Run with --no-verify to bypass, but not recommended)${NC}"
echo ""

# Run validation (skip slow integration tests in pre-commit)
if bash "$SCRIPT_DIR/validate.sh" --skip-slow 2>&1; then
    echo ""
    echo -e "${GREEN}${BOLD}✓ Pre-commit validation passed${NC}"
    echo "Proceeding with commit..."
    exit 0
else
    echo ""
    echo -e "${RED}${BOLD}✗ Pre-commit validation failed${NC}"
    echo ""
    echo "Cannot commit: validation pipeline failed"
    echo ""
    echo "To fix issues:"
    echo "  1. Run: ${YELLOW}bash scripts/validate.sh --fix${NC}"
    echo "  2. Review and fix any remaining issues"
    echo "  3. Stage changes: ${YELLOW}git add .${NC}"
    echo "  4. Try commit again: ${YELLOW}git commit${NC}"
    echo ""
    echo "To bypass validation (NOT RECOMMENDED):"
    echo "  ${YELLOW}git commit --no-verify${NC}"
    echo ""
    exit 1
fi

#!/bin/bash

# Install Git Hooks for E2E Validation Pipeline
# Usage: bash scripts/install-git-hooks.sh

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
BOLD='\033[1m'
NC='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
HOOKS_DIR="$PROJECT_ROOT/.git/hooks"

echo -e "${BLUE}${BOLD}═══════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}${BOLD}Git Hooks Installation${NC}"
echo -e "${BLUE}${BOLD}═══════════════════════════════════════════════════════${NC}"
echo ""

# Check if .git directory exists
if [ ! -d "$PROJECT_ROOT/.git" ]; then
    echo -e "${RED}Error: .git directory not found${NC}"
    echo "This script must be run in a git repository root"
    exit 1
fi

# Create hooks directory if it doesn't exist
if [ ! -d "$HOOKS_DIR" ]; then
    mkdir -p "$HOOKS_DIR"
fi

# Install pre-commit hook
echo -e "${YELLOW}Installing pre-commit hook...${NC}"
cp "$SCRIPT_DIR/git-hook-pre-commit.sh" "$HOOKS_DIR/pre-commit"
chmod +x "$HOOKS_DIR/pre-commit"
echo -e "${GREEN}✓ Pre-commit hook installed${NC}"

# Install prepare-commit-msg hook for helpful messages
echo -e "${YELLOW}Installing prepare-commit-msg hook...${NC}"
cat > "$HOOKS_DIR/prepare-commit-msg" << 'HOOK_EOF'
#!/bin/bash
# Prepend commit message with branch info if not a merge/rebase

# Don't modify merge commits
if [ -f .git/MERGE_HEAD ]; then
    exit 0
fi

# Get current branch
BRANCH=$(git rev-parse --abbrev-ref HEAD 2>/dev/null)

# Add branch to commit message if not on main/master
if [ "$BRANCH" != "main" ] && [ "$BRANCH" != "master" ] && [ "$BRANCH" != "HEAD" ]; then
    # Only if message doesn't already start with branch
    COMMIT_MSG=$(cat "$1")
    if [[ ! "$COMMIT_MSG" =~ ^(feat|fix|docs|style|refactor|test|chore).*\($BRANCH\) ]]; then
        # Add branch reference if not already there
        sed -i.bak "1s/^/[$BRANCH] /" "$1"
    fi
fi
HOOK_EOF
chmod +x "$HOOKS_DIR/prepare-commit-msg"
echo -e "${GREEN}✓ Prepare-commit-msg hook installed${NC}"

echo ""
echo -e "${GREEN}${BOLD}✓ Git hooks installation complete${NC}"
echo ""
echo -e "${BLUE}What's installed:${NC}"
echo "  • pre-commit: Runs full validation pipeline before commits"
echo "  • prepare-commit-msg: Adds branch name to commit messages"
echo ""
echo -e "${BLUE}How it works:${NC}"
echo "  1. You try to commit: ${YELLOW}git commit -m 'Your message'${NC}"
echo "  2. Pre-commit hook runs: validation checks all code"
echo "  3. If all pass → commit succeeds ✓"
echo "  4. If any fail → commit blocked, fix issues, retry"
echo ""
echo -e "${YELLOW}To bypass (NOT RECOMMENDED):${NC}"
echo "  ${YELLOW}git commit --no-verify${NC}"
echo ""
echo -e "${BLUE}Manual validation (before committing):${NC}"
echo "  ${YELLOW}bash scripts/validate.sh${NC}"
echo "  ${YELLOW}bash scripts/validate.sh --fix${NC} (auto-fix formatting/linting)"
echo ""

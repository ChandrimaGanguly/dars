#!/bin/bash

# Setup pre-commit hooks for Dars project
# This script installs pre-commit and configures Git hooks

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}=== Dars Project: Pre-commit Hook Setup ===${NC}\n"

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}Error: Python 3 is required but not installed${NC}"
    exit 1
fi

echo -e "${YELLOW}Step 1: Installing pre-commit${NC}"
pip install pre-commit

echo -e "\n${YELLOW}Step 2: Setting up Git hooks${NC}"
pre-commit install

echo -e "\n${YELLOW}Step 3: Running all hooks on existing files${NC}"
echo -e "${BLUE}This may take a moment...${NC}\n"
pre-commit run --all-files || true

echo -e "\n${GREEN}✓ Pre-commit hooks installed successfully!${NC}\n"

echo -e "${BLUE}What's installed:${NC}"
echo "  • black - Code formatter"
echo "  • ruff - Linter and formatter"
echo "  • mypy - Type checker"
echo "  • pytest - Unit test validator"
echo "  • YAML/JSON validators"
echo "  • Merge conflict detector"

echo -e "\n${BLUE}Usage:${NC}"
echo "  • Hooks run automatically on: ${YELLOW}git commit${NC}"
echo "  • Run manually on all files: ${YELLOW}pre-commit run --all-files${NC}"
echo "  • Run specific hook: ${YELLOW}pre-commit run black --all-files${NC}"
echo "  • Skip hooks (not recommended): ${YELLOW}git commit --no-verify${NC}"

echo -e "\n${BLUE}Testing the setup:${NC}"
echo "  1. Make a code change"
echo "  2. Run: ${YELLOW}git add .${NC}"
echo "  3. Run: ${YELLOW}git commit -m 'Test commit'${NC}"
echo "  4. Watch hooks run automatically\n"

echo -e "${GREEN}Setup complete!${NC}"

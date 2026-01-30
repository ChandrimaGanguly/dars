#!/bin/bash

# End-to-End Validation Pipeline for Dars
# This script runs all quality checks and tests before allowing commits
# Usage: bash scripts/validate.sh [--fix] [--skip-slow]
#
# Exit codes:
#   0 = All checks passed
#   1 = Formatting issues
#   2 = Linting issues
#   4 = Type checking issues
#   8 = Tests failed
#   16 = Coverage insufficient

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
BOLD='\033[1m'
NC='\033[0m' # No Color

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Flags
FIX_MODE=false
SKIP_SLOW=false
VERBOSE=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --fix)
            FIX_MODE=true
            shift
            ;;
        --skip-slow)
            SKIP_SLOW=true
            shift
            ;;
        -v|--verbose)
            VERBOSE=true
            shift
            ;;
        *)
            echo "Unknown flag: $1"
            echo "Usage: $0 [--fix] [--skip-slow] [-v|--verbose]"
            exit 1
            ;;
    esac
done

# Track exit codes
EXIT_CODE=0

print_header() {
    echo ""
    echo -e "${BLUE}${BOLD}════════════════════════════════════════${NC}"
    echo -e "${BLUE}${BOLD}$1${NC}"
    echo -e "${BLUE}${BOLD}════════════════════════════════════════${NC}${NC}"
}

print_step() {
    echo -e "${YELLOW}→${NC} $1"
}

print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

# ============================================================================
# STAGE 1: Code Formatting (Black)
# ============================================================================

print_header "STAGE 1: Code Formatting (Black)"

print_step "Checking Python code formatting..."

if command -v black &> /dev/null; then
    if [ "$FIX_MODE" = true ]; then
        print_step "Fixing formatting issues..."
        if black src tests 2>/dev/null; then
            print_success "Code formatted successfully"
        else
            print_warning "Some files could not be auto-formatted"
            EXIT_CODE=$((EXIT_CODE + 1))
        fi
    else
        if black --check src tests 2>/dev/null; then
            print_success "Code formatting check passed"
        else
            print_error "Formatting issues found. Run: bash scripts/validate.sh --fix"
            EXIT_CODE=$((EXIT_CODE + 1))
        fi
    fi
else
    print_warning "Black not installed. Skipping formatting check."
fi

# ============================================================================
# STAGE 2: Linting (Ruff)
# ============================================================================

print_header "STAGE 2: Linting (Ruff)"

print_step "Checking code style and common issues..."

if command -v ruff &> /dev/null; then
    if [ "$FIX_MODE" = true ]; then
        print_step "Auto-fixing linting issues..."
        ruff check --fix src tests || true
        if ruff check src tests &> /dev/null; then
            print_success "All linting issues resolved"
        else
            print_warning "Some linting issues could not be auto-fixed"
            EXIT_CODE=$((EXIT_CODE + 2))
        fi
    else
        if ruff check src tests &> /dev/null; then
            print_success "Linting check passed"
        else
            print_error "Linting issues found. Run: bash scripts/validate.sh --fix"
            ruff check src tests || true
            EXIT_CODE=$((EXIT_CODE + 2))
        fi
    fi
else
    print_warning "Ruff not installed. Skipping linting check."
fi

# ============================================================================
# STAGE 3: Type Checking (MyPy)
# ============================================================================

print_header "STAGE 3: Type Checking (MyPy)"

print_step "Running strict type checker..."

if command -v mypy &> /dev/null; then
    if [ "$VERBOSE" = true ]; then
        mypy src || EXIT_CODE=$((EXIT_CODE + 4))
    else
        if mypy src &> /tmp/mypy_output.txt; then
            print_success "Type checking passed"
        else
            print_error "Type errors found:"
            cat /tmp/mypy_output.txt | head -20
            print_error "Fix type errors and try again. Run with -v for full output:"
            echo "  mypy src"
            EXIT_CODE=$((EXIT_CODE + 4))
        fi
    fi
else
    print_warning "MyPy not installed. Skipping type checking."
fi

# ============================================================================
# STAGE 4: Unit Tests
# ============================================================================

print_header "STAGE 4: Unit Tests"

print_step "Running unit tests..."

if command -v pytest &> /dev/null; then
    if [ "$VERBOSE" = true ]; then
        pytest tests/unit -v --tb=short --cov=src --cov-report=term-missing:skip-covered --cov-report=html --cov-fail-under=70 || EXIT_CODE=$((EXIT_CODE + 8))
    else
        if pytest tests/unit -q --cov=src --cov-report=term-missing:skip-covered --cov-report=html --cov-fail-under=70 2>/dev/null; then
            print_success "All unit tests passed"
        else
            print_error "Unit tests failed. Run: pytest tests/unit -v"
            pytest tests/unit -q --tb=line --cov=src 2>/dev/null || true
            EXIT_CODE=$((EXIT_CODE + 8))
        fi
    fi
else
    print_warning "Pytest not installed. Skipping unit tests."
fi

# ============================================================================
# STAGE 5: Integration Tests (Optional - can be slow)
# ============================================================================

print_header "STAGE 5: Integration Tests"

if [ "$SKIP_SLOW" = true ]; then
    print_warning "Skipping integration tests (--skip-slow flag set)"
else
    print_step "Running integration tests (this may be slow)..."

    if command -v pytest &> /dev/null; then
        if [ "$VERBOSE" = true ]; then
            pytest tests/integration -v --tb=short || EXIT_CODE=$((EXIT_CODE + 8))
        else
            if pytest tests/integration -q --tb=line 2>/dev/null; then
                print_success "All integration tests passed"
            else
                print_error "Integration tests failed. Run: pytest tests/integration -v"
                pytest tests/integration -q --tb=line 2>/dev/null || true
                EXIT_CODE=$((EXIT_CODE + 8))
            fi
        fi
    else
        print_warning "Pytest not installed. Skipping integration tests."
    fi
fi

# ============================================================================
# STAGE 6: Test Coverage
# ============================================================================

print_header "STAGE 6: Test Coverage"

print_step "Checking test coverage (minimum 70%)..."

if command -v pytest &> /dev/null; then
    if pytest tests/unit --cov=src --cov-fail-under=70 -q &> /tmp/coverage_output.txt; then
        # Extract coverage percentage
        COVERAGE=$(grep -oP '(\d+)%' /tmp/coverage_output.txt | head -1)
        print_success "Coverage check passed: $COVERAGE"
    else
        print_error "Coverage below 70% threshold"
        grep "FAILED" /tmp/coverage_output.txt || cat /tmp/coverage_output.txt | tail -5
        print_error "Run: pytest tests/unit --cov=src --cov-report=html"
        EXIT_CODE=$((EXIT_CODE + 8))
    fi
else
    print_warning "Pytest not installed. Skipping coverage check."
fi

# ============================================================================
# STAGE 7: Git Status Check
# ============================================================================

print_header "STAGE 7: Git Status"

print_step "Checking git status..."

if [ -d .git ]; then
    # Check for untracked important files
    if git status --porcelain | grep -qE '^\?\? (\.env|secrets)'; then
        print_error "Untracked sensitive files detected (.env, secrets/)"
        git status --porcelain | grep '^\?\?'
        EXIT_CODE=$((EXIT_CODE + 1))
    else
        print_success "No sensitive files detected"
    fi

    # Check if there are uncommitted changes
    if ! git diff-index --quiet HEAD --; then
        print_warning "Uncommitted changes found"
        print_step "Changes to be validated:"
        git diff-index HEAD -- | awk '{print $NF}' | sort -u
    else
        print_success "Working directory clean"
    fi
else
    print_warning "Not a git repository"
fi

# ============================================================================
# SUMMARY
# ============================================================================

print_header "VALIDATION SUMMARY"

if [ $EXIT_CODE -eq 0 ]; then
    echo ""
    echo -e "${GREEN}${BOLD}✓ ALL CHECKS PASSED${NC}"
    echo ""
    echo "You are ready to commit! The code meets all quality standards:"
    echo "  ✓ Code formatting (black)"
    echo "  ✓ Linting (ruff)"
    echo "  ✓ Type checking (mypy)"
    echo "  ✓ Unit tests"
    if [ "$SKIP_SLOW" != true ]; then
        echo "  ✓ Integration tests"
    fi
    echo "  ✓ Test coverage (≥70%)"
    echo "  ✓ Git status"
    echo ""
else
    echo ""
    echo -e "${RED}${BOLD}✗ VALIDATION FAILED${NC}"
    echo ""
    echo "Issues found:"
    if [ $((EXIT_CODE & 1)) -ne 0 ]; then
        echo "  ✗ Code formatting (black) - Run: bash scripts/validate.sh --fix"
    fi
    if [ $((EXIT_CODE & 2)) -ne 0 ]; then
        echo "  ✗ Linting (ruff) - Run: bash scripts/validate.sh --fix"
    fi
    if [ $((EXIT_CODE & 4)) -ne 0 ]; then
        echo "  ✗ Type checking (mypy) - Run: mypy src"
    fi
    if [ $((EXIT_CODE & 8)) -ne 0 ]; then
        echo "  ✗ Tests - Run: pytest -v"
    fi
    echo ""
    echo "Fix these issues and run again:"
    echo "  bash scripts/validate.sh [--fix] [--skip-slow]"
    echo ""
fi

exit $EXIT_CODE

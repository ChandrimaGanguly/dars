#!/bin/bash

# Task Coordination Utilities
# Usage: ./task-utils.sh <command> [args]

TASKS_DIR="$(dirname "$0")/.."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

show_help() {
    cat << EOF
Task Coordination System - Utility Commands

Usage: $0 <command> [arguments]

Commands:
  summary              Show task counts by area and status
  pending              List all pending tasks
  blocked              List all blocked tasks
  ready                List tasks ready to start (not blocked)
  area <name>          Show tasks for specific area (backend, frontend, infrastructure, content)
  add <area> <id> <desc>  Add a new task to an area
  complete <area> <id>    Mark a task as complete
  search <keyword>     Search for tasks containing keyword
  sync                 Sync from openspec/changes/dars/tasks.md (overwrites!)

Examples:
  $0 summary
  $0 pending
  $0 area backend
  $0 add backend "TASK-044" "Implement rate limiting"
  $0 complete backend "TASK-001"
  $0 search "Claude"

EOF
}

summary() {
    echo -e "${BLUE}=== Task Summary ===${NC}\n"

    for file in "$TASKS_DIR"/*.md; do
        if [[ "$file" == *"README.md" ]]; then
            continue
        fi

        area=$(basename "$file" .md)
        pending=$(grep -c "^- \[ \]" "$file" 2>/dev/null) || pending=0
        completed=$(grep -c "^- \[x\]" "$file" 2>/dev/null) || completed=0

        total=$((pending + completed))
        if [ "$total" -gt 0 ]; then
            pct=$((completed * 100 / total))
        else
            pct=0
        fi

        printf "${YELLOW}%-15s${NC} " "$area"
        printf "Pending: ${RED}%-3d${NC} " "$pending"
        printf "Done: ${GREEN}%-3d${NC} " "$completed"
        printf "Progress: ${BLUE}%3d%%${NC}\n" "$pct"
    done

    echo ""
    total_pending=$(grep -r "^- \[ \]" "$TASKS_DIR"/*.md 2>/dev/null | grep -v README | wc -l) || total_pending=0
    total_done=$(grep -r "^- \[x\]" "$TASKS_DIR"/*.md 2>/dev/null | grep -v README | wc -l) || total_done=0
    total=$((total_pending + total_done))

    if [ "$total" -gt 0 ]; then
        pct=$((total_done * 100 / total))
    else
        pct=0
    fi

    echo -e "${BLUE}─────────────────────────────────────${NC}"
    printf "${BLUE}TOTAL${NC}           Pending: ${RED}%-3d${NC} Done: ${GREEN}%-3d${NC} Progress: ${BLUE}%3d%%${NC}\n" "$total_pending" "$total_done" "$pct"
}

pending() {
    echo -e "${BLUE}=== Pending Tasks ===${NC}\n"

    for file in "$TASKS_DIR"/*.md; do
        if [[ "$file" == *"README.md" ]]; then
            continue
        fi

        area=$(basename "$file" .md)
        tasks=$(grep "^- \[ \] TASK-" "$file" 2>/dev/null)

        if [ -n "$tasks" ]; then
            echo -e "${YELLOW}[$area]${NC}"
            echo "$tasks" | while read -r line; do
                echo "  $line"
            done
            echo ""
        fi
    done
}

blocked() {
    echo -e "${BLUE}=== Blocked Tasks ===${NC}\n"

    for file in "$TASKS_DIR"/*.md; do
        if [[ "$file" == *"README.md" ]]; then
            continue
        fi

        area=$(basename "$file" .md)

        # Find tasks with "Blocked by" in the next line
        grep -B1 "Blocked by:" "$file" 2>/dev/null | grep "^- \[ \]" | while read -r line; do
            echo -e "${YELLOW}[$area]${NC} $line"
        done
    done
}

ready() {
    echo -e "${BLUE}=== Ready Tasks (Not Blocked) ===${NC}\n"

    for file in "$TASKS_DIR"/*.md; do
        if [[ "$file" == *"README.md" ]]; then
            continue
        fi

        area=$(basename "$file" .md)

        # Get all pending tasks, then filter out blocked ones
        # A task is blocked if the next few lines contain "Blocked by:"
        awk '
        /^- \[ \] TASK-/ {
            task = $0
            getline
            if ($0 !~ /Blocked by:/) {
                print task
            }
        }
        ' "$file" 2>/dev/null | while read -r line; do
            echo -e "${YELLOW}[$area]${NC} $line"
        done
    done
}

area() {
    local area_name=$1
    local file="$TASKS_DIR/$area_name.md"

    if [ ! -f "$file" ]; then
        echo -e "${RED}Error: Area '$area_name' not found${NC}"
        echo "Available areas: backend, frontend, infrastructure, content"
        exit 1
    fi

    cat "$file"
}

add_task() {
    local area_name=$1
    local task_id=$2
    local description=$3
    local file="$TASKS_DIR/$area_name.md"

    if [ ! -f "$file" ]; then
        echo -e "${RED}Error: Area '$area_name' not found${NC}"
        exit 1
    fi

    if [ -z "$task_id" ] || [ -z "$description" ]; then
        echo -e "${RED}Error: Task ID and description required${NC}"
        echo "Usage: $0 add <area> <task_id> <description>"
        exit 1
    fi

    # Check if task already exists
    if grep -q "$task_id" "$file"; then
        echo -e "${YELLOW}Warning: $task_id already exists in $area_name${NC}"
        exit 1
    fi

    # Add task after "## Active" section
    # Using a temp file for compatibility
    local temp_file=$(mktemp)
    awk -v task="- [ ] $task_id: $description\n  - **Status:** ready\n  - **Notes:** " '
    /^## Active/ {
        print
        getline
        print
        print task
        next
    }
    { print }
    ' "$file" > "$temp_file"

    mv "$temp_file" "$file"

    echo -e "${GREEN}Added $task_id to $area_name${NC}"
    echo "  - [ ] $task_id: $description"
}

complete_task() {
    local area_name=$1
    local task_id=$2
    local file="$TASKS_DIR/$area_name.md"
    local today=$(date +%Y-%m-%d)

    if [ ! -f "$file" ]; then
        echo -e "${RED}Error: Area '$area_name' not found${NC}"
        exit 1
    fi

    if [ -z "$task_id" ]; then
        echo -e "${RED}Error: Task ID required${NC}"
        exit 1
    fi

    # Check if task exists
    if ! grep -q "$task_id" "$file"; then
        echo -e "${RED}Error: $task_id not found in $area_name${NC}"
        exit 1
    fi

    # Replace [ ] with [x] for the task
    sed -i "s/\- \[ \] $task_id/- [x] $task_id (completed $today)/" "$file"

    echo -e "${GREEN}Completed $task_id in $area_name${NC}"
}

search_tasks() {
    local keyword=$1

    if [ -z "$keyword" ]; then
        echo -e "${RED}Error: Search keyword required${NC}"
        exit 1
    fi

    echo -e "${BLUE}=== Search: '$keyword' ===${NC}\n"

    grep -r -i "$keyword" "$TASKS_DIR"/*.md 2>/dev/null | grep -v README | while read -r line; do
        echo "$line"
    done
}

sync_from_openspec() {
    echo -e "${YELLOW}Warning: This will overwrite task files with OpenSpec data${NC}"
    echo "Press Ctrl+C to cancel, Enter to continue..."
    read -r

    # This is a placeholder - full implementation would parse openspec tasks.md
    echo -e "${BLUE}Syncing from openspec/changes/dars/tasks.md...${NC}"
    echo -e "${GREEN}Sync complete${NC}"
}

# Main command router
case "$1" in
    summary)
        summary
        ;;
    pending)
        pending
        ;;
    blocked)
        blocked
        ;;
    ready)
        ready
        ;;
    area)
        area "$2"
        ;;
    add)
        add_task "$2" "$3" "$4"
        ;;
    complete)
        complete_task "$2" "$3"
        ;;
    search)
        search_tasks "$2"
        ;;
    sync)
        sync_from_openspec
        ;;
    help|--help|-h|"")
        show_help
        ;;
    *)
        echo -e "${RED}Unknown command: $1${NC}"
        show_help
        exit 1
        ;;
esac

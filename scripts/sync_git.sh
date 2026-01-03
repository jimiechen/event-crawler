#!/bin/bash
# scripts/sync_git.sh

# Stop on error is risky for batch ops if one fails, but we want to know. 
# However, for a "sync all" script, we might want to continue even if one fails.
# So we won't use 'set -e' globally, but handle errors locally.

# List of submodules/repos to sync (Order: Submodules first, then Root)
REPOS=(
    "/Users/mac/ok-mcp/event-crawler/outModules/protocols"
    "/Users/mac/ok-mcp/event-crawler/outModules/protocols-n8n"
    "/Users/mac/ok-mcp/event-crawler/outModules/testCases"
    "/Users/mac/ok-mcp/event-crawler/outModules/TorFApp"
    "/Users/mac/ok-mcp/event-crawler/outModules/MineplanetGo"
    "/Users/mac/ok-mcp/event-crawler/outModules/open-citycloud"
    "/Users/mac/ok-mcp/event-crawler"
)

TIMESTAMP=$(date "+%Y-%m-%d %H:%M:%S")

echo "Starting one-click git sync (Pull -> Commit -> Push) at $TIMESTAMP"

for repo in "${REPOS[@]}"; do
    if [ -d "$repo" ]; then
        echo "--------------------------------------------------"
        echo "Syncing $repo ..."
        cd "$repo"

        # 1. Pull first (to get remote changes before adding ours, reducing merge conflicts if we haven't touched same files)
        # Actually, user said "first pull then push". 
        # But if we have local changes, pull might fail.
        # Best practice: Stash -> Pull -> Pop -> Commit -> Push OR Commit -> Pull --rebase -> Push.
        # User asked for "Auto fill commit message", implying we should commit.
        # So: Add -> Commit -> Pull --rebase -> Push.

        # Check for changes
        if [ -n "$(git status --porcelain)" ]; then
            echo "Changes detected. Committing..."
            git add .
            git commit -m "Auto sync: $TIMESTAMP"
        else
            echo "No local changes to commit."
        fi

        # 2. Pull
        echo "Pulling from remote..."
        if git pull --rebase; then
            echo "Pull successful."
        else
            echo "ERROR: git pull failed in $repo. You may have conflicts."
            # Continue to next repo? Yes, user said "fix all", but we can't fix conflicts auto.
            # We will continue but warn.
        fi

        # 3. Push
        echo "Pushing to remote..."
        if git push; then
            echo "Push successful."
        else
            echo "ERROR: git push failed in $repo."
        fi
        
    else
        echo "Warning: Directory $repo does not exist. Skipping."
    fi
    echo ""
done

echo "=================================================="
echo "All sync operations completed."

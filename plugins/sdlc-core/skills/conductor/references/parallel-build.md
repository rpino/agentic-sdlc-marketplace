# Parallel build (optional)

Read this only when the Build phase has several `todo` tasks.

When Build has several `todo` tasks whose dependencies are all `done` and that touch different files, you may run them in parallel. Dispatch each one to a subagent with `isolation: "worktree"` and `model: "sonnet"` (the standard for build workers; see CONTRIBUTING), running `sdlc-build:task-executor` for that single task on its own `feature/<task-id>-<slug>` branch. Use at most 3 at a time. When they return, review each diff summary, then hand the merges to the human in dependency order. Never merge to the main branch yourself.

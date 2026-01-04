# Git 高級命令指南 - Advanced Git Commands Guide

## 目錄 - Table of Contents

1. [git stash - 暫存工作區更改](#git-stash---暫存工作區更改)
2. [git cherry-pick - 選擇性應用提交](#git-cherry-pick---選擇性應用提交)
3. [git revert - 安全地撤銷提交](#git-revert---安全地撤銷提交)
4. [git reset - 重置提交歷史](#git-reset---重置提交歷史)
5. [最佳實踐 - Best Practices](#最佳實踐---best-practices)

---

## git stash - 暫存工作區更改

### 概述 - Overview

`git stash` allows you to temporarily save uncommitted changes without creating a commit. This is useful when you need to switch branches but aren't ready to commit your current work.

### 基本用法 - Basic Usage

#### 1. 暫存當前更改 - Stash Current Changes

```bash
# Stash all tracked file changes
git stash

# Stash with a descriptive message
git stash save "WIP: feature implementation"

# Stash including untracked files
git stash -u

# Stash including untracked and ignored files
git stash -a
```

**Example Scenario:**

```bash
# You're working on feature-branch
$ git status
On branch feature-branch
Changes not staged for commit:
  modified:   src/app.js
  modified:   src/utils.js

# Need to switch branches urgently
$ git stash save "WIP: app refactoring"
Saved working directory and index state On feature-branch: WIP: app refactoring

# Now your working directory is clean
$ git status
On branch feature-branch
nothing to commit, working tree clean

# Switch to another branch
$ git checkout main
```

#### 2. 查看暫存列表 - List Stashed Changes

```bash
# List all stashes
git stash list

# Example output:
# stash@{0}: On feature-branch: WIP: app refactoring
# stash@{1}: WIP on main: 5c3d2a1 Fix bug in authentication
# stash@{2}: On develop: Testing new feature
```

#### 3. 應用暫存的更改 - Apply Stashed Changes

```bash
# Apply the most recent stash (keeps it in stash list)
git stash apply

# Apply a specific stash
git stash apply stash@{1}

# Apply and remove the most recent stash
git stash pop

# Apply a specific stash and remove it
git stash pop stash@{1}
```

**Example:**

```bash
# Return to your feature branch
$ git checkout feature-branch

# Apply your stashed changes
$ git stash pop
On branch feature-branch
Changes not staged for commit:
  modified:   src/app.js
  modified:   src/utils.js

Dropped refs/stash@{0} (abc123...)
```

#### 4. 檢查暫存內容 - Inspect Stash Contents

```bash
# Show changes in the most recent stash
git stash show

# Show full diff of the most recent stash
git stash show -p

# Show specific stash
git stash show -p stash@{1}
```

#### 5. 刪除暫存 - Delete Stashes

```bash
# Drop a specific stash
git stash drop stash@{1}

# Clear all stashes
git stash clear
```

#### 6. 創建分支從暫存 - Create Branch from Stash

```bash
# Create a new branch and apply stash
git stash branch new-feature-branch

# This is equivalent to:
# git branch new-feature-branch
# git checkout new-feature-branch
# git stash pop
```

---

## git cherry-pick - 選擇性應用提交

### 概述 - Overview

`git cherry-pick` allows you to apply specific commits from one branch to another. This is useful when you want to selectively incorporate changes without merging entire branches.

### 基本用法 - Basic Usage

#### 1. 選擇單個提交 - Pick a Single Commit

```bash
# Apply a specific commit to current branch
git cherry-pick <commit-hash>

# Example:
git cherry-pick a1b2c3d
```

**Example Scenario:**

```bash
# You're on main branch and want a specific fix from develop
$ git log develop --oneline
e5f6g7h Fix critical security vulnerability
d4e5f6g Add new feature
c3d4e5f Update documentation

# Cherry-pick only the security fix
$ git checkout main
$ git cherry-pick e5f6g7h
[main 1a2b3c4] Fix critical security vulnerability
 1 file changed, 5 insertions(+), 2 deletions(-)
```

#### 2. 選擇多個提交 - Pick Multiple Commits

```bash
# Pick multiple commits
git cherry-pick <commit-1> <commit-2> <commit-3>

# Pick a range of commits (exclusive of start)
git cherry-pick start-commit^..end-commit

# Example:
git cherry-pick abc123 def456 ghi789
git cherry-pick abc123^..xyz999
```

**Example:**

```bash
# Pick commits from a feature branch
$ git cherry-pick c3d4e5f e5f6g7h
[main 2b3c4d5] Update documentation
 1 file changed, 10 insertions(+)
[main 3c4d5e6] Fix critical security vulnerability
 1 file changed, 5 insertions(+), 2 deletions(-)
```

#### 3. 處理衝突 - Handle Conflicts

```bash
# If conflicts occur during cherry-pick
# 1. Fix the conflicts in affected files
# 2. Stage the resolved files
git add <resolved-files>

# 3. Continue the cherry-pick
git cherry-pick --continue

# Or abort the cherry-pick
git cherry-pick --abort
```

**Example:**

```bash
$ git cherry-pick a1b2c3d
error: could not apply a1b2c3d... Update feature
hint: after resolving the conflicts, mark the corrected paths
hint: with 'git add <paths>' or 'git rm <paths>'
hint: and commit the result with 'git commit'

# Resolve conflicts in your editor
$ git status
On branch main
You are currently cherry-picking commit a1b2c3d.
  (fix conflicts and run "git cherry-pick --continue")
  (use "git cherry-pick --abort" to cancel the cherry-pick operation)

Unmerged paths:
  both modified:   src/app.js

# After resolving
$ git add src/app.js
$ git cherry-pick --continue
```

#### 4. 高級選項 - Advanced Options

```bash
# Cherry-pick without committing (stage changes only)
git cherry-pick -n <commit-hash>
# or
git cherry-pick --no-commit <commit-hash>

# Cherry-pick and edit the commit message
git cherry-pick -e <commit-hash>
# or
git cherry-pick --edit <commit-hash>

# Cherry-pick and sign off
git cherry-pick -s <commit-hash>
```

---

## git revert - 安全地撤銷提交

### 概述 - Overview

`git revert` creates a new commit that undoes the changes from a previous commit. Unlike `git reset`, it doesn't alter history, making it safe for shared branches.

### 基本用法 - Basic Usage

#### 1. 撤銷單個提交 - Revert a Single Commit

```bash
# Revert a specific commit
git revert <commit-hash>

# Example:
git revert a1b2c3d
```

**Example Scenario:**

```bash
# View commit history
$ git log --oneline
a1b2c3d (HEAD -> main) Add broken feature
b2c3d4e Fix authentication bug
c3d4e5f Update documentation

# Revert the broken feature
$ git revert a1b2c3d
[main d4e5f6g] Revert "Add broken feature"
 1 file changed, 15 deletions(-)

# New commit history
$ git log --oneline
d4e5f6g (HEAD -> main) Revert "Add broken feature"
a1b2c3d Add broken feature
b2c3d4e Fix authentication bug
c3d4e5f Update documentation
```

#### 2. 撤銷多個提交 - Revert Multiple Commits

```bash
# Revert multiple commits (creates multiple revert commits)
git revert <commit-1> <commit-2>

# Revert a range of commits
git revert <oldest-commit>^..<newest-commit>

# Example:
git revert HEAD~3..HEAD
```

**Example:**

```bash
# Revert last three commits
$ git revert HEAD~2..HEAD
[main e5f6g7h] Revert "Third commit"
[main f6g7h8i] Revert "Second commit"
[main g7h8i9j] Revert "First commit"
```

#### 3. 撤銷但不立即提交 - Revert Without Committing

```bash
# Revert changes but don't create a commit yet
git revert -n <commit-hash>
# or
git revert --no-commit <commit-hash>

# Useful for reverting multiple commits as one revert commit
git revert -n <commit-1>
git revert -n <commit-2>
git commit -m "Revert multiple commits"
```

**Example:**

```bash
# Revert two commits as a single revert
$ git revert -n abc123
$ git revert -n def456
$ git status
On branch main
You are currently reverting commit def456.
  (all conflicts fixed: run "git revert --continue")
  (use "git revert --abort" to cancel the revert operation)

Changes to be committed:
  modified:   src/feature1.js
  modified:   src/feature2.js

$ git commit -m "Revert problematic features"
```

#### 4. 處理合併提交 - Revert Merge Commits

```bash
# Revert a merge commit (specify parent number)
git revert -m 1 <merge-commit-hash>

# -m 1 keeps the first parent (usually the branch you merged into)
# -m 2 keeps the second parent (usually the branch you merged from)
```

**Example:**

```bash
# View merge commit
$ git log --oneline --graph
*   m1n2o3p (HEAD -> main) Merge branch 'feature'
|\
| * f1e2d3c Add feature
* | a1b2c3d Fix bug

# Revert the merge
$ git revert -m 1 m1n2o3p
[main p3o2n1m] Revert "Merge branch 'feature'"
```

#### 5. 繼續或中止撤銷 - Continue or Abort Revert

```bash
# If conflicts occur, resolve them and continue
git revert --continue

# Or abort the revert operation
git revert --abort
```

---

## git reset - 重置提交歷史

### 概述 - Overview

`git reset` moves the current branch pointer to a different commit. It's powerful but can alter history, so use with caution on shared branches.

### 重置模式 - Reset Modes

Git reset has three modes that determine what happens to your files:

1. **--soft**: Moves HEAD, keeps changes staged
2. **--mixed** (default): Moves HEAD, unstages changes
3. **--hard**: Moves HEAD, discards all changes

### 基本用法 - Basic Usage

#### 1. 軟重置 (--soft) - Soft Reset

Moves HEAD but keeps all changes staged and ready to commit.

```bash
# Reset to previous commit, keep changes staged
git reset --soft HEAD~1

# Reset to specific commit
git reset --soft <commit-hash>
```

**Example Scenario:**

```bash
# Current state
$ git log --oneline
a1b2c3d (HEAD -> main) Third commit
b2c3d4e Second commit
c3d4e5f First commit

# Reset last commit but keep changes staged
$ git reset --soft HEAD~1

$ git status
On branch main
Changes to be committed:
  modified:   file1.txt
  modified:   file2.txt

$ git log --oneline
b2c3d4e (HEAD -> main) Second commit
c3d4e5f First commit

# Now you can recommit with a different message
$ git commit -m "Better commit message"
```

**Use Case**: Fix a commit message or combine multiple commits into one.

#### 2. 混合重置 (--mixed) - Mixed Reset (Default)

Moves HEAD and unstages changes, but keeps them in working directory.

```bash
# Reset to previous commit, unstage changes
git reset HEAD~1
# or explicitly
git reset --mixed HEAD~1

# Reset to specific commit
git reset <commit-hash>
```

**Example:**

```bash
$ git log --oneline
a1b2c3d (HEAD -> main) Commit with multiple features
b2c3d4e Previous commit

# Reset and unstage
$ git reset HEAD~1

$ git status
On branch main
Changes not staged for commit:
  modified:   feature1.js
  modified:   feature2.js
  modified:   feature3.js

# Now you can stage and commit separately
$ git add feature1.js
$ git commit -m "Add feature 1"
$ git add feature2.js feature3.js
$ git commit -m "Add features 2 and 3"
```

**Use Case**: Split a large commit into smaller, more focused commits.

#### 3. 硬重置 (--hard) - Hard Reset

Moves HEAD and **discards all changes**. ⚠️ **DESTRUCTIVE OPERATION**

```bash
# Reset to previous commit and discard all changes
git reset --hard HEAD~1

# Reset to specific commit
git reset --hard <commit-hash>

# Reset to remote branch state
git reset --hard origin/main
```

**Example:**

```bash
$ git log --oneline
a1b2c3d (HEAD -> main) Bad commit
b2c3d4e Good commit

$ git status
On branch main
Changes not staged for commit:
  modified:   file1.txt

# Discard everything and go back to b2c3d4e
$ git reset --hard b2c3d4e
HEAD is now at b2c3d4e Good commit

$ git status
On branch main
nothing to commit, working tree clean

$ git log --oneline
b2c3d4e (HEAD -> main) Good commit
```

**⚠️ Warning**: This permanently deletes uncommitted changes!

#### 4. 重置特定文件 - Reset Specific Files

```bash
# Unstage a specific file (keeps changes in working directory)
git reset HEAD <file>

# Example:
git reset HEAD src/app.js
```

**Example:**

```bash
$ git status
On branch main
Changes to be committed:
  modified:   file1.txt
  modified:   file2.txt

# Unstage file1.txt only
$ git reset HEAD file1.txt

$ git status
On branch main
Changes to be committed:
  modified:   file2.txt

Changes not staged for commit:
  modified:   file1.txt
```

#### 5. 重置到遠程分支 - Reset to Remote Branch

```bash
# Fetch latest changes
git fetch origin

# Reset to match remote branch exactly
git reset --hard origin/main

# Or reset to remote while keeping local changes
git reset --soft origin/main
```

**Example:**

```bash
# Your local branch has diverged
$ git status
On branch main
Your branch and 'origin/main' have diverged,
and have 3 and 2 different commits each, respectively.

# Discard local commits and match remote
$ git fetch origin
$ git reset --hard origin/main
HEAD is now at x1y2z3a Latest remote commit

$ git status
On branch main
Your branch is up to date with 'origin/main'.
```

#### 6. 恢復被重置的提交 - Recover from Reset

If you reset by mistake, you can often recover using `reflog`:

```bash
# View reflog to find the commit before reset
git reflog

# Reset back to the commit before the mistaken reset
git reset --hard HEAD@{1}
```

**Example:**

```bash
# You accidentally did a hard reset
$ git reset --hard HEAD~3
HEAD is now at old123 Old commit

# Oops! I need those commits back
$ git reflog
old123 (HEAD -> main) HEAD@{0}: reset: moving to HEAD~3
new456 HEAD@{1}: commit: Important feature
mid789 HEAD@{2}: commit: Another feature
old123 HEAD@{3}: commit: Old commit

# Restore to before the reset
$ git reset --hard HEAD@{1}
HEAD is now at new456 Important feature
```

---

## 最佳實踐 - Best Practices

### 1. 選擇正確的命令 - Choose the Right Command

| Scenario | Recommended Command |
|----------|-------------------|
| Need to switch branches with uncommitted work | `git stash` |
| Want specific commits from another branch | `git cherry-pick` |
| Need to undo a commit on shared branch | `git revert` |
| Want to modify local unpushed commits | `git reset` |
| Accidentally committed to wrong branch | `git reset --soft` + checkout correct branch + commit |

### 2. 共享分支的安全性 - Safety on Shared Branches

```bash
# ✅ Safe for shared branches
git revert <commit>        # Creates new commit, preserves history
git stash                  # Local operation only

# ⚠️ Dangerous for shared branches (use only on local branches)
git reset --hard <commit>  # Rewrites history
git cherry-pick           # Can create duplicate commits
```

### 3. 在重置前創建備份 - Backup Before Reset

```bash
# Create a backup branch before dangerous operations
git branch backup-branch

# Now safe to reset
git reset --hard <commit>

# If needed, restore from backup
git checkout backup-branch
```

### 4. 使用 reflog 恢復 - Use Reflog for Recovery

```bash
# View recent operations
git reflog

# Recover from mistakes
git reset --hard HEAD@{n}
```

### 5. 測試重置效果 - Test Reset Effects

```bash
# See what would be reset without doing it
git reset --soft <commit>
git status                  # Review what would change
git reset --soft HEAD@{1}  # Undo the soft reset to try again
```

### 6. 清理工作流 - Clean Workflow Example

```bash
# Working on feature branch
$ git checkout -b feature/new-feature

# Made some commits
$ git add .
$ git commit -m "WIP"

# Need to switch to fix urgent bug
$ git stash save "Feature work in progress"
$ git checkout main
$ git checkout -b hotfix/urgent-bug

# Fix the bug
$ git add .
$ git commit -m "Fix urgent bug"
$ git push origin hotfix/urgent-bug

# Return to feature work
$ git checkout feature/new-feature
$ git stash pop

# Clean up commits before pushing
$ git reset --soft HEAD~3
$ git commit -m "Add new feature implementation"
$ git push origin feature/new-feature
```

### 7. Cherry-pick 最佳實踐 - Cherry-pick Best Practices

```bash
# ✅ Good: Cherry-pick for hotfixes
# Bring a critical fix from develop to main
git checkout main
git cherry-pick <hotfix-commit>

# ❌ Avoid: Cherry-picking entire feature branches
# This creates duplicate commits and complex history
# Instead, use merge or rebase

# ✅ Good: Use --no-commit for multiple related picks
git cherry-pick -n commit1
git cherry-pick -n commit2
git cherry-pick -n commit3
git commit -m "Combined feature from commits 1-3"
```

### 8. 避免常見錯誤 - Avoid Common Mistakes

```bash
# ❌ Don't reset pushed commits on shared branches
git reset --hard HEAD~1  # After pushing - WRONG!

# ✅ Use revert instead
git revert HEAD

# ❌ Don't stash without a message
git stash  # Hard to identify later

# ✅ Always use descriptive messages
git stash save "WIP: user authentication feature"

# ❌ Don't cherry-pick merge commits without -m
git cherry-pick <merge-commit>  # Will fail

# ✅ Specify parent
git cherry-pick -m 1 <merge-commit>
```

---

## 快速參考 - Quick Reference

### Command Comparison

| Command | Alters History | Safe for Shared Branches | Use Case |
|---------|---------------|-------------------------|----------|
| `git stash` | No | ✅ Yes | Temporarily save work |
| `git cherry-pick` | Creates new commits | ⚠️ Be careful | Apply specific commits |
| `git revert` | No (adds commits) | ✅ Yes | Undo published commits |
| `git reset --soft` | Yes | ❌ No | Redo commits locally |
| `git reset --mixed` | Yes | ❌ No | Unstage changes |
| `git reset --hard` | Yes | ❌ No | Discard all changes |

### Common Patterns

```bash
# Save work temporarily
git stash save "Description"

# Apply specific commit
git cherry-pick abc123

# Undo public commit safely
git revert abc123

# Undo local commit, keep changes
git reset --soft HEAD~1

# Unstage everything
git reset HEAD

# Discard everything (DANGEROUS!)
git reset --hard HEAD
```

---

**提示 - Tips:**

1. 始終在執行破壞性操作前創建備份分支
   Always create a backup branch before destructive operations

2. 使用 `git reflog` 可以恢復幾乎任何丟失的提交
   Use `git reflog` to recover almost any lost commit

3. 在共享分支上優先使用 `git revert` 而非 `git reset`
   Prefer `git revert` over `git reset` on shared branches

4. 使用描述性的 stash 訊息以便日後識別
   Use descriptive stash messages for easier identification later

5. 在 cherry-pick 或 reset 之前，確保了解當前分支狀態
   Understand your current branch state before cherry-picking or resetting

---

*本指南涵蓋了 Git 高級命令的常見使用場景。如需更多詳細信息，請參閱 [Git 官方文檔](https://git-scm.com/doc)。*

*This guide covers common use cases for advanced Git commands. For more details, refer to the [official Git documentation](https://git-scm.com/doc).*

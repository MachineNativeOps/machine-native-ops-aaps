#!/usr/bin/env python3

from __future__ import annotations

import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List


def _run(cmd: List[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, capture_output=True, text=True, check=True)


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _update_section(path: Path, start: str, end: str, body: str) -> bool:
    content = path.read_text(encoding="utf-8")
    block = f"{start}\n{body}\n{end}"
    if start in content and end in content:
        new_content = re.sub(
            rf"{re.escape(start)}.*?{re.escape(end)}",
            block,
            content,
            flags=re.DOTALL,
        )
    else:
        new_content = f"{block}\n\n{content}"

    if new_content != content:
        path.write_text(new_content, encoding="utf-8")
        return True
    return False


def _changed_files() -> Dict[str, object]:
    result = _run(["git", "log", "-1", "--name-status", "--pretty=format:%H|%an|%s"])
    lines = [line for line in result.stdout.splitlines() if line.strip()]
    if not lines:
        return {
            "sha": "",
            "author": "",
            "subject": "",
            "files": [],
            "added": 0,
            "modified": 0,
            "deleted": 0,
        }

    sha, author, subject = (lines[0].split("|", 2) + ["", "", ""])[:3]
    added = modified = deleted = 0
    files: List[str] = []
    for line in lines[1:]:
        parts = line.split("\t")
        status = parts[0]
        target = parts[-1] if len(parts) > 1 else parts[0]
        files.append(target)
        if status.startswith("A"):
            added += 1
        elif status.startswith("D"):
            deleted += 1
        else:
            modified += 1

    return {
        "sha": sha,
        "author": author,
        "subject": subject,
        "files": files,
        "added": added,
        "modified": modified,
        "deleted": deleted,
    }


def _format_files(files: List[str], limit: int = 12) -> str:
    if not files:
        return "- 受影響檔案: 無"
    display = files[:limit]
    suffix = " ...（更多變更已省略）" if len(files) > limit else ""
    return f"- 受影響檔案: {', '.join(display)}{suffix}"


def _memory_body(summary: Dict[str, object], timestamp: str) -> str:
    return "\n".join(
        [
            f"### 🔄 最近自動更新（{timestamp}）",
            f"- 最新 commit: {summary['sha']} ({summary['subject']})",
            f"- 作者: {summary['author']}",
            f"- 變更摘要: 新增 {summary['added']}，修改 {summary['modified']}，刪除 {summary['deleted']}",
            _format_files(summary["files"]),  # type: ignore[arg-type]
        ]
    )


def _conversation_body(summary: Dict[str, object], timestamp: str) -> str:
    return "\n".join(
        [
            f"### {timestamp} - 自動記憶更新",
            f"- 目標: 記錄最新變更並同步治理文件",
            f"- Commit: {summary['sha']} ({summary['subject']})",
            f"- 變更: 新增 {summary['added']} / 修改 {summary['modified']} / 刪除 {summary['deleted']}",
            _format_files(summary["files"]),  # type: ignore[arg-type]
        ]
    )


def _collect_tree(root: Path, depth: int = 2) -> List[str]:
    lines: List[str] = [f"{root.name}/"]

    def walk(current: Path, prefix: str, level: int) -> None:
        if level >= depth:
            return
        entries = [p for p in sorted(current.iterdir()) if not p.name.startswith(".")]
        for index, entry in enumerate(entries):
            connector = "└── " if index == len(entries) - 1 else "├── "
            lines.append(f"{prefix}{connector}{entry.name}/" if entry.is_dir() else f"{prefix}{connector}{entry.name}")
            if entry.is_dir():
                next_prefix = f"{prefix}{'    ' if index == len(entries) - 1 else '│   '}"
                walk(entry, next_prefix, level + 1)

    walk(root, "", 0)
    return lines


def _architecture_body(summary: Dict[str, object], timestamp: str, repo_root: Path) -> str:
    controlplane = repo_root / "controlplane"
    workspace = repo_root / "workspace"
    trees: List[str] = []
    for target in (controlplane, workspace):
        if target.exists():
            trees.extend(_collect_tree(target, depth=2))
            trees.append("")

    tree_block = "\n".join(trees).rstrip()
    return "\n".join(
        [
            f"### 🗺️ 自動架構同步（{timestamp}）",
            f"- Commit: {summary['sha']} ({summary['subject']})",
            "- 檔案結構快照：",
            "```",
            tree_block,
            "```",
        ]
    )


def main() -> None:
    repo_root = Path(__file__).resolve().parents[4]
    project_memory = repo_root / "controlplane/governance/docs/PROJECT_MEMORY.md"
    conversation_log = repo_root / "workspace/projects/CONVERSATION_LOG.md"
    architecture_doc = repo_root / "controlplane/governance/docs/ARCHITECTURE.md"

    summary = _changed_files()
    timestamp = _now()

    updated = False
    updated |= _update_section(
        project_memory,
        "<!-- AUTO-MEMORY-UPDATE:START -->",
        "<!-- AUTO-MEMORY-UPDATE:END -->",
        _memory_body(summary, timestamp),
    )
    updated |= _update_section(
        conversation_log,
        "<!-- AUTO-CONVERSATION-LOG:START -->",
        "<!-- AUTO-CONVERSATION-LOG:END -->",
        _conversation_body(summary, timestamp),
    )
    updated |= _update_section(
        architecture_doc,
        "<!-- AUTO-ARCHITECTURE-SYNC:START -->",
        "<!-- AUTO-ARCHITECTURE-SYNC:END -->",
        _architecture_body(summary, timestamp, repo_root),
    )

    if updated:
        print("Updated governance memory files.")
    else:
        print("No governance files required updates.")


if __name__ == "__main__":
    main()

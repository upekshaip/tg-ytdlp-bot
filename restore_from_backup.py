#!/usr/bin/env python3
from CONFIG.messages import Messages, safe_get_messages
"""
Interactive backup restore tool for tg-ytdlp-bot.

- Scans the `_backup/` directory for backup files created by updater
  (filenames end with `.backup_YYYYMMDD_HHMMSS`).
- Groups files by backup index (timestamp) and shows a curses menu.
- User can navigate with arrow keys and press Enter to select a backup.
- Restores ALL files from the selected backup into the project root,
  recreating directories as needed and stripping the `.backup_<timestamp>` suffix.

Non-interactive usage:
  python3 restore_from_backup.py --timestamp YYYYMMDD_HHMMSS
  python3 restore_from_backup.py --list

Safety:
- Reads from `_backup/` only. Writes into current project directory.
- Will create missing directories. Overwrites existing files.
"""

import os
import sys
import re
import curses
import argparse
from datetime import datetime
from typing import Dict, List, Tuple

BACKUP_ROOT = "_backup"
# Support both second-level and minute-level suffixes
SUFFIX_SEC_RE = re.compile(r"^(?P<name>.+)\.backup_(?P<ts>\d{8}_\d{6})$")
SUFFIX_MIN_RE = re.compile(r"^(?P<name>.+)\.backup_(?P<tsm>\d{8}_\d{4})$")

# Keep original constant for compatibility
SUFFIX_RE = SUFFIX_SEC_RE

class BackupIndex:
    def __init__(self, ts: str):
        self.ts = ts  # ID string (YYYYMMDD_HHMM or YYYYMMDD_HHMMSS)
        self.files: List[Tuple[str, str]] = []  # (rel_dir, filename_with_suffix)

    @property
    def human(self) -> str:
        try:
            fmt = "%Y%m%d_%H%M%S" if len(self.ts.replace('_','')) == 14 else "%Y%m%d_%H%M"
            dt = datetime.strptime(self.ts, fmt)
            return dt.strftime("%Y-%m-%d %H:%M:%S")
        except Exception:
            return self.ts

    def count(self) -> int:
        return len(self.files)


def scan_backups() -> Dict[str, BackupIndex]:
    """Walk `_backup/` and collect backup files grouped by timestamp."""
    indices: Dict[str, BackupIndex] = {}
    if not os.path.isdir(BACKUP_ROOT):
        return indices
    for root, _dirs, files in os.walk(BACKUP_ROOT):
        rel_dir = os.path.relpath(root, BACKUP_ROOT)
        rel_dir = "" if rel_dir == "." else rel_dir
        for fname in files:
            m = SUFFIX_SEC_RE.match(fname)
            ts = None
            if m:
                ts = m.group("ts")
                # normalize to minute-level id for grouping
                ts = ts[:-2]  # drop seconds -> YYYYMMDD_HHMM
            else:
                m2 = SUFFIX_MIN_RE.match(fname)
                if m2:
                    ts = m2.group("tsm")
            if not ts:
                continue
            if ts not in indices:
                indices[ts] = BackupIndex(ts)
            indices[ts].files.append((rel_dir, fname))
    return indices


def list_indices(indices: Dict[str, BackupIndex]) -> List[BackupIndex]:
    arr = list(indices.values())
    # sort by timestamp descending (newest first)
    def key(bi: BackupIndex):
        try:
            fmt = "%Y%m%d_%H%M%S" if len(bi.ts.replace('_','')) == 14 else "%Y%m%d_%H%M"
            return datetime.strptime(bi.ts, fmt)
        except Exception:
            return datetime.min
    arr.sort(key=key, reverse=True)
    return arr


def restore_backup(indices: Dict[str, BackupIndex], ts: str) -> Tuple[int, int]:
    """Restore all files for timestamp ts. Returns (restored, errors)."""
    # ГЛОБАЛЬНАЯ ЗАЩИТА: Инициализируем messages
    messages = safe_get_messages(None)
    
    bi = indices.get(ts)
    if not bi:
        messages = safe_get_messages()
        print(messages.RESTORE_BACKUP_NOT_FOUND_MSG.format(ts=ts))
        return (0, 1)
    restored = 0
    errors = 0
    for rel_dir, fname in bi.files:
        # Match any known suffix and derive original name
        m = SUFFIX_SEC_RE.match(fname)
        if m:
            dest_name = m.group("name")
        else:
            m2 = SUFFIX_MIN_RE.match(fname)
            if m2:
                dest_name = m2.group("name")
            else:
                continue
        src = os.path.join(BACKUP_ROOT, rel_dir, fname)
        dest_dir = rel_dir  # same relative directory as in backup
        dest_path = os.path.join(dest_dir, dest_name) if dest_dir else dest_name
        try:
            os.makedirs(os.path.dirname(dest_path) or ".", exist_ok=True)
            with open(src, 'rb') as fsrc, open(dest_path, 'wb') as fdst:
                fdst.write(fsrc.read())
            restored += 1
            messages = safe_get_messages()
            print(messages.RESTORE_SUCCESS_RESTORED_MSG.format(dest_path=dest_path))
        except Exception as e:
            errors += 1
            messages = safe_get_messages()
            print(messages.RESTORE_FAILED_RESTORE_MSG.format(src=src, dest_path=dest_path, e=e))
    return (restored, errors)


def curses_menu(stdscr, items: List[BackupIndex]) -> int:
    curses.curs_set(0)
    current_row = 0
    scroll = 0
    while True:
        stdscr.clear()
        h, w = stdscr.getmaxyx()
        # Minimal size check
        if h and h < 5 or w < 30:
            msg = "Terminal too small. Resize and press any key..."
            stdscr.addstr(0, 0, msg[: max(0, w - 1)])
            stdscr.refresh()
            stdscr.getch()
            continue
        # Title
        title = "Select a backup to restore (Arrow keys: navigate, Enter: select, q: quit)"
        stdscr.addstr(0, 0, title[: max(0, w - 1)])
        # Compute visible window for items
        max_rows = h - 3  # rows available for list
        # Ensure current_row is within [scroll, scroll + max_rows)
        if current_row and current_row < scroll:
            scroll = current_row
        elif current_row >= scroll + max_rows:
            scroll = current_row - max_rows + 1
        start = max(0, scroll)
        end = min(len(items), start + max_rows)
        # Draw items within window
        for vis_idx, idx in enumerate(range(start, end)):
            bi = items[idx]
            label = f"[{bi.human}]  files: {bi.count()}  (id: {bi.ts})"
            line_y = vis_idx + 2
            line_x = 2
            text = label[: max(0, w - line_x - 1)]
            if idx == current_row:
                stdscr.attron(curses.A_REVERSE)
                stdscr.addstr(line_y, line_x, text)
                stdscr.attroff(curses.A_REVERSE)
            else:
                stdscr.addstr(line_y, line_x, text)
        # Footer / hint
        footer = f"Items: {len(items)}  Selected: {current_row + 1 if items else 0}/{len(items)}"
        stdscr.addstr(h - 1, 0, footer[: max(0, w - 1)])
        stdscr.refresh()
        # Keys
        key = stdscr.getch()
        if key in (curses.KEY_UP, ord('k')):
            if items:
                current_row = (current_row - 1) % len(items)
        elif key in (curses.KEY_DOWN, ord('j')):
            if items:
                current_row = (current_row + 1) % len(items)
        elif key in (curses.KEY_PPAGE,):  # Page Up
            current_row = max(0, current_row - max_rows)
        elif key in (curses.KEY_NPAGE,):  # Page Down
            current_row = min(len(items) - 1, current_row + max_rows)
        elif key in (curses.KEY_ENTER, 10, 13):
            return current_row
        elif key in (ord('q'), ord('Q')):
            return -1


def interactive_restore(indices: Dict[str, BackupIndex]) -> int:
    items = list_indices(indices)
    if not items:
        print("⚠️ No backups found in _backup/")
        return 1

    def _run(stdscr):
        return curses_menu(stdscr, items)

    selected_index = curses.wrapper(_run)
    if selected_index is None or selected_index < 0:
        print("Cancelled.")
        return 1

    chosen = items[selected_index]
    print(f"You selected backup: {chosen.human} (id: {chosen.ts}), files: {chosen.count()}")
    # Confirm
    try:
        answer = input("Proceed with restore? (y/N): ").strip().lower()
    except EOFError:
        answer = "n"
    if answer not in ("y", "yes"):
        print("Cancelled.")
        return 1
    restored, errors = restore_backup(indices, chosen.ts)
    print("=" * 50)
    print(f"Restored: {restored}")
    print(f"Errors:   {errors}")
    return 0 if errors == 0 else 2


def main():
    parser = argparse.ArgumentParser(description="Restore files from _backup by backup index (timestamp)")
    parser.add_argument("--timestamp", "-t", help="Backup id in format YYYYMMDD_HHMMSS (non-interactive)")
    parser.add_argument("--list", action="store_true", help="List available backups and exit")
    args = parser.parse_args()

    indices = scan_backups()
    if args.list:
        items = list_indices(indices)
        if not items:
            print("No backups found.")
            return 0
        print("Available backups (newest first):")
        for bi in items:
            print(f"  {bi.ts}  {bi.human}  files:{bi.count()}")
        return 0

    if args.timestamp:
        ts = args.timestamp.strip()
        restored, errors = restore_backup(indices, ts)
        print("=" * 50)
        print(f"Restored: {restored}")
        print(f"Errors:   {errors}")
        return 0 if errors == 0 else 2

    # Interactive menu
    return interactive_restore(indices)


if __name__ == "__main__":
    sys.exit(main())

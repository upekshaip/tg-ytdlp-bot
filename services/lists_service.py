from __future__ import annotations

import os
import re
import subprocess
from pathlib import Path
from typing import Dict, Any, List

from CONFIG.domains import DomainsConfig
from CONFIG.config import Config


def get_file_line_count(file_path: str) -> int:
    """Подсчитывает количество строк в файле."""
    try:
        if not os.path.exists(file_path):
            return 0
        with open(file_path, "r", encoding="utf-8") as f:
            return sum(1 for _ in f if _.strip())
    except Exception:
        return 0


def get_lists_stats() -> Dict[str, Any]:
    """Возвращает статистику по файлам списков."""
    base_dir = Path(__file__).parent.parent
    return {
        "porn_domains": get_file_line_count(base_dir / Config.PORN_DOMAINS_FILE),
        "porn_keywords": get_file_line_count(base_dir / Config.PORN_KEYWORDS_FILE),
        "supported_sites": get_file_line_count(base_dir / Config.SUPPORTED_SITES_FILE),
    }


def get_domain_lists() -> Dict[str, List[str]]:
    """Возвращает все списки доменов из CONFIG/domains.py."""
    return {
        "WHITE_KEYWORDS": list(getattr(DomainsConfig, "WHITE_KEYWORDS", [])),
        "GALLERYDL_ONLY_DOMAINS": list(getattr(DomainsConfig, "GALLERYDL_ONLY_DOMAINS", [])),
        "GALLERYDL_ONLY_PATH": list(getattr(DomainsConfig, "GALLERYDL_ONLY_PATH", [])),
        "GALLERYDL_FALLBACK_DOMAINS": list(getattr(DomainsConfig, "GALLERYDL_FALLBACK_DOMAINS", [])),
        "YTDLP_ONLY_DOMAINS": list(getattr(DomainsConfig, "YTDLP_ONLY_DOMAINS", [])),
        "WHITELIST": list(getattr(DomainsConfig, "WHITELIST", [])),
        "GREYLIST": list(getattr(DomainsConfig, "GREYLIST", [])),
        "NO_COOKIE_DOMAINS": list(getattr(DomainsConfig, "NO_COOKIE_DOMAINS", [])),
        "PROXY_DOMAINS": list(getattr(DomainsConfig, "PROXY_DOMAINS", [])),
        "PROXY_2_DOMAINS": list(getattr(DomainsConfig, "PROXY_2_DOMAINS", [])),
        "NO_FILTER_DOMAINS": list(getattr(DomainsConfig, "NO_FILTER_DOMAINS", [])),
        "TIKTOK_DOMAINS": list(getattr(DomainsConfig, "TIKTOK_DOMAINS", [])),
        "CLEAN_QUERY": list(getattr(DomainsConfig, "CLEAN_QUERY", [])),
        "BLACK_LIST": list(getattr(DomainsConfig, "BLACK_LIST", [])),
    }


def update_domain_list(list_name: str, items: List[str]) -> bool:
    """Обновляет список доменов в CONFIG/domains.py."""
    domains_path = Path(__file__).parent.parent / "CONFIG" / "domains.py"
    try:
        with open(domains_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
        
        # Ищем начало списка
        start_idx = None
        end_idx = None
        indent = "    "
        for i, line in enumerate(lines):
            if re.match(rf'^\s*{list_name}\s*=\s*\[', line):
                start_idx = i
                # Определяем отступ
                indent_match = re.match(r'^(\s*)', line)
                if indent_match:
                    indent = indent_match.group(1)
                break
        
        if start_idx is None:
            return False
        
        # Ищем конец списка
        bracket_count = 0
        found_open = False
        for i in range(start_idx, len(lines)):
            line = lines[i]
            for char in line:
                if char == '[':
                    bracket_count += 1
                    found_open = True
                elif char == ']':
                    bracket_count -= 1
                    if found_open and bracket_count == 0:
                        end_idx = i
                        break
            if end_idx is not None:
                break
        
        if end_idx is None:
            return False
        
        # Формируем новый список
        new_lines = [f"{indent}{list_name} = [\n"]
        for item in items:
            new_lines.append(f'{indent}    "{item}",\n')
        new_lines.append(f"{indent}]\n")
        
        # Заменяем старый список новым
        lines[start_idx:end_idx + 1] = new_lines
        
        with open(domains_path, "w", encoding="utf-8") as f:
            f.writelines(lines)
        return True
    except Exception as e:
        print(f"Error updating domain list {list_name}: {e}")
        return False


def update_lists() -> Dict[str, Any]:
    """Обновляет списки через script.sh."""
    try:
        script_path = "/root/Telegram/tg-ytdlp-bot/script.sh"
        result = subprocess.run(
            ["bash", script_path],
            capture_output=True,
            text=True,
            timeout=300,  # 5 минут
            check=False,
        )
        if result.returncode == 0:
            return {"status": "ok", "message": "Lists updated successfully", "output": result.stdout}
        else:
            return {"status": "error", "message": result.stderr or "Failed to update lists"}
    except Exception as e:
        return {"status": "error", "message": str(e)}


import json
import urllib.request
import urllib.error
from datetime import datetime, timezone
from loguru import logger
from utils.config import AppConfig


def markdown_to_notion_blocks(md):
    blocks = []
    lines = md.splitlines()
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if not line:
            i += 1
            continue
        if line.startswith('- [ ]') or line.startswith('[ ]'):
            content = line.replace('- [ ]', '').replace('[ ]', '').strip()
            blocks.append({
                "object": "block",
                "type": "to_do",
                "to_do": {
                    "rich_text": [{"text": {"content": content}}],
                    "checked": False
                }
            })
            i += 1
        elif line.startswith('### '):
            blocks.append({
                "object": "block",
                "type": "heading_2",
                "heading_2": {
                    "rich_text": [{"text": {"content": line[4:].strip()}}]
                }
            })
            i += 1
        elif line.startswith('- '):
            while i < len(lines) and lines[i].strip().startswith('- ') and not (lines[i].strip().startswith('- [ ]')):
                item = lines[i].strip()[2:].strip()
                blocks.append({
                    "object": "block",
                    "type": "bulleted_list_item",
                    "bulleted_list_item": {
                        "rich_text": [{"text": {"content": item}}]
                    }
                })
                i += 1
        else:
            blocks.append({
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [{"text": {"content": line}}]
                }
            })
            i += 1
    return blocks


def send_to_notion(markdown: str, notion_token: str, notion_db_id: str, category: str, title: str):
    """Sends the formatted summary to Notion."""
    now_utc = datetime.now(timezone.utc)
    date_str = now_utc.isoformat(timespec='seconds').replace('+00:00', 'Z')
    properties = {
        "Name": {
            "title": [{"text": {"content": title}}]
        },
        "Date": {
            "date": {"start": date_str}
        },
        "Category": {
            "select": {"name": category}
        },
        "Attendees": {
            "people": []
        }
    }
    children = [
        {
            "object": "block",
            "type": "heading_2",
            "heading_2": {
                "rich_text": [{"text": {"content": "Daily Summary"}}]
            }
        }
    ]
    children += markdown_to_notion_blocks(markdown)
    payload = {
        "parent": {"database_id": notion_db_id.replace('-', '')},
        "properties": properties,
        "children": children
    }
    headers = {
        "Notion-Version": "2022-06-28",
        "Content-Type": "application/json",
        "Authorization": f"Bearer {notion_token}"
    }
    req = urllib.request.Request(
        url=AppConfig.notion_api_url,
        data=json.dumps(payload).encode(),
        headers=headers,
        method="POST"
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            resp.read()
    except urllib.error.HTTPError as e:
        error_body = e.read().decode()
        logger.error(f"❌ Notion API error ({e.code}): {error_body}")
        raise RuntimeError(f"Notion API returned HTTP {e.code}") from e
    except Exception as e:
        logger.error(f"❌ Unexpected error during Notion API call: {e}")
        raise

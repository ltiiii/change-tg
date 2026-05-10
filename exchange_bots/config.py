from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


@dataclass(slots=True)
class Settings:
    client_bot_token: str
    admin_bot_token: str
    admin_ids: set[int]
    data_dir: Path


def load_settings() -> Settings:
    load_dotenv()

    client_bot_token = os.getenv("CLIENT_BOT_TOKEN", "").strip()
    admin_bot_token = os.getenv("ADMIN_BOT_TOKEN", "").strip()
    admin_ids_raw = os.getenv("ADMIN_IDS", "").strip()
    data_dir = Path(os.getenv("DATA_DIR", "./data")).resolve()

    if not client_bot_token:
        raise RuntimeError("CLIENT_BOT_TOKEN is not set")
    if not admin_bot_token:
        raise RuntimeError("ADMIN_BOT_TOKEN is not set")
    if not admin_ids_raw:
        raise RuntimeError("ADMIN_IDS is not set")

    admin_ids = {
        int(chunk.strip())
        for chunk in admin_ids_raw.split(",")
        if chunk.strip()
    }
    if not admin_ids:
        raise RuntimeError("ADMIN_IDS is empty")

    return Settings(
        client_bot_token=client_bot_token,
        admin_bot_token=admin_bot_token,
        admin_ids=admin_ids,
        data_dir=data_dir,
    )

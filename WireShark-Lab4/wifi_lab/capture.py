"""Download and extraction of 802.11 trace files."""

from __future__ import annotations

import io
import logging
import os
import zipfile
from pathlib import Path

import requests

from .config import ZIP_MEMBER, ZIP_URL

logger = logging.getLogger(__name__)


def download_trace(
    url: str = ZIP_URL,
    member: str = ZIP_MEMBER,
    output_path: str | Path = "",
) -> str:
    """Download the trace ZIP and extract *member* to *output_path*.

    Returns the path to the extracted file.  If the file already exists on
    disk, the download is skipped.
    """
    output_path = str(output_path) if output_path else member
    if os.path.exists(output_path):
        logger.info("Trace file already exists: %s", output_path)
        return output_path

    logger.info("Downloading trace archive from %s …", url)
    resp = requests.get(url, timeout=60)
    resp.raise_for_status()

    with zipfile.ZipFile(io.BytesIO(resp.content)) as zf:
        names = zf.namelist()
        # Find the member (may be in a subdirectory inside the zip)
        match = None
        for name in names:
            if name.endswith(member) or os.path.basename(name) == member:
                match = name
                break
        if match is None:
            raise FileNotFoundError(
                f"'{member}' not found in archive.  Contents: {names}"
            )
        data = zf.read(match)

    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
    with open(output_path, "wb") as f:
        f.write(data)
    logger.info("Extracted %s → %s", match, output_path)
    return output_path

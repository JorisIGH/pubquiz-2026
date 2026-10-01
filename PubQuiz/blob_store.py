"""
Shared storage helpers for the pub quiz.

Every submission is ONE blob in Azure Blob Storage:
  - the blob content is the generated PNG
  - the player's name and prompt are stored as blob metadata

The blob name starts with a UTC timestamp, so listing the blobs returns them in
submission order. This replaces the old Google Sheet.
"""
import uuid
from datetime import datetime, timezone
from urllib.parse import quote, unquote

import streamlit as st
from azure.core.exceptions import ResourceExistsError
from azure.storage.blob import BlobServiceClient, ContainerClient, ContentSettings

AZURE_BLOB_CONNECTION_STRING = st.secrets["AZURE_BLOB_CONNECTION_STRING"]
AZURE_BLOB_CONTAINER = st.secrets["AZURE_BLOB_CONTAINER"]
# Only blobs under this "folder" belong to the current quiz.
# (Older images from previous years live under "pubquiz/" and are ignored.)
BLOB_PREFIX = st.secrets.get("AZURE_BLOB_PREFIX", "pubquiz/current/")

# Blob metadata travels as HTTP headers: ASCII only, 8 KB in total.
# We URL-encode values (so names like "Zoë" work) and cap the prompt length.
MAX_PROMPT_CHARS = 2000


@st.cache_resource
def get_container_client() -> ContainerClient:
    service = BlobServiceClient.from_connection_string(AZURE_BLOB_CONNECTION_STRING)
    container = service.get_container_client(AZURE_BLOB_CONTAINER)
    try:
        container.create_container()
    except ResourceExistsError:
        pass
    return container


def save_submission(name: str, prompt: str, image_bytes: bytes) -> str:
    """Store the image plus name/prompt as one blob. Returns the blob name."""
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%f")
    blob_name = f"{BLOB_PREFIX}{timestamp}_{uuid.uuid4().hex[:8]}.png"
    get_container_client().upload_blob(
        name=blob_name,
        data=image_bytes,
        overwrite=False,
        metadata={
            "name": quote(name),
            "prompt": quote(prompt[:MAX_PROMPT_CHARS]),
        },
        content_settings=ContentSettings(content_type="image/png"),
    )
    return blob_name


def list_submissions() -> list[dict]:
    """All submissions of the current quiz, oldest first."""
    blobs = get_container_client().list_blobs(
        name_starts_with=BLOB_PREFIX, include=["metadata"]
    )
    submissions = []
    for blob in blobs:
        meta = blob.metadata or {}
        prompt = unquote(meta.get("prompt", ""))
        if not prompt:
            continue
        submissions.append(
            {"blob_name": blob.name, "name": unquote(meta.get("name", "")), "prompt": prompt}
        )
    # Blob names start with the timestamp, so sorting by name = sorting by time
    return sorted(submissions, key=lambda s: s["blob_name"])


@st.cache_data(max_entries=100, show_spinner=False)
def get_image_bytes(blob_name: str) -> bytes:
    """Download an image. Cached: a blob never changes once it is written."""
    return get_container_client().download_blob(blob_name).readall()


def delete_all_submissions() -> int:
    """Delete every blob of the current quiz. Returns how many were deleted."""
    container = get_container_client()
    names = [b.name for b in container.list_blobs(name_starts_with=BLOB_PREFIX)]
    for name in names:
        container.delete_blob(name, delete_snapshots="include")
    get_image_bytes.clear()
    return len(names)

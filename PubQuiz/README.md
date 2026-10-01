# PubQuiz

A Streamlit pub quiz game. Players type a prompt, Azure OpenAI (`gpt-image-1.5`) turns it into
an image, and the results page shows everyone's images in a 3×4 grid.

| Page | File | Purpose |
|---|---|---|
| Input | `input.py` | Players enter their name and prompt |
| Results | `pages/results.py` | Big-screen grid, **Refresh Results** and **Delete Results** buttons |
| — | `blob_store.py` | Saves, lists and deletes submissions in Azure Blob Storage |

Each submission is one blob: the PNG image, with the player's name and prompt stored as blob metadata.

## Setup

1. **Azure OpenAI:** a `gpt-image-1.5` deployment (here: `gpt-image-1.5-pubquiz`).
2. **Azure Storage account:** one private container (e.g. `pubquiz`). The app creates the
   container itself if it doesn't exist yet.
3. **Streamlit Community Cloud:** create the app from this repo with main file `input.py`, then paste
   the contents of `.streamlit/secrets.toml.example` (with real values) into
   *App → Settings → Secrets*.

For local runs: copy `.streamlit/secrets.toml.example` to `.streamlit/secrets.toml`, fill it in,
then `pip install -r requirements.txt` and `streamlit run input.py`.
`secrets.toml` is in `.gitignore`, so never commit it.

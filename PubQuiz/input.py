import base64

import streamlit as st
from openai import APIStatusError, AzureOpenAI, BadRequestError, RateLimitError

from blob_store import save_submission

# Make page
st.set_page_config(page_title="Input")

# --- Configuration (from .streamlit/secrets.toml or Streamlit Cloud secrets) ---
AZURE_OPENAI_ENDPOINT = st.secrets["AZURE_OPENAI_ENDPOINT"]
AZURE_OPENAI_API_KEY = st.secrets["AZURE_OPENAI_API_KEY"]
AZURE_OPENAI_IMAGE_DEPLOYMENT = st.secrets.get(
    "AZURE_OPENAI_IMAGE_DEPLOYMENT", "gpt-image-1.5-pubquiz"
)
AZURE_OPENAI_API_VERSION = st.secrets.get("AZURE_OPENAI_API_VERSION", "2025-04-01-preview")
# low | medium | high  (medium is a good speed/quality balance for a pub quiz)
IMAGE_QUALITY = st.secrets.get("AZURE_OPENAI_IMAGE_QUALITY", "medium")


@st.cache_resource
def get_openai_client() -> AzureOpenAI:
    return AzureOpenAI(
        azure_endpoint=AZURE_OPENAI_ENDPOINT,
        api_key=AZURE_OPENAI_API_KEY,
        api_version=AZURE_OPENAI_API_VERSION,
        timeout=180,  # gpt-image can take up to a minute or more
        max_retries=2,
    )


def generate_image(prompt: str) -> bytes:
    """Generate an image with Azure OpenAI gpt-image-1.5 and return the PNG bytes."""
    result = get_openai_client().images.generate(
        model=AZURE_OPENAI_IMAGE_DEPLOYMENT,  # = the deployment name in Azure
        prompt=prompt,
        n=1,
        size="1024x1024",  # square, same as the old 1:1 aspect ratio
        quality=IMAGE_QUALITY,
        output_format="png",
        # NB: don't pass response_format – gpt-image models always return base64
    )
    if not result.data or not result.data[0].b64_json:
        raise RuntimeError("Azure OpenAI response did not contain image data.")
    return base64.b64decode(result.data[0].b64_json)


st.title("Prompt Engineering")

name = st.text_input("Your name: ")
prompt = st.text_input("Your prompt: ")

button_pressed = st.button("Generate Image")

if button_pressed:
    if not prompt.strip():
        st.warning("Please enter a prompt first.")
        st.stop()

    with st.spinner("We are saving your input. This may take up to a minute..."):
        try:
            image_bytes = generate_image(prompt)
        except RateLimitError:
            st.error("Too many requests at the same time – please wait a few seconds and try again.")
            st.stop()
        except BadRequestError as e:
            # Typically the content filter rejecting the prompt
            st.error(f"Your prompt was rejected by the image model. Try rephrasing it.\n\n{e}")
            st.stop()
        except APIStatusError as e:
            st.error(f"Image generation failed ({e.status_code}): {e}")
            st.stop()
        except Exception as e:
            st.error(f"Image generation failed: {e}")
            st.stop()

        try:
            save_submission(name, prompt, image_bytes)
        except Exception as e:
            st.error(f"Saving your image failed: {e}")
            st.stop()

    st.success("Your input has been saved!")

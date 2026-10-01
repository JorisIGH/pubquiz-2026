import streamlit as st

from blob_store import delete_all_submissions, get_image_bytes, list_submissions

st.title("The results!")

placeholder_image_path = "https://i.imgur.com/G8snaMz.png"

# Add a refresh button to reload the results
if st.button("Refresh Results"):
    st.rerun()

# Read the current submissions from blob storage (oldest first)
submissions = list_submissions()

# Create the 3x4 image grid; empty slots show the placeholder
num_rows, num_cols = 3, 4

for row in range(num_rows):
    cols = st.columns(num_cols)
    for col_idx, col in enumerate(cols):
        image_idx = row * num_cols + col_idx
        if image_idx < len(submissions):
            sub = submissions[image_idx]
            caption = f"{sub['name']}: {sub['prompt']}"
            try:
                col.image(get_image_bytes(sub["blob_name"]), caption=caption)
            except Exception:
                col.image(placeholder_image_path, caption=caption)
        else:
            col.image(placeholder_image_path, caption="Waiting for a prompt")

# Add a reset button to clear the results
if st.button("Delete Results"):
    delete_all_submissions()
    st.write("All results have been deleted!")
    st.rerun()

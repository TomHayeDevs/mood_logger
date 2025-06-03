"""
app.py

Streamlit app that:
- Lets user select a mood (1-5) and optional free-text note.
- On submit, calls storage.append_row(...)
- Fetches today's mood counts, plots a bar chart.
"""

import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

from storage import append_row, get_today_counts

from dotenv import load_dotenv

load_dotenv()

# ─── PAGE CONFIG ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Mood of the Queue",
    page_icon="😊",
    layout="centered",
)

# ─── HEADER ─────────────────────────────────────────────────────────────────────
st.markdown(
    """
    <h1 style="text-align:center;">✨ Mood of the Queue ✨</h1>
    <p style="text-align:center;">Log and visualize team mood (1-5)</p>
    """,
    unsafe_allow_html=True,
)
st.write("---")

# ─── LOGGING SECTION ────────────────────────────────────────────────────────────
st.subheader("Log Your Mood")
col1, col2 = st.columns([1, 3])

with col1:
    mood = st.radio(
        "Select mood", options=[1, 2, 3, 4, 5], index=2, horizontal=True
    )

with col2:
    note = st.text_input("Optional note", placeholder="Any extra context?")

if st.button("Submit"):
    success = append_row(mood, note)
    if success:
        st.success("Logged successfully!")
    else:
        st.error("Failed to log – check credentials or Sheet permissions.")

st.write("---")

# ─── VISUALIZATION SECTION ─────────────────────────────────────────────────────
st.subheader("Today's Mood Distribution")

counts = get_today_counts()
df = pd.DataFrame({
    "Mood": list(counts.keys()),
    "Count": list(counts.values()),
})

# If all zero, show a message
if df["Count"].sum() == 0:
    st.write("No mood logged yet today.")
else:
    fig, ax = plt.subplots(figsize=(6, 4))
    bars = ax.bar(df["Mood"], df["Count"], color="#3399ff")
    ax.set_xlabel("Mood (1 = low, 5 = high)")
    ax.set_ylabel("Number of entries")
    ax.set_title("Mood Counts for Today")
    ax.set_xticks([1, 2, 3, 4, 5])
    ax.set_ylim(0, df["Count"].max() + 1)
    for bar in bars:
        height = bar.get_height()
        if height > 0:
            ax.annotate(f"{int(height)}",
                        xy=(bar.get_x() + bar.get_width() / 2, height),
                        xytext=(0, 3),
                        textcoords="offset points",
                        ha='center', va='bottom')
    plt.tight_layout()
    st.pyplot(fig)

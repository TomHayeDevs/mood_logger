"""
app.py

Streamlit app that:
- Lets user select a mood (1-5) and optional free-text note.
- On submit, calls storage.append_row(...)
- Fetches today's mood counts, plots a bar chart.
"""

from datetime import datetime
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

from streamlit_autorefresh import st_autorefresh
from storage import append_row, get_today_counts, get_counts_between

from dotenv import load_dotenv

load_dotenv()

st_autorefresh(interval=5000, key="auto_refresh")

EMOJI_MAP = {
    "😡": 1,
    "😠": 2,
    "🤔": 3,
    "🙂": 4,
    "😁": 5,
}

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
    # mood = st.radio(
    #     "Select mood", options=[1, 2, 3, 4, 5], index=2, horizontal=True
    # )
    emoji = st.selectbox(
        "Select mood",
        options=list(EMOJI_MAP.keys()),
        index=2,  # default is 🤔
        help="Scroll to pick an emoji"
    )
    mood = EMOJI_MAP[emoji]

with col2:
    note = st.text_input("Optional note", placeholder="Any extra context?")

if st.button("Submit"):
    success = append_row(mood, note)
    if success:
        st.success("Logged successfully!")
    else:
        st.error("Failed to log - check credentials or Sheet permissions.")

st.write("---")

# ─── VISUALIZATION SECTION ─────────────────────────────────────────────────────
st.subheader("Current Mood Distribution")

# dates filter
# Note: This is a placeholder for future functionality.
st.subheader("Filter by Date")
col_start, col_end = st.columns(2)
with col_start:
    start = st.date_input(
        "Start date", value=datetime.now().date(), 
        help="Select the beginning of the range"
    )
with col_end:
    end = st.date_input(
        "End date", value=datetime.now().date(), 
        help="Select the end of the range"
    )


if start > end:
    st.error("Start date cannot be after end date.")
else:
    # Fetch counts for that range:
    counts = get_counts_between(start.isoformat(), end.isoformat())
    df = pd.DataFrame({
        "Mood": list(counts.keys()),
        "Count": list(counts.values()),
    })
    
# counts = get_today_counts()
# df = pd.DataFrame({
#     "Mood": list(counts.keys()),
#     "Count": list(counts.values()),
# })

EMOJI_TICKS = {v: k for k, v in EMOJI_MAP.items()}

# If all zero, show a message
if df["Count"].sum() == 0:
    st.write("No mood logged in this period. Please log your mood above.")
else:
    fig, ax = plt.subplots(figsize=(6, 4))
    bars = ax.bar(df["Mood"], df["Count"], color="#3399ff")
    ax.set_xlabel("Mood")
    ax.set_ylabel("Number of tickets")
    ax.set_xticks([1, 2, 3, 4, 5])
    ax.set_xticklabels([EMOJI_TICKS[i] for i in [1, 2, 3, 4, 5]])
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

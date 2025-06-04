import os
import pandas as pd
import matplotlib.pyplot as plt
import plotly.express as px
import streamlit as st
from datetime import datetime
from dotenv import load_dotenv
from streamlit_autorefresh import st_autorefresh

from storage import append_row, get_counts_between, get_latest_notes

load_dotenv()

st.set_page_config(
    page_title="Mood of the Queue",
    page_icon="😊",
    layout="centered",
)

# Force a rerun every 5 seconds:
st_autorefresh(interval=5000, key="auto_refresh")

st.markdown(
    """
    <h1 style="text-align:center;">✨ Mood of the Queue ✨</h1>
    <p style="text-align:center;">Log and visualize team mood</p>
    """,
    unsafe_allow_html=True,
)
st.write("---")

# ─── LOGGING SECTION ────────────────────────────────────────────────────────────
st.subheader("Log Your Mood")

EMOJI_MAP = {"😡": 1, "😠": 2, "🤔": 3, "🙂": 4, "😁": 5}
# emoji = st.selectbox("Select mood", options=list(EMOJI_MAP.keys()), index=2)
emoji = st.select_slider(
    "Select mood",
    options=list(EMOJI_MAP.keys()),
    value="🤔",
    format_func=lambda x: x,  # the slider was not displaying the emoji correctly, so added this format function (Copilot recommendation)
)
mood = EMOJI_MAP[emoji]
note = st.text_input("Optional note", placeholder="Any extra context?")

if st.button("Submit"):
    success = append_row(mood, note)
    if success:
        st.success("Logged successfully!")
    else:
        st.error("Failed to log - check credentials or Sheet permissions.")

st.write("---")

# ─── FILTER SECTION ─────────────────────────────────────────────────────────────
# st.subheader("Filter by Date")
# col_start, col_end = st.columns(2)
# with col_start:
#     start = st.date_input("Start date", value=datetime.now().date())
# with col_end:
#     end = st.date_input("End date", value=datetime.now().date())

# if start > end:
#     st.error("Start date cannot be after end date.")
#     st.stop()

# ─── VISUALIZATION SECTION ─────────────────────────────────────────────────────
st.subheader("Mood Distribution")
col_start, col_end = st.columns(2)
with col_start:
    start = st.date_input("Start date", value=datetime.now().date())
with col_end:
    end = st.date_input("End date", value=datetime.now().date())

if start > end:
    st.error("Start date cannot be after end date.")
    st.stop()


counts = get_counts_between(start.isoformat(), end.isoformat())
df = pd.DataFrame({"Mood": list(counts.keys()), "Count": list(counts.values())})


if df["Count"].sum() == 0:
    st.write("No mood logged in this date range.")
else:
    EMOJI_TICKS = {v: k for k, v in EMOJI_MAP.items()}

    # fig, ax = plt.subplots(figsize=(6, 4))
    # bars = ax.bar(df["Mood"], df["Count"], color="#33eca5")
    # ax.set_xlabel("Mood")
    # ax.set_ylabel("Number of entries")
    # ax.set_title(f"Mood Counts: {start.isoformat()} to {end.isoformat()}")
    # ax.set_xticks([1, 2, 3, 4, 5])
    # ax.set_xticklabels([EMOJI_TICKS[i] for i in [1, 2, 3, 4, 5]])
    # ax.set_ylim(0, df["Count"].max() + 1)
    # for bar in bars:
    #     h = bar.get_height()
    #     if h > 0:
    #         ax.annotate(
    #             f"{int(h)}",
    #             xy=(bar.get_x() + bar.get_width() / 2, h),
    #             xytext=(0, 3),
    #             textcoords="offset points",
    #             ha="center",
    #             va="bottom",
    #         )
    # plt.tight_layout()
    # st.pyplot(fig)

    latest_notes = get_latest_notes()
    hover_texts = [latest_notes.get(i, "(no note)") for i in [1, 2, 3, 4, 5]]

    fig = px.bar(
        x=[EMOJI_TICKS[i] for i in [1, 2, 3, 4, 5]],
        y=[counts[i] for i in [1, 2, 3, 4, 5]],
        labels={"x": "Mood", "y": "Number of entries"},
        hover_data={"Note": hover_texts},
    )

    fig.update_layout(
        title_text=f"Mood Counts: {start.isoformat()} to {end.isoformat()}",
        xaxis={'categoryorder':'array','categoryarray':[EMOJI_TICKS[i] for i in [1,2,3,4,5]]}
    )
    st.plotly_chart(fig, use_container_width=True)

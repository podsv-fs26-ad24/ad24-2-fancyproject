import streamlit as st
from datetime import datetime
st.set_page_config(page_title="Feature Wishbox", layout="centered")

st.title("💡 Feature Wishbox")
st.write("Tell us what features or information you’d like to see in the future:")

feedback = st.text_area(
    "Your ideas",
    placeholder="Example: I’d love to filter by country and see CO₂ per person…",
    height=150
)

name = st.text_input("Optional: Your name or initials")

if st.button("Submit"):
    if feedback.strip():
        timestamp = datetime.now().isoformat(timespec="seconds")
        entry = f"---\nTime: {timestamp}\nName: {name or 'anonymous'}\nFeedback:\n{feedback.strip()}\n\n"
        with open("feature_requests.txt", "a", encoding="utf-8") as f:
            f.write(entry)
        st.success("Thank you! Your idea has been saved. 🙌")
    else:
        st.warning("Please write something before submitting.")
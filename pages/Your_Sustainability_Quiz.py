# Travel Sustainability Quiz
import streamlit as st

from components.navbar import navbar
navbar()

st.title("Travel Sustainability Quiz")

# ---------------------------------------------------
# 1. Initialize session state
# ---------------------------------------------------
st.session_state.setdefault("page", "start")   # start | quiz | results
st.session_state.setdefault("answers", {})

# ---------------------------------------------------
# 2. Define questions
# ---------------------------------------------------
questions = [
    ("How do you usually commute to the office?",
     [("Car alone", 0), ("Carpool / mixed", 1), ("Bike / walk / public transport", 2)]),
    ("How often do you fly for leisure?",
     [("Several times a year", 0), ("Once a year", 1), ("Rarely", 2)]),
    ("How often do you fly for business?",
     [("Monthly or more", 0), ("A few times a year", 1), ("Only when absolutely necessary", 2)]),
    ("For business trips under 600 km, what do you choose?",
     [("Always fly", 0), ("Depends on schedule", 1), ("Train whenever possible", 2)]),
    ("How do you plan your holidays?",
     [("Long‑haul flights every year", 0), ("Mix of near and far destinations", 1), ("Mostly regional / train‑friendly", 2)]),
    ("How do you travel within cities on trips?",
     [("Taxi/Uber by default", 0), ("Mix of taxi and public transport", 1), ("Public transport / walking", 2)]),
    ("How often do you rent a car?",
     [("Frequently", 0), ("Sometimes", 1), ("Rarely / only when necessary", 2)]),
    ("What type of car do you drive (if applicable)?",
     [("Large petrol/diesel", 0), ("Small/efficient petrol/diesel", 1), ("Hybrid / electric", 2)]),
    ("How often do you offset your flights?",
     [("Never", 0), ("Sometimes", 1), ("Always", 2)]),
    ("How do you choose hotels?",
     [("Price only", 0), ("Price + some sustainability", 1), ("Prefer eco‑certified hotels", 2)]),
    ("How do you pack for trips?",
     [("Heavy luggage", 0), ("Medium", 1), ("Light / hand luggage only", 2)]),
    ("How do you handle food on business trips?",
     [("No attention to waste", 0), ("Try to avoid waste", 1), ("Plan / choose low‑waste options", 2)]),
    ("How do you handle water on trips?",
     [("Buy bottled water daily", 0), ("Sometimes reusable bottle", 1), ("Always bring reusable bottle", 2)]),
    ("How do you join meetings abroad?",
     [("Prefer in‑person", 0), ("Hybrid", 1), ("Prefer virtual unless essential", 2)]),
    ("How do you think about your travel footprint?",
     [("Never considered it", 0), ("Sometimes aware", 1), ("Actively try to reduce it", 2)]),
]

# ---------------------------------------------------
# PAGE 1 — Start
# ---------------------------------------------------
if st.session_state.page == "start":
    st.write("""Ready to discover your travel sustainability persona?  
             This quiz shows where your habits shine and where you can level up to help reduce our company's carbon footprint.""")
    st.write("Click to begin quiz")


    if st.button("Begin Quiz"):
        st.session_state.answers = {}
        st.session_state.page = "quiz"
        st.rerun()   # ← FIX double-click


# ---------------------------------------------------
# PAGE 2 — Quiz Questions
# ---------------------------------------------------
elif st.session_state.page == "quiz":

    st.header("Answer all questions")

    for i, (question, options) in enumerate(questions):

        st.markdown(f"### **{question}**")

        choice = st.radio(
            "",
            [opt[0] for opt in options],
            key=f"q{i}",
            index=None   # no preselected answer
        )

        if choice is not None:
            for text, score in options:
                if choice == text:
                    st.session_state.answers[i] = score

    if st.button("Submit Answers"):
        if len(st.session_state.answers) == len(questions):
            st.session_state.page = "results"
            st.rerun()
        else:
            st.warning("Please answer all questions before submitting.")


# ---------------------------------------------------
# PAGE 3 — Results
# ---------------------------------------------------
elif st.session_state.page == "results":

    total_score = sum(st.session_state.answers.values())

    st.header("Your Travel Sustainability Profile")
    st.markdown(
        f"<p style='font-size:18px;'>Your total score: <b>{total_score} / 30</b></p>",
        unsafe_allow_html=True
    )

    if total_score <= 10:
        st.subheader("The Smog‑Orc Syndicate")
        st.image("docs/pics/smogorc.png", width=200)
        st.write("""
        Your travel habits generate a high carbon footprint.  
        Small changes like choosing trains for regional trips or reducing flight frequency  
        can make a big difference. Try being more mindful!
        """)

    elif 11 <= total_score <= 20:
        st.subheader("Rohan Riders of the Middle Ground")
        st.image("docs/pics/rohanrider.png", width=200)
        st.write("""
        You make some sustainable choices, but there's room to improve.  
        With a few adjustments like lighter packing or more virtual meetings  
        you can significantly reduce your travel impact.
        """)

    else:
        st.subheader("Gandalf the Green")
        st.image("docs/pics/gandalfgreen.png", width=200)
        st.write("""
        You travel consciously and efficiently.  
        Your habits already reduce emissions keep inspiring others in the company  
        to follow your lead. Good job!
        """)

    if st.button("Restart Quiz"):
        st.session_state.page = "start"
        st.session_state.answers = {}
        st.rerun()   # ← FIX double-click

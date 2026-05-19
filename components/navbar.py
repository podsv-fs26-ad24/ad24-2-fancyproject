import streamlit as st

def navbar():
    col1, col2, col3, col4, col5 = st.columns([1, 1, 1, 1, 2])

    with col1:
        st.page_link("Booking.py", label="Booking", icon="✈️")

    with col2:
        st.page_link("pages/europe.py", label="Europe", icon="🌍")

    with col3:
        st.page_link("pages/worldwide.py", label="Worldwide", icon="🗺️")

    with col4:
        st.page_link("pages/Your_Sustainability_Quiz.py", label="Quiz", icon="❓")

    with col5:
        st.page_link("pages/Your_Thoughts_&_Wishes.py", label="Your thoughts & wishes", icon="💬")

    st.markdown("---")
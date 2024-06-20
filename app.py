#app.py
import streamlit as st
import requests

# Title
st.title("Rectangle Area Calculator")

# Input fields for length and breadth
length = st.number_input("Enter the length:", min_value=0.0, step=0.1)
breadth = st.number_input("Enter the breadth:", min_value=0.0, step=0.1)

# Calculate the area
if st.button("Calculate Area"):
    # Send a request to the backend to calculate the area
    response = requests.post('http://localhost:8000/calculate_area', json={"length": length, "breadth": breadth})
    area = response.json().get('area', 'Error calculating area')
    st.write(f"The area of the rectangle is: {area} square units.")
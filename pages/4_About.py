import streamlit as st

st.set_page_config(page_title="About the Project", layout="wide")

# ---- PAGE TITLE ----
st.title("About the Project")

st.write("")
st.write("")

# ---- INTRO ----
st.markdown(
    """
    ### Project Overview
    This project is part of our coursework at **Georgian College**, completed by a four-member team:
    **Hrishi Sonar, Hamza Syed, Mustafa Al-Obaidi, and Damilola Jimoh**.

    We collaborated with **Zoinc Intelligence & Consulting**, with strategic guidance and support from:
    - **Robin Lobb – Executive Director**  
    - **Andrew McNeil – Director of Analytics**

    The goal of the project is to analyze **voter participation trends** across Toronto’s **Federal, Provincial, and Municipal elections**, 
    and present meaningful insights through interactive geospatial maps and dashboards.
    """
)

st.write("---")

# ---- BENEFICIARIES ----
st.markdown(
    """
    ### Who Can Benefit From This Project?
    - **Researchers & Policy Analysts** interested in civic engagement patterns  
    - **City Planners & Public Service Departments** who rely on data-driven insights  
    - **Community Organizations** promoting voter awareness and turnout  
    - **Educators & Students** using geospatial data in academic settings  
    - **General Public**, through easy-to-understand, interactive tools  
    """
)

st.write("---")

# ---- DATA SOURCES ----
st.markdown(
    """
    ### Data Sources & Transparency
    All datasets used in this project were collected from publicly accessible sources, primarily:
    - Government open data portals  
    - Elections Canada, Elections Ontario, and the City of Toronto  
    - Supporting statistical and demographic sources  

    To maintain full transparency and reproducibility, the team created a detailed  
    **Data Inventory Sheet**, which documents data sources, formats, licenses, and purpose.
    """
)

# ---- DATA INVENTORY LINK ----
st.markdown(
    """
    🔗 **Access the Data Inventory Sheet:**  
    [https://docs.google.com/spreadsheets/d/1Y6xNkAhqBA0_KD-9PhBypJIy1ZnlmwtRnJDG7pj8z8Q/edit?gid=0#gid=0](https://docs.google.com/spreadsheets/d/1Y6xNkAhqBA0_KD-9PhBypJIy1ZnlmwtRnJDG7pj8z8Q/edit?gid=0#gid=0)
    """
)

st.write("---")

# ---- THANK YOU ----
st.markdown(
    """
    ### Acknowledgment
    Special thanks to **Zoinc Intelligence & Consulting**  
    for their mentorship throughout this project, and to our professors at Georgian College  
    for supporting the academic and technical development of this work.
    """
)

st.write("")
st.write("")
st.caption("Civic Engagements – Toronto Elections Project • 2025")

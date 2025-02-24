import streamlit as st

st.set_page_config(
    page_title="Calculadora Financiera Interactiva",
    layout="wide",
    page_icon="imgs/calc.ico",
    initial_sidebar_state="expanded",
)

tasa_fija_page = st.Page(
    "pages/tasa_fija_page.py", title="Tasa Fija", icon=":material/finance_mode:"
)
ibr_page = st.Page("pages/ibr_page.py", title="IBR", icon=":material/attach_money:")
ipc_page = st.Page("pages/ipc_page.py", title="IPC", icon=":material/money_bag:")

pg = st.navigation({"Calculadoras": [tasa_fija_page, ibr_page, ipc_page]})
pg.run()

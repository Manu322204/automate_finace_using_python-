import streamlit as st
import pandas as pd
import plotly.express as px
import json
import os

st.set_page_config(
    page_title="Simple Finance App",
    page_icon="$",
    layout="wide"
)

category_file = "categories.json"

if "categories" not in st.session_state:
    if os.path.exists(category_file):
        with open(category_file, "r") as f:
            st.session_state["categories"] = json.load(f)
    else:
        st.session_state["categories"] = {}

def save_categories():
    with open("categories.json", "w") as f:
        json.dump(st.session_state["categories"], f)

def load_transactions(file):
    try:
        if file.name.endswith(".csv"):
            df = pd.read_csv(file)
        else:
            df = pd.read_excel(file)

        df.columns = [col.strip() for col in df.columns]

        df["Amount"] = (
            df["Amount"]
            .astype(str)
            .str.replace(",", "", regex=False)
        )

        df["Amount"] = pd.to_numeric(df["Amount"], errors="coerce")
        df["Date"] = pd.to_datetime(df["Date"], format="%d-%b-%y")

        st.write(df)
        return df

    except Exception as e:
        st.error(f"Error processing file: {e}")
        return None

def main():
    st.title("Simple Finance Dashboard")

    uploaded_file = st.file_uploader(
        "Upload your transaction file",
        type=["csv", "xls", "xlsx"]
    )

    if uploaded_file is not None:
        df = load_transactions(uploaded_file)

        if df is not None:
            debits_df = df[df["Debit/Credit"] == "Debit"].copy()
            credits_df = df[df["Debit/Credit"] == "Credit"].copy()

            tab1, tab2 = st.tabs(["Expenses (debits)", "payments (credits)"])

            with tab1:
                new_category = st.text_input("new category name")
                add_button = st.button("add category")

                if add_button and new_category:
                    if new_category not in st.session_state["categories"]:
                        st.session_state["categories"][new_category] = []
                        save_categories()
                        st.success(f"added a new category: {new_category}")
                        st.rerun()

                st.write(debits_df)

            with tab2:
                st.write(credits_df)

if __name__ == "__main__":
    main()
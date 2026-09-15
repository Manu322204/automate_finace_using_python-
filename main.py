from io import BytesIO

import pandas as pd
import plotly.express as px
import streamlit as st


st.set_page_config(
    page_title="Ledger | Personal Finance",
    page_icon="$",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
        :root {
            --ink: #17212b;
            --muted: #667085;
            --line: #e4e7ec;
            --paper: #fbfcfd;
            --teal: #177e89;
            --coral: #dc6b4c;
        }
        .stApp { background: var(--paper); }
        .block-container { max-width: 1500px; padding: 2.4rem 3.5rem 4rem; }
        [data-testid="stSidebar"] { background: #f2f6f6; border-right: 1px solid var(--line); }
        [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] h2 { color: var(--ink); }
        .stApp h1, .stApp h2, .stApp h3 { color: var(--ink) !important; letter-spacing: -0.035em; }
        h1 { font-size: 2.5rem; margin-bottom: 0.2rem; }
        h2 { font-size: 1.25rem; margin-top: 0.5rem; }
        .eyebrow { color: var(--teal) !important; font-size: 0.72rem; font-weight: 800; letter-spacing: 0.13em; text-transform: uppercase; }
        .subtitle, .status-line { color: var(--muted) !important; }
        .subtitle { font-size: 1rem; margin-bottom: 1.4rem; }
        .status-line { font-size: 0.82rem; padding: 0.7rem 0; }
        [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p,
        [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] h2,
        [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] h3 { color: var(--ink) !important; }
        [data-testid="stMetric"] { background: white; border: 1px solid var(--line); border-radius: 10px; padding: 1rem 1.1rem; box-shadow: 0 1px 2px #1018280a; }
        [data-testid="stMetricLabel"] { color: var(--muted); }
        [data-testid="stMetricValue"] { color: var(--ink); font-size: 1.35rem !important; white-space: nowrap; }
        [data-testid="stMetricDelta"] { font-size: 0.72rem; white-space: nowrap; }
        [data-testid="stDataFrame"] { border: 1px solid var(--line); }
        [data-testid="stFileUploaderFile"], [data-testid="stFileUploaderFile"] * { color: var(--ink) !important; }
        .empty-panel { background: white; border: 1px solid var(--line); border-radius: 12px; padding: 2.5rem; text-align: center; }
        .empty-panel h3 { color: var(--ink) !important; margin: 0 0 0.5rem; }
        .empty-panel p { color: var(--muted) !important; margin: 0; }
    </style>
    """,
    unsafe_allow_html=True,
)


CATEGORY_RULES = {
    "Food & dining": ["ZOMATO", "UBER EATS", "RESTAURANT", "CAFE", "SPINNEYS", "LULU", "HYPERMARKET"],
    "Shopping": ["AMAZON", "NOON", "APPLE.COM", "BOOKING"],
    "Travel": ["ETIHAD", "EMIRATES", "HILTON", "UBER", "AIRWAYS"],
    "Bills & subscriptions": ["NETFLIX", "ADCB BANK FEE", "INSURANCE"],
}
REQUIRED_COLUMNS = {"Date", "Details", "Amount", "Debit/Credit"}
PALETTE = ["#177e89", "#e0a458", "#dc6b4c", "#355070", "#6c8ead", "#8fb9a8", "#9b6b8c"]


def load_transactions(uploaded_file):
    try:
        file_bytes = uploaded_file.getvalue()
        source = BytesIO(file_bytes)
        if uploaded_file.name.lower().endswith(".csv"):
            transactions = pd.read_csv(source)
        else:
            transactions = pd.read_excel(source)

        transactions.columns = [str(column).strip() for column in transactions.columns]
        missing = REQUIRED_COLUMNS - set(transactions.columns)
        if missing:
            missing_columns = ", ".join(sorted(missing))
            st.error(f"This statement is missing required columns: {missing_columns}.")
            return None

        raw_dates = transactions["Date"].copy()
        transactions["Date"] = pd.to_datetime(raw_dates, format="%d-%b-%y", errors="coerce")
        missing_dates = transactions["Date"].isna()
        if missing_dates.any():
            transactions.loc[missing_dates, "Date"] = pd.to_datetime(
                raw_dates.loc[missing_dates], errors="coerce", dayfirst=True
            )
        transactions["Amount"] = (
            transactions["Amount"].astype(str).str.replace(",", "", regex=False)
            .str.replace(r"[^0-9.\-]", "", regex=True)
        )
        transactions["Amount"] = pd.to_numeric(transactions["Amount"], errors="coerce").abs()
        transactions["Details"] = transactions["Details"].fillna("Unknown transaction").astype(str).str.strip()
        transactions["Debit/Credit"] = transactions["Debit/Credit"].fillna("").astype(str).str.strip().str.title()
        if "Status" not in transactions:
            transactions["Status"] = "Recorded"
        transactions["Status"] = transactions["Status"].fillna("Unknown").astype(str).str.strip().str.upper()
        transactions = transactions.dropna(subset=["Date", "Amount"])
        transactions = transactions[transactions["Amount"] > 0].copy()
        transactions = transactions[transactions["Debit/Credit"].isin(["Debit", "Credit"])]

        if transactions.empty:
            st.warning("No usable transactions were found in this statement.")
            return None
        return categorize_transactions(transactions)
    except Exception as error:
        st.error(f"We could not read this statement: {error}")
        return None


def categorize_transactions(transactions):
    def category_for(details):
        normalized = str(details).upper()
        for category, terms in CATEGORY_RULES.items():
            if any(term in normalized for term in terms):
                return category
        return "Other"

    transactions["Category"] = transactions["Details"].map(category_for)
    return transactions


def format_money(value, currency):
    return f"{currency} {value:,.0f}"


def format_compact_money(value, currency):
    absolute_value = abs(value)
    if absolute_value >= 1_000_000:
        amount = f"{value / 1_000_000:.1f}M"
    elif absolute_value >= 1_000:
        amount = f"{value / 1_000:.1f}K"
    else:
        amount = f"{value:,.0f}"
    return f"{currency} {amount}"


def chart_layout(figure, height=340):
    figure.update_layout(
        height=height,
        margin=dict(l=0, r=0, t=12, b=0),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Arial, sans-serif", color="#667085", size=12),
        legend=dict(orientation="h", y=1.08, x=0, title_text=""),
        hoverlabel=dict(bgcolor="#17212b", font_color="white"),
    )
    figure.update_xaxes(showgrid=False, linecolor="#e4e7ec")
    figure.update_yaxes(showgrid=True, gridcolor="#eef1f3", zeroline=False, linecolor="#e4e7ec")
    return figure


def render_empty_state():
    st.markdown(
        """
        <div class="empty-panel">
            <h3>Your money story starts here</h3>
            <p>Upload a CSV or Excel bank statement from the sidebar to see your cash flow, spending patterns, and transaction details.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_overview(transactions, currency):
    expenses = transactions.loc[transactions["Debit/Credit"] == "Debit", "Amount"].sum()
    income = transactions.loc[transactions["Debit/Credit"] == "Credit", "Amount"].sum()
    net = income - expenses
    expense_count = int((transactions["Debit/Credit"] == "Debit").sum())
    savings_rate = net / income if income else 0

    st.markdown('<div class="eyebrow">Financial snapshot</div>', unsafe_allow_html=True)
    metrics = st.columns(4)
    metrics[0].metric("Income", format_compact_money(income, currency))
    metrics[1].metric("Expenses", format_compact_money(expenses, currency))
    delta_text = f"{savings_rate:.1%} saved" if net >= 0 and income else "Overspent" if net < 0 else None
    metrics[2].metric("Net cash flow", format_compact_money(net, currency), delta=delta_text, delta_color="normal" if net >= 0 else "inverse")
    metrics[3].metric("Expense count", f"{expense_count:,}")

    transactions = transactions.copy()
    transactions["Month"] = transactions["Date"].dt.to_period("M").dt.to_timestamp()
    monthly = transactions.groupby(["Month", "Debit/Credit"], as_index=False)["Amount"].sum()
    st.subheader("Cash flow over time")
    flow = px.bar(
        monthly, x="Month", y="Amount", color="Debit/Credit", barmode="relative",
        color_discrete_map={"Debit": "#dc6b4c", "Credit": "#177e89"},
        labels={"Amount": currency, "Debit/Credit": ""}, template="plotly_white",
    )
    chart_layout(flow, 360)
    st.plotly_chart(flow, use_container_width=True, config={"displayModeBar": False})

    left, right = st.columns([1.1, 0.9])
    with left:
        st.subheader("Where expenses go")
        category_totals = (
            transactions[transactions["Debit/Credit"] == "Debit"]
            .groupby("Category", as_index=False)["Amount"].sum().sort_values("Amount", ascending=True)
        )
        category_chart = px.bar(category_totals, x="Amount", y="Category", orientation="h", text_auto=".2s",
                                 color="Category", color_discrete_sequence=PALETTE, labels={"Amount": currency, "Category": ""})
        category_chart.update_traces(textposition="outside", cliponaxis=False)
        chart_layout(category_chart, 340)
        category_chart.update_layout(showlegend=False)
        st.plotly_chart(category_chart, use_container_width=True, config={"displayModeBar": False})
    with right:
        st.subheader("Income and expenses")
        split = pd.DataFrame({"Type": ["Income", "Expenses"], "Amount": [income, expenses]})
        split_chart = px.pie(split, names="Type", values="Amount", hole=0.64, color="Type",
                              color_discrete_map={"Income": "#177e89", "Expenses": "#dc6b4c"})
        split_chart.update_traces(textposition="inside", textinfo="percent", marker=dict(line=dict(color="white", width=3)))
        chart_layout(split_chart, 340)
        st.plotly_chart(split_chart, use_container_width=True, config={"displayModeBar": False})


def render_transactions(transactions, currency):
    st.markdown('<div class="eyebrow">Ledger</div>', unsafe_allow_html=True)
    st.subheader("Transactions")
    filters = st.columns([2, 1, 1, 1])
    search = filters[0].text_input("Search merchant or detail", placeholder="Try Amazon or rent", label_visibility="collapsed")
    types = filters[1].multiselect("Type", ["Debit", "Credit"], default=["Debit", "Credit"], label_visibility="collapsed")
    categories = filters[2].multiselect("Category", sorted(transactions["Category"].unique()), default=sorted(transactions["Category"].unique()), label_visibility="collapsed")
    limit = filters[3].selectbox("Show", [25, 50, 100, "All"], index=0, label_visibility="collapsed")

    visible = transactions[transactions["Debit/Credit"].isin(types) & transactions["Category"].isin(categories)].copy()
    if search:
        visible = visible[visible["Details"].str.contains(search, case=False, na=False)]
    visible = visible.sort_values("Date", ascending=False)
    display = visible[["Date", "Details", "Category", "Debit/Credit", "Amount", "Status"]].copy()
    display["Date"] = display["Date"].dt.strftime("%d %b %Y")
    display["Amount"] = display.apply(lambda row: ("-" if row["Debit/Credit"] == "Debit" else "+") + format_money(row["Amount"], currency), axis=1)
    if limit != "All":
        display = display.head(limit)
    st.caption(f"Showing {len(display):,} of {len(visible):,} matching transactions")
    st.dataframe(display, use_container_width=True, hide_index=True, column_config={
        "Date": st.column_config.TextColumn("Date", width="small"),
        "Details": st.column_config.TextColumn("Description", width="large"),
        "Amount": st.column_config.TextColumn("Amount", width="medium"),
    })


def render_insights(transactions, currency):
    st.markdown('<div class="eyebrow">Patterns</div>', unsafe_allow_html=True)
    st.subheader("Spending insights")
    debits = transactions[transactions["Debit/Credit"] == "Debit"]
    merchants = debits.groupby("Details", as_index=False).agg(Spent=("Amount", "sum"), Transactions=("Amount", "size"))
    merchants = merchants.sort_values("Spent", ascending=False).head(10)
    merchants["Spent"] = merchants["Spent"].map(lambda value: format_money(value, currency))
    merchants = merchants.rename(columns={"Details": "Merchant"})

    left, right = st.columns([1.25, 0.75])
    with left:
        st.subheader("Top merchants by spend")
        st.dataframe(merchants, use_container_width=True, hide_index=True)
    with right:
        st.subheader("Quick read")
        total = debits["Amount"].sum()
        top_category = debits.groupby("Category")["Amount"].sum().idxmax() if not debits.empty else "No data"
        top_category_amount = debits.groupby("Category")["Amount"].sum().max() if not debits.empty else 0
        st.metric("Largest category", top_category)
        st.metric("Largest category share", f"{top_category_amount / total:.1%}" if total else "0.0%")
        st.metric("Average expense", format_money(debits["Amount"].mean(), currency) if not debits.empty else format_money(0, currency))


def main():
    with st.sidebar:
        st.markdown("## Ledger")
        st.caption("Private, simple, and focused on your cash flow.")
        uploaded_file = st.file_uploader("Import statement", type=["csv", "xls", "xlsx"], help="CSV and Excel bank statements are supported.")

    st.markdown('<div class="eyebrow">Personal finance workspace</div>', unsafe_allow_html=True)
    st.title("Know where your money goes.")
    st.markdown('<div class="subtitle">A focused view of your cash flow, spending habits, and everyday transactions.</div>', unsafe_allow_html=True)

    if uploaded_file is None:
        render_empty_state()
        st.info("Use the Import statement control in the sidebar. Your data is processed locally in this app.")
        return

    transactions = load_transactions(uploaded_file)
    if transactions is None:
        return

    currency = str(transactions["Currency"].mode().iloc[0]) if "Currency" in transactions and not transactions["Currency"].dropna().empty else ""
    with st.sidebar:
        st.divider()
        st.markdown("### Refine view")
        min_date, max_date = transactions["Date"].min().date(), transactions["Date"].max().date()
        date_range = st.date_input("Date range", value=(min_date, max_date), min_value=min_date, max_value=max_date)
        statuses = sorted(transactions["Status"].unique())
        selected_statuses = st.multiselect("Status", statuses, default=statuses)
        st.divider()
        st.caption(f"{len(transactions):,} transactions · {min_date:%d %b %Y} to {max_date:%d %b %Y}")

    if len(date_range) != 2:
        st.warning("Choose both a start date and an end date to view your data.")
        return
    filtered = transactions[
        transactions["Date"].dt.date.between(date_range[0], date_range[1])
        & transactions["Status"].isin(selected_statuses)
    ].copy()
    if filtered.empty:
        st.warning("No transactions match these filters. Try widening the date range or status selection.")
        return

    st.markdown(f'<div class="status-line">Showing {len(filtered):,} transactions from {date_range[0]:%d %b %Y} to {date_range[1]:%d %b %Y}</div>', unsafe_allow_html=True)
    overview_tab, transactions_tab, insights_tab = st.tabs(["Overview", "Transactions", "Insights"])
    with overview_tab:
        render_overview(filtered, currency)
    with transactions_tab:
        render_transactions(filtered, currency)
    with insights_tab:
        render_insights(filtered, currency)


if __name__ == "__main__":
    main()

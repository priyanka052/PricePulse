"""
dashboard.py — Streamlit UI for PricePulse.
Shows price stats, history chart, LSTM forecast, and buy/wait recommendation.
"""

import sqlite3
import time
from datetime import datetime, timedelta

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from database import DB_PATH, get_all_prices, get_price_stats, init_db
from model import predict_next_7_days


def _recommendation(current: float, forecast: list) -> str:
    """
    Decide Buy Now vs Wait based on whether the forecast dips below current.
    Returns a human-readable recommendation string.
    """
    if not forecast or current is None:
        return "Not enough data for a recommendation."

    min_pred = min(forecast)
    if min_pred < current:
        # Days until the lowest predicted point (1-indexed from tomorrow)
        day_index = forecast.index(min_pred) + 1
        return f"Wait {day_index} day(s) — predicted low of Rs.{min_pred:,.0f}"
    return "Buy Now — price unlikely to drop further based on forecast."


def main():
    """Render the PricePulse Streamlit dashboard."""
    st.set_page_config(page_title="PricePulse", layout="wide")

    # Ensure the DB + table exist before we try to read from it in the sidebar.
    init_db()

    # ---- Sidebar ----
    with st.sidebar:
        st.title("PricePulse")
        st.write(
            "Autonomous e-commerce price monitoring & forecast. "
            "Track live prices, history, and LSTM predictions."
        )
        st.divider()
        
        # Product selector
        conn = sqlite3.connect(DB_PATH)
        try:
            products = [row[0] for row in conn.execute("SELECT DISTINCT product_name FROM prices").fetchall()]
        finally:
            conn.close()

        if products:
            selected_product = st.selectbox("Select Product", products)
        else:
            st.warning("No products found in prices.db")
            selected_product = None
        
        st.divider()
        st.caption(f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        if st.button("Refresh", use_container_width=True):
            st.rerun()

    st.title("PricePulse")
    st.caption("Autonomous e-commerce price monitoring & forecast")
    
    if not selected_product:
        st.warning("Please select a product from the sidebar.")
        return
    
    st.info(f"📦 Monitoring: **{selected_product}**")

    try:
        # Fetch all prices for the selected product (history chart).
        rows = get_all_prices(selected_product)
        df = pd.DataFrame(rows, columns=["time", "product_name", "price"])
        if not df.empty:
            df["time"] = pd.to_datetime(df["time"], format="mixed")

        # Fetch summary stats for the selected product (metric cards).
        stats = get_price_stats(selected_product)
        current = stats.get("current") if stats else None
        highest = stats.get("highest") if stats else None
        lowest = stats.get("lowest") if stats else None

        # ---- Stat cards ----
        col1, col2, col3 = st.columns(3)
        with col1:
            with st.container(border=True):
                current_display = f"Rs.{current:,}" if current is not None else "No data yet"
                st.metric(
                    "Current Price",
                    current_display,
                )
        with col2:
            with st.container(border=True):
                highest_display = f"Rs.{highest:,}" if highest is not None else "No data yet"
                st.metric(
                    "Highest Price",
                    highest_display,
                )
        with col3:
            with st.container(border=True):
                lowest_display = f"Rs.{lowest:,}" if lowest is not None else "No data yet"
                st.metric(
                    "Lowest Price",
                    lowest_display,
                )

        st.divider()

        # ---- Price alert threshold ----
        st.subheader("Price Alert")
        default_target = int(current) if current is not None else 50000
        target_price = st.number_input(
            "Set your target price (Rs.)",
            min_value=0,
            value=default_target,
            step=100,
        )
        if current is not None:
            if current < target_price:
                st.success("Good time to buy!")
            else:
                st.error("Price is high, wait")
        else:
            st.info("No current price available for alert comparison.")

        st.divider()

        # ---- Price history chart ----
        st.subheader("Price History")
        if not df.empty:
            fig = px.line(df, x="time", y="price", markers=True)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info(
                "No price history yet. Run the agent (`python main.py`) to collect data."
            )

        st.divider()

        # ---- Forecast section ----
        st.subheader("7-Day Price Forecast")
        price_list = df["price"].tolist() if not df.empty else []

        with st.spinner("Running LSTM forecast..."):
            forecast = predict_next_7_days(price_list)

        if forecast:
            start = datetime.now().date() + timedelta(days=1)
            forecast_dates = [start + timedelta(days=i) for i in range(len(forecast))]
            forecast_df = pd.DataFrame(
                {"date": forecast_dates, "predicted_price": forecast}
            )

            fig2 = go.Figure()
            fig2.add_trace(
                go.Scatter(
                    x=forecast_df["date"],
                    y=forecast_df["predicted_price"],
                    mode="lines+markers",
                    name="Forecast",
                    line=dict(color="#C45C26", width=2, dash="dash"),
                    marker=dict(size=8),
                )
            )
            fig2.update_layout(
                xaxis_title="Date",
                yaxis_title="Predicted Price (Rs.)",
                hovermode="x unified",
                margin=dict(l=20, r=20, t=30, b=20),
                height=350,
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)",
            )
            st.plotly_chart(fig2, use_container_width=True)

            st.dataframe(
                forecast_df.style.format({"predicted_price": "Rs.{:,.2f}"}),
                use_container_width=True,
                hide_index=True,
            )

            # ---- Recommendation ----
            st.subheader("Recommendation")
            advice = _recommendation(current, forecast)
            if advice.startswith("Buy Now"):
                st.success(advice)
            elif advice.startswith("Wait"):
                st.warning(advice)
            else:
                st.info(advice)
        else:
            st.warning(
                "Forecast unavailable. Check model logs or collect more price data."
            )

    except Exception as exc:
        st.error(f"Dashboard error: {exc}")

    # ---- Auto-refresh every 60 seconds ----
    time.sleep(60)
    st.rerun()


# Streamlit executes the script top-to-bottom on every run
main()

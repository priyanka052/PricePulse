"""
dashboard.py — Streamlit UI for PricePulse.
Shows price stats, history chart, LSTM forecast, and buy/wait recommendation.
"""

import time
from datetime import datetime, timedelta

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from database import get_all_prices, get_price_stats, init_db
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
    st.set_page_config(page_title="PricePulse", page_icon="📉", layout="wide")
    st.title("PricePulse")
    st.caption("Autonomous e-commerce price monitoring & forecast")

    try:
        init_db()
        stats = get_price_stats()
        rows = get_all_prices()

        # ---- Stat cards ----
        col1, col2, col3 = st.columns(3)
        with col1:
            current = stats.get("current")
            st.metric(
                "Current Price",
                f"Rs.{current:,}" if current is not None else "—",
            )
        with col2:
            highest = stats.get("highest")
            st.metric(
                "Highest Price",
                f"Rs.{highest:,}" if highest is not None else "—",
            )
        with col3:
            lowest = stats.get("lowest")
            st.metric(
                "Lowest Price",
                f"Rs.{lowest:,}" if lowest is not None else "—",
            )

        st.divider()

        # ---- Price history chart ----
        st.subheader("Price History")
        if rows:
            df = pd.DataFrame(rows, columns=["time", "price"])
            df["time"] = pd.to_datetime(df["time"])

            fig = go.Figure()
            fig.add_trace(
                go.Scatter(
                    x=df["time"],
                    y=df["price"],
                    mode="lines+markers",
                    name="Observed",
                    line=dict(color="#0B6E4F", width=2),
                    marker=dict(size=6),
                )
            )
            fig.update_layout(
                xaxis_title="Time",
                yaxis_title="Price (Rs.)",
                hovermode="x unified",
                margin=dict(l=20, r=20, t=30, b=20),
                height=400,
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No price history yet. Run the agent (`python main.py`) to collect data.")

        st.divider()

        # ---- Forecast section ----
        st.subheader("7-Day Price Forecast")
        price_list = [r[1] for r in rows] if rows else []

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
            )
            st.plotly_chart(fig2, use_container_width=True)

            st.dataframe(
                forecast_df.style.format({"predicted_price": "Rs.{:,.2f}"}),
                use_container_width=True,
                hide_index=True,
            )

            # ---- Recommendation ----
            st.subheader("Recommendation")
            advice = _recommendation(stats.get("current"), forecast)
            if advice.startswith("Buy Now"):
                st.success(advice)
            elif advice.startswith("Wait"):
                st.warning(advice)
            else:
                st.info(advice)
        else:
            st.warning("Forecast unavailable. Check model logs or collect more price data.")

    except Exception as exc:
        st.error(f"Dashboard error: {exc}")

    # ---- Auto-refresh every 60 seconds ----
    time.sleep(60)
    st.rerun()


# Streamlit executes the script top-to-bottom on every run
main()

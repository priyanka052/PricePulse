"""
dashboard.py — Streamlit UI for PricePulse.
Shows price stats, history chart, LSTM forecast, and buy/wait recommendation.
"""

import time
from datetime import datetime, timedelta

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from database import get_all_prices, init_db
from model import predict_next_7_days

# Phone product — ignore junk/test scrapes below this floor
MIN_VALID_PRICE = 5000


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


def _compute_stats(df: pd.DataFrame) -> dict:
    """Compute current / highest / lowest / previous from filtered price rows."""
    if df.empty:
        return {"highest": None, "lowest": None, "current": None, "previous": None}

    prices = df["price"].tolist()
    return {
        "highest": int(max(prices)),
        "lowest": int(min(prices)),
        "current": int(prices[-1]),
        "previous": int(prices[-2]) if len(prices) >= 2 else None,
    }


def main():
    """Render the PricePulse Streamlit dashboard."""
    st.set_page_config(page_title="PricePulse", layout="wide")

    # ---- Sidebar ----
    with st.sidebar:
        st.title("PricePulse")
        st.write(
            "Autonomous e-commerce price monitoring & forecast. "
            "Track live prices, history, and LSTM predictions."
        )
        st.divider()
        st.caption(f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        if st.button("Refresh", use_container_width=True):
            st.rerun()

    st.title("PricePulse")
    st.caption("Autonomous e-commerce price monitoring & forecast")

    try:
        init_db()
        rows = get_all_prices()

        if rows:
            df = pd.DataFrame(rows, columns=["time", "price"])
            df["time"] = pd.to_datetime(df["time"], format="mixed")
            # Drop junk test prices (e.g. Rs.960) — real phone prices are >= Rs.5000
            df = df[df["price"] >= MIN_VALID_PRICE].reset_index(drop=True)
        else:
            df = pd.DataFrame(columns=["time", "price"])

        stats = _compute_stats(df)
        current = stats.get("current")
        previous = stats.get("previous")
        highest = stats.get("highest")
        lowest = stats.get("lowest")

        delta_value = None
        if current is not None and previous is not None:
            delta_value = current - previous

        # ---- Stat cards ----
        col1, col2, col3 = st.columns(3)
        with col1:
            with st.container(border=True):
                st.metric(
                    "Current Price",
                    f"Rs.{current:,}" if current is not None else "—",
                    delta=f"Rs.{delta_value:,}" if delta_value is not None else None,
                    delta_color="inverse",  # drop = green, rise = red
                )
        with col2:
            with st.container(border=True):
                st.metric(
                    "Highest Price",
                    f"Rs.{highest:,}" if highest is not None else "—",
                )
        with col3:
            with st.container(border=True):
                st.metric(
                    "Lowest Price",
                    f"Rs.{lowest:,}" if lowest is not None else "—",
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
            fig = go.Figure()
            fig.add_trace(
                go.Scatter(
                    x=df["time"],
                    y=df["price"],
                    mode="lines+markers",
                    name="Observed",
                    line=dict(color="#1a1a1a", width=2),
                    marker=dict(size=7, color="#1a1a1a"),
                    fill="tozeroy",
                    fillcolor="rgba(26, 26, 26, 0.12)",
                    hovertemplate=(
                        "Price: Rs.%{y:,.0f}<br>"
                        "Time: %{x|%Y-%m-%d %H:%M:%S}"
                        "<extra></extra>"
                    ),
                )
            )
            fig.update_layout(
                hovermode="closest",
                margin=dict(l=20, r=20, t=30, b=20),
                height=400,
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)",
                xaxis=dict(
                    title="Timestamp",
                    showgrid=True,
                    gridcolor="#e0e0e0",
                    zeroline=False,
                ),
                yaxis=dict(
                    title="Price (Rs.)",
                    showgrid=True,
                    gridcolor="#e0e0e0",
                    zeroline=False,
                ),
            )
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

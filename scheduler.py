"""
scheduler.py — Runs the PricePulse agent every hour via APScheduler.
Fires immediately on startup, then repeats.
"""

from apscheduler.schedulers.blocking import BlockingScheduler

from main import run_agent


def start_scheduler():
    """
    Start a BlockingScheduler that invokes run_agent() every hour.
    Also runs once immediately at startup. Handles Ctrl+C cleanly.
    """
    scheduler = BlockingScheduler()

    # Schedule hourly runs
    scheduler.add_job(run_agent, "interval", hours=1, id="pricepulse_hourly")

    print("[scheduler] PricePulse scheduler starting...")
    print("[scheduler] Running first check immediately, then every 1 hour.")
    print("[scheduler] Press Ctrl+C to stop.\n")

    try:
        # Fire immediately on startup
        run_agent()
        # Then block and run on the interval
        scheduler.start()
    except KeyboardInterrupt:
        print("\n[scheduler] KeyboardInterrupt received — shutting down gracefully.")
        scheduler.shutdown(wait=False)
        print("[scheduler] Stopped.")
    except Exception as exc:
        print(f"[scheduler] Unexpected error: {exc}")
        try:
            scheduler.shutdown(wait=False)
        except Exception:
            pass


if __name__ == "__main__":
    start_scheduler()

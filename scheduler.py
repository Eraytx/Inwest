from apscheduler.schedulers.background import BackgroundScheduler
import report_generator
import engine
import time

def scheduled_job():
    """Runs the full portfolio price update and generates the daily AI report."""
    print("Scheduled Event: Starting portfolio update and report generation...")
    try:
        report = report_generator.generate_ai_report("daily")
        print(f"Scheduled Event: Successfully completed. Report saved to database.")
    except Exception as e:
        print(f"Scheduled Event Error: Failed to run update: {e}")

def start_scheduler():
    """Starts the background scheduler scheduler."""
    scheduler = BackgroundScheduler()
    
    # Job 1: Run daily at 18:00 (BIST Market Close)
    scheduler.add_job(scheduled_job, 'cron', hour=18, minute=0)
    
    # Job 2: Run hourly to calculate portfolio stats and save values for the chart
    scheduler.add_job(engine.calculate_portfolio, 'interval', hours=1)
    
    scheduler.start()
    print("Background scheduler started successfully.")
    print("  -> Daily reports scheduled for 18:00")
    print("  -> Portfolio history logging scheduled for every hour")
    return scheduler

if __name__ == "__main__":
    # If run standalone, run scheduler in block-mode for demo purposes
    print("Starting standalone scheduler service (Ctrl+C to exit)...")
    scheduler = start_scheduler()
    try:
        # Keep main thread alive
        while True:
            time.sleep(1)
    except (KeyboardInterrupt, SystemExit):
        scheduler.shutdown()
        print("Scheduler stopped.")

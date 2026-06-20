from apscheduler.schedulers.background import BackgroundScheduler
import engine
import database
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def update_all_portfolios():
    """
    Background job that iterates through all users and updates their portfolio snapshots.
    """
    logger.info("Starting background portfolio update for all users...")
    try:
        # We need a way to get all user IDs.
        # Adding a simple helper to database.py or doing it here via raw connection.
        conn = database.get_connection()
        cursor = database.get_cursor(conn)

        ph = "%s" if database.DATABASE_URL else "?"
        cursor.execute("SELECT id FROM users")
        users = cursor.fetchall()
        conn.close()

        for user in users:
            user_id = user['id']
            try:
                logger.info(f"Updating portfolio for user {user_id}")
                engine.calculate_portfolio(user_id)
            except Exception as e:
                logger.error(f"Failed to update portfolio for user {user_id}: {e}")

        logger.info("Background portfolio update completed.")
    except Exception as e:
        logger.error(f"Critical error in scheduler: {e}")

def start_scheduler():
    scheduler = BackgroundScheduler()
    # Updated to call our new wrapper function instead of engine.calculate_portfolio directly
    scheduler.add_job(update_all_portfolios, 'interval', hours=1)
    scheduler.start()
    return scheduler

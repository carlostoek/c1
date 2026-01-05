#!/usr/bin/env python3
"""
Migration script to add the database tables for ONDA D (Lifecycle Management).

This script ensures the following tables are created:
- user_lifecycle
- notification_preferences
- reengagement_log
"""
import asyncio
import logging
import sys
import os
from sqlalchemy import text

# Add project root to the Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def migrate_onda_d():
    """Executes the migration to add ONDA D tables."""
    logger.info("🚀 Starting migration: Add ONDA D Lifecycle Tables")
    
    try:
        from bot.database.engine import init_db, get_engine, close_db

        # This will create all tables defined in the models, including the new ones.
        await init_db()

        engine = get_engine()
        
        tables_to_check = [
            "user_lifecycle",
            "notification_preferences",
            "reengagement_log"
        ]
        
        async with engine.begin() as conn:
            for table_name in tables_to_check:
                result = await conn.execute(
                    text(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table_name}'")
                )
                if result.scalar() is not None:
                    logger.info(f"✅ Table '{table_name}' found.")
                else:
                    logger.error(f"❌ Migration failed: Table '{table_name}' was not created.")
                    return False
        
        await close_db()
        logger.info("✅ ONDA D migration completed successfully.")
        return True

    except Exception as e:
        logger.error(f"❌ An error occurred during migration: {e}", exc_info=True)
        return False

async def main():
    """Script entry point."""
    success = await migrate_onda_d()
    if not success:
        exit(1)

if __name__ == "__main__":
    asyncio.run(main())

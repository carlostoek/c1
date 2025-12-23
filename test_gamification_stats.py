"""
Test script to verify the gamification stats fix.
"""

import asyncio
import logging
from datetime import datetime, timedelta, UTC

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

from bot.database import init_db, close_db, get_session
from bot.gamification.services.stats import StatsService
from bot.gamification.database.models import UserGamification, UserReaction, Reaction


async def test_gamification_stats():
    """Test the gamification stats service."""
    print("\n" + "="*70)
    print("🧪 TEST: Gamification Stats Service")
    print("="*70)

    try:
        await init_db()

        # Setup test data
        print("\n📝 Creating test data...")

        async with get_session() as session:
            # Create a test user
            user = UserGamification(user_id=99999)
            session.add(user)
            await session.flush()

            # Create test reactions
            reaction1 = Reaction(emoji="👍", besitos_value=1)
            reaction2 = Reaction(emoji="❤️", besitos_value=2)
            reaction3 = Reaction(emoji="😂", besitos_value=3)
            session.add_all([reaction1, reaction2, reaction3])
            await session.flush()

            # Create user reactions
            now = datetime.now(UTC)
            user_reaction1 = UserReaction(
                user_id=user.user_id,
                reaction_id=reaction1.id,
                channel_id=123456,
                message_id=1001,
                reacted_at=now - timedelta(hours=1)
            )
            user_reaction2 = UserReaction(
                user_id=user.user_id,
                reaction_id=reaction2.id,
                channel_id=123456,
                message_id=1002,
                reacted_at=now - timedelta(hours=2)
            )
            user_reaction3 = UserReaction(
                user_id=user.user_id,
                reaction_id=reaction1.id,
                channel_id=123456,
                message_id=1003,
                reacted_at=now - timedelta(days=1)
            )
            session.add_all([user_reaction1, user_reaction2, user_reaction3])
            await session.commit()

        print("✅ Test data created")

        # Test the stats service
        print("\n" + "-"*70)
        print("🧪 Testing StatsService.get_engagement_stats()")
        print("-"*70)

        async with get_session() as session:
            service = StatsService(session)
            engagement_stats = await service.get_engagement_stats()

            assert isinstance(engagement_stats, dict), "Engagement stats should be a dict"
            assert "total_reactions" in engagement_stats, "Missing total_reactions"
            assert "reactions_7d" in engagement_stats, "Missing reactions_7d"
            assert "avg_reactions_per_user" in engagement_stats, "Missing avg_reactions_per_user"
            assert "top_emojis" in engagement_stats, "Missing top_emojis"
            assert "active_streaks" in engagement_stats, "Missing active_streaks"
            assert "longest_streak" in engagement_stats, "Missing longest_streak"

            # Check that top_emojis is properly populated
            top_emojis = engagement_stats["top_emojis"]
            assert isinstance(top_emojis, dict), "top_emojis should be a dict"
            
            # Should have at least the emojis we created
            assert "👍" in top_emojis, "Missing thumbs up emoji"
            assert top_emojis["👍"] >= 2, f"Expected at least 2 thumbs up reactions, got {top_emojis['👍']}"
            
            if "❤️" in top_emojis:
                assert top_emojis["❤️"] >= 1, f"Expected at least 1 heart reaction, got {top_emojis['❤️']}"

            print(f"✅ Engagement stats valid:")
            print(f"   - Total reactions: {engagement_stats['total_reactions']}")
            print(f"   - Reactions 7d: {engagement_stats['reactions_7d']}")
            print(f"   - Avg reactions per user: {engagement_stats['avg_reactions_per_user']}")
            print(f"   - Top emojis: {top_emojis}")
            print(f"   - Active streaks: {engagement_stats['active_streaks']}")
            print(f"   - Longest streak: {engagement_stats['longest_streak']}")

        # Clean up test data
        print("\n🧹 Cleaning up test data...")
        async with get_session() as session:
            from sqlalchemy import delete
            await session.execute(delete(UserReaction).where(UserReaction.user_id == 99999))
            await session.execute(delete(Reaction).where(Reaction.emoji.in_(["👍", "❤️", "😂"])))
            await session.execute(delete(UserGamification).where(UserGamification.user_id == 99999))
            await session.commit()
        print("✅ Test data cleaned up")

        print("\n" + "="*70)
        print("✅✅✅ ALL TESTS PASSED")
        print("="*70)

        return True

    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        await close_db()


if __name__ == "__main__":
    success = asyncio.run(test_gamification_stats())
    exit(0 if success else 1)
"""Main entry point for Portfolio Tracker"""

import asyncio
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from portfolio_tracker import PortfolioTracker


async def main():
    """Main function for running the tracker"""
    tracker = PortfolioTracker()
    await tracker.track_all_items()


if __name__ == "__main__":
    asyncio.run(main())
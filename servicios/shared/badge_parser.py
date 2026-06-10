"""Pure-function badge/role parser for all supported platforms.

No wxPython, no data_store, no UI imports. Safe to import without a running wx.App.
"""
from __future__ import annotations

from typing import Any


class BadgeParser:
    """Unified badge-to-role parser across all platforms.

    Priority order: owner > moderator > subscriber > verified > general.
    """

    @staticmethod
    def parse_role(author: Any, platform: str) -> str:
        """Determine the user's role from platform-specific badge data.

        Args:
            author: Platform-specific author/badge data (dict, SimpleNamespace, etc.).
            platform: Platform identifier string.

        Returns:
            One of: "owner", "moderator", "subscriber", "verified", "general".
        """
        match platform:
            case "youtube":
                return BadgeParser._parse_youtube(author)
            case "twitch":
                return BadgeParser._parse_twitch(author)
            case "kick":
                return BadgeParser._parse_kick(author)
            case "youtube_realtime":
                return BadgeParser._parse_youtube_rt(author)
            case "tiktok" | "sala":
                return "general"
            case _:
                return "general"

    @staticmethod
    def _parse_youtube(author: dict) -> str:
        """YouTube: author['badges'] is a list of dicts with 'title' key."""
        badges = author.get("badges", [])
        titles = {b.get("title", "") for b in badges}

        if "Owner" in titles:
            return "owner"
        if "Moderator" in titles:
            return "moderator"
        if "Member" in titles:
            return "subscriber"
        if "Verified" in titles:
            return "verified"
        return "general"

    @staticmethod
    def _parse_twitch(author: dict) -> str:
        """Twitch: author dict with 'badges' list + boolean flags."""
        if author.get("is_moderator", False):
            return "moderator"

        badges = author.get("badges", [])
        for badge in badges:
            badge_type = badge.get("type", "") if isinstance(badge, dict) else ""
            if badge_type == "subscriber":
                return "subscriber"

        return "general"

    @staticmethod
    def _parse_kick(author: Any) -> str:
        """Kick: author.badges is a list of dicts or objects with .type."""
        badges = getattr(author, "badges", [])
        for badge in badges:
            badge_type = ""
            if isinstance(badge, dict):
                badge_type = badge.get("type", "")
            else:
                badge_type = getattr(badge, "type", "")

            if badge_type == "moderator":
                return "moderator"
            if badge_type == "subscriber":
                return "subscriber"

        return "general"

    @staticmethod
    def _parse_youtube_rt(author: Any) -> str:
        """YouTube Realtime: author has boolean attributes."""
        if getattr(author, "isChatOwner", False):
            return "owner"
        if getattr(author, "isChatModerator", False):
            return "moderator"
        if getattr(author, "isChatSponsor", False):
            return "subscriber"
        if getattr(author, "isVerified", False):
            return "verified"
        return "general"

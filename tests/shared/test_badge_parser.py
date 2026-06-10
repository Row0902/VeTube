"""Tests for servicios.shared.badge_parser — BadgeParser.parse_role()"""
from __future__ import annotations

from types import SimpleNamespace

import pytest

from servicios.shared.badge_parser import BadgeParser


# --- YouTube ---

class TestBadgeParserYouTube:
    """YouTube: author['badges'] list of dicts with 'title' key."""

    def test_owner(self):
        author = {"badges": [{"title": "Owner"}]}
        assert BadgeParser.parse_role(author, "youtube") == "owner"

    def test_moderator(self):
        author = {"badges": [{"title": "Moderator"}]}
        assert BadgeParser.parse_role(author, "youtube") == "moderator"

    def test_verified(self):
        author = {"badges": [{"title": "Verified"}]}
        assert BadgeParser.parse_role(author, "youtube") == "verified"

    def test_member(self):
        author = {"badges": [{"title": "Member"}]}
        assert BadgeParser.parse_role(author, "youtube") == "subscriber"

    def test_no_badges(self):
        author = {"badges": []}
        assert BadgeParser.parse_role(author, "youtube") == "general"

    def test_owner_priority_over_moderator(self):
        author = {"badges": [{"title": "Moderator"}, {"title": "Owner"}]}
        assert BadgeParser.parse_role(author, "youtube") == "owner"


# --- Twitch ---

class TestBadgeParserTwitch:
    """Twitch: author dict with 'badges' list + boolean flags."""

    def test_subscriber(self):
        author = {"badges": [{"type": "subscriber"}], "is_moderator": False}
        assert BadgeParser.parse_role(author, "twitch") == "subscriber"

    def test_moderator(self):
        author = {"badges": [], "is_moderator": True}
        assert BadgeParser.parse_role(author, "twitch") == "moderator"

    def test_general(self):
        author = {"badges": [], "is_moderator": False}
        assert BadgeParser.parse_role(author, "twitch") == "general"


# --- Kick ---

class TestBadgeParserKick:
    """Kick: author.badges as list of dicts or objects with .type."""

    def test_subscriber_dict(self):
        author = SimpleNamespace(badges=[{"type": "subscriber"}])
        assert BadgeParser.parse_role(author, "kick") == "subscriber"

    def test_moderator_dict(self):
        author = SimpleNamespace(badges=[{"type": "moderator"}])
        assert BadgeParser.parse_role(author, "kick") == "moderator"

    def test_general(self):
        author = SimpleNamespace(badges=[])
        assert BadgeParser.parse_role(author, "kick") == "general"


# --- YouTube Realtime ---

class TestBadgeParserYouTubeRT:
    """YouTubeRT: author with boolean attributes."""

    def test_owner(self):
        author = SimpleNamespace(
            isChatOwner=True, isChatModerator=False,
            isChatSponsor=False, isVerified=False
        )
        assert BadgeParser.parse_role(author, "youtube_realtime") == "owner"

    def test_moderator(self):
        author = SimpleNamespace(
            isChatOwner=False, isChatModerator=True,
            isChatSponsor=False, isVerified=False
        )
        assert BadgeParser.parse_role(author, "youtube_realtime") == "moderator"

    def test_subscriber(self):
        author = SimpleNamespace(
            isChatOwner=False, isChatModerator=False,
            isChatSponsor=True, isVerified=False
        )
        assert BadgeParser.parse_role(author, "youtube_realtime") == "subscriber"

    def test_verified(self):
        author = SimpleNamespace(
            isChatOwner=False, isChatModerator=False,
            isChatSponsor=False, isVerified=True
        )
        assert BadgeParser.parse_role(author, "youtube_realtime") == "verified"

    def test_general(self):
        author = SimpleNamespace(
            isChatOwner=False, isChatModerator=False,
            isChatSponsor=False, isVerified=False
        )
        assert BadgeParser.parse_role(author, "youtube_realtime") == "general"


# --- TikTok and Sala (always general) ---

class TestBadgeParserSimple:
    """TikTok and Sala always return 'general'."""

    def test_tiktok_always_general(self):
        assert BadgeParser.parse_role({}, "tiktok") == "general"

    def test_sala_always_general(self):
        assert BadgeParser.parse_role({}, "sala") == "general"


# --- Unknown platform ---

class TestBadgeParserUnknown:
    """Unknown platform returns 'general'."""

    def test_unknown_platform(self):
        assert BadgeParser.parse_role({}, "unknown_platform") == "general"

    def test_empty_platform(self):
        assert BadgeParser.parse_role({}, "") == "general"

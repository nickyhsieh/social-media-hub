"""Instagram Graph API integration (Business/Creator accounts)."""
import httpx

GRAPH_BASE = "https://graph.facebook.com/v19.0"


def get_account_stats(ig_user_id: str, access_token: str) -> dict:
    with httpx.Client(timeout=10) as client:
        info = client.get(
            f"{GRAPH_BASE}/{ig_user_id}",
            params={"fields": "id,username,name,biography,followers_count,follows_count,media_count,profile_picture_url", "access_token": access_token},
        ).raise_for_status().json()

        insights_data = client.get(
            f"{GRAPH_BASE}/{ig_user_id}/insights",
            params={"metric": "reach,impressions,profile_views", "period": "day", "access_token": access_token},
        ).raise_for_status().json().get("data", [])

    insights = {}
    for item in insights_data:
        values = item.get("values", [])
        insights[item["name"]] = values[-1].get("value", 0) if values else 0

    return {
        "platform": "instagram",
        "user_id": info.get("id"),
        "username": info.get("username"),
        "name": info.get("name"),
        "biography": info.get("biography"),
        "followers": info.get("followers_count", 0),
        "following": info.get("follows_count", 0),
        "media_count": info.get("media_count", 0),
        "profile_picture": info.get("profile_picture_url"),
        "reach": insights.get("reach", 0),
        "impressions": insights.get("impressions", 0),
        "profile_views": insights.get("profile_views", 0),
    }


def get_recent_media(ig_user_id: str, access_token: str, limit: int = 10) -> list:
    with httpx.Client(timeout=10) as client:
        items = client.get(
            f"{GRAPH_BASE}/{ig_user_id}/media",
            params={"fields": "id,caption,media_type,media_url,thumbnail_url,permalink,timestamp,like_count,comments_count", "limit": limit, "access_token": access_token},
        ).raise_for_status().json().get("data", [])

    return [{
        "platform": "instagram",
        "id": m.get("id"),
        "text": m.get("caption", ""),
        "media_type": m.get("media_type"),
        "media_url": m.get("media_url") or m.get("thumbnail_url"),
        "permalink": m.get("permalink"),
        "created_at": m.get("timestamp"),
        "likes": m.get("like_count", 0),
        "comments": m.get("comments_count", 0),
    } for m in items]

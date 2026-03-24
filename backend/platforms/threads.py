"""Threads API integration."""
import httpx

THREADS_BASE = "https://graph.threads.net/v1.0"


def get_profile_stats(user_id: str, access_token: str) -> dict:
    with httpx.Client(timeout=10) as client:
        profile = client.get(
            f"{THREADS_BASE}/{user_id}",
            params={"fields": "id,username,name,threads_profile_picture_url,threads_biography", "access_token": access_token},
        ).raise_for_status().json()

        insights_data = client.get(
            f"{THREADS_BASE}/{user_id}/threads_insights",
            params={"metric": "views,likes,replies,reposts,quotes,followers_count", "period": "day", "access_token": access_token},
        ).raise_for_status().json().get("data", [])

    insights = {}
    for item in insights_data:
        values = item.get("values", [])
        insights[item["name"]] = sum(v.get("value", 0) for v in values)

    return {
        "platform": "threads",
        "user_id": profile.get("id"),
        "username": profile.get("username"),
        "name": profile.get("name"),
        "biography": profile.get("threads_biography"),
        "profile_picture": profile.get("threads_profile_picture_url"),
        "followers": insights.get("followers_count", 0),
        "views": insights.get("views", 0),
        "likes": insights.get("likes", 0),
        "replies": insights.get("replies", 0),
        "reposts": insights.get("reposts", 0),
    }


def get_recent_threads(user_id: str, access_token: str, limit: int = 10) -> list:
    with httpx.Client(timeout=10) as client:
        items = client.get(
            f"{THREADS_BASE}/{user_id}/threads",
            params={"fields": "id,text,media_type,media_url,permalink,timestamp,likes,replies,reposts", "limit": limit, "access_token": access_token},
        ).raise_for_status().json().get("data", [])

    return [{
        "platform": "threads",
        "id": t.get("id"),
        "text": t.get("text", ""),
        "media_url": t.get("media_url"),
        "permalink": t.get("permalink"),
        "created_at": t.get("timestamp"),
        "likes": t.get("likes", 0),
        "comments": t.get("replies", 0),
        "reposts": t.get("reposts", 0),
    } for t in items]

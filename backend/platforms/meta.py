"""Meta (Facebook) Graph API integration."""
import httpx

GRAPH_BASE = "https://graph.facebook.com/v19.0"


def get_page_stats(page_id: str, access_token: str) -> dict:
    with httpx.Client(timeout=10) as client:
        info = client.get(
            f"{GRAPH_BASE}/{page_id}",
            params={"fields": "id,name,fan_count,followers_count,picture", "access_token": access_token},
        ).raise_for_status().json()

        insights_data = client.get(
            f"{GRAPH_BASE}/{page_id}/insights",
            params={"metric": "page_impressions,page_engaged_users,page_post_engagements", "period": "day", "access_token": access_token},
        ).raise_for_status().json().get("data", [])

    insights = {}
    for item in insights_data:
        values = item.get("values", [])
        insights[item["name"]] = values[-1].get("value", 0) if values else 0

    return {
        "platform": "meta",
        "page_id": info.get("id"),
        "name": info.get("name"),
        "followers": info.get("followers_count", 0),
        "fans": info.get("fan_count", 0),
        "picture": info.get("picture", {}).get("data", {}).get("url"),
        "impressions": insights.get("page_impressions", 0),
        "engaged_users": insights.get("page_engaged_users", 0),
        "post_engagements": insights.get("page_post_engagements", 0),
    }


def get_recent_posts(page_id: str, access_token: str, limit: int = 10) -> list:
    with httpx.Client(timeout=10) as client:
        posts = client.get(
            f"{GRAPH_BASE}/{page_id}/posts",
            params={"fields": "id,message,story,created_time,likes.summary(true),comments.summary(true),shares", "limit": limit, "access_token": access_token},
        ).raise_for_status().json().get("data", [])

    return [{
        "platform": "meta",
        "id": p.get("id"),
        "text": p.get("message") or p.get("story", ""),
        "created_at": p.get("created_time"),
        "likes": p.get("likes", {}).get("summary", {}).get("total_count", 0),
        "comments": p.get("comments", {}).get("summary", {}).get("total_count", 0),
        "shares": p.get("shares", {}).get("count", 0),
    } for p in posts]

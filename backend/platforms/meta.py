"""Meta (Facebook) Graph API integration."""
import httpx

GRAPH_BASE = "https://graph.facebook.com/v19.0"


def _get_page_token(page_id: str, user_token: str, client: httpx.Client) -> str:
    """Exchange a user token for a page access token."""
    try:
        accounts = client.get(
            f"{GRAPH_BASE}/me/accounts",
            params={"access_token": user_token},
        ).raise_for_status().json().get("data", [])
        for page in accounts:
            if page.get("id") == page_id:
                return page.get("access_token", user_token)
    except Exception:
        pass
    return user_token


def get_page_stats(page_id: str, access_token: str) -> dict:
    with httpx.Client(timeout=10) as client:
        page_token = _get_page_token(page_id, access_token, client)

        info = client.get(
            f"{GRAPH_BASE}/{page_id}",
            params={"fields": "id,name,fan_count,followers_count,picture", "access_token": page_token},
        ).raise_for_status().json()

        insights = {}
        try:
            insights_data = client.get(
                f"{GRAPH_BASE}/{page_id}/insights",
                params={"metric": "page_impressions,page_engaged_users,page_post_engagements", "period": "day", "access_token": page_token},
            ).raise_for_status().json().get("data", [])
            for item in insights_data:
                values = item.get("values", [])
                insights[item["name"]] = values[-1].get("value", 0) if values else 0
        except Exception:
            pass

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
        page_token = _get_page_token(page_id, access_token, client)
        posts = client.get(
            f"{GRAPH_BASE}/{page_id}/posts",
            params={"fields": "id,message,story,created_time,likes.summary(true),comments.summary(true),shares", "limit": limit, "access_token": page_token},
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

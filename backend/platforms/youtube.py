"""YouTube Data API v3 integration."""
import httpx

YT_BASE = "https://www.googleapis.com/youtube/v3"


def get_channel_stats(channel_id: str, api_key: str) -> dict:
    with httpx.Client(timeout=10) as client:
        items = client.get(
            f"{YT_BASE}/channels",
            params={"part": "snippet,statistics,brandingSettings", "id": channel_id, "key": api_key},
        ).raise_for_status().json().get("items", [])

    if not items:
        return {"platform": "youtube", "error": "Channel not found"}

    ch      = items[0]
    snippet = ch.get("snippet", {})
    stats   = ch.get("statistics", {})

    return {
        "platform":    "youtube",
        "channel_id":  ch.get("id"),
        "name":        snippet.get("title"),
        "description": snippet.get("description"),
        "profile_picture": snippet.get("thumbnails", {}).get("default", {}).get("url"),
        "subscribers": int(stats.get("subscriberCount", 0)),
        "total_views": int(stats.get("viewCount", 0)),
        "video_count": int(stats.get("videoCount", 0)),
    }


def get_recent_videos(channel_id: str, api_key: str, limit: int = 10) -> list:
    with httpx.Client(timeout=10) as client:
        search_items = client.get(
            f"{YT_BASE}/search",
            params={"part": "snippet", "channelId": channel_id, "order": "date", "type": "video", "maxResults": limit, "key": api_key},
        ).raise_for_status().json().get("items", [])

        if not search_items:
            return []

        video_ids = [i["id"]["videoId"] for i in search_items]
        video_items = client.get(
            f"{YT_BASE}/videos",
            params={"part": "snippet,statistics", "id": ",".join(video_ids), "key": api_key},
        ).raise_for_status().json().get("items", [])

    results = []
    for v in video_items:
        snippet = v.get("snippet", {})
        stats   = v.get("statistics", {})
        vid_id  = v.get("id")
        results.append({
            "platform":   "youtube",
            "id":         vid_id,
            "text":       snippet.get("title", ""),
            "media_url":  snippet.get("thumbnails", {}).get("medium", {}).get("url"),
            "permalink":  f"https://www.youtube.com/watch?v={vid_id}",
            "created_at": snippet.get("publishedAt"),
            "views":      int(stats.get("viewCount", 0)),
            "likes":      int(stats.get("likeCount", 0)),
            "comments":   int(stats.get("commentCount", 0)),
        })
    return results

"""
Social Media Hub — Flask Backend
Aggregates Meta, Instagram, Threads, and YouTube into one API.
"""
import os
from concurrent.futures import ThreadPoolExecutor, as_completed

from flask import Flask, jsonify, request, send_from_directory
from dotenv import load_dotenv

from platforms import meta, instagram, threads, youtube

load_dotenv()

app = Flask(__name__, static_folder=None)

# ── CORS (allow frontend dev server) ─────────────────────────
@app.after_request
def add_cors(response):
    response.headers["Access-Control-Allow-Origin"]  = "*"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type"
    response.headers["Access-Control-Allow-Methods"] = "GET,POST,OPTIONS"
    return response

@app.route("/api/<path:p>", methods=["OPTIONS"])
def options_handler(p):
    return "", 204

# ── In-memory config ──────────────────────────────────────────
_config: dict = {
    "meta_page_id":       os.getenv("META_PAGE_ID", ""),
    "meta_access_token":  os.getenv("META_ACCESS_TOKEN", ""),
    "ig_user_id":         os.getenv("IG_USER_ID", ""),
    "threads_user_id":    os.getenv("THREADS_USER_ID", ""),
    "youtube_channel_id": os.getenv("YOUTUBE_CHANNEL_ID", ""),
    "youtube_api_key":    os.getenv("YOUTUBE_API_KEY", ""),
}


def cfg(key):
    val = _config.get(key, "")
    if not val:
        raise ValueError(f"Missing config: {key}. Set it in .env or POST /api/config")
    return val


# ── Config endpoints ──────────────────────────────────────────
@app.get("/api/config")
def get_config():
    safe = {k: ("***" if ("token" in k or "key" in k) and v else v) for k, v in _config.items()}
    return jsonify(safe)


@app.post("/api/config")
def update_config():
    data = request.get_json(silent=True) or {}
    for k, v in data.items():
        if k in _config and v:
            _config[k] = v
    return jsonify({"status": "ok"})


# ── Dashboard ─────────────────────────────────────────────────
@app.get("/api/dashboard")
def dashboard():
    tasks = {}
    if _config.get("meta_page_id") and _config.get("meta_access_token"):
        tasks["meta"] = (meta.get_page_stats, [_config["meta_page_id"], _config["meta_access_token"]])
    if _config.get("ig_user_id") and _config.get("meta_access_token"):
        tasks["instagram"] = (instagram.get_account_stats, [_config["ig_user_id"], _config["meta_access_token"]])
    if _config.get("threads_user_id") and _config.get("meta_access_token"):
        tasks["threads"] = (threads.get_profile_stats, [_config["threads_user_id"], _config["meta_access_token"]])
    if _config.get("youtube_channel_id") and _config.get("youtube_api_key"):
        tasks["youtube"] = (youtube.get_channel_stats, [_config["youtube_channel_id"], _config["youtube_api_key"]])

    if not tasks:
        return jsonify({"platforms": {}, "message": "No platforms configured yet."})

    results = {}
    with ThreadPoolExecutor() as ex:
        futures = {ex.submit(fn, *args): key for key, (fn, args) in tasks.items()}
        for future in as_completed(futures):
            key = futures[future]
            try:
                results[key] = future.result()
            except Exception as e:
                results[key] = {"platform": key, "error": str(e)}

    return jsonify({"platforms": results})


# ── Unified feed ──────────────────────────────────────────────
@app.get("/api/feed")
def unified_feed():
    limit = min(int(request.args.get("limit", 10)), 50)
    tasks = {}
    if _config.get("meta_page_id") and _config.get("meta_access_token"):
        tasks["meta"] = (meta.get_recent_posts, [_config["meta_page_id"], _config["meta_access_token"], limit])
    if _config.get("ig_user_id") and _config.get("meta_access_token"):
        tasks["instagram"] = (instagram.get_recent_media, [_config["ig_user_id"], _config["meta_access_token"], limit])
    if _config.get("threads_user_id") and _config.get("meta_access_token"):
        tasks["threads"] = (threads.get_recent_threads, [_config["threads_user_id"], _config["meta_access_token"], limit])
    if _config.get("youtube_channel_id") and _config.get("youtube_api_key"):
        tasks["youtube"] = (youtube.get_recent_videos, [_config["youtube_channel_id"], _config["youtube_api_key"], limit])

    if not tasks:
        return jsonify({"feed": [], "message": "No platforms configured yet."})

    all_posts = []
    with ThreadPoolExecutor() as ex:
        futures = {ex.submit(fn, *args): key for key, (fn, args) in tasks.items()}
        for future in as_completed(futures):
            try:
                all_posts.extend(future.result())
            except Exception:
                pass

    all_posts.sort(key=lambda p: p.get("created_at") or "", reverse=True)
    return jsonify({"feed": all_posts})


# ── Per-platform stats ────────────────────────────────────────
@app.get("/api/meta/stats")
def meta_stats():
    try:
        return jsonify(meta.get_page_stats(cfg("meta_page_id"), cfg("meta_access_token")))
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@app.get("/api/instagram/stats")
def ig_stats():
    try:
        return jsonify(instagram.get_account_stats(cfg("ig_user_id"), cfg("meta_access_token")))
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@app.get("/api/threads/stats")
def threads_stats():
    try:
        return jsonify(threads.get_profile_stats(cfg("threads_user_id"), cfg("meta_access_token")))
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@app.get("/api/youtube/stats")
def yt_stats():
    try:
        return jsonify(youtube.get_channel_stats(cfg("youtube_channel_id"), cfg("youtube_api_key")))
    except Exception as e:
        return jsonify({"error": str(e)}), 400


# ── Per-platform feeds ────────────────────────────────────────
@app.get("/api/meta/posts")
def meta_posts():
    limit = int(request.args.get("limit", 10))
    try:
        return jsonify({"posts": meta.get_recent_posts(cfg("meta_page_id"), cfg("meta_access_token"), limit)})
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@app.get("/api/instagram/media")
def ig_media():
    limit = int(request.args.get("limit", 10))
    try:
        return jsonify({"media": instagram.get_recent_media(cfg("ig_user_id"), cfg("meta_access_token"), limit)})
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@app.get("/api/threads/posts")
def threads_posts():
    limit = int(request.args.get("limit", 10))
    try:
        return jsonify({"posts": threads.get_recent_threads(cfg("threads_user_id"), cfg("meta_access_token"), limit)})
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@app.get("/api/youtube/videos")
def yt_videos():
    limit = int(request.args.get("limit", 10))
    try:
        return jsonify({"videos": youtube.get_recent_videos(cfg("youtube_channel_id"), cfg("youtube_api_key"), limit)})
    except Exception as e:
        return jsonify({"error": str(e)}), 400


# ── Serve frontend ────────────────────────────────────────────
FRONTEND = os.path.join(os.path.dirname(__file__), "..", "frontend")

@app.get("/")
def index():
    return send_from_directory(FRONTEND, "index.html")

@app.get("/<path:filename>")
def static_files(filename):
    return send_from_directory(FRONTEND, filename)


if __name__ == "__main__":
    print("\n  Social Media Hub running at http://localhost:8000\n")
    app.run(host="0.0.0.0", port=8000, debug=False)

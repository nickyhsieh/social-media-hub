/**
 * Social Media Hub — Frontend App
 * Talks to the FastAPI backend at /api/*
 */

const API = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1'
  ? 'http://localhost:8000'
  : '';  // same-origin when served by FastAPI

// ── State ────────────────────────────────────────────────────
let currentView = 'dashboard';
let feedData    = [];
let dashData    = {};

// ── Navigation ───────────────────────────────────────────────
document.querySelectorAll('.nav-item').forEach(el => {
  el.addEventListener('click', e => {
    e.preventDefault();
    const view = el.dataset.view;
    navigateTo(view);
  });
});

function navigateTo(view) {
  currentView = view;

  document.querySelectorAll('.nav-item').forEach(el =>
    el.classList.toggle('active', el.dataset.view === view)
  );
  document.querySelectorAll('.view').forEach(el =>
    el.classList.toggle('active', el.id === `view-${view}`)
  );

  const titles = {
    dashboard: 'Dashboard',
    feed:      'Unified Feed',
    meta:      'Facebook',
    instagram: 'Instagram',
    threads:   'Threads',
    youtube:   'YouTube',
    settings:  'Settings',
  };
  document.getElementById('pageTitle').textContent = titles[view] || view;

  loadView(view);
}

// ── Load view data ───────────────────────────────────────────
async function loadView(view) {
  switch (view) {
    case 'dashboard': return loadDashboard();
    case 'feed':      return loadFeed();
    case 'meta':      return loadPlatformDetail('meta');
    case 'instagram': return loadPlatformDetail('instagram');
    case 'threads':   return loadPlatformDetail('threads');
    case 'youtube':   return loadPlatformDetail('youtube');
    case 'settings':  return loadSettings();
  }
}

// ── Dashboard ────────────────────────────────────────────────
async function loadDashboard() {
  setSkeletons(true);
  try {
    const data = await apiFetch('/api/dashboard');
    dashData = data.platforms || {};
    renderDashboardCards(dashData);
    // Also load a small unified feed preview
    const feedResp = await apiFetch('/api/feed?limit=8');
    feedData = feedResp.feed || [];
    renderFeedItems('dashboardFeed', feedData, 'all');
    updateTimestamp();
  } catch (err) {
    showDashboardError(err.message);
  }
  setSkeletons(false);
}

function setSkeletons(on) {
  document.querySelectorAll('.stat-card').forEach(c =>
    c.classList.toggle('skeleton', on)
  );
}

function renderDashboardCards(platforms) {
  // Meta
  const m = platforms.meta;
  if (m && !m.error) {
    setText('meta-followers',   fmt(m.followers));
    setText('meta-fans',        fmt(m.fans));
    setText('meta-impressions', fmt(m.impressions));
    setText('meta-engagements', fmt(m.post_engagements));
    document.getElementById('card-meta').classList.remove('error');
  } else {
    markCardError('card-meta');
  }

  // Instagram
  const ig = platforms.instagram;
  if (ig && !ig.error) {
    setText('ig-followers', fmt(ig.followers));
    setText('ig-following', fmt(ig.following));
    setText('ig-posts',     fmt(ig.media_count));
    setText('ig-reach',     fmt(ig.reach));
    document.getElementById('card-instagram').classList.remove('error');
  } else {
    markCardError('card-instagram');
  }

  // Threads
  const th = platforms.threads;
  if (th && !th.error) {
    setText('th-followers', fmt(th.followers));
    setText('th-views',     fmt(th.views));
    setText('th-likes',     fmt(th.likes));
    setText('th-replies',   fmt(th.replies));
    document.getElementById('card-threads').classList.remove('error');
  } else {
    markCardError('card-threads');
  }

  // YouTube
  const yt = platforms.youtube;
  if (yt && !yt.error) {
    setText('yt-subscribers', fmt(yt.subscribers));
    setText('yt-views',       fmt(yt.total_views));
    setText('yt-videos',      fmt(yt.video_count));
    document.getElementById('card-youtube').classList.remove('error');
  } else {
    markCardError('card-youtube');
  }
}

function markCardError(cardId) {
  const card = document.getElementById(cardId);
  card.classList.add('error');
  card.querySelectorAll('.stat-number, .stat-sub-value').forEach(el => el.textContent = '—');
}

// ── Unified Feed ─────────────────────────────────────────────
async function loadFeed() {
  const container = document.getElementById('unifiedFeed');
  container.innerHTML = '<div class="empty-state"><p>Loading feed...</p></div>';
  try {
    const data = await apiFetch('/api/feed?limit=30');
    feedData = data.feed || [];
    renderFeedItems('unifiedFeed', feedData, 'all');
    updateTimestamp();
  } catch (err) {
    container.innerHTML = `<div class="error-msg">${err.message}</div>`;
  }
}

// Filter buttons
document.querySelectorAll('.filter-btn').forEach(btn => {
  btn.addEventListener('click', () => {
    document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
    renderFeedItems('unifiedFeed', feedData, btn.dataset.platform);
  });
});

function renderFeedItems(containerId, items, platform) {
  const container = document.getElementById(containerId);
  const filtered = platform === 'all' ? items : items.filter(i => i.platform === platform);

  if (!filtered.length) {
    container.innerHTML = `
      <div class="empty-state">
        <svg viewBox="0 0 24 24"><path d="M20 4H4c-1.1 0-2 .9-2 2v12c0 1.1.9 2 2 2h16c1.1 0 2-.9 2-2V6c0-1.1-.9-2-2-2zm0 14H4V6h16v12z"/></svg>
        <p>No posts yet. Configure your platforms in Settings.</p>
      </div>`;
    return;
  }

  container.innerHTML = filtered.map(item => buildFeedCard(item)).join('');
}

function buildFeedCard(item) {
  const p = item.platform;
  const tagLabels = { meta: 'Facebook', instagram: 'Instagram', threads: 'Threads', youtube: 'YouTube' };
  const time = item.created_at ? relativeTime(item.created_at) : '';

  const thumb = item.media_url
    ? `<img class="feed-thumb" src="${esc(item.media_url)}" alt="" loading="lazy" onerror="this.style.display='none'">`
    : '';

  const statsHtml = buildPostStats(item);

  const link = item.permalink
    ? `<a class="feed-link" href="${esc(item.permalink)}" target="_blank" rel="noopener">View &rarr;</a>`
    : '';

  return `
    <div class="feed-item" data-platform="${p}">
      <div class="feed-platform-dot dot-${p}"></div>
      <div class="feed-content">
        <div class="feed-header">
          <span class="feed-platform-tag tag-${p}">${tagLabels[p] || p}</span>
          <span class="feed-time">${time}</span>
        </div>
        <div class="feed-text">${esc(item.text || '(no caption)')}</div>
        <div class="feed-stats">
          ${statsHtml}
          ${link}
        </div>
      </div>
      ${thumb}
    </div>`;
}

function buildPostStats(item) {
  const parts = [];
  const heart = `<svg viewBox="0 0 24 24"><path d="M12 21.35l-1.45-1.32C5.4 15.36 2 12.28 2 8.5 2 5.42 4.42 3 7.5 3c1.74 0 3.41.81 4.5 2.09C13.09 3.81 14.76 3 16.5 3 19.58 3 22 5.42 22 8.5c0 3.78-3.4 6.86-8.55 11.54L12 21.35z"/></svg>`;
  const comment = `<svg viewBox="0 0 24 24"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/></svg>`;
  const eye = `<svg viewBox="0 0 24 24"><path d="M12 4.5C7 4.5 2.73 7.61 1 12c1.73 4.39 6 7.5 11 7.5s9.27-3.11 11-7.5c-1.73-4.39-6-7.5-11-7.5zM12 17c-2.76 0-5-2.24-5-5s2.24-5 5-5 5 2.24 5 5-2.24 5-5 5zm0-8c-1.66 0-3 1.34-3 3s1.34 3 3 3 3-1.34 3-3-1.34-3-3-3z"/></svg>`;
  const share = `<svg viewBox="0 0 24 24"><path d="M18 16.08c-.76 0-1.44.3-1.96.77L8.91 12.7c.05-.23.09-.46.09-.7s-.04-.47-.09-.7l7.05-4.11c.54.5 1.25.81 2.04.81 1.66 0 3-1.34 3-3s-1.34-3-3-3-3 1.34-3 3c0 .24.04.47.09.7L8.04 9.81C7.5 9.31 6.79 9 6 9c-1.66 0-3 1.34-3 3s1.34 3 3 3c.79 0 1.5-.31 2.04-.81l7.12 4.16c-.05.21-.08.43-.08.65 0 1.61 1.31 2.92 2.92 2.92 1.61 0 2.92-1.31 2.92-2.92s-1.31-2.92-2.92-2.92z"/></svg>`;

  if (item.likes    != null) parts.push(`<span class="feed-stat">${heart} ${fmt(item.likes)}</span>`);
  if (item.comments != null) parts.push(`<span class="feed-stat">${comment} ${fmt(item.comments)}</span>`);
  if (item.views    != null) parts.push(`<span class="feed-stat">${eye} ${fmt(item.views)}</span>`);
  if (item.shares   != null) parts.push(`<span class="feed-stat">${share} ${fmt(item.shares)}</span>`);
  if (item.reposts  != null) parts.push(`<span class="feed-stat">${share} ${fmt(item.reposts)}</span>`);

  return parts.join('');
}

// ── Platform detail pages ─────────────────────────────────────
const platformEndpoints = {
  meta:      { stats: '/api/meta/stats',      feed: '/api/meta/posts',      feedKey: 'posts' },
  instagram: { stats: '/api/instagram/stats', feed: '/api/instagram/media', feedKey: 'media' },
  threads:   { stats: '/api/threads/stats',   feed: '/api/threads/posts',   feedKey: 'posts' },
  youtube:   { stats: '/api/youtube/stats',   feed: '/api/youtube/videos',  feedKey: 'videos' },
};

async function loadPlatformDetail(platform) {
  const containerId = { meta: 'metaDetail', instagram: 'igDetail', threads: 'threadsDetail', youtube: 'ytDetail' }[platform];
  const container = document.getElementById(containerId);
  container.innerHTML = '<div class="empty-state"><p>Loading...</p></div>';

  const ep = platformEndpoints[platform];
  try {
    const [stats, feedResp] = await Promise.all([
      apiFetch(ep.stats),
      apiFetch(`${ep.feed}?limit=15`),
    ]);
    const posts = feedResp[ep.feedKey] || [];

    container.innerHTML = buildDetailHeader(stats) + buildDetailFeed(posts, platform);
    updateTimestamp();
  } catch (err) {
    container.innerHTML = `<div class="error-msg">${err.message}</div><div class="settings-hint" style="padding:16px">Configure credentials in <a href="#" onclick="navigateTo('settings');return false" style="color:var(--accent)">Settings</a>.</div>`;
  }
}

function buildDetailHeader(stats) {
  const name    = stats.name || stats.username || stats.channel_id || '';
  const handle  = stats.username ? `@${stats.username}` : '';
  const avatar  = stats.profile_picture || stats.picture || '';
  const avatarHtml = avatar
    ? `<img class="detail-avatar" src="${esc(avatar)}" alt="" onerror="this.style.display='none'">`
    : `<div class="detail-avatar" style="display:flex;align-items:center;justify-content:center;background:var(--surface2);color:var(--text-muted);font-size:24px">${(name[0]||'?').toUpperCase()}</div>`;

  const statPairs = buildStatPairs(stats);

  return `
    <div class="detail-header">
      ${avatarHtml}
      <div class="detail-info">
        <h2>${esc(name)}</h2>
        ${handle ? `<p>${esc(handle)}</p>` : ''}
        <div style="display:flex;gap:20px;margin-top:10px;flex-wrap:wrap">
          ${statPairs}
        </div>
      </div>
    </div>
    <div class="section-title">Recent Posts</div>`;
}

function buildStatPairs(stats) {
  const kv = [];
  if (stats.followers    != null) kv.push(['Followers', fmt(stats.followers)]);
  if (stats.subscribers  != null) kv.push(['Subscribers', fmt(stats.subscribers)]);
  if (stats.fans         != null) kv.push(['Fans', fmt(stats.fans)]);
  if (stats.following    != null) kv.push(['Following', fmt(stats.following)]);
  if (stats.media_count  != null) kv.push(['Posts', fmt(stats.media_count)]);
  if (stats.video_count  != null) kv.push(['Videos', fmt(stats.video_count)]);
  if (stats.total_views  != null) kv.push(['Total Views', fmt(stats.total_views)]);
  if (stats.impressions  != null) kv.push(['Impressions', fmt(stats.impressions)]);
  if (stats.reach        != null) kv.push(['Reach', fmt(stats.reach)]);

  return kv.map(([label, val]) => `
    <div>
      <div style="font-size:20px;font-weight:700">${val}</div>
      <div style="font-size:11px;color:var(--text-muted);text-transform:uppercase;letter-spacing:.5px">${label}</div>
    </div>`).join('');
}

function buildDetailFeed(posts, platform) {
  if (!posts.length) return '<div class="empty-state"><p>No posts found.</p></div>';
  return `<div class="feed-container">${posts.map(p => buildFeedCard({ ...p, platform })).join('')}</div>`;
}

// ── Settings ─────────────────────────────────────────────────
async function loadSettings() {
  try {
    const cfg = await apiFetch('/api/config');
    const fields = ['meta_page_id', 'meta_access_token', 'ig_user_id', 'threads_user_id', 'youtube_channel_id', 'youtube_api_key'];
    fields.forEach(f => {
      const el = document.getElementById(`cfg-${f}`);
      if (el && cfg[f] && cfg[f] !== '***') el.value = cfg[f];
    });
  } catch (_) {}
}

document.getElementById('btnSaveConfig').addEventListener('click', async () => {
  const fields = ['meta_page_id', 'meta_access_token', 'ig_user_id', 'threads_user_id', 'youtube_channel_id', 'youtube_api_key'];
  const body = {};
  fields.forEach(f => {
    const val = document.getElementById(`cfg-${f}`)?.value?.trim();
    if (val) body[f] = val;
  });

  const status = document.getElementById('saveStatus');
  status.textContent = 'Saving...';
  status.style.color = 'var(--text-muted)';

  try {
    await apiFetch('/api/config', { method: 'POST', body: JSON.stringify(body), headers: { 'Content-Type': 'application/json' } });
    status.textContent = 'Saved! Refreshing dashboard...';
    status.style.color = '#22c55e';
    setTimeout(() => navigateTo('dashboard'), 1200);
  } catch (err) {
    status.textContent = `Error: ${err.message}`;
    status.style.color = '#f87171';
  }
});

// ── Refresh button ────────────────────────────────────────────
document.getElementById('btnRefresh').addEventListener('click', () => loadView(currentView));

// ── Helpers ───────────────────────────────────────────────────
async function apiFetch(path, opts = {}) {
  const res = await fetch(`${API}${path}`, opts);
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || res.statusText);
  }
  return res.json();
}

function setText(id, val) {
  const el = document.getElementById(id);
  if (el) el.textContent = val;
}

function fmt(n) {
  if (n == null) return '—';
  const num = Number(n);
  if (isNaN(num)) return String(n);
  if (num >= 1_000_000) return (num / 1_000_000).toFixed(1) + 'M';
  if (num >= 1_000)     return (num / 1_000).toFixed(1) + 'K';
  return num.toLocaleString();
}

function esc(str) {
  if (!str) return '';
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;');
}

function relativeTime(iso) {
  const diff = Date.now() - new Date(iso).getTime();
  const s = Math.floor(diff / 1000);
  if (s < 60)   return `${s}s ago`;
  const m = Math.floor(s / 60);
  if (m < 60)   return `${m}m ago`;
  const h = Math.floor(m / 60);
  if (h < 24)   return `${h}h ago`;
  const d = Math.floor(h / 24);
  if (d < 30)   return `${d}d ago`;
  const mo = Math.floor(d / 30);
  if (mo < 12)  return `${mo}mo ago`;
  return `${Math.floor(mo / 12)}y ago`;
}

function showDashboardError(msg) {
  document.getElementById('dashboardFeed').innerHTML = `<div class="error-msg">${msg}</div>`;
}

function updateTimestamp() {
  document.getElementById('lastUpdated').textContent =
    'Updated ' + new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
}

// ── Init ──────────────────────────────────────────────────────
navigateTo('dashboard');

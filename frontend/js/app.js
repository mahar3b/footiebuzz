/* FootieBuzz frontend — WebSocket + Chart.js + entity tracker */

const API_BASE = "";

let selectedEntity = "all";
let activeTab = "teams";
let ws, lastPing = Date.now();
let timelineChart, distributionChart, shiftChart;
let lastEntities = [];

// Fallback so chart always renders even before API responds
const DEMO_ENTITIES_FALLBACK = [
  { id: "argentina", name: "Argentina", type: "team", icon: "🇦🇷", color: "#75aadb", mention_count: 0, positive: 0, neutral: 0, negative: 0, avg_sentiment: 0 },
  { id: "france", name: "France", type: "team", icon: "🇫🇷", color: "#0055a4", mention_count: 0, positive: 0, neutral: 0, negative: 0, avg_sentiment: 0 },
  { id: "brazil", name: "Brazil", type: "team", icon: "🇧🇷", color: "#ffdf00", mention_count: 0, positive: 0, neutral: 0, negative: 0, avg_sentiment: 0 },
  { id: "england", name: "England", type: "team", icon: "🏴", color: "#cf142b", mention_count: 0, positive: 0, neutral: 0, negative: 0, avg_sentiment: 0 },
  { id: "messi", name: "Messi", type: "player", icon: "⭐", color: "#00e676", mention_count: 0, positive: 0, neutral: 0, negative: 0, avg_sentiment: 0 },
  { id: "mbappe", name: "Mbappé", type: "player", icon: "⚡", color: "#448aff", mention_count: 0, positive: 0, neutral: 0, negative: 0, avg_sentiment: 0 },
  { id: "ronaldo", name: "Ronaldo", type: "player", icon: "👑", color: "#ffd740", mention_count: 0, positive: 0, neutral: 0, negative: 0, avg_sentiment: 0 },
  { id: "bellingham", name: "Bellingham", type: "player", icon: "🔥", color: "#ff5252", mention_count: 0, positive: 0, neutral: 0, negative: 0, avg_sentiment: 0 },
];

function entityTypeForTab(tab) {
  return tab === "teams" ? "team" : "player";
}

function wsUrl() {
  const base = location.host;
  const q = selectedEntity && selectedEntity !== "all" ? `?entity=${selectedEntity}` : "";
  return `ws://${base}/api/ws${q}`;
}

Chart.defaults.color = "#6b7d8f";
Chart.defaults.borderColor = "rgba(255,255,255,0.06)";
Chart.defaults.font.family = "'Outfit', sans-serif";

function initCharts() {
  timelineChart = new Chart(document.getElementById("timeline-chart"), {
    type: "line",
    data: {
      labels: [],
      datasets: [
        {
          label: "Sentiment",
          data: [],
          borderColor: "#00e676",
          backgroundColor: "rgba(0,230,118,0.08)",
          fill: true,
          tension: 0.4,
          pointRadius: 3,
          yAxisID: "y",
        },
        {
          label: "Volume",
          data: [],
          type: "bar",
          backgroundColor: "rgba(68,138,255,0.35)",
          borderRadius: 4,
          yAxisID: "y1",
        },
      ],
    },
    options: chartLineOptions(),
  });

  distributionChart = new Chart(document.getElementById("distribution-chart"), {
    type: "doughnut",
    data: {
      labels: ["Positive", "Neutral", "Negative"],
      datasets: [{ data: [0, 0, 0], backgroundColor: ["#00e676", "#78909c", "#ff5252"], borderWidth: 0 }],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      cutout: "65%",
      plugins: { legend: { position: "bottom", labels: { boxWidth: 10, font: { size: 11 } } } },
    },
  });

  shiftChart = new Chart(document.getElementById("shift-chart"), {
    type: "bar",
    data: {
      labels: [],
      datasets: [
        { label: "Before", data: [], backgroundColor: "rgba(120,144,156,0.7)", borderRadius: 6 },
        { label: "After", data: [], backgroundColor: "rgba(0,230,118,0.75)", borderRadius: 6 },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: { legend: { labels: { boxWidth: 12 } } },
      scales: {
        x: { grid: { display: false } },
        y: { min: -1.05, max: 1.05, grid: { color: "rgba(255,255,255,0.04)" } },
      },
    },
  });
}

function chartLineOptions() {
  return {
    responsive: true,
    maintainAspectRatio: false,
    interaction: { mode: "index", intersect: false },
    plugins: { legend: { labels: { boxWidth: 12 } } },
    scales: {
      x: { grid: { display: false }, ticks: { maxTicksLimit: 8, font: { size: 10 } } },
      y: { position: "left", min: -1.05, max: 1.05, grid: { color: "rgba(255,255,255,0.04)" } },
      y1: { position: "right", grid: { drawOnChartArea: false } },
    },
  };
}

function formatTime(iso) {
  try {
    return new Date(iso).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", second: "2-digit" });
  } catch { return iso; }
}

function sentimentLabel(avg) {
  if (avg > 0.15) return "Bullish 🟢";
  if (avg < -0.15) return "Bearish 🔴";
  return "Neutral ⚪";
}

function sentimentClass(avg) {
  if (avg > 0.1) return "pos";
  if (avg < -0.1) return "neg";
  return "neu";
}

function escapeHtml(str) {
  return str.replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;").replace(/"/g,"&quot;");
}

function updateStats(stats, activeEntity) {
  document.getElementById("stat-total").textContent = stats.total_processed.toLocaleString();
  document.getElementById("stat-avg").textContent = stats.avg_sentiment.toFixed(2);
  document.getElementById("stat-avg-label").textContent = sentimentLabel(stats.avg_sentiment);
  document.getElementById("stat-pos").textContent = stats.positive;
  document.getElementById("stat-neu").textContent = stats.neutral;
  document.getElementById("stat-neg").textContent = stats.negative;
  document.getElementById("feed-count").textContent = `${stats.window_total} in window`;

  const label = activeEntity
    ? `Showing: ${activeEntity.icon} ${activeEntity.name}`
    : "Showing: All mentions";
  document.getElementById("tracker-active-label").textContent = label;

  document.getElementById("keywords-list").innerHTML =
    (stats.keywords || []).map(k => `<span class="kw-tag">#${k.replace(/^#/, "")}</span>`).join("") || "—";
}

function updateTimeline(timeline) {
  timelineChart.data.labels = timeline.map(p => formatTime(p.timestamp));
  timelineChart.data.datasets[0].data = timeline.map(p => p.avg_sentiment);
  timelineChart.data.datasets[1].data = timeline.map(p => p.volume);

  const color = selectedEntity !== "all"
    ? (lastEntities.find(e => e.id === selectedEntity)?.color || "#00e676")
    : "#00e676";
  timelineChart.data.datasets[0].borderColor = color;
  timelineChart.data.datasets[0].backgroundColor = color + "22";
  timelineChart.update("none");
}

function updateDistribution(stats) {
  distributionChart.data.datasets[0].data = [stats.positive, stats.neutral, stats.negative];
  distributionChart.update("none");
}

function updateShifts(shifts) {
  shiftChart.data.labels = shifts.map(s => `${s.event} ${formatTime(s.timestamp)}`);
  shiftChart.data.datasets[0].data = shifts.map(s => s.before);
  shiftChart.data.datasets[1].data = shifts.map(s => s.after);
  shiftChart.update("none");
}

function updateEvents(events) {
  const el = document.getElementById("events-list");
  if (!events.length) {
    el.innerHTML = `<div style="color:var(--muted);font-size:0.8rem;padding:8px 0">No events yet</div>`;
    return;
  }
  el.innerHTML = [...events].reverse().slice(0, 8).map(e => {
    const cls = e.label.toLowerCase() === "goal" ? "goal" : e.label.toLowerCase() === "upset" ? "upset" : "other";
    return `<div class="event-item">
      <span class="event-badge ${cls}">${e.label}</span>
      <span class="event-time">${formatTime(e.timestamp)}</span>
      <span class="event-desc">${escapeHtml(e.description || "—")}</span>
    </div>`;
  }).join("");
}

function updateTweets(tweets) {
  const feed = document.getElementById("tweet-feed");
  if (!tweets.length) {
    feed.innerHTML = `<div class="tweet-empty">No tweets mentioning this ${activeTab === "teams" ? "team" : "player"} yet…</div>`;
    return;
  }
  feed.innerHTML = tweets.map(t => `
    <div class="tweet-card">
      <div class="sentiment-dot ${t.label}"></div>
      <div class="tweet-body">
        <div class="tweet-text">${escapeHtml(t.text)}</div>
        <div class="tweet-meta">${formatTime(t.created_at)} · @${escapeHtml(t.author)}</div>
      </div>
      <span class="tweet-label ${t.label}">${t.label}</span>
    </div>
  `).join("");
}

function renderFeaturedCard(e) {
  const cls = sentimentClass(e.avg_sentiment);
  const score = e.mention_count ? e.avg_sentiment.toFixed(2) : "0.00";
  const barPct = Math.round(((e.avg_sentiment + 1) / 2) * 100);
  const active = selectedEntity === e.id ? "active" : "";

  return `
    <div class="featured-card ${active}" data-id="${e.id}" style="--fc-color: ${e.color}">
      <div class="featured-card-header">
        <span class="featured-icon">${e.icon}</span>
        <div>
          <div class="featured-name">${escapeHtml(e.name)}</div>
          <div class="featured-type">${e.type}</div>
        </div>
      </div>
      <div class="featured-score ${cls}">${score}</div>
      <div class="featured-mood">${sentimentLabel(e.avg_sentiment)} · ${e.mention_count} mentions</div>
      <div class="featured-bar-wrap">
        <div class="featured-bar" style="width:${barPct}%; background:${e.color}"></div>
      </div>
      <div class="featured-breakdown">
        <span class="pos">+${e.positive}</span>
        <span class="neu">=${e.neutral}</span>
        <span class="neg">−${e.negative}</span>
      </div>
    </div>`;
}

function renderFeaturedMatchup(featured) {
  const container = document.getElementById("featured-matchup");
  if (!featured || featured.length < 2) {
    container.innerHTML = "";
    return;
  }

  const arg = featured.find(e => e.id === "argentina") || featured[0];
  const mbappe = featured.find(e => e.id === "mbappe") || featured[1];

  container.innerHTML = `
    ${renderFeaturedCard(arg)}
    <div class="featured-vs">VS</div>
    ${renderFeaturedCard(mbappe)}
  `;

  container.querySelectorAll(".featured-card").forEach(card => {
    card.addEventListener("click", () => selectEntity(card.dataset.id));
  });
}

function renderEntityChips(entities) {
  lastEntities = entities;
  const container = document.getElementById("entity-chips");

  const allChip = `
    <button class="entity-chip all-chip ${selectedEntity === "all" ? "active" : ""}" data-id="all" data-type="all">
      <span class="entity-chip-icon">🌐</span>
      <div class="entity-chip-info">
        <span class="entity-chip-name">All</span>
        <span class="entity-chip-meta">every mention</span>
      </div>
    </button>`;

  const chips = entities.map(e => {
    const cls = sentimentClass(e.avg_sentiment);
    const hidden = e.type !== entityTypeForTab(activeTab) ? "hidden" : "";
    const active = selectedEntity === e.id ? "active" : "";
    const score = e.mention_count ? e.avg_sentiment.toFixed(2) : "—";
    return `
      <button class="entity-chip ${hidden} ${active}" data-id="${e.id}" data-type="${e.type}"
              style="--chip-color: ${e.color}">
        <span class="entity-chip-icon">${e.icon}</span>
        <div class="entity-chip-info">
          <span class="entity-chip-name">${escapeHtml(e.name)}</span>
          <span class="entity-chip-meta">${e.mention_count} mentions</span>
        </div>
        <span class="entity-chip-sentiment ${cls}">${score}</span>
      </button>`;
  }).join("");

  container.innerHTML = allChip + chips;

  container.querySelectorAll(".entity-chip").forEach(btn => {
    btn.addEventListener("click", () => selectEntity(btn.dataset.id));
  });
}

function renderEntityBarChart(entities) {
  const container = document.getElementById("entity-bar-chart");
  const type = entityTypeForTab(activeTab);
  const list = (entities && entities.length ? entities : DEMO_ENTITIES_FALLBACK)
    .filter(e => e.type === type);

  const title = document.getElementById("entity-chart-title");
  const hint = document.getElementById("entity-chart-hint");
  if (activeTab === "teams") {
    title.textContent = "Team Sentiment";
    hint.textContent = "Argentina · France · Brazil · England";
  } else {
    title.textContent = "Player Sentiment";
    hint.textContent = "Messi · Mbappé · Ronaldo · Bellingham";
  }

  if (!list.length) {
    container.innerHTML = `<div class="bar-empty">No data for this tab yet…</div>`;
    return;
  }

  const maxMentions = Math.max(...list.map(e => e.mention_count), 1);

  const rows = list.map(e => {
    const total = e.mention_count || 0;
    const trackWidth = 100;
    let posW = 0, neuW = 0, negW = 0;
    if (total > 0) {
      posW = (e.positive / total) * trackWidth;
      neuW = (e.neutral / total) * trackWidth;
      negW = (e.negative / total) * trackWidth;
    } else {
      neuW = 100; // grey placeholder bar when no mentions yet
    }
    return `
      <div class="bar-row" title="${escapeHtml(e.name)}: +${e.positive} / =${e.neutral} / −${e.negative}">
        <span class="bar-label">${e.icon} ${escapeHtml(e.name)}</span>
        <div class="bar-track">
          <div class="bar-seg pos" style="width:${posW}%"></div>
          <div class="bar-seg neu" style="width:${neuW}%"></div>
          <div class="bar-seg neg" style="width:${negW}%"></div>
        </div>
        <span class="bar-count">${total}</span>
      </div>`;
  }).join("");

  container.innerHTML = `
    <div class="bar-legend">
      <span class="leg-pos">Positive</span>
      <span class="leg-neu">Neutral</span>
      <span class="leg-neg">Negative</span>
    </div>
    ${rows}
  `;
}

function updateEntityCompare(entities) {
  lastEntities = entities && entities.length ? entities : DEMO_ENTITIES_FALLBACK;
  renderEntityBarChart(lastEntities);
}

function renderDashboard(data) {
  if (!data) return;
  const entities = data.entities && data.entities.length ? data.entities : DEMO_ENTITIES_FALLBACK;

  updateStats(data.stats || {}, data.active_entity);
  updateTimeline(data.timeline || []);
  updateDistribution(data.stats || { positive: 0, neutral: 0, negative: 0 });
  updateShifts(data.shifts || []);
  updateEvents(data.events || []);
  updateTweets(data.tweets || []);
  renderFeaturedMatchup(data.featured || entities.filter(e => ["argentina","mbappe"].includes(e.id)));
  renderEntityChips(entities);
  renderEntityBarChart(entities);
}

function selectEntity(id) {
  if (id === selectedEntity) return;
  selectedEntity = id;
  connectWebSocket();
  pollDashboard();
}

function setConnection(status, text) {
  const el = document.getElementById("connection-status");
  el.textContent = text;
  el.className = "connection " + status;
}

function connectWebSocket() {
  if (ws) { try { ws.close(); } catch {} }

  ws = new WebSocket(wsUrl());

  ws.onopen = () => {
    setConnection("connected", "Connected");
    lastPing = Date.now();
  };

  ws.onmessage = (evt) => {
    try {
      renderDashboard(JSON.parse(evt.data));
      document.getElementById("ws-latency").textContent = `updated ${Date.now() - lastPing}ms ago`;
      lastPing = Date.now();
    } catch (e) { console.error(e); }
  };

  ws.onclose = () => {
    setConnection("error", "Reconnecting…");
    setTimeout(connectWebSocket, 3000);
  };

  ws.onerror = () => setConnection("error", "Connection error");
}

async function pollDashboard() {
  try {
    const q = selectedEntity !== "all" ? `?entity=${selectedEntity}` : "";
    const res = await fetch(`${API_BASE}/api/dashboard${q}`);
    if (res.ok) renderDashboard(await res.json());
  } catch {}
}

// Tab switching
document.querySelectorAll(".tracker-tab").forEach(tab => {
  tab.addEventListener("click", () => {
    document.querySelectorAll(".tracker-tab").forEach(t => t.classList.remove("active"));
    tab.classList.add("active");
    activeTab = tab.dataset.tab;
    document.querySelectorAll(".entity-chip").forEach(chip => {
      if (chip.dataset.type === "all") return;
      chip.classList.toggle("hidden", chip.dataset.type !== entityTypeForTab(activeTab));
    });
    updateEntityCompare(lastEntities);
  });
});

// Event form
document.getElementById("event-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  const label = document.getElementById("event-type").value;
  const description = document.getElementById("event-desc").value;
  const fb = document.getElementById("event-feedback");

  try {
    const res = await fetch(`${API_BASE}/api/events`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ label, description }),
    });
    if (!res.ok) throw new Error("Failed");
    const event = await res.json();
    fb.textContent = `✓ Logged ${event.label} at ${formatTime(event.timestamp)}`;
    document.getElementById("event-desc").value = "";
    setTimeout(() => { fb.textContent = ""; }, 4000);
  } catch {
    fb.textContent = "Failed to log event";
    fb.style.color = "var(--red)";
  }
});

initCharts();
renderEntityBarChart(DEMO_ENTITIES_FALLBACK);
renderEntityChips(DEMO_ENTITIES_FALLBACK);
pollDashboard();
connectWebSocket();
setInterval(() => { if (Date.now() - lastPing > 10000) pollDashboard(); }, 5000);

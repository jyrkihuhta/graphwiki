(function () {
  "use strict";

  const TASKS_POLL_MS  = 5000;
  const STATUS_POLL_MS = 8000;
  const MAX_ACTIVITY   = 30;

  // ── State ────────────────────────────────────────────────────────────────

  var prevByName   = {};
  var activityLog  = [];

  // ── DOM helpers ───────────────────────────────────────────────────────────

  function el(tag, cls) {
    var e = document.createElement(tag);
    if (cls) e.className = cls;
    return e;
  }

  function setText(id, text) {
    var e = document.getElementById(id);
    if (e) e.textContent = text;
  }

  function setBody(id, node) {
    var container = document.getElementById(id);
    if (!container) return;
    while (container.firstChild) container.removeChild(container.firstChild);
    if (Array.isArray(node)) {
      node.forEach(function (n) { container.appendChild(n); });
    } else {
      container.appendChild(node);
    }
  }

  // ── Tasks API poll ────────────────────────────────────────────────────────

  function pollTasks() {
    var statuses = ["planned", "in_progress", "review", "merged", "failed", "rejected"];
    Promise.all(
      statuses.map(function (s) {
        return fetch("/api/v1/tasks?assignee=factory&status=" + s)
          .then(function (r) { return r.ok ? r.json() : []; })
          .catch(function () { return []; });
      })
    ).then(function (results) {
      var byStatus = {};
      statuses.forEach(function (s, i) { byStatus[s] = results[i] || []; });
      detectTransitions(byStatus);
      renderPipeline(byStatus);
      var updEl = document.getElementById("fc-updated");
      if (updEl) {
        var now = new Date();
        updEl.textContent = "Updated " + now.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", second: "2-digit" });
      }
    }).catch(function () {}).finally(function () {
      setTimeout(pollTasks, TASKS_POLL_MS);
    });
  }

  function detectTransitions(byStatus) {
    var nextByName = {};
    Object.keys(byStatus).forEach(function (s) {
      (byStatus[s] || []).forEach(function (t) { nextByName[t.name] = s; });
    });
    Object.keys(nextByName).forEach(function (name) {
      var status = nextByName[name];
      var prev   = prevByName[name];
      if (prev !== undefined && prev !== status) {
        pushActivity({ name: name, from: prev, to: status, time: Date.now() });
      } else if (prev === undefined) {
        pushActivity({ name: name, from: null, to: status, time: Date.now() });
      }
    });
    prevByName = nextByName;
  }

  function pushActivity(item) {
    activityLog.unshift(item);
    if (activityLog.length > MAX_ACTIVITY) activityLog.length = MAX_ACTIVITY;
    renderActivity();
  }

  // ── Pipeline bar ──────────────────────────────────────────────────────────

  function renderPipeline(byStatus) {
    setText("fc-count-planned",    String((byStatus.planned    || []).length));
    setText("fc-count-in_progress",String((byStatus.in_progress|| []).length));
    setText("fc-count-review",     String((byStatus.review     || []).length));
    setText("fc-count-merged",     String((byStatus.merged     || []).length));
    setText("fc-count-failed",     String((byStatus.failed     || []).length));
    setText("fc-count-rejected",   String((byStatus.rejected   || []).length));

    var progressStage = document.getElementById("fc-pipe-progress");
    if (progressStage) {
      var active = (byStatus.in_progress || []).length > 0;
      progressStage.classList.toggle("fc-pipe-stage--pulsing", active);
    }
  }

  // ── Orchestrator status poll ──────────────────────────────────────────────

  function pollStatus() {
    fetch("/api/factory/status")
      .then(function (r) { return r.ok ? r.json() : null; })
      .then(function (data) {
        if (!data) return;
        renderGraphs(data.active_graphs || []);
        renderBots(data.bots || []);
        renderResources(data.resources || {});
      })
      .catch(function () {})
      .finally(function () {
        setTimeout(pollStatus, STATUS_POLL_MS);
      });
  }

  // ── Active graphs panel ───────────────────────────────────────────────────

  var GRAPH_STATUS_LABELS = {
    intake:       "Intake",
    decomposing:  "Decomposing",
    dispatching:  "Dispatching",
    grinding:     "Grinding",
    reviewing:    "Reviewing",
    completed:    "Completed",
    failed:       "Failed",
    escalated:    "Escalated",
  };

  function renderGraphs(graphs) {
    setText("fc-graphs-badge", String(graphs.length));
    if (!graphs.length) {
      setBody("fc-graphs-body", makeEmpty("No active graphs"));
      return;
    }
    setBody("fc-graphs-body", graphs.map(buildGraphRow));
  }

  function buildGraphRow(g) {
    var row = el("div", "fc-graph-row");

    var header = el("div", "fc-graph-header");
    var titleEl = el("span", "fc-graph-title");
    titleEl.textContent = truncate(g.title || g.thread_id, 36);
    header.appendChild(titleEl);
    var statusBadge = el("span", "fc-graph-status fc-graph-status--" + (g.graph_status || "unknown"));
    statusBadge.textContent = GRAPH_STATUS_LABELS[g.graph_status] || g.graph_status;
    header.appendChild(statusBadge);
    row.appendChild(header);

    var meta = el("div", "fc-graph-meta");

    // Subtask progress bar
    var total = g.subtasks_total || 0;
    var done  = (g.subtasks_completed || 0) + (g.subtasks_failed || 0);
    if (total > 0) {
      var progressWrap = el("div", "fc-progress-wrap");
      var bar = el("div", "fc-progress-bar");
      var pct = Math.round((done / total) * 100);
      bar.style.width = pct + "%";
      progressWrap.appendChild(bar);
      meta.appendChild(progressWrap);

      var subtaskLabel = el("span", "fc-graph-stat");
      subtaskLabel.textContent = done + "/" + total + " subtasks";
      meta.appendChild(subtaskLabel);
    }

    if (g.active_grinders > 0) {
      var grinderEl = el("span", "fc-graph-stat fc-graph-stat--active");
      grinderEl.textContent = g.active_grinders + " grinder" + (g.active_grinders !== 1 ? "s" : "");
      meta.appendChild(grinderEl);
    }

    if (g.cost_usd > 0) {
      var costEl = el("span", "fc-graph-stat fc-graph-stat--cost");
      costEl.textContent = "$" + g.cost_usd.toFixed(3);
      meta.appendChild(costEl);
    }

    row.appendChild(meta);
    return row;
  }

  // ── Bots panel ────────────────────────────────────────────────────────────

  function renderBots(bots) {
    setText("fc-bots-badge", String(bots.length));
    if (!bots.length) {
      setBody("fc-bots-body", makeEmpty("No bots registered"));
      return;
    }
    setBody("fc-bots-body", bots.map(buildBotRow));
  }

  function buildBotRow(bot) {
    var row = el("div", "fc-bot-row");

    var header = el("div", "fc-bot-header");
    var dot = el("span", "fc-bot-dot " + (bot.running ? "fc-bot-dot--running" : "fc-bot-dot--stopped"));
    header.appendChild(dot);
    var nameEl = el("span", "fc-bot-name");
    nameEl.textContent = bot.name;
    header.appendChild(nameEl);
    if (bot.last_ran_at) {
      var ago = el("span", "fc-bot-ago");
      ago.textContent = timeAgo(bot.last_ran_at * 1000);
      header.appendChild(ago);
    }
    row.appendChild(header);

    var stats = el("div", "fc-bot-stats");

    var runsEl = el("span", "fc-bot-stat");
    runsEl.textContent = bot.total_runs + " runs";
    stats.appendChild(runsEl);

    var actionsEl = el("span", "fc-bot-stat");
    actionsEl.textContent = bot.total_actions + " actions";
    stats.appendChild(actionsEl);

    if (bot.last_details) {
      var detailEl = el("span", "fc-bot-detail");
      detailEl.textContent = truncate(bot.last_details, 48);
      stats.appendChild(detailEl);
    }

    row.appendChild(stats);
    return row;
  }

  // ── Resources panel ───────────────────────────────────────────────────────

  function renderResources(res) {
    if (!Object.keys(res).length) {
      setBody("fc-resources-body", makeEmpty("Orchestrator unreachable"));
      return;
    }

    var rows = [
      buildResourceRow("Parent tasks",    res.active_parent_tasks,     res.max_concurrent_parent_tasks),
      buildResourceRow("Grinders",        res.active_grinders,         res.max_concurrent_sandboxes),
      buildResourceDollar("Session cost", res.total_cost_usd),
    ];

    setBody("fc-resources-body", rows);
  }

  function buildResourceRow(label, current, cap) {
    var row = el("div", "fc-res-row");
    var labelEl = el("span", "fc-res-label");
    labelEl.textContent = label;
    row.appendChild(labelEl);

    var right = el("span", "fc-res-right");
    var valEl = el("span", "fc-res-value");
    valEl.textContent = (current !== null && current !== undefined) ? String(current) : "—";
    right.appendChild(valEl);

    if (cap !== null && cap !== undefined) {
      var capEl = el("span", "fc-res-cap");
      capEl.textContent = "/ " + cap;
      right.appendChild(capEl);

      // Gauge bar
      if (typeof current === "number" && current >= 0) {
        var wrap = el("div", "fc-gauge-wrap");
        var fill = el("div", "fc-gauge-fill");
        var pct  = cap > 0 ? Math.min(100, Math.round((current / cap) * 100)) : 0;
        fill.style.width = pct + "%";
        if (pct >= 80) fill.classList.add("fc-gauge-fill--warn");
        wrap.appendChild(fill);
        row.appendChild(wrap);
      }
    }

    row.appendChild(right);
    return row;
  }

  function buildResourceDollar(label, value) {
    var row = el("div", "fc-res-row");
    var labelEl = el("span", "fc-res-label");
    labelEl.textContent = label;
    row.appendChild(labelEl);
    var right = el("span", "fc-res-right");
    var valEl = el("span", "fc-res-value");
    valEl.textContent = (value !== null && value !== undefined) ? "$" + value.toFixed(4) : "—";
    right.appendChild(valEl);
    row.appendChild(right);
    return row;
  }

  // ── Activity panel ────────────────────────────────────────────────────────

  function renderActivity() {
    if (!activityLog.length) {
      setBody("fc-activity-body", makeEmpty("Watching for transitions…"));
      return;
    }
    setBody("fc-activity-body", activityLog.map(buildActivityItem));
  }

  function buildActivityItem(item) {
    var wrap = el("div", "fc-activity-item");

    var nameEl = el("span", "fc-activity-name");
    nameEl.textContent = truncate(item.name, 28);
    wrap.appendChild(nameEl);

    if (item.from) {
      wrap.appendChild(buildStatusBadge(item.from));
      var arr = el("span", "fc-activity-arrow");
      arr.textContent = "→";
      wrap.appendChild(arr);
    }
    wrap.appendChild(buildStatusBadge(item.to));

    var ago = el("span", "fc-activity-ago");
    ago.textContent = timeAgo(item.time);
    wrap.appendChild(ago);

    return wrap;
  }

  function buildStatusBadge(s) {
    var b = el("span", "fc-status-badge fc-status-badge--" + s);
    b.textContent = s.replace("_", " ");
    return b;
  }

  // ── Utilities ─────────────────────────────────────────────────────────────

  function truncate(str, max) {
    return str.length > max ? str.slice(0, max - 1) + "…" : str;
  }

  function timeAgo(ms) {
    var s = Math.floor((Date.now() - ms) / 1000);
    if (s < 5)    return "just now";
    if (s < 60)   return s + "s ago";
    if (s < 3600) return Math.floor(s / 60) + "m ago";
    return Math.floor(s / 3600) + "h ago";
  }

  function makeEmpty(text) {
    var d = el("div", "fc-empty");
    d.textContent = text;
    return d;
  }

  // ── Init ──────────────────────────────────────────────────────────────────

  pollTasks();
  pollStatus();
})();

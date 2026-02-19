(function () {
    "use strict";

    var container = document.getElementById("graph-container");
    var svg = d3.select("#graph-svg");
    var statsEl = document.getElementById("graph-stats");
    var wsStatusEl = document.getElementById("ws-status");
    var unavailableEl = document.getElementById("graph-unavailable");

    // Read theme colors from CSS variables
    function getThemeColor(varName, fallback) {
        return getComputedStyle(document.documentElement).getPropertyValue(varName).trim() || fallback;
    }

    // Sizing
    function getSize() {
        var rect = container.getBoundingClientRect();
        return { width: rect.width, height: rect.height };
    }

    var size = getSize();
    var width = size.width;
    var height = size.height;
    svg.attr("width", width).attr("height", height);

    // Data arrays (D3 mutates these in-place)
    var nodes = [];
    var links = [];

    // Color scale
    var color = d3.scaleOrdinal(d3.schemeTableau10);

    // SVG groups for layering (links below nodes)
    var g = svg.append("g");
    var linkGroup = g.append("g").attr("class", "links");
    var nodeGroup = g.append("g").attr("class", "nodes");

    // Arrow marker for directed edges
    svg.append("defs").append("marker")
        .attr("id", "arrowhead")
        .attr("viewBox", "0 -5 10 10")
        .attr("refX", 20)
        .attr("refY", 0)
        .attr("markerWidth", 6)
        .attr("markerHeight", 6)
        .attr("orient", "auto")
        .append("path")
        .attr("d", "M0,-5L10,0L0,5")
        .attr("fill", "var(--color-text-muted)");

    // Force simulation
    var simulation = d3.forceSimulation(nodes)
        .force("link", d3.forceLink(links).id(function (d) { return d.id; }).distance(120))
        .force("charge", d3.forceManyBody().strength(-300))
        .force("center", d3.forceCenter(width / 2, height / 2))
        .force("collision", d3.forceCollide().radius(30))
        .on("tick", ticked);

    // Zoom
    var zoom = d3.zoom()
        .scaleExtent([0.1, 4])
        .on("zoom", function (event) { g.attr("transform", event.transform); });
    svg.call(zoom);

    // Selection references
    var linkSel = linkGroup.selectAll("line");
    var nodeSel = nodeGroup.selectAll("g.node");

    // Drag behavior
    function drag(sim) {
        return d3.drag()
            .on("start", function (event, d) {
                if (!event.active) sim.alphaTarget(0.3).restart();
                d.fx = d.x;
                d.fy = d.y;
            })
            .on("drag", function (event, d) {
                d.fx = event.x;
                d.fy = event.y;
            })
            .on("end", function (event, d) {
                if (!event.active) sim.alphaTarget(0);
                d.fx = null;
                d.fy = null;
            });
    }

    function render() {
        var linkColor = getThemeColor("--color-text-muted", "#999");
        var textColor = getThemeColor("--color-text", "#333");
        var nodeStroke = getThemeColor("--color-bg", "#fff");

        // Links
        linkSel = linkGroup.selectAll("line")
            .data(links, function (d) {
                var src = typeof d.source === "object" ? d.source.id : d.source;
                var tgt = typeof d.target === "object" ? d.target.id : d.target;
                return src + "->" + tgt;
            });
        linkSel.exit().remove();
        linkSel = linkSel.enter().append("line")
            .attr("stroke", linkColor)
            .attr("stroke-opacity", 0.6)
            .attr("stroke-width", 1.5)
            .attr("marker-end", "url(#arrowhead)")
            .merge(linkSel);

        // Nodes
        nodeSel = nodeGroup.selectAll("g.node")
            .data(nodes, function (d) { return d.id; });
        nodeSel.exit().remove();

        var nodeEnter = nodeSel.enter().append("g")
            .attr("class", "node")
            .style("cursor", "pointer")
            .call(drag(simulation))
            .on("click", function (event, d) {
                window.location.href = "/page/" + encodeURIComponent(d.id);
            });

        nodeEnter.append("circle")
            .attr("r", 8)
            .attr("fill", function (d) { return color(d.id); })
            .attr("stroke", nodeStroke)
            .attr("stroke-width", 1.5);

        nodeEnter.append("text")
            .attr("dx", 12)
            .attr("dy", 4)
            .attr("font-size", "12px")
            .attr("fill", textColor)
            .text(function (d) { return d.id; });

        nodeSel = nodeEnter.merge(nodeSel);

        // Restart simulation
        simulation.nodes(nodes);
        simulation.force("link").links(links);
        simulation.alpha(0.3).restart();

        updateStats();
    }

    function ticked() {
        linkSel
            .attr("x1", function (d) { return d.source.x; })
            .attr("y1", function (d) { return d.source.y; })
            .attr("x2", function (d) { return d.target.x; })
            .attr("y2", function (d) { return d.target.y; });

        nodeSel
            .attr("transform", function (d) { return "translate(" + d.x + "," + d.y + ")"; });
    }

    function updateStats() {
        statsEl.textContent = nodes.length + " pages, " + links.length + " links";
    }

    function flashNode(name) {
        var nodeStroke = getThemeColor("--color-bg", "#fff");
        nodeGroup.selectAll("g.node")
            .filter(function (d) { return d.id === name; })
            .select("circle")
            .transition().duration(200)
            .attr("r", 14)
            .attr("stroke", "#f59e0b")
            .attr("stroke-width", 3)
            .transition().duration(600)
            .attr("r", 8)
            .attr("stroke", nodeStroke)
            .attr("stroke-width", 1.5);
    }

    // Resize handler
    window.addEventListener("resize", function () {
        var s = getSize();
        width = s.width;
        height = s.height;
        svg.attr("width", width).attr("height", height);
        simulation.force("center", d3.forceCenter(width / 2, height / 2));
        simulation.alpha(0.1).restart();
    });

    // ========== Load initial data ==========
    fetch("/api/graph")
        .then(function (r) { return r.json(); })
        .then(function (data) {
            nodes.push.apply(nodes, data.nodes);
            links.push.apply(links, data.links);
            render();
        })
        .catch(function (err) {
            console.error("Failed to load graph:", err);
            unavailableEl.style.display = "block";
        });

    // ========== WebSocket for live updates ==========
    function getLinkId(link) {
        var src = typeof link.source === "object" ? link.source.id : link.source;
        var tgt = typeof link.target === "object" ? link.target.id : link.target;
        return { source: src, target: tgt };
    }

    function handleEvent(msg) {
        switch (msg.type) {
            case "page_created":
                if (!nodes.find(function (n) { return n.id === msg.page; })) {
                    nodes.push({ id: msg.page });
                    render();
                    flashNode(msg.page);
                }
                break;

            case "page_updated":
                flashNode(msg.page);
                break;

            case "page_deleted":
                var idx = nodes.findIndex(function (n) { return n.id === msg.page; });
                if (idx !== -1) {
                    nodes.splice(idx, 1);
                    for (var i = links.length - 1; i >= 0; i--) {
                        var ids = getLinkId(links[i]);
                        if (ids.source === msg.page || ids.target === msg.page) {
                            links.splice(i, 1);
                        }
                    }
                    render();
                }
                break;

            case "link_created":
                if (!nodes.find(function (n) { return n.id === msg.from; })) {
                    nodes.push({ id: msg.from });
                }
                if (!nodes.find(function (n) { return n.id === msg.to; })) {
                    nodes.push({ id: msg.to });
                }
                links.push({ source: msg.from, target: msg.to });
                render();
                break;

            case "link_removed":
                for (var j = links.length - 1; j >= 0; j--) {
                    var lid = getLinkId(links[j]);
                    if (lid.source === msg.from && lid.target === msg.to) {
                        links.splice(j, 1);
                        break;
                    }
                }
                render();
                break;
        }
    }

    function connectWebSocket() {
        var protocol = location.protocol === "https:" ? "wss:" : "ws:";
        var ws = new WebSocket(protocol + "//" + location.host + "/ws/graph");

        ws.onopen = function () {
            wsStatusEl.textContent = "Live";
            wsStatusEl.classList.add("connected");
        };

        ws.onclose = function () {
            wsStatusEl.textContent = "Disconnected";
            wsStatusEl.classList.remove("connected");
            setTimeout(connectWebSocket, 3000);
        };

        ws.onerror = function () {
            wsStatusEl.textContent = "Error";
            wsStatusEl.classList.remove("connected");
        };

        ws.onmessage = function (event) {
            var msg = JSON.parse(event.data);
            handleEvent(msg);
        };
    }

    connectWebSocket();
})();

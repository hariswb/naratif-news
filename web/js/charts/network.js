export function drawNetworkChart(selector, data, options = { showSearched: true, excludedEntities: [] }) {
    const container = document.querySelector(selector);
    const width = container.clientWidth;
    const height = container.clientHeight || 600; // Use container height (set by CSS min-height) or fallback

    // Clear previous SVG
    d3.select(selector).selectAll("svg").remove();

    const color = d3.scaleOrdinal(d3.schemeCategory10);

    // Filter data based on options
    let nodes = data.nodes.map(d => ({ ...d })); // Deep copy to prevent mutating original data
    let links = data.links.map(d => ({ ...d }));

    // Filter excluded entities
    if (options.excludedEntities && options.excludedEntities.length > 0) {
        const excluded = new Set(options.excludedEntities.map(e => e.toLowerCase()));
        nodes = nodes.filter(n => !excluded.has(n.id.toLowerCase()));
        links = links.filter(l => !excluded.has(l.source.toLowerCase()) && !excluded.has(l.target.toLowerCase()));
    }

    if (!options.showSearched) {
        const searchedNode = nodes.find(n => n.group === "SEARCHED");
        if (searchedNode) {
            nodes = nodes.filter(n => n.id !== searchedNode.id);
            // Filter links where source or target is the searched node's ID
            links = links.filter(l => l.source !== searchedNode.id && l.target !== searchedNode.id);
        }
    }

    const svg = d3.select(selector).append("svg")
        .attr("viewBox", [0, 0, width, height])
        .attr("width", width)
        .attr("height", height)
        .style("max-width", "100%")
        .style("background", "transparent");

    // Main wrapper for zoom
    const g = svg.append("g");

    // Force simulation with central gravity
    const simulation = d3.forceSimulation(nodes)
        .force("link", d3.forceLink(links).id(d => d.id).distance(d => {
            // Note: d.source and d.target here are node objects after forceLink processes them
            const isSearched = d.source.group === "SEARCHED" || d.target.group === "SEARCHED" ||
                d.source.id === nodes.find(n => n.group === "SEARCHED")?.id ||
                d.target.id === nodes.find(n => n.group === "SEARCHED")?.id;
            return (isSearched ? 200 : 100) / Math.sqrt(d.value);
        }))
        .force("charge", d3.forceManyBody().strength(d => d.group === "SEARCHED" ? -2000 : -300))
        .force("x", d3.forceX(width / 2).strength(0.05))
        .force("y", d3.forceY(height / 2).strength(0.05))
        .force("center", d3.forceCenter(width / 2, height / 2))
        .force("collide", d3.forceCollide(d => Math.sqrt(d.count) * 2 + 15));

    // Zoom behavior
    svg.call(d3.zoom()
        .extent([[0, 0], [width, height]])
        .scaleExtent([0.1, 4])
        .on("zoom", ({ transform }) => {
            g.attr("transform", transform);
        }));

    const link = g.append("g")
        .attr("stroke", "#aaacafff")
        .attr("stroke-opacity", 0.6)
        .selectAll("line")
        .data(links)
        .join("line")
        .attr("stroke-width", d => Math.sqrt(d.value) * 1.5);

    const node = g.append("g")
        .attr("stroke", "#fff")
        .attr("stroke-width", 1.5)
        .selectAll("circle")
        .data(nodes)
        .join("circle")
        .attr("r", d => Math.sqrt(d.count) * 2 + 8)
        .attr("fill", d => d.group === "SEARCHED" ? "#105b7eff" : color(d.group))
        .style("cursor", "pointer")
        .call(drag(simulation))
        .on("click", (event, d) => {
            event.stopPropagation();
            const active = d.active = !d.active;

            // Reset all
            node.attr("stroke-width", 1.5).attr("stroke", "#fff");
            link.attr("stroke", "#414244ff").attr("stroke-opacity", 0.6);

            if (active) {
                d3.select(event.currentTarget).attr("stroke-width", 4).attr("stroke", "#0ea5e9");
                link.filter(l => l.source.id === d.id || l.target.id === d.id)
                    .attr("stroke", "#0ea5e9")
                    .attr("stroke-opacity", 1)
                    .attr("stroke-width", l => Math.sqrt(l.value) * 2.5);
            }
        });

    node.append("title")
        .text(d => `${d.id} (${d.group}) - Articles: ${d.count}`);

    const labels = g.append("g")
        .selectAll("text")
        .data(nodes)
        .join("text")
        .attr("dx", d => Math.sqrt(d.count) * 2 + 12)
        .attr("dy", ".35em")
        .text(d => d.id)
        .style("fill", "#1e293b")
        .style("font-size", "12px")
        .style("font-weight", "600")
        .style("pointer-events", "none")
        .style("text-shadow", "0 1px 4px rgba(255,255,255,0.8)");

    simulation.on("tick", () => {
        link
            .attr("x1", d => d.source.x)
            .attr("y1", d => d.source.y)
            .attr("x2", d => d.target.x)
            .attr("y2", d => d.target.y);

        node
            .attr("cx", d => d.x)
            .attr("cy", d => d.y);

        labels
            .attr("x", d => d.x)
            .attr("y", d => d.y);
    });

    // Reset highlighting on clicking background
    svg.on("click", () => {
        nodes.forEach(n => n.active = false);
        node.attr("stroke-width", 1.5).attr("stroke", "#fff");
        link.attr("stroke", "#cbd5e1").attr("stroke-opacity", 0.6).attr("stroke-width", d => Math.sqrt(d.value) * 1.5);
    });

    // Legend
    const uniqueGroups = Array.from(new Set(nodes.map(d => d.group))).sort();

    const legend = svg.append("g")
        .attr("class", "legend")
        .attr("transform", "translate(20, 20)");

    uniqueGroups.forEach((group, i) => {
        const legendRow = legend.append("g")
            .attr("transform", `translate(0, ${i * 20})`);

        legendRow.append("circle")
            .attr("r", 5)
            .attr("fill", group === "SEARCHED" ? "#0ea5e9" : color(group));

        legendRow.append("text")
            .attr("x", 15)
            .attr("y", 4)
            .style("font-size", "12px")
            .style("font-family", "sans-serif")
            .style("fill", "#64748b") // Slate-500 for better visibility on light bg
            .text(group);
    });

    function drag(simulation) {
        function dragstarted(event) {
            if (!event.active) simulation.alphaTarget(0.3).restart();
            event.subject.fx = event.subject.x;
            event.subject.fy = event.subject.y;
        }

        function dragged(event) {
            event.subject.fx = event.x;
            event.subject.fy = event.y;
        }

        function dragended(event) {
            if (!event.active) simulation.alphaTarget(0);
            event.subject.fx = null;
            event.subject.fy = null;
        }

        return d3.drag()
            .on("start", dragstarted)
            .on("drag", dragged)
            .on("end", dragended);
    }
}

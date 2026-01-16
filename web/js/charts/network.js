export function drawNetworkChart(selector, data) {
    const container = document.querySelector(selector);
    const width = container.clientWidth;
    const height = window.innerHeight * 0.8; // Fill 80% viewport height for better fit within card

    const color = d3.scaleOrdinal(d3.schemeCategory10);

    const svg = d3.select(selector).append("svg")
        .attr("viewBox", [0, 0, width, height])
        .attr("width", width)
        .attr("height", height)
        .style("max-width", "100%")
        .style("background", "transparent");

    // Main wrapper for zoom
    const g = svg.append("g");

    // Force simulation with central gravity
    const simulation = d3.forceSimulation(data.nodes)
        .force("link", d3.forceLink(data.links).id(d => d.id).distance(d => 100 / Math.sqrt(d.value)))
        .force("charge", d3.forceManyBody().strength(-300))
        .force("x", d3.forceX(width / 2).strength(0.1))
        .force("y", d3.forceY(height / 2).strength(0.1))
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
        .attr("stroke", "#475569")
        .attr("stroke-opacity", 0.4)
        .selectAll("line")
        .data(data.links)
        .join("line")
        .attr("stroke-width", d => Math.sqrt(d.value) * 1.5);

    const node = g.append("g")
        .attr("stroke", "#fff")
        .attr("stroke-width", 1.5)
        .selectAll("circle")
        .data(data.nodes)
        .join("circle")
        .attr("r", d => Math.sqrt(d.count) * 2 + 8)
        .attr("fill", d => d.group === "SEARCHED" ? "#38bdf8" : color(d.group))
        .style("cursor", "pointer")
        .call(drag(simulation))
        .on("click", (event, d) => {
            event.stopPropagation();
            const active = d.active = !d.active;

            // Reset all
            node.attr("stroke-width", 1.5).attr("stroke", "#fff");
            link.attr("stroke", "#475569").attr("stroke-opacity", 0.4);

            if (active) {
                d3.select(event.currentTarget).attr("stroke-width", 4).attr("stroke", "#38bdf8");
                link.filter(l => l.source.id === d.id || l.target.id === d.id)
                    .attr("stroke", "#38bdf8")
                    .attr("stroke-opacity", 1)
                    .attr("stroke-width", l => Math.sqrt(l.value) * 2.5);
            }
        });

    node.append("title")
        .text(d => `${d.id} (${d.group}) - Articles: ${d.count}`);

    const labels = g.append("g")
        .selectAll("text")
        .data(data.nodes)
        .join("text")
        .attr("dx", d => Math.sqrt(d.count) * 2 + 12)
        .attr("dy", ".35em")
        .text(d => d.id)
        .style("fill", "#fff")
        .style("font-size", "12px")
        .style("font-weight", "500")
        .style("pointer-events", "none")
        .style("text-shadow", "0 1px 4px rgba(0,0,0,0.8)");

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
        data.nodes.forEach(n => n.active = false);
        node.attr("stroke-width", 1.5).attr("stroke", "#fff");
        link.attr("stroke", "#475569").attr("stroke-opacity", 0.4).attr("stroke-width", d => Math.sqrt(d.value) * 1.5);
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

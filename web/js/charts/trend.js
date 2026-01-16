export function drawTrendChart(selector, data) {
    const container = document.querySelector(selector);
    const width = container.clientWidth;
    const height = container.clientHeight || 400;
    const margin = { top: 20, right: 30, bottom: 30, left: 40 };

    // 1. Pivot data
    const pivoted = {};
    const dates = new Set();

    data.forEach(d => {
        const dateKey = d.date.split('T')[0];
        dates.add(dateKey);
        if (!pivoted[dateKey]) pivoted[dateKey] = { date: new Date(dateKey), positive: 0, negative: 0, neutral: 0 };
        pivoted[dateKey][d.label.toLowerCase()] = d.count;
    });

    const chartData = Object.values(pivoted).sort((a, b) => a.date - b.date);

    // Filter out data points with 0 total counts if needed, but let's keep timeseries continuity

    // Clear previous
    d3.select(selector).innerHTML = "";

    const svg = d3.select(selector).append("svg")
        .attr("viewBox", [0, 0, width, height])
        .attr("width", width)
        .attr("height", height)
        .style("max-width", "100%")
        .style("background", "transparent");

    const x = d3.scaleTime()
        .domain(d3.extent(chartData, d => d.date))
        .range([margin.left, width - margin.right]);

    const y = d3.scaleLinear()
        .domain([0, d3.max(chartData, d => Math.max(d.positive, d.negative, d.neutral))])
        .nice()
        .range([height - margin.bottom, margin.top]);

    const color = d3.scaleOrdinal()
        .domain(["negative", "neutral", "positive"])
        .range(["#ef4444", "#94a3b8", "#22c55e"]); // Red-500, Slate-400, Green-500

    const line = d3.line()
        .x(d => x(d.date))
        .y(d => y(d.value));

    let keys = ["negative", "neutral", "positive"];

    keys.forEach(key => {
        svg.append("path")
            .datum(chartData.map(d => ({ date: d.date, value: d[key] })))
            .attr("fill", "none")
            .attr("stroke", color(key))
            .attr("stroke-width", 3)
            .attr("d", line)
            .append("title")
            .text(key);
    });

    // Axes with Bootstrap light mode colors
    svg.append("g")
        .attr("transform", `translate(0,${height - margin.bottom})`)
        .call(d3.axisBottom(x))
        .selectAll("text")
        .style("fill", "#64748b");

    svg.append("g")
        .attr("transform", `translate(${margin.left},0)`)
        .call(d3.axisLeft(y).ticks(5))
        .selectAll("text")
        .style("fill", "#64748b");

    // Axis lines
    svg.selectAll(".domain, .tick line").style("stroke", "#e2e8f0");

    // Legend
    const legend = svg.append("g")
        .attr("transform", `translate(${width - 120}, ${margin.top})`);

    // Reorder for legend
    keys = ["positive", "neutral", "negative"];
    keys.forEach((key, i) => {
        legend.append("rect")
            .attr("x", 0)
            .attr("y", i * 20)
            .attr("width", 12)
            .attr("height", 12)
            .attr("rx", 2)
            .attr("fill", color(key));

        legend.append("text")
            .attr("x", 18)
            .attr("y", i * 20 + 10)
            .text(key)
            .style("fill", "#475569")
            .style("font-size", "12px")
            .style("font-family", "sans-serif");
    });
}

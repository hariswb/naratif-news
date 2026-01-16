export function drawTrendChart(selector, data) {
    const container = document.querySelector(selector);
    const width = container.clientWidth;
    const height = container.clientHeight || 400;
    const margin = { top: 20, right: 30, bottom: 30, left: 40 };

    // Preprocess data: Group by date and label to Stack?
    // User wants "weekly trend with sentiment". 
    // We can do a stacked bar chart or a multi-line chart using "positive", "negative", "neutral" as series.
    // Let's do a Stacked Area Chart or Stacked Bar. Stacked Bar is better for counts. Area is "sexier".
    // Let's try Stacked Area.

    // 1. Pivot data
    // existing format: [{date: "...", label: "positive", count: 10}, ...]
    // needed: [{date: "...", positive: 10, negative: 5, neutral: 2}, ...]

    const pivoted = {};
    const dates = new Set();

    data.forEach(d => {
        const dateKey = d.date.split('T')[0];
        dates.add(dateKey);
        if (!pivoted[dateKey]) pivoted[dateKey] = { date: new Date(dateKey), positive: 0, negative: 0, neutral: 0 };
        pivoted[dateKey][d.label.toLowerCase()] = d.count;
    });

    const chartData = Object.values(pivoted).sort((a, b) => a.date - b.date);

    const svg = d3.select(selector).append("svg")
        .attr("viewBox", [0, 0, width, height])
        .attr("width", width)
        .attr("height", height);

    const x = d3.scaleTime()
        .domain(d3.extent(chartData, d => d.date))
        .range([margin.left, width - margin.right]);

    const y = d3.scaleLinear()
        .domain([0, d3.max(chartData, d => Math.max(d.positive, d.negative, d.neutral))])
        .nice()
        .range([height - margin.bottom, margin.top]);

    const color = d3.scaleOrdinal()
        .domain(["negative", "neutral", "positive"])
        .range(["#f87171", "#94a3b8", "#4ade80"]); // Red, Gray, Green

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

    svg.append("g")
        .attr("transform", `translate(0,${height - margin.bottom})`)
        .call(d3.axisBottom(x));

    svg.append("g")
        .attr("transform", `translate(${margin.left},0)`)
        .call(d3.axisLeft(y));

    // Legend
    const legend = svg.append("g")
        .attr("transform", `translate(${width - 150}, ${margin.top})`);

    keys = ["positive", "neutral", "negative"];
    keys.forEach((key, i) => {
        legend.append("rect")
            .attr("x", 0)
            .attr("y", i * 20)
            .attr("width", 15)
            .attr("height", 15)
            .attr("fill", color(key));

        legend.append("text")
            .attr("x", 20)
            .attr("y", i * 20 + 12)
            .text(key)
            .style("fill", "#fff")
            .style("font-size", "12px");
    });
}

import { fetchTrends, fetchPhrases, fetchNetwork } from './api.js';
import { drawTrendChart } from './charts/trend.js';
import { drawPhraseChart } from './charts/phrases.js';
import { drawNetworkChart } from './charts/network.js';

const searchBtn = document.getElementById('search-btn');
const searchInput = document.getElementById('entity-search');
const dashboard = document.getElementById('dashboard');
const loading = document.getElementById('loading');

searchBtn.addEventListener('click', handleSearch);
searchInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') handleSearch();
});

// Download buttons
document.querySelectorAll('.download-btn').forEach(btn => {
    btn.addEventListener('click', (e) => {
        const targetId = e.target.getAttribute('data-target');
        downloadChart(targetId);
    });
});

// Initialize Default Dates
const endDateInput = document.getElementById('end-date');
const startDateInput = document.getElementById('start-date');

const today = new Date();
const sevenDaysAgo = new Date();
sevenDaysAgo.setDate(today.getDate() - 7);

endDateInput.value = today.toISOString().split('T')[0];
startDateInput.value = sevenDaysAgo.toISOString().split('T')[0];

async function drawCharts(trends, phrases, network) {
    // Clear previous charts
    document.getElementById('trend-chart').innerHTML = '';
    document.getElementById('phrase-chart').innerHTML = '';
    document.getElementById('network-chart').innerHTML = '';

    if (trends && trends.length > 0) drawTrendChart('#trend-chart', trends);
    else document.getElementById('trend-chart').innerHTML = '<p class="no-data">No trend data found</p>';

    if (phrases && phrases.length > 0) {
        let currentPage = 0;
        const rowsPerPage = 10;

        const render = () => {
            drawPhraseChart('#phrase-chart', phrases, currentPage, rowsPerPage, (nextPage) => {
                currentPage = nextPage;
                render();
            });
        };
        render();
    } else {
        document.getElementById('phrase-chart').innerHTML = '<p class="no-data">No phrases found</p>';
    }

    // Exclusion Filter State
    let excludedEntities = [];

    const excludedInput = document.getElementById('exclude-entity-input');
    const pillsContainer = document.getElementById('excluded-pills');

    function updatePills() {
        pillsContainer.innerHTML = '';
        excludedEntities.forEach(entity => {
            const pill = document.createElement('div');
            pill.className = 'pill';
            pill.innerHTML = `
                <span>${entity}</span>
                <span class="pill-remove" data-entity="${entity}">×</span>
            `;
            pillsContainer.appendChild(pill);
        });

        // Add remove listeners
        document.querySelectorAll('.pill-remove').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const entityToRemove = e.target.getAttribute('data-entity');
                excludedEntities = excludedEntities.filter(e => e !== entityToRemove);
                updatePills();
                renderNetwork();
            });
        });
    }

    excludedInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            const val = excludedInput.value.trim();
            if (val && !excludedEntities.includes(val)) {
                excludedEntities.push(val);
                excludedInput.value = '';
                updatePills();
                renderNetwork();
            }
        }
    });

    function renderNetwork() {
        if (network && network.nodes.length > 1) {
            const showSearched = document.getElementById('toggle-searched-node').checked;
            drawNetworkChart('#network-chart', network, {
                showSearched,
                excludedEntities
            });
        } else {
            document.getElementById('network-chart').innerHTML = '<p class="no-data">No network data found</p>';
        }
    }
    renderNetwork();

    // Remove existing listener to prevent duplicates if drawCharts is called multiple times
    const toggle = document.getElementById('toggle-searched-node');
    const newToggle = toggle.cloneNode(true);
    toggle.parentNode.replaceChild(newToggle, toggle);

    newToggle.addEventListener('change', () => renderNetwork());
}

async function handleSearch() {
    const entity = searchInput.value.trim();
    if (!entity) return;

    // Collect Filter Values
    const startDate = startDateInput.value;
    const endDate = endDateInput.value;
    const minScore = document.getElementById('min-score').value;
    const maxScore = document.getElementById('max-score').value;
    const selectedGroups = Array.from(document.querySelectorAll('#entity-groups input:checked')).map(cb => cb.value);

    const commonParams = { start_date: startDate, end_date: endDate };
    const networkParams = { ...commonParams, min_score: minScore, max_score: maxScore, groups: selectedGroups };

    // UI State
    dashboard.classList.add('d-none'); // Bootstrap visibility
    loading.classList.remove('d-none'); // Bootstrap visibility

    try {
        // Parallel data fetching
        const [trends, phrases, network] = await Promise.all([
            fetchTrends(entity, commonParams),
            fetchPhrases(entity, commonParams),
            fetchNetwork(entity, networkParams)
        ]);

        // Render
        loading.classList.add('d-none');
        dashboard.classList.remove('d-none');

        await drawCharts(trends, phrases, network);

    } catch (err) {
        console.error(err);
        loading.classList.add('d-none');
        alert('Failed to fetch data. See console.');
    }
}

function downloadChart(elementId) {
    const container = document.getElementById(elementId);

    // For phrase table, we need a special approach or just capture SVG if it was SVG.
    // User wants PNG. If it's a table, we'd need html2canvas or similar.
    // For D3 charts (SVG), we can use canvas.
    const svg = container.querySelector('svg');
    if (svg) {
        downloadSvgAsPng(svg, `${elementId}.png`);
    } else {
        // If it's the table, maybe just skip for now or alert
        const table = container.querySelector('table');
        if (table) {
            alert('Table download as PNG requires additional libraries like html2canvas. Downloading SVG charts only for now.');
        }
    }
}

function downloadSvgAsPng(svgElement, filename) {
    const svgData = new XMLSerializer().serializeToString(svgElement);
    const canvas = document.createElement('canvas');
    const ctx = canvas.getContext('2d');
    const img = new Image();

    const svgSize = svgElement.getBoundingClientRect();
    canvas.width = svgSize.width * 2; // Better resolution
    canvas.height = svgSize.height * 2;

    img.onload = () => {
        ctx.fillStyle = '#1e293b'; // Card background color
        ctx.fillRect(0, 0, canvas.width, canvas.height);
        ctx.drawImage(img, 0, 0, canvas.width, canvas.height);
        const pngUrl = canvas.toDataURL('image/png');
        const downloadLink = document.createElement('a');
        downloadLink.href = pngUrl;
        downloadLink.download = filename;
        document.body.appendChild(downloadLink);
        downloadLink.click();
        document.body.removeChild(downloadLink);
    };

    img.src = 'data:image/svg+xml;base64,' + btoa(unescape(encodeURIComponent(svgData)));
}

// Side Panel Toggle (Desktop)
const sidePanel = document.getElementById('side-panel');
const togglePanelBtn = document.getElementById('toggle-panel-btn');
const closePanelBtnDesktop = document.getElementById('close-panel-desktop');

function togglePanel() {
    sidePanel.classList.toggle('collapsed');
}

if (togglePanelBtn) togglePanelBtn.addEventListener('click', togglePanel);
if (closePanelBtnDesktop) closePanelBtnDesktop.addEventListener('click', togglePanel);

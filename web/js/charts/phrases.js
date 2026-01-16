// Simplified visualization for phases: A styled list or "Word Cloud" style packing
// Since we want "list of dominant phrases", a horizontal bar chart or just a grid of chips is nice.
// Let's do a bubble pack or simple list. User said "List/Cloud".
// Let's do a sorted horizontal bar chart, it's easiest to read for phrases.

export function drawPhraseChart(selector, data, page = 0, rowsPerPage = 10, onPageChange) {
    const container = document.querySelector(selector);
    container.innerHTML = '';

    const start = page * rowsPerPage;
    const end = start + rowsPerPage;
    const paginatedData = data.slice(start, end);

    // Create table structure
    const table = document.createElement('table');
    table.className = 'phrases-table';

    const thead = document.createElement('thead');
    const headerRow = document.createElement('tr');
    ['Phrase', 'Count'].forEach(text => {
        const th = document.createElement('th');
        th.textContent = text;
        headerRow.appendChild(th);
    });
    thead.appendChild(headerRow);
    table.appendChild(thead);

    const tbody = document.createElement('tbody');
    paginatedData.forEach(d => {
        const tr = document.createElement('tr');
        const tdPhrase = document.createElement('td');
        tdPhrase.textContent = d.phrase;
        const tdCount = document.createElement('td');
        tdCount.textContent = d.count;
        tr.appendChild(tdPhrase);
        tr.appendChild(tdCount);
        tbody.appendChild(tr);
    });
    table.appendChild(tbody);
    container.appendChild(table);

    // Pagination Controls
    const totalPages = Math.ceil(data.length / rowsPerPage);
    if (totalPages > 1) {
        const controls = document.createElement('div');
        controls.className = 'pagination-controls';

        const prevBtn = document.createElement('button');
        prevBtn.textContent = '<';
        prevBtn.disabled = page === 0;
        prevBtn.onclick = () => onPageChange(page - 1);

        const pageInfo = document.createElement('span');
        pageInfo.textContent = `Page ${page + 1} of ${totalPages}`;

        const nextBtn = document.createElement('button');
        nextBtn.textContent = '>';
        nextBtn.disabled = page >= totalPages - 1;
        nextBtn.onclick = () => onPageChange(page + 1);

        controls.appendChild(prevBtn);
        controls.appendChild(pageInfo);
        controls.appendChild(nextBtn);
        container.appendChild(controls);
    }
}

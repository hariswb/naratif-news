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
    table.className = 'table table-hover table-borderless mb-0 align-middle w-100';
    table.style.tableLayout = 'fixed';

    const thead = document.createElement('thead');
    const headerRow = document.createElement('tr');
    ['Phrase', 'Count'].forEach(text => {
        const th = document.createElement('th');
        th.textContent = text;
        th.className = 'text-secondary text-uppercase fs-7 fw-bold ls-1 px-4 py-3 border-bottom border-dark border-opacity-10';

        if (text === 'Count') {
            th.classList.add('text-end');
            th.style.width = '100px'; // Fixed width for count
        }
        headerRow.appendChild(th);
    });
    thead.appendChild(headerRow);
    table.appendChild(thead);

    const tbody = document.createElement('tbody');
    paginatedData.forEach(d => {
        const tr = document.createElement('tr');
        const tdPhrase = document.createElement('td');
        tdPhrase.textContent = d.phrase;
        tdPhrase.className = 'text-body-emphasis fw-medium px-4 py-2 text-truncate'; // Truncate long text

        const tdCount = document.createElement('td');
        tdCount.textContent = d.count;
        tdCount.className = 'text-end font-monospace text-primary px-4 py-2';

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
        controls.className = 'd-flex justify-content-center align-items-center gap-3 mt-3 pt-2 border-top border-secondary-subtle';

        const prevBtn = document.createElement('button');
        prevBtn.innerHTML = '<i class="bi bi-chevron-left"></i>';
        prevBtn.className = 'btn btn-sm btn-outline-secondary border-0';
        prevBtn.disabled = page === 0;
        prevBtn.onclick = () => onPageChange(page - 1);

        const pageInfo = document.createElement('span');
        pageInfo.className = 'text-secondary small font-monospace';
        pageInfo.textContent = `${page + 1} / ${totalPages}`;

        const nextBtn = document.createElement('button');
        nextBtn.innerHTML = '<i class="bi bi-chevron-right"></i>';
        nextBtn.className = 'btn btn-sm btn-outline-secondary border-0';
        nextBtn.disabled = page >= totalPages - 1;
        nextBtn.onclick = () => onPageChange(page + 1);

        controls.appendChild(prevBtn);
        controls.appendChild(pageInfo);
        controls.appendChild(nextBtn);
        container.appendChild(controls);
    }
}

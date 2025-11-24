const form = document.getElementById('fact-form');
const factsEl = document.getElementById('facts');
const traceEl = document.getElementById('trace');
const statusEl = document.getElementById('status');
const clearBtn = document.getElementById('clear-btn');

function setStatus(text) {
    if (statusEl) {
        statusEl.textContent = text;
    }
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text == null ? '' : String(text);
    return div.innerHTML.replace(/"/g, '&quot;').replace(/'/g, '&#39;');
}

function renderFacts(facts) {
    if (!factsEl) return;
    if (!facts || Object.keys(facts).length === 0) {
        factsEl.innerHTML = '<p class="muted">No facts were produced.</p>';
        return;
    }

    const items = Object.entries(facts).map(([key, value]) => {
        return `
            <div class="result-card">
                <div class="result-label">${escapeHtml(key)}</div>
                <div class="result-value">${escapeHtml(JSON.stringify(value, null, 2))}</div>
            </div>
        `;
    });
    factsEl.innerHTML = items.join('');
}

function renderTrace(trace) {
    if (!traceEl) return;
    if (!trace || trace.length === 0) {
        traceEl.innerHTML = '<p class="muted">No resolvers executed.</p>';
        return;
    }
    const items = trace.map(
        (step) => `<li><span class="badge">${escapeHtml(step.name)}</span> &mdash; ${escapeHtml(step.description || 'completed')}</li>`,
    );
    traceEl.innerHTML = `<ul class="trace-list">${items.join('')}</ul>`;
}

function deriveColumns(rows, preferred = []) {
    const columnSet = new Set(preferred);
    rows.forEach((row) => {
        if (row && typeof row === 'object') {
            Object.keys(row).forEach((key) => columnSet.add(key));
        }
    });
    return Array.from(columnSet);
}

function syncRows(field, rows) {
    const textarea = field.querySelector('textarea[data-table-rows]');
    field.__tableRows = rows;
    if (textarea) {
        textarea.value = rows.length ? JSON.stringify(rows, null, 2) : '';
    }
    updateTablePreview(field, rows);
    renderTableEditor(field, rows);
}

function parseRowsFromTextarea(field) {
    const textarea = field.querySelector('textarea[data-table-rows]');
    if (!textarea) return [];
    const raw = textarea.value.trim();
    if (!raw) return [];
    const parsed = JSON.parse(raw);
    if (!Array.isArray(parsed)) {
        throw new Error('Rows must be an array of objects.');
    }
    return parsed;
}

function parseTableField(field) {
    if (field.__tableRows && Array.isArray(field.__tableRows)) {
        return field.__tableRows;
    }
    const textarea = field.querySelector('textarea[data-table-rows]');
    if (!textarea) {
        return undefined;
    }
    const raw = textarea.value.trim();
    if (!raw) {
        return undefined;
    }
    try {
        return parseRowsFromTextarea(field);
    } catch (error) {
        const preview = field.querySelector('[data-preview]');
        if (preview) {
            preview.innerHTML = `<p class="error">${escapeHtml(error.message)}</p>`;
        }
        setStatus('Invalid relation input');
        throw error;
    }
}

function updateTablePreview(field, rows = []) {
    const preview = field.querySelector('[data-preview]');
    if (!preview) return;

    if (!rows || rows.length === 0) {
        preview.innerHTML = '<p class="muted">No rows added yet.</p>';
        return;
    }

    try {
        const columns = deriveColumns(rows);
        if (columns.length === 0) {
            preview.innerHTML = '<p class="muted">Add at least one column to preview the relation.</p>';
            return;
        }

        const header = columns.map((col) => `<th>${escapeHtml(col)}</th>`).join('');
        const body = rows
            .map((row) => {
                const cells = columns.map((col) => `<td>${escapeHtml(row?.[col] ?? '')}</td>`).join('');
                return `<tr>${cells}</tr>`;
            })
            .join('');

        preview.innerHTML = `<table class="data-table"><thead><tr>${header}</tr></thead><tbody>${body}</tbody></table>`;
    } catch (error) {
        preview.innerHTML = `<p class="error">${escapeHtml(error.message)}</p>`;
    }
}

function renderTableEditor(field, rows = []) {
    const editor = field.querySelector('[data-table-editor]');
    const columnList = field.querySelector('[data-column-list]');
    if (!editor || !columnList) return;

    const columns = deriveColumns(rows, field.__tableColumns || []);
    field.__tableColumns = columns;

    columnList.innerHTML =
        columns.length === 0
            ? '<span class="muted">No columns yet</span>'
            : columns.map((col) => `<span class="chip">${escapeHtml(col)}</span>`).join('');

    if (columns.length === 0) {
        editor.innerHTML = '<p class="muted">Add a column to start entering rows.</p>';
        return;
    }

    const header = columns.map((col) => `<th>${escapeHtml(col)}</th>`).join('');
    const body = rows
        .map((row, rowIndex) => {
            const cells = columns
                .map((col) => {
                    const value = row?.[col] ?? '';
                    return `<td><input type="text" data-row="${rowIndex}" data-column="${escapeHtml(col)}" value="${escapeHtml(
                        value,
                    )}" /></td>`;
                })
                .join('');
            return `<tr>${cells}<td class="row-actions"><button type="button" class="ghost compact" data-remove-row="${rowIndex}">Remove</button></td></tr>`;
        })
        .join('');

    editor.innerHTML = `<table class="data-table editable"><thead><tr>${header}<th></th></tr></thead><tbody>${body}</tbody></table>`;

    editor.querySelectorAll('input[data-row]').forEach((input) => {
        input.addEventListener('input', (event) => {
            const rowIndex = Number(event.target.getAttribute('data-row'));
            const column = event.target.getAttribute('data-column');
            const nextRows = rows.map((row, idx) => {
                if (idx !== rowIndex) return row;
                return { ...row, [column]: event.target.value };
            });
            syncRows(field, nextRows);
        });
    });

    editor.querySelectorAll('button[data-remove-row]').forEach((btn) => {
        btn.addEventListener('click', (event) => {
            const rowIndex = Number(event.target.getAttribute('data-remove-row'));
            const nextRows = rows.filter((_, idx) => idx !== rowIndex);
            syncRows(field, nextRows);
        });
    });
}

function hydrateTableFields() {
    document.querySelectorAll('[data-input-type="table"]').forEach((field) => {
        const sample = field.dataset.sample ? JSON.parse(field.dataset.sample) : [];
        const textarea = field.querySelector('textarea[data-table-rows]');
        const sampleBtn = field.querySelector('[data-fill-sample]');
        const addColumnBtn = field.querySelector('[data-add-column]');
        const addRowBtn = field.querySelector('[data-add-row]');
        const newColumnInput = field.querySelector('input[data-new-column]');

        const initialRows = textarea?.value.trim()
            ? parseTableField(field) || []
            : sample.length
              ? sample
              : [];
        syncRows(field, initialRows);

        if (textarea) {
            textarea.placeholder = textarea.placeholder || (sample.length ? JSON.stringify(sample, null, 2) : '');
            textarea.addEventListener('input', () => {
                try {
                    const parsed = parseRowsFromTextarea(field);
                    syncRows(field, parsed);
                } catch (error) {
                    const preview = field.querySelector('[data-preview]');
                    if (preview) {
                        preview.innerHTML = `<p class="error">${escapeHtml(error.message)}</p>`;
                    }
                }
            });
        }

        if (sampleBtn) {
            sampleBtn.addEventListener('click', () => {
                syncRows(field, sample);
            });
        }

        if (addColumnBtn && newColumnInput) {
            addColumnBtn.addEventListener('click', () => {
                const name = newColumnInput.value.trim();
                if (!name) return;
                const rows = field.__tableRows || [];
                const columns = deriveColumns(rows, field.__tableColumns || []);
                if (!columns.includes(name)) {
                    columns.push(name);
                }
                field.__tableColumns = columns;
                const nextRows = rows.map((row) => ({ ...row, [name]: row?.[name] ?? '' }));
                newColumnInput.value = '';
                syncRows(field, nextRows.length ? nextRows : [{}]);
            });
        }

        if (addRowBtn) {
            addRowBtn.addEventListener('click', () => {
                const columns = field.__tableColumns || deriveColumns(field.__tableRows || []);
                const blankRow = columns.reduce((row, col) => ({ ...row, [col]: '' }), {});
                const rows = [...(field.__tableRows || []), blankRow];
                syncRows(field, rows);
            });
        }
    });
}

form?.addEventListener('submit', async (event) => {
    event.preventDefault();
    setStatus('Running...');

    const inputs = {};
    try {
        document.querySelectorAll('[data-fact-id]').forEach((field) => {
            const factId = field.getAttribute('data-fact-id');
            const inputType = field.getAttribute('data-input-type');
            if (!factId) return;

            if (inputType === 'table') {
                const rows = parseTableField(field);
                if (rows && rows.length) {
                    inputs[factId] = rows;
                }
                return;
            }

            const inputEl = field.querySelector('input');
            if (inputEl && inputEl.value.trim() !== '') {
                inputs[inputEl.name] = inputEl.value.trim();
            }
        });
    } catch (error) {
        return;
    }

    try {
        const response = await fetch('/api/run', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ inputs, required_facts: [] }),
        });

        if (!response.ok) {
            throw new Error(`Request failed: ${response.status}`);
        }

        const payload = await response.json();
        renderFacts(payload.facts);
        renderTrace(payload.trace);
        setStatus('Completed');
    } catch (error) {
        console.error(error);
        factsEl.innerHTML = `<p class="muted">${escapeHtml(error.message || 'Unable to run planner.')}</p>`;
        traceEl.innerHTML = '<p class="muted">No trace available.</p>';
        setStatus('Error');
    }
});

clearBtn?.addEventListener('click', () => {
    document.querySelectorAll('[data-fact-id] input').forEach((input) => (input.value = ''));
    document.querySelectorAll('[data-input-type="table"]').forEach((field) => {
        syncRows(field, []);
    });
    if (factsEl) {
        factsEl.innerHTML = '<p class="muted">Cleared. Run the planner to see results.</p>';
    }
    if (traceEl) {
        traceEl.innerHTML = '<p class="muted">Waiting for next execution.</p>';
    }
    setStatus('Idle');
});

hydrateTableFields();

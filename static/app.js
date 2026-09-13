let currentMode = 'student';

const ROUTE_LABELS = {
    'faculty_rag': 'Faculty Matching',
    'project': 'Project Suggestions',
    'collaboration': 'Interdisciplinary Collaboration',
    'web_search': 'Web Research Search'
};

function switchTab(mode) {
    currentMode = mode;
    const tabStudent = document.getElementById('tabStudent');
    const tabProfessor = document.getElementById('tabProfessor');
    const studentView = document.getElementById('studentView');
    const professorView = document.getElementById('professorView');
    const resultsContainer = document.getElementById('resultsContainer');

    resultsContainer.innerHTML = '';

    if (mode === 'student') {
        tabStudent.classList.add('active');
        tabProfessor.classList.remove('active');
        studentView.style.display = 'block';
        professorView.style.display = 'none';
    } else {
        tabProfessor.classList.add('active');
        tabStudent.classList.remove('active');
        professorView.style.display = 'block';
        studentView.style.display = 'none';
    }
}

function handleKeyPress(event, mode) {
    if (event.key === 'Enter') {
        if (mode === 'student') submitStudentQuery();
        else submitProfessorQuery();
    }
}

function usePrompt(text, mode) {
    if (mode === 'student') {
        document.getElementById('studentInput').value = text;
        submitStudentQuery();
    } else {
        document.getElementById('professorInput').value = text;
        submitProfessorQuery();
    }
}

function showLoading(show, message = 'Processing query...') {
    const spinner = document.getElementById('loadingSpinner');
    const loadingText = document.getElementById('loadingText');
    loadingText.innerText = message;
    spinner.style.display = show ? 'block' : 'none';
}

function showToast(message) {
    const toast = document.getElementById('toastMessage');
    toast.innerText = message;
    toast.style.display = 'block';
    setTimeout(() => {
        toast.style.display = 'none';
    }, 3500);
}

async function submitStudentQuery() {
    const input = document.getElementById('studentInput');
    const query = input.value.trim();
    if (!query) return;

    const resultsContainer = document.getElementById('resultsContainer');
    resultsContainer.innerHTML = '';
    showLoading(true, 'Matching faculty & generating insights...');

    try {
        const response = await fetch('/api/student', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ query })
        });

        if (!response.ok) {
            throw new Error('Failed to process request');
        }

        const data = await response.json();
        renderStudentResults(data);
    } catch (err) {
        resultsContainer.innerHTML = `
            <div class="content-card" style="border-left: 4px solid var(--vignan-red);">
                <div class="card-heading" style="color: var(--vignan-red);">Error</div>
                <div>An error occurred while connecting to the backend server. Please try again.</div>
            </div>
        `;
    } finally {
        showLoading(false);
    }
}

async function submitProfessorQuery() {
    const input = document.getElementById('professorInput');
    const query = input.value.trim();
    if (!query) return;

    const resultsContainer = document.getElementById('resultsContainer');
    resultsContainer.innerHTML = '';
    showLoading(true, 'Synthesizing research directions...');

    try {
        const response = await fetch('/api/professor', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ query })
        });

        if (!response.ok) {
            throw new Error('Failed to process request');
        }

        const data = await response.json();
        renderProfessorResults(data.response);
    } catch (err) {
        resultsContainer.innerHTML = `
            <div class="content-card" style="border-left: 4px solid var(--vignan-red);">
                <div class="card-heading" style="color: var(--vignan-red);">Error</div>
                <div>An error occurred while connecting to the backend server. Please try again.</div>
            </div>
        `;
    } finally {
        showLoading(false);
    }
}

function renderStudentResults(data) {
    const container = document.getElementById('resultsContainer');
    const route = data.route;
    const routeLabel = ROUTE_LABELS[route] || route;

    let html = `<div class="route-badge">Target Route: ${routeLabel}</div>`;

    if (route === 'faculty_rag' || route === 'project') {
        const matches = data.matches || [];
        if (matches.length === 0) {
            html += `
                <div class="content-card">
                    <div class="card-heading">No Faculty Matches Found</div>
                    <p>No matching faculty members were found. Try clicking <b>🔄 Sync Database</b> in the top right.</p>
                </div>
            `;
        } else {
            const junkKeywords = ["file:/", "http:/", "https:/", ".pdf", ".doc", "downloads/", "h index", "i-10", "citations", "ph.d", "sanctioned", "rs.", "patent", "dst-seed", "a.p."];
            const isJunkTag = (t) => {
                const l = t.toLowerCase();
                return junkKeywords.some(k => l.includes(k)) || /^\d+(\s*(rs|publications|phd|citations))?$/i.test(l) || t.length > 80;
            };

            matches.forEach(faculty => {
                const pubs = faculty.publications && faculty.publications !== 'N/A' ? faculty.publications : 'None listed';
                const mobile = faculty.mobile_number && faculty.mobile_number !== 'N/A' ? faculty.mobile_number : null;
                const areaList = faculty.research_areas
                    ? faculty.research_areas.split(',')
                        .map(a => a.trim())
                        .filter(a => a.length > 2 && !isJunkTag(a))
                    : [];
                const areas = areaList.map(a => `<span class="tag">${a}</span>`).join(' ');

                html += `
                    <div class="faculty-card">
                        <div class="faculty-header">
                            <div class="faculty-name">Prof. ${faculty.name}</div>
                            <div class="match-score">${faculty.score}% Match</div>
                        </div>
                        <div class="faculty-info-grid">
                            <div class="info-item"><span class="info-label">Department:</span> ${faculty.department}</div>
                            ${mobile ? `<div class="info-item"><span class="info-label">Contact:</span> ${mobile}</div>` : ''}
                        </div>
                        <div style="margin-bottom: 10px;">
                            <span class="info-label">Research Areas:</span>
                            <div class="tag-list">${areas || '<span style="color:#666;font-size:0.9em;">General Research</span>'}</div>
                        </div>
                        <div class="pubs-box">
                            <strong>Matching Publications:</strong> ${pubs}
                        </div>
                    </div>
                `;
            });

        }

        if (route === 'project' && data.project_suggestions) {
            html += `
                <div class="content-card" style="margin-top: 10px;">
                    <div class="card-heading">💡 Suggested Research Projects</div>
                    <div class="formatted-text">${formatMarkdownText(data.project_suggestions)}</div>
                </div>
            `;
        }
    } else {
        html += `
            <div class="content-card">
                <div class="card-heading">${routeLabel} Insights</div>
                <div class="formatted-text">${formatMarkdownText(data.response)}</div>
            </div>
        `;
    }

    container.innerHTML = html;
}

function renderProfessorResults(text) {
    const container = document.getElementById('resultsContainer');
    container.innerHTML = `
        <div class="content-card">
            <div class="card-heading"> Strategic Research Analysis</div>
            <div class="formatted-text">${formatMarkdownText(text)}</div>
        </div>
    `;
}

function formatMarkdownText(text) {
    if (!text) return '';
    return text
        .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
        .replace(/\*(.*?)\*/g, '<em>$1</em>')
        .replace(/^### (.*$)/gim, '<h3 style="color:var(--vignan-blue-dark);margin:14px 0 6px;">$1</h3>')
        .replace(/^## (.*$)/gim, '<h2 style="color:var(--vignan-blue-dark);margin:16px 0 8px;">$1</h2>')
        .replace(/^# (.*$)/gim, '<h1 style="color:var(--vignan-blue-dark);margin:18px 0 10px;">$1</h1>')
        .replace(/^\* (.*$)/gim, '• $1');
}

async function reloadData() {
    showToast('Reloading database...');
    try {
        const res = await fetch('/api/reload', { method: 'POST' });
        const data = await res.json();
        showToast('Database reloaded successfully!');
    } catch (e) {
        showToast('Error reloading database');
    }
}

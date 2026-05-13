const API_URL = window.location.origin;

document.getElementById('course-form').addEventListener('submit', async (e) => {
    e.preventDefault();

    const btn = document.getElementById('generate-btn');
    const btnText = btn.querySelector('.btn-text');
    const loader = document.getElementById('btn-loader');

    // Prepare payload
    const payload = {
        topic: document.getElementById('topic').value.trim(),
        skill_level: document.getElementById('skill_level').value,
        hours_per_week: parseInt(document.getElementById('hours_per_week').value),
        learning_style: document.getElementById('learning_style').value,
        goal: document.getElementById('goal').value.trim()
    };

    // Basic client-side validation
    if (!payload.topic || !payload.goal || isNaN(payload.hours_per_week)) {
        alert('Please fill out all required fields (Topic and Learning Goal).');
        return;
    }

    // UI Loading state
    btn.disabled = true;
    btnText.textContent = 'Generating AI Roadmap...';
    loader.classList.remove('hidden');

    let success = false;

    try {
        const response = await fetch(`${API_URL}/generate-course`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });

        if (!response.ok) {
            const errText = await response.text();
            throw new Error(`Server error ${response.status}: ${errText}`);
        }

        const data = await response.json();
        console.log('[generate-course] response', data);

        // Validate response shape
        if (!data || !data.course) {
            throw new Error('Invalid response from server: missing course object.');
        }
        if (!Array.isArray(data.course.modules)) {
            throw new Error('Invalid response from server: modules array missing.');
        }

        // Render roadmap
        renderRoadmap(data.course, data.id);

        // Show/hide fallback warning
        const warning = document.getElementById('fallback-warning');
        const warningText = warning.querySelector('.warning-text');

        // Reset all warning state classes first
        warning.classList.remove('hidden', 'curated-warning', 'generic-warning');

        if (data.is_fallback) {
            if (data.fallback_type === 'curated') {
                warning.classList.add('curated-warning');
                warningText.innerHTML = `<strong>Expert-Curated Roadmap</strong> We've surfaced a high-quality, professional roadmap for <strong>${payload.topic}</strong>. These paths are designed by experts and highly recommended for your profile.`;
            } else {
                warning.classList.add('generic-warning');
                warningText.innerHTML = `<strong>AI Capacity reached.</strong> We're currently using a structured roadmap template. For a fully custom AI-generated path, please check back in a few minutes.`;
            }
        } else {
            warning.classList.add('hidden');
        }

        success = true;

    } catch (error) {
        console.error('[generate-course] error:', error);
        alert(`An error occurred: ${error.message}\n\nPlease ensure the backend is running on port 8000 and your Gemini API key is configured correctly.`);
    } finally {
        // Reset button state
        btn.disabled = false;
        btnText.textContent = 'Generate Roadmap';
        loader.classList.add('hidden');
    }

    // Only swap sections if everything succeeded (done outside try/finally to avoid race)
    if (success) {
        document.getElementById('input-section').classList.add('hidden');
        document.getElementById('output-section').classList.remove('hidden');
        window.scrollTo({ top: 0, behavior: 'smooth' });
    }
});

let currentCourseJson = null;
let currentCourseId = null;

function renderRoadmap(course, id) {
    currentCourseJson = course;
    currentCourseId = id;

    document.getElementById('course-title').textContent = course.course_title;
    document.getElementById('course-overview').textContent = course.overview;
    document.getElementById('course-duration').textContent = `Est. Duration: ${course.estimated_duration}`;

    const container = document.getElementById('modules-container');
    container.innerHTML = '';

    course.modules.forEach(mod => {
        const card = document.createElement('div');
        card.className = 'module-card';
        card.id = `module-${mod.module_number}`;

        card.innerHTML = `
            <div class="module-header">
                <div class="module-title-wrap" onclick="this.parentElement.parentElement.classList.toggle('open')">
                    <div class="module-num">${mod.module_number}</div>
                    <div class="module-title">${mod.title}</div>
                </div>
                <div class="module-meta">
                    <div class="module-duration">${mod.duration}</div>
                    <label class="progress-checkbox">
                        <input type="checkbox" onchange="toggleComplete(this, '${card.id}')">
                        <span class="checkmark"></span>
                    </label>
                </div>
            </div>
            <div class="module-content">
                <div class="module-section">
                    <h4>Objectives</h4>
                    <ul>${mod.objectives.map(o => `<li>${o}</li>`).join('')}</ul>
                </div>
                <div class="module-section">
                    <h4>Topics</h4>
                    <ul>${mod.topics.map(t => `<li>${t}</li>`).join('')}</ul>
                </div>
                <div class="module-section visual-aid-section">
                    <h4>Visual Guide</h4>
                    <div class="visual-placeholder">
                        <div class="visual-content"></div>
                    </div>
                </div>
                ${mod.mini_project ? `
                <div class="module-section">
                    <h4>Mini Project</h4>
                    <p>${mod.mini_project}</p>
                </div>` : ''}
                <div class="module-section">
                    <h4>Resources & Exercises</h4>
                    <ul>
                        ${mod.resources.map(r => `<li>${r}</li>`).join('')}
                        <li><strong>Exercise:</strong> ${mod.exercise}</li>
                    </ul>
                </div>
            </div>
        `;
        container.appendChild(card);
        // Expand module so visual guides are visible by default
        card.classList.add('open');
        // Always render a visual: prefer external image URLs (non-temp), otherwise render generated SVG flowchart
        {
            const visualHolder = card.querySelector('.visual-content');
            const aid = (mod.visual_aid || '').toString().trim();
            const isExternalImage = /^(https?:\/\/|\/|data:)/i.test(aid) && !aid.startsWith('/visual/temp/');
            visualHolder.innerHTML = '';

            // If this is a temporary server-side visual, fetch it and render inline
            if (aid && aid.startsWith('/visual/temp/')) {
                (async () => {
                    try {
                        const r = await fetch(aid);
                        if (!r.ok) throw new Error('Visual fetch failed');
                        const ct = r.headers.get('Content-Type') || '';
                        const text = await r.text();
                        if (ct.includes('image/svg') || text.trim().startsWith('<svg')) {
                            // Insert raw SVG markup so it renders inline
                            visualHolder.innerHTML = text;
                            // Create downloadable blob URL
                            const blob = new Blob([text], { type: 'image/svg+xml' });
                            const url = URL.createObjectURL(blob);
                            const dl = document.createElement('a');
                            dl.className = 'visual-download-btn';
                            dl.textContent = 'Download';
                            dl.href = url;
                            dl.setAttribute('download', `${(course.course_title||'visual').replace(/\s+/g,'_')}_module_${mod.module_number}.svg`);
                            visualHolder.appendChild(dl);
                        } else {
                            // fallback: generate our own SVG
                            const svg = createFlowchartSVG(mod.topics || []);
                            visualHolder.appendChild(svg);
                        }
                    } catch (e) {
                        const svg = createFlowchartSVG(mod.topics || []);
                        visualHolder.appendChild(svg);
                    }
                })();
                return;
            }

            if (isExternalImage) {
                const img = document.createElement('img');
                img.src = aid;
                img.alt = `Visual aid for ${mod.title}`;
                img.className = 'module-visual-img';
                visualHolder.appendChild(img);
                const dl = document.createElement('a');
                dl.className = 'visual-download-btn';
                dl.textContent = 'Download';
                dl.href = img.src;
                dl.setAttribute('download', `${(course.course_title||'visual').replace(/\s+/g,'_')}_module_${mod.module_number}.svg`);
                visualHolder.appendChild(dl);
            } else {
                const svg = createFlowchartSVG(mod.topics || []);
                visualHolder.appendChild(svg);
                const dlSvg = document.createElement('a');
                dlSvg.className = 'visual-download-btn';
                dlSvg.textContent = 'Download';
                try {
                    const serializer = new XMLSerializer();
                    const s = serializer.serializeToString(svg);
                    const url = 'data:image/svg+xml;charset=utf-8,' + encodeURIComponent(s);
                    dlSvg.href = url;
                    dlSvg.setAttribute('download', `${(course.course_title||'visual').replace(/\s+/g,'_')}_module_${mod.module_number}.svg`);
                } catch (e) {
                    dlSvg.href = '#';
                    dlSvg.onclick = (ev) => { ev.preventDefault(); alert('Download not available'); };
                }
                visualHolder.appendChild(dlSvg);
            }
        }
    });

    function createFlowchartSVG(topics) {
        const ns = 'http://www.w3.org/2000/svg';
        const padding = 20;
        const boxH = 48;
        const spacing = 18;

        // Heuristic: horizontal layout if <=3 topics, else vertical
        const horizontal = topics.length <= 3;
        const boxW = 220;
        const width = horizontal
            ? Math.max(420, padding * 2 + topics.length * (boxW + spacing))
            : Math.max(420, padding * 2 + boxW + spacing * 2);
        const height = horizontal
            ? Math.max(140, padding * 2 + boxH + spacing * 2)
            : Math.max(140, padding * 2 + topics.length * (boxH + spacing));

        const svg = document.createElementNS(ns, 'svg');
        svg.setAttribute('width', width);
        svg.setAttribute('height', height);
        svg.setAttribute('viewBox', `0 0 ${width} ${height}`);
        svg.classList.add('module-visual-svg');

        // small keyword -> emoji mapping to give concept hints
        const iconMap = {
            'function': '⚙️', 'functions': '⚙️', 'list': '📋', 'lists': '📋', 'dict': '🗂️', 'dictionary': '🗂️',
            'file': '📁', 'files': '📁', 'api': '🔗', 'data': '📊', 'oop': '🏗️', 'object': '🏗️', 'loop': '🔁',
            'syntax': '✍️', 'project': '🛠️', 'algorithm': '🧠', 'model': '🧩', 'network': '🌐'
        };

        function pickIcon(text) {
            const t = (text || '').toLowerCase();
            for (const k in iconMap) if (t.includes(k)) return iconMap[k];
            return '🔹';
        }

        // draw boxes and connectors
        topics.forEach((t, i) => {
            const label = t || '';
            const icon = pickIcon(label);
            let x, y;
            if (horizontal) {
                x = padding + i * (boxW + spacing);
                y = padding;
            } else {
                x = padding;
                y = padding + i * (boxH + spacing);
            }

            // connector from previous
            if (i > 0) {
                const line = document.createElementNS(ns, 'line');
                if (horizontal) {
                    line.setAttribute('x1', x - spacing / 2);
                    line.setAttribute('y1', y + boxH / 2);
                    line.setAttribute('x2', x);
                    line.setAttribute('y2', y + boxH / 2);
                } else {
                    line.setAttribute('x1', x + boxW / 2);
                    line.setAttribute('y1', y - spacing / 2);
                    line.setAttribute('x2', x + boxW / 2);
                    line.setAttribute('y2', y);
                }
                line.setAttribute('stroke', '#cbd5e1');
                line.setAttribute('stroke-width', '2');
                svg.appendChild(line);

                // arrowhead
                if (horizontal) {
                    const ax = x - 6; const ay = y + boxH / 2;
                    const poly = document.createElementNS(ns, 'polygon');
                    poly.setAttribute('points', `${ax},${ay-6} ${ax+6},${ay} ${ax},${ay+6}`);
                    poly.setAttribute('fill', '#cbd5e1');
                    svg.appendChild(poly);
                } else {
                    const ax = x + boxW / 2; const ay = y - 6;
                    const poly = document.createElementNS(ns, 'polygon');
                    poly.setAttribute('points', `${ax-6},${ay} ${ax+6},${ay} ${ax},${ay+6}`);
                    poly.setAttribute('fill', '#cbd5e1');
                    svg.appendChild(poly);
                }
            }

            const rect = document.createElementNS(ns, 'rect');
            rect.setAttribute('x', x);
            rect.setAttribute('y', y);
            rect.setAttribute('rx', 8);
            rect.setAttribute('ry', 8);
            rect.setAttribute('width', boxW);
            rect.setAttribute('height', boxH);
            rect.setAttribute('fill', '#ffffff');
            rect.setAttribute('stroke', '#94a3b8');
            rect.setAttribute('stroke-width', '1.5');
            svg.appendChild(rect);

            // icon (emoji) on left
            const iconText = document.createElementNS(ns, 'text');
            iconText.setAttribute('x', x + 12);
            iconText.setAttribute('y', y + boxH / 2 + 6);
            iconText.setAttribute('font-size', '18');
            iconText.setAttribute('fill', '#0f172a');
            iconText.textContent = icon;
            svg.appendChild(iconText);

            // main label
            const text = document.createElementNS(ns, 'text');
            text.setAttribute('x', x + 40);
            text.setAttribute('y', y + boxH / 2 + 6);
            text.setAttribute('fill', '#0f172a');
            text.setAttribute('font-size', '13');
            text.setAttribute('font-family', 'Inter, Arial, sans-serif');
            const short = label.length > 50 ? label.slice(0, 47) + '...' : label;
            text.textContent = short;
            svg.appendChild(text);
        });

        return svg;
    }
}
function toggleComplete(checkbox, cardId) {
    const card = document.getElementById(cardId);
    if (checkbox.checked) {
        card.classList.add('completed');
    } else {
        card.classList.remove('completed');
    }
}

document.getElementById('start-over').addEventListener('click', () => {
    document.getElementById('output-section').classList.add('hidden');
    document.getElementById('input-section').classList.remove('hidden');
    loadRecentCourses(); // Refresh history when going back
});

document.getElementById('download-json').addEventListener('click', () => {
    if (!currentCourseJson) return;
    const dataStr = "data:text/json;charset=utf-8," + encodeURIComponent(JSON.stringify(currentCourseJson, null, 2));
    const dlAnchorElem = document.createElement('a');
    dlAnchorElem.setAttribute("href", dataStr);
    dlAnchorElem.setAttribute("download", "roadmap.json");
    dlAnchorElem.click();
});

document.getElementById('download-pdf').addEventListener('click', async () => {
    if (!currentCourseId) return alert('Cannot download PDF without saving course first.');

    const btn = document.getElementById('download-pdf');
    const originalText = btn.textContent;
    btn.disabled = true;
    btn.textContent = 'Preparing PDF...';

    try {
        const response = await fetch(`${API_URL}/export/pdf/${currentCourseId}`);
        if (!response.ok) throw new Error('PDF generation failed');

        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `roadmap_${currentCourseId}.pdf`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
    } catch (err) {
        alert('Failed to download PDF: ' + err.message);
    } finally {
        btn.disabled = false;
        btn.textContent = originalText;
    }
});

// History Logic
async function loadRecentCourses() {
    try {
        const response = await fetch(`${API_URL}/recent-courses`);
        if (!response.ok) return;
        const courses = await response.json();

        const section = document.getElementById('recent-courses-section');
        const list = document.getElementById('recent-courses-list');

        if (courses.length === 0) {
            section.classList.add('hidden');
            return;
        }

        section.classList.remove('hidden');
        list.innerHTML = '';

        courses.forEach(c => {
            const date = new Date(c.created_at).toLocaleDateString(undefined, {
                month: 'short',
                day: 'numeric'
            });

            const card = document.createElement('div');
            card.className = 'recent-course-card';
            card.innerHTML = `
                <div class="topic-tag">${c.topic}</div>
                <div class="course-title">${c.course_title}</div>
                <div class="date">${date}</div>
            `;

            card.addEventListener('click', () => loadCourseDetails(c.id));
            list.appendChild(card);
        });
    } catch (err) {
        console.error("Error loading history:", err);
    }
}

async function loadCourseDetails(id) {
    try {
        const response = await fetch(`${API_URL}/course/${id}`);
        if (!response.ok) throw new Error("Failed to fetch course details");
        const data = await response.json();

        renderRoadmap(data.course, data.id);

        // Hide warning for history items
        document.getElementById('fallback-warning').classList.add('hidden');

        document.getElementById('input-section').classList.add('hidden');
        document.getElementById('output-section').classList.remove('hidden');
        window.scrollTo({ top: 0, behavior: 'smooth' });
    } catch (err) {
        alert("Error loading roadmap: " + err.message);
    }
}

document.getElementById('share-roadmap').addEventListener('click', () => {
    if (!currentCourseJson) return;
    const shareText = `Check out my personalized learning roadmap for ${currentCourseJson.course_title} created with Pathweaver AI!`;
    const shareUrl = window.location.href; // In a real app, this would be a deep link to the course ID

    if (navigator.share) {
        navigator.share({
            title: currentCourseJson.course_title,
            text: shareText,
            url: shareUrl
        }).catch(err => console.error('Error sharing:', err));
    } else {
        // Fallback to copy to clipboard
        const fullText = `${shareText}\n${shareUrl}`;
        navigator.clipboard.writeText(fullText).then(() => {
            const btn = document.getElementById('share-roadmap');
            const originalText = btn.textContent;
            btn.textContent = 'Link Copied!';
            setTimeout(() => btn.textContent = originalText, 2000);
        });
    }
});

// Initial Load
window.addEventListener('DOMContentLoaded', loadRecentCourses);

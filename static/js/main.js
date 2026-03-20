// Auto-detect which backend to use:
//   • localhost / 127.0.0.1  → relative URL (Flask dev server handles it)
//   • any other host (Vercel) → absolute Render.com URL
const API_BASE = (window.location.hostname === 'localhost' ||
                  window.location.hostname === '127.0.0.1')
    ? ''
    : 'https://tomato-disease-web-2hwc.onrender.com';

// ── Server health ping ────────────────────────────────────────────────────────
// Fires immediately on script load (before DOMContentLoaded so the request
// is in-flight as early as possible). Also warms up Render's free-tier dyno.
function showStatus(msg, ok) {
    const el = document.getElementById('serverStatus');
    if (!el) return;
    if (ok) {
        el.style.background = '#dcfce7';
        el.style.color      = '#166534';
    } else {
        el.style.background = '#fff7ed';
        el.style.color      = '#9a3412';
    }
    el.innerHTML = msg;
}

// Use a 10s timeout for the health probe so it doesn't hang forever
const _hc = new AbortController();
const _hcTimer = setTimeout(() => _hc.abort(), 10000);
fetch(API_BASE + '/health', { signal: _hc.signal })
    .then(r => r.json())
    .then(data => {
        clearTimeout(_hcTimer);
        if (data.status === 'ok') {
            showStatus('Server ready &#x2705;', true);
        } else {
            showStatus('Server responded but may be busy &#x26A0;&#xFE0F;', false);
        }
    })
    .catch(err => {
        clearTimeout(_hcTimer);
        if (err.name === 'AbortError') {
            showStatus('Server warming up&hellip; first request may take 30&ndash;60 s &#x23F3;', false);
        } else {
            showStatus('Server warming up&hellip; first request may take 30&ndash;60 s &#x23F3;', false);
        }
    });

document.addEventListener('DOMContentLoaded', function () {

    const dropZone = document.getElementById('dropZone');
    const fileInput = document.getElementById('fileInput');
    const preview = document.getElementById('preview');
    const analyzeBtn = document.getElementById('analyzeBtn');
    const analyzeBtnText = document.getElementById('analyzeBtnText');
    const analyzeBtnLoading = document.getElementById('analyzeBtnLoading');
    const dzDefault = document.getElementById('dzDefault');
    const dzPreview = document.getElementById('dzPreview');
    const browseBtn = document.getElementById('browseBtn');
    const changeBtn = document.getElementById('changeBtn');
    const fileInfo = document.getElementById('fileInfo');
    const fileName = document.getElementById('fileName');
    const fileSize = document.getElementById('fileSize');
    const errorMsg = document.getElementById('errorMsg');
    const errorText = document.getElementById('errorText');

    // Browse button
    if (browseBtn) browseBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        fileInput.click();
    });

    // Click dropzone
    if (dropZone) dropZone.addEventListener('click', () => fileInput.click());

    // Change image button
    if (changeBtn) changeBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        fileInput.click();
    });

    // Drag over
    if (dropZone) {
        dropZone.addEventListener('dragover', (e) => {
            e.preventDefault();
            dropZone.classList.add('dragover');
        });
        dropZone.addEventListener('dragleave', () => {
            dropZone.classList.remove('dragover');
        });
        dropZone.addEventListener('drop', (e) => {
            e.preventDefault();
            dropZone.classList.remove('dragover');
            const files = e.dataTransfer.files;
            if (files.length > 0) {
                fileInput.files = files;
                showPreview(files[0]);
            }
        });
    }

    // File input change
    if (fileInput) {
        fileInput.addEventListener('change', () => {
            if (fileInput.files.length > 0) showPreview(fileInput.files[0]);
        });
    }

    // Show preview
    function showPreview(file) {
        const allowed = ['image/jpeg', 'image/jpg', 'image/png', 'image/webp'];
        if (!allowed.includes(file.type)) {
            showError('Invalid file type! Use JPG, JPEG, or PNG.');
            return;
        }
        if (file.size > 16 * 1024 * 1024) {
            showError('File too large! Max size is 16MB.');
            return;
        }
        hideError();
        const reader = new FileReader();
        reader.onload = (e) => {
            if (preview) preview.src = e.target.result;
            if (dzDefault) dzDefault.style.display = 'none';
            if (dzPreview) dzPreview.style.display = 'block';
        };
        reader.readAsDataURL(file);
        if (fileName) fileName.textContent = file.name;
        if (fileSize) fileSize.textContent = formatSize(file.size);
        if (fileInfo) fileInfo.style.display = 'flex';
    }

    function formatSize(bytes) {
        if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
        return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
    }

    // Analyze button
    if (analyzeBtn) {
        analyzeBtn.addEventListener('click', async () => {
            const file = fileInput.files[0];
            if (!file) { showError('Please select an image first!'); return; }

            setLoading(true);
            hideError();
            hideSleepWarning();

            const formData = new FormData();
            formData.append('file', file);

            // Show "server waking up" notice if Render takes > 8 seconds
            const sleepTimer = setTimeout(showSleepWarning, 8000);

            // Hard-abort after 60 seconds (Render cold-start can take ~30s)
            const controller = new AbortController();
            const abortTimer = setTimeout(() => controller.abort(), 60000);

            try {
                const response = await fetch(API_BASE + '/predict', {
                    method: 'POST',
                    body: formData,
                    signal: controller.signal
                });
                clearTimeout(sleepTimer);
                clearTimeout(abortTimer);
                hideSleepWarning();

                const result = await response.json();
                console.log('Result:', result);

                if (result.status === 'success') {
                    displayResult(result);
                } else if (result.status === 'rejected') {
                    showRejected(result);
                } else {
                    showError(result.message || 'Something went wrong.');
                }
            } catch (err) {
                clearTimeout(sleepTimer);
                clearTimeout(abortTimer);
                hideSleepWarning();
                console.error(err);
                if (err.name === 'AbortError') {
                    showError('Request timed out (60s). The server may be starting up — please try again in a moment.');
                } else {
                    showError('Cannot reach server. Check your connection or try again later.');
                }
            } finally {
                setLoading(false);
            }
        });
    }

    function setLoading(on) {
        if (!analyzeBtn) return;
        analyzeBtn.disabled = on;
        if (analyzeBtnText) analyzeBtnText.style.display = on ? 'none' : 'flex';
        if (analyzeBtnLoading) analyzeBtnLoading.style.display = on ? 'flex' : 'none';
    }

    // Display result
    function displayResult(result) {
        toggleSections('result');

        const conf = result.confidence || 0;

        // Disease name
        const el = document.getElementById('diseaseName');
        if (el) el.textContent = result.display_name || result.disease_name;

        // Confidence number
        const confEl = document.getElementById('confidence');
        if (confEl) confEl.textContent = conf + '%';

        // Confidence ring animation
        const circle = document.getElementById('confCircle');
        if (circle) {
            const offset = 264 - (conf / 100) * 264;
            setTimeout(() => {
                circle.style.strokeDashoffset = offset;
                circle.style.stroke = conf >= 70
                    ? '#40916c' : conf >= 45
                    ? '#f4a261' : '#ef4444';
            }, 200);
        }

        // Confidence bar
        const bar = document.getElementById('confidenceBar');
        if (bar) {
            setTimeout(() => {
                bar.style.width = conf + '%';
                bar.style.background = conf >= 70
                    ? 'linear-gradient(90deg,#40916c,#74c69d)'
                    : conf >= 45
                    ? 'linear-gradient(90deg,#f4a261,#f7b27a)'
                    : 'linear-gradient(90deg,#ef4444,#f87171)';
            }, 300);
        }

        // Confidence label badge
        const label = document.getElementById('confidenceLabel');
        if (label) {
            label.textContent = result.confidence_label || '';
            label.className = 'conf-badge badge bg-'
                + (result.confidence_badge || 'secondary');
            if (result.confidence_badge === 'warning') {
                label.classList.add('text-dark');
            }
        }

        // Warning
        const warn = document.getElementById('warningMsg');
        const warnText = document.getElementById('warningText');
        if (warn) {
            if (result.message) {
                if (warnText) warnText.textContent = result.message;
                warn.style.display = 'flex';
            } else {
                warn.style.display = 'none';
            }
        }

        // Tips
        const tips = document.getElementById('tipsBox');
        if (tips) {
            if (result.tips && result.tips.length > 0) {
                tips.innerHTML = '<strong>Tips:</strong><ul style="margin:6px 0 0;padding-left:18px;">'
                    + result.tips.map(t => `<li style="font-size:12px;">${t}</li>`).join('')
                    + '</ul>';
                tips.style.display = 'block';
            } else {
                tips.style.display = 'none';
            }
        }

        // Description
        const desc = document.getElementById('description');
        if (desc) desc.textContent = result.description || '';

        // Lists
        setList('symptomsList', result.symptoms);
        setList('treatmentList', result.treatment);
        setList('preventionList', result.prevention);

        // Top 3 predictions
        const top3Box = document.getElementById('top3Box');
        if (top3Box && result.top3 && result.top3.length > 0) {
            top3Box.innerHTML = '<strong style="font-size:13px;">Top predictions:</strong>'
                + result.top3.map((p, i) =>
                    `<div class="d-flex justify-content-between align-items-center mt-1" style="font-size:12px;">`
                    + `<span>${i + 1}. ${p.disease}</span>`
                    + `<span class="badge bg-secondary">${p.confidence}%</span>`
                    + `</div>`
                ).join('');
            top3Box.style.display = 'block';
        } else if (top3Box) {
            top3Box.style.display = 'none';
        }
    }

    function setList(id, items) {
        const el = document.getElementById(id);
        if (el && items) {
            el.innerHTML = items.map(i => `<li>${i}</li>`).join('');
        }
    }

    // Show rejected
    function showRejected(result) {
        toggleSections('rejected');

        const msg = document.getElementById('rejectedMsg');
        if (msg) msg.textContent = result.message || 'Image not recognized';

        const conf = document.getElementById('rejectedConf');
        if (conf) {
            if (result.confidence > 0) {
                conf.textContent = `Confidence: ${result.confidence}%`;
                conf.style.display = 'block';
            } else {
                conf.style.display = 'none';
            }
        }

        const tips = document.getElementById('rejectedTips');
        if (tips && result.tips) {
            tips.innerHTML = result.tips.map(t => `<li>${t}</li>`).join('');
        }
    }

    // Toggle sections
    function toggleSections(show) {
        const upload = document.querySelector('.upload-card');
        const result = document.getElementById('resultSection');
        const rejected = document.getElementById('rejectedSection');

        if (upload) upload.style.display = show === 'upload' ? 'flex' : 'none';
        if (result) result.style.display = show === 'result' ? 'block' : 'none';
        if (rejected) rejected.style.display = show === 'rejected' ? 'flex' : 'none';

        if (show !== 'upload') {
            const target = show === 'result' ? result : rejected;
            if (target) setTimeout(() => target.scrollIntoView({
                behavior: 'smooth', block: 'start'
            }), 100);
        }
    }

    function showError(msg) {
        if (errorMsg) errorMsg.style.display = 'flex';
        if (errorText) errorText.textContent = msg;
    }

    function hideError() {
        if (errorMsg) errorMsg.style.display = 'none';
    }

    function showSleepWarning() {
        const el = document.getElementById('sleepWarning');
        if (el) el.style.display = 'flex';
    }

    function hideSleepWarning() {
        const el = document.getElementById('sleepWarning');
        if (el) el.style.display = 'none';
    }

    // Share button
    const shareBtn = document.getElementById('shareBtn');
    if (shareBtn) {
        shareBtn.addEventListener('click', () => {
            const name = document.getElementById('diseaseName')?.textContent;
            const conf = document.getElementById('confidence')?.textContent;
            const text = `CropGuard detected: ${name} (${conf} confidence)`;
            if (navigator.share) {
                navigator.share({ title: 'CropGuard', text });
            } else {
                navigator.clipboard.writeText(text).then(() => {
                    shareBtn.innerHTML = '<i class="bi bi-check2 me-1"></i>Copied!';
                    setTimeout(() => {
                        shareBtn.innerHTML = '<i class="bi bi-share me-1"></i>Share';
                    }, 2000);
                });
            }
        });
    }
});

// Reset to upload
function resetToUpload() {
    const fileInput = document.getElementById('fileInput');
    if (fileInput) fileInput.value = '';

    const dzDefault = document.getElementById('dzDefault');
    const dzPreview = document.getElementById('dzPreview');
    const fileInfo = document.getElementById('fileInfo');
    const confCircle = document.getElementById('confCircle');
    const confBar = document.getElementById('confidenceBar');

    if (dzDefault) dzDefault.style.display = 'flex';
    if (dzPreview) dzPreview.style.display = 'none';
    if (fileInfo) fileInfo.style.display = 'none';
    if (confCircle) confCircle.style.strokeDashoffset = '264';
    if (confBar) confBar.style.width = '0%';

    const upload = document.querySelector('.upload-card');
    const result = document.getElementById('resultSection');
    const rejected = document.getElementById('rejectedSection');

    if (upload) upload.style.display = 'flex';
    if (result) result.style.display = 'none';
    if (rejected) rejected.style.display = 'none';

    window.scrollTo({ top: 0, behavior: 'smooth' });
}

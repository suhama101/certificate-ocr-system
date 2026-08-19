const fileInput = document.getElementById('fileInput');
const dropZone = document.getElementById('dropZone');
const extractBtn = document.getElementById('extractBtn');
const fileMeta = document.getElementById('fileMeta');
const previewImage = document.getElementById('previewImage');
const previewEmpty = document.getElementById('previewEmpty');
const pdfPreview = document.getElementById('pdfPreview');
const progress = document.getElementById('progress');
const message = document.getElementById('message');
const resultsSection = document.getElementById('resultsSection');
let selectedFile = null;
let latestResult = null;

function formatBytes(bytes) {
  const units = ['B', 'KB', 'MB', 'GB'];
  let i = 0;
  let n = bytes;
  while (n >= 1024 && i < units.length - 1) { n /= 1024; i++; }
  return `${n.toFixed(i ? 1 : 0)} ${units[i]}`;
}

function chooseFile(file) {
  if (!file) return;
  selectedFile = file;
  extractBtn.disabled = false;
  fileMeta.textContent = `${file.name} • ${formatBytes(file.size)}`;
  fileMeta.classList.remove('hidden');
  message.textContent = '';
  resultsSection.classList.add('hidden');

  const isPdf = file.type === 'application/pdf' || file.name.toLowerCase().endsWith('.pdf');
  if (isPdf) {
    previewImage.classList.add('hidden');
    previewEmpty.classList.add('hidden');
    pdfPreview.classList.remove('hidden');
  } else {
    const reader = new FileReader();
    reader.onload = e => {
      previewImage.src = e.target.result;
      previewImage.classList.remove('hidden');
      previewEmpty.classList.add('hidden');
      pdfPreview.classList.add('hidden');
    };
    reader.readAsDataURL(file);
  }
}

fileInput.addEventListener('change', e => chooseFile(e.target.files[0]));
['dragenter', 'dragover'].forEach(evt => dropZone.addEventListener(evt, e => {
  e.preventDefault(); dropZone.classList.add('drag');
}));
['dragleave', 'drop'].forEach(evt => dropZone.addEventListener(evt, e => {
  e.preventDefault(); dropZone.classList.remove('drag');
}));
dropZone.addEventListener('drop', e => chooseFile(e.dataTransfer.files[0]));

extractBtn.addEventListener('click', async () => {
  if (!selectedFile) return;
  const form = new FormData();
  form.append('file', selectedFile);
  extractBtn.disabled = true;
  progress.classList.remove('hidden');
  message.className = 'message';
  message.textContent = 'Processing document. OCR may take a few seconds...';

  try {
    const response = await fetch('/extract', { method: 'POST', body: form });
    const data = await response.json();
    if (!response.ok) throw new Error(data.detail || 'Extraction failed');
    latestResult = data;
    renderResult(data);
    message.className = 'message success';
    message.textContent = 'Extraction completed successfully.';
  } catch (err) {
    message.className = 'message error';
    message.textContent = err.message;
  } finally {
    progress.classList.add('hidden');
    extractBtn.disabled = false;
  }
});

function label(key) {
  return key.replaceAll('_', ' ').replace(/\b\w/g, c => c.toUpperCase());
}

function renderResult(data) {
  resultsSection.classList.remove('hidden');
  document.getElementById('pageCount').textContent = data.page_count;
  document.getElementById('confidence').textContent = data.average_confidence == null ? 'N/A' : `${data.average_confidence}%`;
  document.getElementById('docId').textContent = data.id;
  document.getElementById('rawText').textContent = data.raw_text || '';
  document.getElementById('jsonBtn').href = `/results/${data.id}/json`;
  document.getElementById('csvBtn').href = `/results/${data.id}/csv`;

  const grid = document.getElementById('fieldsGrid');
  grid.innerHTML = '';
  Object.entries(data.fields || {}).forEach(([key, value]) => {
    const box = document.createElement('div');
    box.className = 'field';
    const shown = typeof value === 'object' ? JSON.stringify(value) : (value || 'Not detected');
    box.innerHTML = `<span>${label(key)}</span><strong>${escapeHtml(shown)}</strong>`;
    grid.appendChild(box);
  });
  resultsSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
}

function escapeHtml(value) {
  return String(value).replace(/[&<>'"]/g, char => ({
    '&': '&amp;', '<': '&lt;', '>': '&gt;', "'": '&#39;', '"': '&quot;'
  }[char]));
}

document.getElementById('copyBtn').addEventListener('click', async () => {
  if (!latestResult) return;
  const text = Object.entries(latestResult.fields).map(([k, v]) => `${label(k)}: ${typeof v === 'object' ? JSON.stringify(v) : (v || '')}`).join('\n');
  await navigator.clipboard.writeText(text);
  message.className = 'message success';
  message.textContent = 'Extracted fields copied to clipboard.';
});

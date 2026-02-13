const dropZone = document.getElementById('dropZone');
const fileInput = document.getElementById('fileInput');
const convertBtn = document.getElementById('convertBtn');
const statusSection = document.getElementById('statusSection');
const statusText = document.getElementById('statusText');
const resultSection = document.getElementById('resultSection');
const reportContent = document.getElementById('reportContent');
const badge = document.getElementById('badge');
const downloadLink = document.getElementById('downloadLink');

// API URL (assuming local dev)
const API_URL = 'http://localhost:8000';

let selectedFile = null;

// Drag & Drop
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
    if (e.dataTransfer.files.length) {
        handleFileSelect(e.dataTransfer.files[0]);
    }
});

dropZone.addEventListener('click', () => fileInput.click());

fileInput.addEventListener('change', (e) => {
    if (e.target.files.length) {
        handleFileSelect(e.target.files[0]);
    }
});

function handleFileSelect(file) {
    if (!file.name.endsWith('.xlsx')) {
        alert('Please upload an Excel file (.xlsx)');
        return;
    }
    selectedFile = file;
    dropZone.querySelector('p').textContent = `Selected: ${file.name}`;
    convertBtn.disabled = false;
}

convertBtn.addEventListener('click', async () => {
    if (!selectedFile) return;

    // Reset UI
    resultSection.classList.add('hidden');
    statusSection.classList.remove('hidden');
    statusText.textContent = 'Processing... This may take a moment.';
    convertBtn.disabled = true;

    const formData = new FormData();
    formData.append('file', selectedFile);

    try {
        const response = await fetch(`${API_URL}/convert`, {
            method: 'POST',
            body: formData
        });

        const data = await response.json();

        if (response.ok) {
            showResult(true, data.report, `${API_URL}/download/ttl`); // Fixed download URL construction
        } else {
            showResult(false, data.report || data.details || 'Unknown error');
        }

    } catch (error) {
        statusText.textContent = `Error: ${error.message}`;
    } finally {
        convertBtn.disabled = false;
    }
});

function showResult(success, report, downloadUrl) {
    statusSection.classList.add('hidden');
    resultSection.classList.remove('hidden');
    
    reportContent.textContent = report;
    
    if (success) {
        badge.textContent = 'VALIDATION PASSED';
        badge.className = 'badge success';
        downloadLink.href = downloadUrl; // Use the URL from backend response path logic
        downloadLink.style.display = 'inline-block';
        
        // Check report content for "False" just in case status was OK but logic failed
        if (report.includes('Conforms: False') || report.includes('SHACL conforms: False')) {
             badge.textContent = 'VALIDATION FAILED';
             badge.className = 'badge failure';
        }

    } else {
        badge.textContent = 'FAILED';
        badge.className = 'badge failure';
        downloadLink.style.display = 'none';
    }
}

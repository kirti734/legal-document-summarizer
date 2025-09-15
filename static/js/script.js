const uploadArea = document.getElementById('upload-area');
const fileInput = document.getElementById('file-input');
const fileNameDisplay = document.getElementById('file-name');

// Prevent default drag behaviors
['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
    uploadArea.addEventListener(eventName, preventDefaults, false);
    document.body.addEventListener(eventName, preventDefaults, false);
});

// Highlight drop area when item is dragged over it
['dragenter', 'dragover'].forEach(eventName => {
    uploadArea.addEventListener(eventName, highlight, false);
});

// Remove highlight when drag leaves or file is dropped
['dragleave', 'drop'].forEach(eventName => {
    uploadArea.addEventListener(eventName, unhighlight, false);
});

// Handle dropped files
uploadArea.addEventListener('drop', handleDrop, false);
// Handle file selection with input
fileInput.addEventListener('change', handleFiles, false);

function preventDefaults(e) {
    e.preventDefault();
    e.stopPropagation();
}

function highlight(e) {
    uploadArea.classList.add('dragover');
}

function unhighlight(e) {
    uploadArea.classList.remove('dragover');
}

function handleDrop(e) {
    const dt = e.dataTransfer;
    const files = dt.files;

    if (files.length > 0) {
        fileInput.files = files;
        handleFiles();
    }
}

function handleFiles() {
    const files = fileInput.files;
    if (files.length > 0) {
        const fileName = files[0].name;
        fileNameDisplay.textContent = `${fileName}`;
        fileNameDisplay.style.display = 'block';
    }
}

async function analyzeDocument() {
    if (fileInput.files.length === 0) {
        alert('Please select a document to analyze first.');
        return;
    }

    const file = fileInput.files[0];
    const analyzeBtn = document.querySelector('.analyze-btn');
    const originalText = analyzeBtn.textContent;
    analyzeBtn.textContent = 'Analyzing...';
    analyzeBtn.disabled = true;

    // Prepare form data for upload
    const formData = new FormData();
    formData.append('file', file);

    try {
        const response = await fetch('/upload', {
            method: 'POST',
            body: formData
        });
        const result = await response.json();

        if (result.success) {
            alert(`Analysis complete for: ${result.data.filename}`);

            // Store all the analysis data including highlighted HTML
            localStorage.setItem("highlighted_html", result.data.highlightedHtml);
            localStorage.setItem("clauses_data", JSON.stringify(result.data.clauses));
            localStorage.setItem("document_info", JSON.stringify({
                filename: result.data.filename,
                documentType: result.data.documentType,
                lawyerSpecialty: result.data.lawyerSpecialty,
                summary: result.data.summary,
                totalClauses: result.data.totalClauses
            }));

            setTimeout(() => {
                window.location.href = "/result";  // Navigate to Flask route
            }, 2000);
        }


         else {
            alert(`Error: ${result.error}`);
        }
    } catch (error) {
        alert(`An error occurred: ${error.message}`);
    } finally {
        analyzeBtn.textContent = originalText;
        analyzeBtn.disabled = false;
    }
}

// Add smooth scrolling for better UX on anchor links
document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function (e) {
        e.preventDefault();
        document.querySelector(this.getAttribute('href')).scrollIntoView({
            behavior: 'smooth'
        });
    });
});

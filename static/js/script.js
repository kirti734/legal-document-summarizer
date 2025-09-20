const uploadArea = document.getElementById("upload-area");
const fileInput = document.getElementById("file-input");
const fileNameDisplay = document.getElementById("file-name");

// Prevent default drag behaviors
["dragenter", "dragover", "dragleave", "drop"].forEach((eventName) => {
  uploadArea.addEventListener(eventName, preventDefaults, false);
  document.body.addEventListener(eventName, preventDefaults, false);
});

// Highlight drop area when item is dragged over it
["dragenter", "dragover"].forEach((eventName) => {
  uploadArea.addEventListener(eventName, highlight, false);
});

// Remove highlight when drag leaves or file is dropped
["dragleave", "drop"].forEach((eventName) => {
  uploadArea.addEventListener(eventName, unhighlight, false);
});

// Handle dropped files
uploadArea.addEventListener("drop", handleDrop, false);
// Handle file selection with input
fileInput.addEventListener("change", handleFiles, false);

function preventDefaults(e) {
  e.preventDefault();
  e.stopPropagation();
}

function highlight(e) {
  uploadArea.classList.add("dragover");
}

function unhighlight(e) {
  uploadArea.classList.remove("dragover");
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
    fileNameDisplay.style.background = "#e8f5e8";
    fileNameDisplay.style.borderRadius = "8px";
    fileNameDisplay.style.fontSize = "24px";
    fileNameDisplay.style.color = "#28a745";
  }
}

async function analyzeDocument() {
  if (fileInput.files.length === 0) {
    alert("Please select a document to analyze first.");
    return;
  }
  const file = fileInput.files[0];
const analyzeBtn = document.querySelector(".analyze-btn");
const originalText = analyzeBtn.textContent;
analyzeBtn.textContent = "Analyzing...";
analyzeBtn.disabled = true;

try {
  // 1. Upload request
  const formData1 = new FormData();
  formData1.append("file", file);

  const response1 = await fetch("/upload", {
    method: "POST",
    body: formData1,
  });
  const result1 = await response1.json();

  if (result1.success) {
    // Save upload analysis data
    localStorage.setItem("highlighted_html", result1.data.highlightedHtml);
    localStorage.setItem("clauses_data", JSON.stringify(result1.data.clauses));
    localStorage.setItem(
      "document_info",
      JSON.stringify({
        filename: result1.data.filename,
        documentType: result1.data.documentType,
        lawyerSpecialty: result1.data.lawyerSpecialty,
        summary: result1.data.summary,
        totalClauses: result1.data.totalClauses,
      })
    );
  } else {
    alert(`Error: ${result1.error}`);
    return; 
  }

  // 2. Summarizer request
  const formData2 = new FormData();
  formData2.append("file", file);

  const response2 = await fetch("/summariser", {
    method: "POST",
    body: formData2,
  });
  const result2 = await response2.json();

  if (result2.success) {
    alert("Analysis is complete!😊");
    localStorage.setItem("analysisData", result2.data.summary);

  } else {
    alert(`Error: ${result2.error}`);
  }
} catch (error) {
  alert(`An error occurred: ${error.message}`);
} finally {
  analyzeBtn.textContent = originalText;
  analyzeBtn.disabled = false;
}

setTimeout(() => {
      window.location.href = "/result";
    }, 500);
} 

// Add smooth scrolling for better UX on anchor links
document.querySelectorAll('a[href^="#"]').forEach((anchor) => {
  anchor.addEventListener("click", function (e) {
    e.preventDefault();
    document.querySelector(this.getAttribute("href")).scrollIntoView({
      behavior: "smooth",
    });
  });
})

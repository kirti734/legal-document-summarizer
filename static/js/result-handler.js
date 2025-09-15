// Get data from localStorage
const highlightedHtml = localStorage.getItem("highlighted_html");
const clausesData = JSON.parse(localStorage.getItem("clauses_data") || "[]");
const documentInfo = JSON.parse(localStorage.getItem("document_info") || "{}");

// 🔥 NEW: Check if user is authenticated (you can store this in localStorage or get from server)
let isUserAuthenticated = localStorage.getItem("user_authenticated") === "true";

// Display the pre-highlighted document
function displayHighlightedDocument() {
    const contentDiv = document.getElementById('document-content');

    if (highlightedHtml) {
        contentDiv.innerHTML = highlightedHtml;

        if (documentInfo.filename) {
            const titleElement = document.querySelector('h2');
            if (titleElement) {
                titleElement.textContent = `Document Analysis - ${documentInfo.filename}`;
            }
        }
    } else {
        contentDiv.innerHTML = '<p>No document analysis data found. Please <a href="/">upload a document</a> first.</p>';
    }
}

// 🔥 MODIFIED: Show login modal for non-authenticated users
function showClausePopup(clauseIndex) {
    // console.log(`Clause ${clauseIndex} clicked`);

    // 🔥 CHECK AUTHENTICATION FIRST
    if (!isUserAuthenticated) {
        // console.log("User not authenticated, showing login modal");
        showLoginModal();
        return;
    }

    // Original clause popup logic for authenticated users
    const clause = clausesData[clauseIndex];
    if (!clause) {
        // console.error('No clause found for index:', clauseIndex);
        return;
    }

    const popup = document.getElementById('clause-popup');
    const title = document.getElementById('popup-title');
    const explanation = document.getElementById('popup-explanation');
    const suggestions = document.getElementById('popup-suggestions');

    if (!popup || !title || !explanation || !suggestions) {
        // console.error("Popup elements not found!");
        return;
    }

    const riskLevel = clause.riskLevel || 'medium';
    title.textContent = `${riskLevel.charAt(0).toUpperCase() + riskLevel.slice(1)} Risk Clause`;
    explanation.textContent = clause.explanation || 'No explanation available';

    if (clause.suggestions && clause.suggestions.length > 0) {
        suggestions.innerHTML = `
            <h4>Suggested Questions to Ask:</h4>
            <ul>
                ${clause.suggestions.map(suggestion => `<li>${suggestion}</li>`).join('')}
            </ul>
        `;
    } else {
        suggestions.innerHTML = '<p><strong>This appears to be a standard clause.</strong></p>';
    }

    popup.classList.remove('hidden');
}

// 🔥 NEW: Login Modal Functions
function showLoginModal() {
    const modal = document.getElementById('login-modal');
    modal.classList.remove('hidden');
}

function hideLoginModal() {
    const modal = document.getElementById('login-modal');
    modal.classList.add('hidden');
}

function showSignupForm() {
    // You can redirect to a signup page or show signup form
    alert('Redirecting to signup page...');
    window.location.href = '/signup';
}

// 🔥 NEW: Handle Login Form Submission
document.addEventListener('DOMContentLoaded', function () {
    const loginForm = document.getElementById('login-form');
    if (loginForm) {
        loginForm.addEventListener('submit', async function (e) {
            e.preventDefault();

            const email = document.getElementById('email').value;
            const password = document.getElementById('password').value;

            // console.log('Attempting login...');

            try {
                const response = await fetch('/login', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ email, password })
                });

                const result = await response.json();

                if (result.success) {
                    // Store authentication status
                    localStorage.setItem("user_authenticated", "true");
                    localStorage.setItem("user_email", email);
                    isUserAuthenticated = true;

                    hideLoginModal();
                    alert('Login successful! You can now access premium features.');
                } else {
                    alert('Login failed: ' + result.error);
                }
            } catch (error) {
                // console.error('Login error:', error);
                alert('Login failed. Please try again.');
            }
        });
    }
});

// Hide clause popup function
function hideClausePopup() {
    document.getElementById('clause-popup').classList.add('hidden');
}

// Make functions global for onclick handlers
window.showClausePopup = showClausePopup;
window.hideClausePopup = hideClausePopup;
window.hideLoginModal = hideLoginModal;

// Event listeners
document.addEventListener('DOMContentLoaded', function () {
    displayHighlightedDocument();

    // Close popup event listeners
    const closeBtn = document.querySelector('.close-btn');
    if (closeBtn) {
        closeBtn.addEventListener('click', hideClausePopup);
    }

    const popup = document.getElementById('clause-popup');
    if (popup) {
        popup.addEventListener('click', function (e) {
            if (e.target === this) {
                hideClausePopup();
            }
        });
    }

    // Close login modal on background click
    const loginModal = document.getElementById('login-modal');
    if (loginModal) {
        loginModal.addEventListener('click', function (e) {
            if (e.target === this) {
                hideLoginModal();
            }
        });
    }

    document.addEventListener('keydown', function (e) {
        if (e.key === 'Escape') {
            hideClausePopup();
            hideLoginModal();
        }
    });
});

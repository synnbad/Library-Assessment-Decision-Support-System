// API endpoint for classification
const API_URL = '/classify';

/**
 * Load an example message into the textarea
 * @param {string} text - The example text to load
 */
function loadExample(text) {
    document.getElementById('message-input').value = text;
}

/**
 * Send the message to the API for classification
 * Handles the entire classification workflow including UI updates and error handling
 */
async function classifyMessage() {
    const messageInput = document.getElementById('message-input');
    const text = messageInput.value.trim();
    
    // Validate that user entered some text
    if (!text) {
        alert('Please enter a message to classify.');
        return;
    }
    
    // Update button state to show loading
    const classifyBtn = document.getElementById('classify-btn');
    classifyBtn.textContent = 'Classifying...';
    classifyBtn.disabled = true;
    
    try {
        // Send POST request to classification API
        const response = await fetch(API_URL, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ text: text })
        });
        
        // Check if request was successful
        if (!response.ok) {
            throw new Error('Classification failed');
        }
        
        // Parse and display the result
        const result = await response.json();
        displayResult(result);
        
    } catch (error) {
        console.error('Error:', error);
        alert('An error occurred during classification. Please try again.');
    } finally {
        // Reset button state
        classifyBtn.textContent = 'Classify Message';
        classifyBtn.disabled = false;
    }
}

/**
 * Display the classification result in the UI
 * Updates all result elements with data from the API response
 * @param {Object} result - The classification result from the API
 * @param {string} result.label - The sentiment label (positive/neutral/negative)
 * @param {number} result.confidence - Confidence score (0-100)
 * @param {string} result.reason - Explanation for the classification
 * @param {boolean} result.escalate - Whether human review is needed
 */
function displayResult(result) {
    // Get all DOM elements we need to update
    const resultSection = document.getElementById('result-section');
    const labelElement = document.getElementById('result-label');
    const confidenceElement = document.getElementById('result-confidence');
    const confidenceFill = document.getElementById('confidence-fill');
    const reasonElement = document.getElementById('result-reason');
    const escalateSection = document.getElementById('escalate-section');
    
    // Update label with appropriate styling class
    labelElement.textContent = result.label;
    labelElement.className = `value label-badge ${result.label}`;
    
    // Update confidence display
    const confidence = Math.round(result.confidence);
    confidenceElement.textContent = `${confidence}%`;
    confidenceFill.style.width = `${confidence}%`;
    confidenceFill.textContent = `${confidence}%`;
    
    // Color-code the confidence bar based on confidence level
    // Green for high confidence (80%+), orange for medium (60-79%), red for low (<60%)
    if (confidence >= 80) {
        confidenceFill.style.background = 'linear-gradient(90deg, #4caf50 0%, #8bc34a 100%)';
    } else if (confidence >= 60) {
        confidenceFill.style.background = 'linear-gradient(90deg, #ff9800 0%, #ffc107 100%)';
    } else {
        confidenceFill.style.background = 'linear-gradient(90deg, #f44336 0%, #e57373 100%)';
    }
    
    // Display the reasoning explanation
    reasonElement.textContent = result.reason;
    
    // Show escalation warning if confidence is below threshold
    if (result.escalate) {
        escalateSection.style.display = 'flex';
    } else {
        escalateSection.style.display = 'none';
    }
    
    // Make result section visible
    resultSection.style.display = 'block';
    
    // Scroll to results smoothly for better UX
    resultSection.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
}

/**
 * Set up keyboard shortcuts when the page loads
 * Enter key submits the form, Shift+Enter adds a new line
 */
document.addEventListener('DOMContentLoaded', () => {
    const messageInput = document.getElementById('message-input');
    
    // Add keyboard event listener for convenient submission
    messageInput.addEventListener('keydown', (event) => {
        // Submit on Enter, but allow Shift+Enter for multi-line input
        if (event.key === 'Enter' && !event.shiftKey) {
            event.preventDefault();
            classifyMessage();
        }
    });
});

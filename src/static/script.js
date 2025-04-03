async function submitIncident() {
    const description = document.getElementById('incidentDescription').value;
    if (!description.trim()) return;

    // Add user message to chat
    addMessage('user-message', description);
    
    // Clear input
    document.getElementById('incidentDescription').value = '';

    try {
        // Show loading state
        addMessage('bot-message', 'Processing your incident...');

        // Make API call
        const response = await fetch('/api/query', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ description: description })
        });

        if (!response.ok) {
            throw new Error('Failed to get response');
        }

        const data = await response.json();
        
        // Remove loading message
        document.querySelector('.chat-messages').lastElementChild.remove();
        
        // Add bot response
        addMessage('bot-message', data.response);
        
        // Update reference incidents
        updateReferences(data.reference_incidents);
        
    } catch (error) {
        console.error('Error:', error);
        addMessage('bot-message', 'Sorry, there was an error processing your request.');
    }
}

function addMessage(className, content) {
    const messagesDiv = document.getElementById('chatMessages');
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${className}`;
    messageDiv.textContent = content;
    messagesDiv.appendChild(messageDiv);
    messagesDiv.scrollTop = messagesDiv.scrollHeight;
}

function updateReferences(incidents) {
    const referencesDiv = document.getElementById('referenceIncidents');
    referencesDiv.innerHTML = incidents.map(incidentNo => 
        `<div class="reference-incident" onclick="showIncidentDetails('${incidentNo}')">
            ${incidentNo}
        </div>`
    ).join('');
}

async function showIncidentDetails(incidentNo) {
    // TODO: Implement incident detail view
    console.log('Show details for incident:', incidentNo);
} 
async function analyzeIncident() {
    const description = document.getElementById('incidentDescription').value;
    if (!description.trim()) return;

    // Show loading spinner
    document.getElementById('loadingSpinner').classList.remove('d-none');
    document.getElementById('resultsSection').classList.add('d-none');

    try {
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
        
        // Process and display results
        displayResults(data);
        
    } catch (error) {
        console.error('Error:', error);
        alert('An error occurred while processing your request.');
    } finally {
        // Hide loading spinner
        document.getElementById('loadingSpinner').classList.add('d-none');
    }
}

function displayResults(data) {
    // Parse the response into sections
    const sections = parseResponse(data.response);
    
    // Display root cause
    document.getElementById('rootCauseList').innerHTML = formatList(sections.rootCause);
    
    // Display resolution steps
    document.getElementById('resolutionList').innerHTML = formatList(sections.resolution);
    
    // Display preventive measures
    document.getElementById('preventiveList').innerHTML = formatList(sections.preventiveMeasures);
    
    // Display similar incidents
    document.getElementById('similarIncidents').innerHTML = data.reference_incidents
        .map(inc => `<span class="incident-badge" onclick="showIncidentDetails('${inc}')">${inc}</span>`)
        .join('');

    // Show results section with animation
    const resultsSection = document.getElementById('resultsSection');
    resultsSection.classList.remove('d-none');
    setTimeout(() => resultsSection.classList.add('show'), 100);
}

function parseResponse(response) {
    const sections = {
        rootCause: [],
        resolution: [],
        preventiveMeasures: [],
        references: []  // New section for references
    };

    const lines = response.split('\n');
    let currentSection = null;

    for (const line of lines) {
        const cleanLine = line.trim();
        if (!cleanLine) continue;

        // Check if line is an incident reference
        if (cleanLine.match(/^Incident INC_\d+:/)) {
            sections.references.push(cleanLine);
            continue;
        }

        // Determine section
        if (cleanLine.toLowerCase().includes('root cause')) {
            currentSection = 'rootCause';
            continue;
        } else if (cleanLine.toLowerCase().includes('resolution')) {
            currentSection = 'resolution';
            continue;
        } else if (cleanLine.toLowerCase().includes('preventive')) {
            currentSection = 'preventiveMeasures';
            continue;
        } else if (cleanLine.toLowerCase().includes('reference')) {
            currentSection = 'references';
            continue;
        }

        // Clean up the line
        if (currentSection) {
            // Skip if line is an incident reference
            if (cleanLine.includes('INC_')) continue;

            // Remove leading numbers, letters, and special characters
            let cleanedItem = cleanLine
                .replace(/^[0-9]+\.\s*/, '')
                .replace(/^[a-z]\.\s*/i, '')
                .replace(/^[-•]\s*/, '')
                .replace(/^[)\]]/g, '')
                .trim();

            // Only add non-empty lines that aren't section headers
            if (cleanedItem && 
                !cleanedItem.toLowerCase().includes('root cause') &&
                !cleanedItem.toLowerCase().includes('resolution') &&
                !cleanedItem.toLowerCase().includes('preventive') &&
                !cleanedItem.toLowerCase().includes('reference')) {
                sections[currentSection].push(cleanedItem);
            }
        }
    }

    return sections;
}

function formatList(items) {
    if (!items.length) return '<p>No information available</p>';
    
    const listItems = items.map(item => {
        // Ensure the item starts with a capital letter
        const formattedItem = item.charAt(0).toUpperCase() + item.slice(1);
        return `<li>${formattedItem}</li>`;
    });

    return `<ul class="clean-list">${listItems.join('')}</ul>`;
}

async function showIncidentDetails(incidentNo) {
    try {
        const response = await fetch(`/api/incident/${incidentNo}`);
        if (!response.ok) throw new Error('Failed to fetch incident details');
        
        const incident = await response.json();
        
        // Format preventive measures as a list
        const preventiveMeasures = Array.isArray(incident.preventive_measures) 
            ? incident.preventive_measures
            : [incident.preventive_measures];
        
        const modalContent = `
            <div class="incident-detail">
                <h6>Incident Number</h6>
                <p>${incident.incident_no}</p>
            </div>
            <div class="incident-detail">
                <h6>Title</h6>
                <p>${incident.title}</p>
            </div>
            <div class="incident-detail">
                <h6>Description</h6>
                <p>${incident.description}</p>
            </div>
            <div class="incident-detail">
                <h6>Root Cause</h6>
                <p>${incident.root_cause}</p>
            </div>
            <div class="incident-detail">
                <h6>Resolution</h6>
                <p>${incident.resolution}</p>
            </div>
            <div class="incident-detail">
                <h6>Preventive Measures</h6>
                <div class="content-list">
                    <ul>
                        ${preventiveMeasures.map(measure => `<li>${measure}</li>`).join('')}
                    </ul>
                </div>
            </div>
        `;
        
        document.getElementById('modalContent').innerHTML = modalContent;
        
        const modal = new bootstrap.Modal(document.getElementById('incidentModal'));
        modal.show();
        
    } catch (error) {
        console.error('Error:', error);
        alert('Failed to fetch incident details');
    }
} 
document.addEventListener('DOMContentLoaded', async () => {
    const stravaLoginBtn = document.getElementById('stravaLoginBtn');
    let stravaConfig = {};

    try {
        const response = await fetch('/api/strava-config');
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        stravaConfig = await response.json();
        console.log('Fetched Strava config:', stravaConfig);
    } catch (error) {
        console.error('Error fetching Strava config:', error);
        if (stravaLoginBtn) {
            stravaLoginBtn.disabled = true;
            stravaLoginBtn.textContent = 'Error loading config';
        }
        return; 
    }

    if (stravaLoginBtn) {
        stravaLoginBtn.addEventListener('click', () => {
            const { clientId, redirectUri } = stravaConfig;
            if (!clientId || !redirectUri) {
                console.error('Strava client ID or redirect URI is missing from config.');
                alert('Configuration error. Please contact support.');
                return;
            }
            const scope = 'read,activity:read_all';
            const approvalPrompt = 'force'; 
            const responseType = 'code';
            const authUrl = `https://www.strava.com/oauth/authorize?client_id=${clientId}&redirect_uri=${encodeURIComponent(redirectUri)}&response_type=${responseType}&approval_prompt=${approvalPrompt}&scope=${encodeURIComponent(scope)}`;
            window.location.href = authUrl;
        });
    }

    function getQueryParam(param) {
        const urlParams = new URLSearchParams(window.location.search);
        return urlParams.get(param);
    }

    const authCode = getQueryParam('code');
    if (authCode) {
        console.log('Authorization code received:', authCode);
    }

    // --- Social Media Image Generation ---
    const socialShareSection = document.getElementById('socialShareSection');
    const activityImagePreview = document.getElementById('activity-image-preview');
    const imageLoadingOverlay = document.getElementById('image-loading'); // Defined in HTML

    let activityData = null;
    let athleteData = null;
    let activityImageGenerator = null;
    let activitiesLoaded = []; // Added from design doc

    async function loadActivityData() {
        try {
            const activityResponse = await fetch('strava_activities_data.json');
            if (!activityResponse.ok) throw new Error('Failed to load activity data');
            activitiesLoaded = await activityResponse.json(); 
            
            if (activitiesLoaded.length > 0) {
                activityData = activitiesLoaded[0]; // Set the first activity as default
                populateActivitySelector(activitiesLoaded); // Populate selector
            } else {
                console.warn('No activities found in strava_activities_data.json');
                return false;
            }

            const athleteResponse = await fetch('strava_athlete_data.json');
            if (!athleteResponse.ok) throw new Error('Failed to load athlete data');
            athleteData = await athleteResponse.json();
            
            console.log('Loaded activity data:', activityData);
            console.log('Loaded athlete data:', athleteData);
            return true;
        } catch (error) {
            console.error('Error loading local activity/athlete data:', error);
            return false;
    }
}

// The old ActivityImageGenerator class has been removed as it's now in EnhancedActivityImageGenerator.js

function populateActivitySelector(activities) {
        const selector = document.createElement('select');
        selector.id = 'activity-selector';
        selector.className = 'activity-selector'; // For CSS styling
        
        activities.forEach((activity, index) => {
            const option = document.createElement('option');
            option.value = index;
            const activityDate = new Date(activity.start_date_local).toLocaleDateString();
            const distanceKm = (activity.distance / 1000).toFixed(1);
            option.textContent = `${activity.name} - ${distanceKm}km (${activityDate})`;
            selector.appendChild(option);
        });
        
        const container = document.createElement('div');
        container.className = 'activity-selector-container';
        const label = document.createElement('label');
        label.htmlFor = 'activity-selector';
        label.textContent = 'Select Activity:';
        container.appendChild(label);
        container.appendChild(selector);
        
        const previewContainer = document.querySelector('.image-preview-container');
        if (previewContainer && previewContainer.parentNode) {
             previewContainer.parentNode.insertBefore(container, previewContainer);
        } else {
            // Fallback if preview container isn't found, though it should be.
            socialShareSection.insertBefore(container, socialShareSection.firstChild);
        }
       
        selector.addEventListener('change', (e) => {
            const selectedIndex = parseInt(e.target.value);
            activityData = activitiesLoaded[selectedIndex];
            
            activityImageGenerator = new EnhancedActivityImageGenerator(activityData, athleteData, { // Use new class
                template: document.getElementById('image-template').value,
                colorTheme: getSelectedColorTheme(),
                includeMap: document.getElementById('include-map').checked,
                includeHeartRate: document.getElementById('include-hr').checked,
                includePace: document.getElementById('include-pace').checked,
                includeElevation: document.getElementById('include-elevation').checked,
                customText: document.getElementById('custom-message').value
            });
            activityImageGenerator.generateImage();
        });
    }

    function getSelectedColorTheme() {
        const activeColorButton = document.querySelector('.color-option.active');
        return activeColorButton ? activeColorButton.dataset.theme : 'gradient-blue'; // Default if none active
    }

    function setupEventListeners() {
        const templateSelector = document.getElementById('image-template');
        const colorOptionButtons = document.querySelectorAll('.color-option');
        const includeMapCheckbox = document.getElementById('include-map');
        const includeHrCheckbox = document.getElementById('include-hr');
        const includePaceCheckbox = document.getElementById('include-pace');
        const includeElevationCheckbox = document.getElementById('include-elevation');
        const customMessageTextarea = document.getElementById('custom-message');
        const regenerateBtn = document.getElementById('regenerate-image'); // Corrected ID from design doc
        const downloadBtn = document.getElementById('download-image'); // Corrected ID

        if (templateSelector) templateSelector.addEventListener('change', (e) => activityImageGenerator.updateOptions({ template: e.target.value }));
        
        colorOptionButtons.forEach(button => {
            button.addEventListener('click', (e) => {
                colorOptionButtons.forEach(b => b.classList.remove('active'));
                e.target.classList.add('active');
                activityImageGenerator.updateOptions({ colorTheme: e.target.dataset.theme });
            });
        });

        if (includeMapCheckbox) includeMapCheckbox.addEventListener('change', (e) => activityImageGenerator.updateOptions({ includeMap: e.target.checked }));
        if (includeHrCheckbox) includeHrCheckbox.addEventListener('change', (e) => activityImageGenerator.updateOptions({ includeHeartRate: e.target.checked }));
        if (includePaceCheckbox) includePaceCheckbox.addEventListener('change', (e) => activityImageGenerator.updateOptions({ includePace: e.target.checked }));
        if (includeElevationCheckbox) includeElevationCheckbox.addEventListener('change', (e) => activityImageGenerator.updateOptions({ includeElevation: e.target.checked }));
        if (customMessageTextarea) customMessageTextarea.addEventListener('input', (e) => activityImageGenerator.updateOptions({ customText: e.target.value }));

        if (regenerateBtn) {
            regenerateBtn.addEventListener('click', () => {
                if (!activityImageGenerator) return;
                // Options are updated directly by other listeners, so just regenerate.
                // Or, explicitly gather current state if preferred:
                const currentOpts = {
                    template: templateSelector ? templateSelector.value : 'standard',
                    colorTheme: getSelectedColorTheme(),
                    includeMap: includeMapCheckbox ? includeMapCheckbox.checked : true,
                    includeHeartRate: includeHrCheckbox ? includeHrCheckbox.checked : true,
                    includePace: includePaceCheckbox ? includePaceCheckbox.checked : true,
                    includeElevation: includeElevationCheckbox ? includeElevationCheckbox.checked : true,
                    customText: customMessageTextarea ? customMessageTextarea.value : ''
                };
                activityImageGenerator.updateOptions(currentOpts); // This calls generateImage()
            });
        }

        if (downloadBtn) {
            downloadBtn.addEventListener('click', async () => {
                if (activityImageGenerator) {
                    const imageUrl = await activityImageGenerator.exportAsImage();
                    const link = document.createElement('a');
                    const activityDateStr = new Date(activityData.start_date_local).toISOString().slice(0,10);
                    const fileName = `${activityData.name.replace(/\s+/g, '_')}_${activityDateStr}.png`;
                    link.href = imageUrl;
                    link.download = fileName;
                    document.body.appendChild(link);
                    link.click();
                    document.body.removeChild(link);
                }
            });
        }
    }
    
    async function initializeSocialShare() {
        const dataLoaded = await loadActivityData(); // loadActivityData now populates selector
        if (dataLoaded && activityData && athleteData) {
            if (socialShareSection) socialShareSection.style.display = 'block';
            const loginSection = document.querySelector('.login');
            if (loginSection) loginSection.style.display = 'none';
            const benefitsSection = document.querySelector('.benefits');
            if (benefitsSection) benefitsSection.style.display = 'none';

            // Instantiate the new EnhancedActivityImageGenerator
            activityImageGenerator = new EnhancedActivityImageGenerator(activityData, athleteData, {
                template: document.getElementById('image-template') ? document.getElementById('image-template').value : 'modern', // Default to 'modern' if element not found
                colorTheme: getSelectedColorTheme(),
                includeMap: document.getElementById('include-map') ? document.getElementById('include-map').checked : true,
                includeHeartRate: document.getElementById('include-hr') ? document.getElementById('include-hr').checked : true,
                includePace: document.getElementById('include-pace') ? document.getElementById('include-pace').checked : true,
                includeElevation: document.getElementById('include-elevation') ? document.getElementById('include-elevation').checked : true,
                customText: document.getElementById('custom-message') ? document.getElementById('custom-message').value : ''
            });
            
            activityImageGenerator.generateImage();
            setupEventListeners(); // Setup all event listeners after initialization
        } else {
            console.log('Social share section not initialized due to missing data or not on success page.');
        }
    }

    if (getQueryParam('login') === 'success') {
        initializeSocialShare();
    } else {
        if (stravaLoginBtn) stravaLoginBtn.style.display = 'block';
        if (socialShareSection) socialShareSection.style.display = 'none';
    }
});

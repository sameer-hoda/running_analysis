class EnhancedActivityImageGenerator {
    constructor(activity, athlete, options = {}) {
        this.activity = activity;
        this.athlete = athlete;
        this.options = {
            template: 'modern',  // 'modern', 'minimal', 'stats-focus', 'achievement'
            colorTheme: 'gradient-blue',
            includeMap: true,
            includeHeartRate: true,
            includePace: true,
            includeElevation: true,
            customText: '',
            ...options
        };
        this.canvas = document.getElementById('activity-image-preview');
        if (!this.canvas) {
            console.error('Canvas element not found!');
            // Potentially throw an error or handle this more gracefully
            return;
        }
        this.ctx = this.canvas.getContext('2d');
        this.canvas.width = 1080;
        this.canvas.height = 1920;

        // Font loading is initiated here, drawing should wait for fonts if possible.
        this.loadFonts();
    }

    async loadFonts() {
        // Dynamically load Google Fonts
        const fontId = 'google-font-montserrat';
        if (!document.getElementById(fontId)) { // Load font only once
            const fontLink = document.createElement('link');
            fontLink.id = fontId;
            fontLink.href = 'https://fonts.googleapis.com/css2?family=Montserrat:wght@400;500;600;700&display=swap';
            fontLink.rel = 'stylesheet';
            document.head.appendChild(fontLink);
        }

        // Try to ensure fonts load before rendering using FontFaceSet API
        if (document.fonts) {
            try {
                await document.fonts.load('12px Montserrat'); // Load a small size to check availability
                await document.fonts.load('700 48px Montserrat');
                await document.fonts.load('600 32px Montserrat');
                await document.fonts.load('500 24px Montserrat');
                // console.log('Montserrat font loaded.');
            } catch (e) {
                console.warn('Failed to load Montserrat font, falling back to system fonts.', e);
            }
        }
    }

    async drawBackground() {
        const gradient = this.ctx.createLinearGradient(0, 0, 0, this.canvas.height);
        switch(this.options.colorTheme) {
            case 'gradient-blue':
                gradient.addColorStop(0, '#2C3E50');
                gradient.addColorStop(0.5, '#4C6FFF');
                gradient.addColorStop(1, '#345FDA');
                break;
            case 'gradient-red':
                gradient.addColorStop(0, '#7C0F0F');
                gradient.addColorStop(0.5, '#E74C3C');
                gradient.addColorStop(1, '#C0392B');
                break;
            case 'dark':
                gradient.addColorStop(0, '#121212');
                gradient.addColorStop(0.5, '#2D3436');
                gradient.addColorStop(1, '#1E272E');
                break;
            case 'light':
                gradient.addColorStop(0, '#F5F7FA');
                gradient.addColorStop(0.5, '#E4E7EB');
                gradient.addColorStop(1, '#F5F7FA');
                break;
            default: // Fallback theme
                gradient.addColorStop(0, '#2C3E50');
                gradient.addColorStop(1, '#345FDA');
                break;
        }
        this.ctx.fillStyle = gradient;
        this.ctx.fillRect(0, 0, this.canvas.width, this.canvas.height);

        if (this.options.template !== 'minimal') {
            this.drawPattern();
        }
    }

    drawPattern() {
        this.ctx.save();
        this.ctx.globalAlpha = 0.03;
        const patternSize = 40;
        const isDarkTheme = ['gradient-blue', 'gradient-red', 'dark'].includes(this.options.colorTheme);
        this.ctx.fillStyle = isDarkTheme ? '#ffffff' : '#000000';
        for (let i = 0; i < this.canvas.width; i += patternSize) {
            for (let j = 0; j < this.canvas.height; j += patternSize) {
                this.ctx.beginPath();
                this.ctx.arc(i, j, 0.7, 0, Math.PI * 2);
                this.ctx.fill();
            }
        }
        this.ctx.restore();
    }

    async drawHeader() {
        const headerHeight = 160;
        this.ctx.save();
        this.ctx.fillStyle = 'rgba(0,0,0,0.3)';
        this.ctx.fillRect(0, 0, this.canvas.width, headerHeight);

        const iconSize = 60;
        const iconX = 100;
        const iconY = headerHeight / 2;

        const iconGradient = this.ctx.createRadialGradient(iconX, iconY, 0, iconX, iconY, iconSize / 2);
        iconGradient.addColorStop(0, this.getActivityTypeColor(0.9));
        iconGradient.addColorStop(1, this.getActivityTypeColor(0.7));

        this.ctx.shadowColor = this.getActivityTypeColor(0.5);
        this.ctx.shadowBlur = 20;
        this.ctx.beginPath();
        this.ctx.arc(iconX, iconY, iconSize / 2, 0, Math.PI * 2);
        this.ctx.fillStyle = iconGradient;
        this.ctx.fill();
        this.ctx.shadowColor = 'transparent';
        this.ctx.shadowBlur = 0;

        this.ctx.fillStyle = '#fff';
        this.ctx.font = '36px "Montserrat", sans-serif';
        this.ctx.textAlign = 'center';
        this.ctx.textBaseline = 'middle';
        this.ctx.fillText(this.getActivityTypeSymbol(), iconX, iconY);

        this.ctx.fillStyle = '#fff';
        this.ctx.font = '700 42px "Montserrat", sans-serif';
        this.ctx.textAlign = 'left';
        this.ctx.fillText(this.activity.name || 'Activity', iconX + iconSize / 2 + 40, iconY - 15);

        const activityDate = new Date(this.activity.start_date_local);
        const formattedDate = activityDate.toLocaleDateString(undefined, {
            weekday: 'short', year: 'numeric', month: 'short', day: 'numeric'
        });
        this.ctx.font = '500 22px "Montserrat", sans-serif';
        this.ctx.fillText(`${this.activity.type || 'Workout'} • ${formattedDate}`, iconX + iconSize / 2 + 40, iconY + 25);
        this.ctx.restore();
    }

    getActivityTypeColor(alpha = 1) {
        switch(this.activity.type) {
            case 'Run': return `rgba(255, 87, 34, ${alpha})`;
            case 'Ride': return `rgba(76, 175, 80, ${alpha})`;
            case 'Swim': return `rgba(33, 150, 243, ${alpha})`;
            case 'Walk': return `rgba(255, 193, 7, ${alpha})`;
            case 'Hike': return `rgba(139, 195, 74, ${alpha})`;
            case 'VirtualRide': return `rgba(156, 39, 176, ${alpha})`;
            default: return `rgba(117, 117, 117, ${alpha})`;
        }
    }

    getActivityTypeSymbol() {
        switch(this.activity.type) {
            case 'Run': return '🏃';
            case 'Ride': return '🚴';
            case 'Swim': return '🏊';
            case 'Walk': return '🚶';
            case 'Hike': return '⛰️';
            case 'VirtualRide': return '💻';
            default: return '💪';
        }
    }

    async drawMetricCards() {
        const metrics = this.prepareMetrics();
        const cardStartY = 200; // Adjusted Y position
        const cardWidth = this.canvas.width * 0.43;
        const cardHeight = 120;
        const spacing = 25; // Increased spacing

        const col1X = (this.canvas.width - (cardWidth * 2 + spacing)) / 2;
        const col2X = col1X + cardWidth + spacing;

        await this.drawEnhancedMetricCard(col1X, cardStartY, cardWidth, cardHeight, 'DISTANCE', metrics.distance, 'km', '📏', '#3498db');
        await this.drawEnhancedMetricCard(col2X, cardStartY, cardWidth, cardHeight, 'TIME', metrics.time, '', '⏱️', '#e74c3c');

        const row2Y = cardStartY + cardHeight + spacing;
        let itemsInRow2 = 0;
        let nextAvailableX = col1X;

        if (metrics.elevation !== null) {
            await this.drawEnhancedMetricCard(nextAvailableX, row2Y, cardWidth, cardHeight, 'ELEVATION', metrics.elevation, 'm', '⛰️', '#f39c12');
            nextAvailableX += cardWidth + spacing;
            itemsInRow2++;
        }

        if (metrics.pace !== null) {
            await this.drawEnhancedMetricCard(nextAvailableX, row2Y, cardWidth, cardHeight, metrics.paceLabel, metrics.pace, metrics.paceUnit, '🏎️', '#9b59b6');
            itemsInRow2++;
        } else if (metrics.speed !== null) {
            await this.drawEnhancedMetricCard(nextAvailableX, row2Y, cardWidth, cardHeight, 'AVG SPEED', metrics.speed, 'km/h', '💨', '#2ecc71');
            itemsInRow2++;
        }
        
        return itemsInRow2 > 0 ? row2Y + cardHeight + spacing : cardStartY + cardHeight + spacing;
    }

    prepareMetrics() {
        const metrics = {
            distance: (this.activity.distance / 1000).toFixed(2),
            time: this.formatTime(this.activity.moving_time),
            elevation: this.activity.total_elevation_gain ? this.activity.total_elevation_gain.toFixed(0) : null,
            pace: null,
            paceLabel: 'AVG PACE',
            paceUnit: '/km',
            speed: null
        };
        if (this.activity.type === 'Run' && this.activity.average_speed > 0) {
            const paceSecondsTotal = 1000 / this.activity.average_speed;
            const paceMin = Math.floor(paceSecondsTotal / 60);
            const paceSec = Math.round(paceSecondsTotal % 60);
            metrics.pace = `${paceMin}:${paceSec.toString().padStart(2, '0')}`;
        } else if (this.activity.average_speed > 0) {
            metrics.speed = (this.activity.average_speed * 3.6).toFixed(1);
        }
        return metrics;
    }

    formatTime(seconds) {
        const hrs = Math.floor(seconds / 3600);
        const mins = Math.floor((seconds % 3600) / 60);
        const secs = Math.floor(seconds % 60);
        if (hrs > 0) return `${hrs}:${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
        return `${mins}:${secs.toString().padStart(2, '0')}`;
    }

    async drawEnhancedMetricCard(x, y, width, height, label, value, unit, icon, accentColor) {
        this.ctx.save();
        this.ctx.shadowColor = 'rgba(0,0,0,0.2)';
        this.ctx.shadowBlur = 15;
        this.ctx.shadowOffsetY = 5;

        const cardGradient = this.ctx.createLinearGradient(x, y, x, y + height);
        const isDarkTheme = ['gradient-blue', 'gradient-red', 'dark'].includes(this.options.colorTheme);
        if (isDarkTheme) {
            cardGradient.addColorStop(0, 'rgba(255,255,255,0.15)');
            cardGradient.addColorStop(1, 'rgba(255,255,255,0.1)');
        } else {
            cardGradient.addColorStop(0, 'rgba(255,255,255,0.95)');
            cardGradient.addColorStop(1, 'rgba(255,255,255,0.85)');
        }
        this.ctx.fillStyle = cardGradient;
        this.roundRect(x, y, width, height, 16);
        this.ctx.shadowColor = 'transparent'; this.ctx.shadowBlur = 0;

        this.ctx.fillStyle = accentColor;
        this.roundRect(x, y, width, 6, {tl: 16, tr: 16, bl: 0, br: 0});

        this.ctx.fillStyle = isDarkTheme ? 'rgba(255,255,255,0.7)' : 'rgba(0,0,0,0.6)';
        this.ctx.font = '500 18px "Montserrat", sans-serif'; // Increased label font
        this.ctx.textAlign = 'left';
        this.ctx.fillText(label, x + 20, y + 35); // Adjusted Y

        const valueText = unit ? `${value} ${unit}` : value;
        this.ctx.fillStyle = isDarkTheme ? '#fff' : '#000';
        this.ctx.font = '700 36px "Montserrat", sans-serif'; // Increased value font
        this.ctx.fillText(valueText, x + 20, y + height - 30); // Adjusted Y

        this.ctx.font = '36px Arial'; // Icon font size
        this.ctx.textAlign = 'right';
        this.ctx.fillText(icon, x + width - 25, y + height / 2 + 10); // Adjusted icon position
        this.ctx.restore();
    }

    roundRect(x, y, width, height, radius) {
        if (typeof radius === 'number') {
            radius = {tl: radius, tr: radius, br: radius, bl: radius};
        } else { // Ensure all radii are defined
            const defaultRadius = 0;
            radius = {
                tl: radius.tl === undefined ? defaultRadius : radius.tl,
                tr: radius.tr === undefined ? defaultRadius : radius.tr,
                br: radius.br === undefined ? defaultRadius : radius.br,
                bl: radius.bl === undefined ? defaultRadius : radius.bl,
            };
        }
        this.ctx.beginPath();
        this.ctx.moveTo(x + radius.tl, y);
        this.ctx.lineTo(x + width - radius.tr, y);
        this.ctx.quadraticCurveTo(x + width, y, x + width, y + radius.tr);
        this.ctx.lineTo(x + width, y + height - radius.br);
        this.ctx.quadraticCurveTo(x + width, y + height, x + width - radius.br, y + height);
        this.ctx.lineTo(x + radius.bl, y + height);
        this.ctx.quadraticCurveTo(x, y + height, x, y + height - radius.bl);
        this.ctx.lineTo(x, y + radius.tl);
        this.ctx.quadraticCurveTo(x, y, x + radius.tl, y);
        this.ctx.closePath();
        this.ctx.fill();
    }

    async drawMap(currentY) { // Accept currentY to position map dynamically
        if (!this.options.includeMap || !this.activity.map?.summary_polyline) return currentY;

        const mapTopMargin = 30;
        const mapY = currentY + mapTopMargin;
        const mapWidth = this.canvas.width * 0.9; // Slightly wider map
        const mapHeight = mapWidth * 0.6;
        const mapX = (this.canvas.width - mapWidth) / 2;
        const spacingAfterMap = 40;

        this.ctx.save();
        this.ctx.shadowColor = 'rgba(0,0,0,0.3)';
        this.ctx.shadowBlur = 20;
        this.ctx.shadowOffsetY = 10;
        const isDarkTheme = ['gradient-blue', 'gradient-red', 'dark'].includes(this.options.colorTheme);
        this.ctx.fillStyle = isDarkTheme ? 'rgba(255,255,255,0.1)' : 'rgba(255,255,255,0.9)';
        this.roundRect(mapX, mapY, mapWidth, mapHeight, 16);
        this.ctx.shadowColor = 'transparent'; this.ctx.shadowBlur = 0;

        this.ctx.fillStyle = isDarkTheme ? '#fff' : '#333';
        this.ctx.font = '600 22px "Montserrat", sans-serif'; // Larger title
        this.ctx.textAlign = 'left';
        this.ctx.fillText('ROUTE', mapX + 25, mapY + 35); // Adjusted padding

        const points = this.decodePolyline(this.activity.map.summary_polyline);
        if (points.length > 0) {
            let minLat = points[0][0], maxLat = points[0][0], minLng = points[0][1], maxLng = points[0][1];
            points.forEach(p => {
                minLat = Math.min(minLat, p[0]); maxLat = Math.max(maxLat, p[0]);
                minLng = Math.min(minLng, p[1]); maxLng = Math.max(maxLng, p[1]);
            });
            const latR = maxLat - minLat, lngR = maxLng - minLng;
            const pLat = latR === 0 ? 0.001 : latR * 0.1, pLng = lngR === 0 ? 0.001 : lngR * 0.1;
            minLat -= pLat; maxLat += pLat; minLng -= pLng; maxLng += pLng;

            const drawX = mapX + 20, drawY = mapY + 60; // More space for title
            const drawW = mapWidth - 40, drawH = mapHeight - 80; // More space for title/attr

            this.ctx.beginPath();
            points.forEach((p, i) => {
                const x = drawX + (drawW * (p[1] - minLng) / (maxLng - minLng || 1));
                const y = drawY + (drawH - (drawH * (p[0] - minLat) / (maxLat - minLat || 1)));
                if (i === 0) this.ctx.moveTo(x, y); else this.ctx.lineTo(x, y);
            });
            this.ctx.strokeStyle = this.getRouteColor();
            this.ctx.lineWidth = 4;
            this.ctx.lineCap = 'round'; this.ctx.lineJoin = 'round';
            this.ctx.shadowColor = this.getRouteColor(); this.ctx.shadowBlur = 8; // Enhanced glow
            this.ctx.stroke();
            this.ctx.shadowColor = 'transparent'; this.ctx.shadowBlur = 0;

            const sP = points[0], eP = points[points.length - 1];
            const sX = drawX + (drawW * (sP[1] - minLng) / (maxLng - minLng || 1));
            const sY = drawY + (drawH - (drawH * (sP[0] - minLat) / (maxLat - minLat || 1)));
            const eX = drawX + (drawW * (eP[1] - minLng) / (maxLng - minLng || 1));
            const eY = drawY + (drawH - (drawH * (eP[0] - minLat) / (maxLat - minLat || 1)));
            this.drawMapMarker(sX, sY, '#4CAF50'); this.drawMapMarker(eX, eY, '#F44336');
        }
        this.ctx.font = '14px "Montserrat", sans-serif'; // Larger attribution
        this.ctx.fillStyle = isDarkTheme ? 'rgba(255,255,255,0.5)' : 'rgba(0,0,0,0.5)';
        this.ctx.textAlign = 'right';
        this.ctx.fillText('Map data © Strava', mapX + mapWidth - 20, mapY + mapHeight - 20); // Adjusted pos
        this.ctx.restore();
        return mapY + mapHeight + spacingAfterMap;
    }

    drawMapMarker(x, y, color) {
        this.ctx.save();
        this.ctx.shadowColor = 'rgba(0,0,0,0.4)'; // Darker shadow
        this.ctx.shadowBlur = 8; this.ctx.shadowOffsetY = 2;
        this.ctx.beginPath(); this.ctx.arc(x, y, 9, 0, Math.PI * 2); // Larger marker
        this.ctx.fillStyle = color; this.ctx.fill();
        this.ctx.beginPath(); this.ctx.arc(x, y, 5, 0, Math.PI * 2); // Larger inner
        this.ctx.fillStyle = '#fff'; this.ctx.fill();
        this.ctx.restore();
    }

    decodePolyline(encoded) { /* ... (same as provided) ... */ 
        let points = [];
        let index = 0, lat = 0, lng = 0;
        while (index < encoded.length) {
            let b, shift = 0, result = 0;
            do {
                b = encoded.charCodeAt(index++) - 63;
                result |= (b & 0x1f) << shift;
                shift += 5;
            } while (b >= 0x20);
            let dlat = ((result & 1) ? ~(result >> 1) : (result >> 1));
            lat += dlat;
            shift = 0; result = 0;
            do {
                b = encoded.charCodeAt(index++) - 63;
                result |= (b & 0x1f) << shift;
                shift += 5;
            } while (b >= 0x20);
            let dlng = ((result & 1) ? ~(result >> 1) : (result >> 1));
            lng += dlng;
            points.push([lat * 1e-5, lng * 1e-5]);
        }
        return points;
    }


    getRouteColor() {
        switch(this.options.colorTheme) {
            case 'gradient-blue': return '#6fa8dc'; // Lighter blue for visibility
            case 'gradient-red': return '#e06666'; // Lighter red
            case 'dark': return '#f6b26b'; // Lighter orange
            default: return '#ff8c69'; // Lighter deep orange
        }
    }

    async drawHeartRateAndPaceCharts(yPosition) {
        if (!this.options.includeHeartRate && !this.options.includePace) return yPosition;

        const chartWidth = this.canvas.width * 0.42;
        const chartHeight = 190; // Increased height
        const spacing = 30; // Spacing between charts
        const chartTopMargin = 30; // Margin above charts
        const currentChartY = yPosition + chartTopMargin;

        // Calculate X positions for centered two-chart layout
        const totalChartsWidth = (chartWidth * 2) + spacing;
        const chartStartX = (this.canvas.width - totalChartsWidth) / 2;
        
        const hrX = chartStartX;
        const paceX = chartStartX + chartWidth + spacing;
        let chartDrawn = false;

        if (this.options.includeHeartRate && this.activity.has_heartrate) {
            await this.drawHeartRateChart(hrX, currentChartY, chartWidth, chartHeight);
            chartDrawn = true;
        }

        if (this.options.includePace) {
            const currentPaceX = (this.options.includeHeartRate && this.activity.has_heartrate && chartDrawn) ? paceX : hrX; // If only pace, use first slot
            await this.drawPaceChart(currentPaceX, currentChartY, chartWidth, chartHeight);
            chartDrawn = true;
        }
        
        return chartDrawn ? currentChartY + chartHeight + spacing : yPosition; // Return new Y pos
    }

    async drawHeartRateChart(x, y, width, height) { /* ... (similar to provided, with minor layout tweaks) ... */ 
        if (!this.activity.has_heartrate) return;
        this.ctx.save();
        this.ctx.shadowColor = 'rgba(0,0,0,0.2)'; this.ctx.shadowBlur = 15; this.ctx.shadowOffsetY = 5;
        const isDarkTheme = ['gradient-blue', 'gradient-red', 'dark'].includes(this.options.colorTheme);
        this.ctx.fillStyle = isDarkTheme ? 'rgba(255,255,255,0.1)' : 'rgba(255,255,255,0.9)';
        this.roundRect(x, y, width, height, 16);
        this.ctx.shadowColor = 'transparent'; this.ctx.shadowBlur = 0;

        this.ctx.fillStyle = isDarkTheme ? '#fff' : '#333';
        this.ctx.font = '600 20px "Montserrat", sans-serif'; // Title font
        this.ctx.textAlign = 'left';
        this.ctx.fillText('HEART RATE', x + 20, y + 30);

        const avgHR = this.activity.average_heartrate;
        const maxHR = this.activity.max_heartrate;
        const graphX = x + 20, graphY = y + 50;
        const graphWidth = width - 40, graphHeight = height - 95; // More space for text

        this.ctx.strokeStyle = isDarkTheme ? 'rgba(255,255,255,0.15)' : 'rgba(0,0,0,0.1)'; // Grid lines
        this.ctx.lineWidth = 1;
        for (let i = 0; i <= 4; i++) {
            const lineY = graphY + (graphHeight * i / 4);
            this.ctx.beginPath(); this.ctx.moveTo(graphX, lineY); this.ctx.lineTo(graphX + graphWidth, lineY); this.ctx.stroke();
        }

        const numPoints = 30; const hrPoints = []; let lastY = graphY + graphHeight * 0.7;
        for (let i = 0; i <= numPoints; i++) {
            const pX = graphX + (graphWidth * i / numPoints);
            let pY = (i === 0) ? lastY : lastY + (graphHeight * (Math.random() * 0.2 - 0.1 + Math.sin(i / 3) * 0.15));
            pY = Math.max(graphY, Math.min(graphY + graphHeight, pY));
            hrPoints.push({ x: pX, y: pY }); lastY = pY;
        }
        
        this.ctx.beginPath(); this.ctx.moveTo(graphX, graphY + graphHeight);
        hrPoints.forEach(p => this.ctx.lineTo(p.x, p.y));
        this.ctx.lineTo(graphX + graphWidth, graphY + graphHeight); this.ctx.closePath();
        const hrGradient = this.ctx.createLinearGradient(0, graphY, 0, graphY + graphHeight);
        hrGradient.addColorStop(0, 'rgba(231, 76, 60, 0.7)'); hrGradient.addColorStop(1, 'rgba(231, 76, 60, 0.1)');
        this.ctx.fillStyle = hrGradient; this.ctx.fill();

        this.ctx.beginPath();
        hrPoints.forEach((p, i) => { if (i === 0) this.ctx.moveTo(p.x, p.y); else this.ctx.lineTo(p.x, p.y); });
        this.ctx.strokeStyle = '#e74c3c'; this.ctx.lineWidth = 3; this.ctx.stroke();

        this.ctx.fillStyle = '#e74c3c';
        this.ctx.font = '700 34px "Montserrat", sans-serif'; // Main value
        this.ctx.textAlign = 'center';
        this.ctx.fillText(`${Math.round(avgHR || 0)} bpm`, x + width / 2, y + height - 40);
        if (maxHR) {
            this.ctx.font = '600 18px "Montserrat", sans-serif'; // Sub value
            this.ctx.fillText(`MAX: ${Math.round(maxHR)} bpm`, x + width / 2, y + height - 15);
        }
        this.ctx.restore();
    }


    async drawPaceChart(x, y, width, height) { /* ... (similar to provided, with minor layout tweaks) ... */ 
        this.ctx.save();
        this.ctx.shadowColor = 'rgba(0,0,0,0.2)'; this.ctx.shadowBlur = 15; this.ctx.shadowOffsetY = 5;
        const isDarkTheme = ['gradient-blue', 'gradient-red', 'dark'].includes(this.options.colorTheme);
        this.ctx.fillStyle = isDarkTheme ? 'rgba(255,255,255,0.1)' : 'rgba(255,255,255,0.9)';
        this.roundRect(x, y, width, height, 16);
        this.ctx.shadowColor = 'transparent'; this.ctx.shadowBlur = 0;

        this.ctx.fillStyle = isDarkTheme ? '#fff' : '#333';
        this.ctx.font = '600 20px "Montserrat", sans-serif'; // Title
        this.ctx.textAlign = 'left';
        this.ctx.fillText('PACE', x + 20, y + 30);

        let paceDisplay = "N/A"; const unitText = this.activity.type === 'Run' ? '/km' : 'km/h';
        if (this.activity.average_speed > 0) {
            if (this.activity.type === 'Run') {
                const ps = 1000 / this.activity.average_speed;
                paceDisplay = `${Math.floor(ps / 60)}:${Math.round(ps % 60).toString().padStart(2, '0')}`;
            } else { paceDisplay = (this.activity.average_speed * 3.6).toFixed(1); }
        }

        const graphX = x + 20, graphY = y + 50;
        const graphWidth = width - 40, graphHeight = height - 95; // More space for text

        this.ctx.strokeStyle = isDarkTheme ? 'rgba(255,255,255,0.15)' : 'rgba(0,0,0,0.1)'; // Grid
        this.ctx.lineWidth = 1;
        for (let i = 0; i <= 4; i++) {
            const lY = graphY + (graphHeight * i / 4);
            this.ctx.beginPath(); this.ctx.moveTo(graphX, lY); this.ctx.lineTo(graphX + graphWidth, lY); this.ctx.stroke();
        }

        const barCount = 12, barSpace = 3;
        const barW = (graphWidth - (barCount - 1) * barSpace) / barCount;
        for (let i = 0; i < barCount; i++) {
            const barH = (Math.random() * 0.6 + 0.2) * graphHeight;
            const barCurrentX = graphX + i * (barW + barSpace);
            const barCurrentY = graphY + graphHeight - barH;
            const barGrad = this.ctx.createLinearGradient(barCurrentX, barCurrentY, barCurrentX, barCurrentY + barH);
            barGrad.addColorStop(0, 'rgba(52, 152, 219, 0.9)'); // Pace blue
            barGrad.addColorStop(1, 'rgba(52, 152, 219, 0.3)');
            this.ctx.fillStyle = barGrad;
            this.roundRect(barCurrentX, barCurrentY, barW, barH, {tl: 3, tr: 3, bl: 0, br: 0});
        }

        this.ctx.fillStyle = '#3498db'; // Pace blue
        this.ctx.font = '700 34px "Montserrat", sans-serif'; // Main value
        this.ctx.textAlign = 'center';
        this.ctx.fillText(`${paceDisplay} ${unitText}`, x + width / 2, y + height - 40);

        if (this.activity.max_speed) {
            let maxPaceDisp;
            if (this.activity.type === 'Run') {
                const mps = 1000 / this.activity.max_speed;
                maxPaceDisp = `${Math.floor(mps / 60)}:${Math.round(mps % 60).toString().padStart(2, '0')} ${unitText}`;
            } else { maxPaceDisp = `${(this.activity.max_speed * 3.6).toFixed(1)} ${unitText}`; }
            this.ctx.font = '600 18px "Montserrat", sans-serif'; // Sub value
            this.ctx.fillText(`BEST: ${maxPaceDisp}`, x + width / 2, y + height - 15);
        }
        this.ctx.restore();
    }


    async drawAdditionalStats(yPosition) { /* ... (similar to provided, with minor layout tweaks) ... */ 
        const statItems = [];
        if (this.activity.average_cadence) statItems.push({ v: `${Math.round(this.activity.average_cadence)}`, l: 'CADENCE', c: '#9b59b6', i: '⚙️' });
        if (this.activity.suffer_score) statItems.push({ v: `${this.activity.suffer_score}`, l: 'SUFFER SCORE', c: '#e67e22', i: '🔥' });
        if (this.activity.kudos_count !== undefined) statItems.push({ v: `${this.activity.kudos_count}`, l: 'KUDOS', c: '#f1c40f', i: '👍' });

        if (statItems.length === 0) return yPosition;

        const topMargin = 30;
        const currentY = yPosition + topMargin;
        const containerWidth = this.canvas.width * 0.9;
        const containerHeight = 130; // Increased height
        const containerX = (this.canvas.width - containerWidth) / 2;
        const spacingAfter = 40;

        this.ctx.save();
        this.ctx.shadowColor = 'rgba(0,0,0,0.2)'; this.ctx.shadowBlur = 15; this.ctx.shadowOffsetY = 5;
        const isDarkTheme = ['gradient-blue', 'gradient-red', 'dark'].includes(this.options.colorTheme);
        this.ctx.fillStyle = isDarkTheme ? 'rgba(255,255,255,0.1)' : 'rgba(255,255,255,0.9)';
        this.roundRect(containerX, currentY, containerWidth, containerHeight, 16);
        this.ctx.shadowColor = 'transparent'; this.ctx.shadowBlur = 0;

        this.ctx.fillStyle = isDarkTheme ? '#fff' : '#333';
        this.ctx.font = '600 20px "Montserrat", sans-serif'; // Title
        this.ctx.textAlign = 'left';
        this.ctx.fillText('ADDITIONAL STATS', containerX + 25, currentY + 30);

        const statBoxWidth = containerWidth / statItems.length;
        const iconY = currentY + 65;
        const valueY = currentY + 70; // Value slightly lower than icon
        const labelY = currentY + 100;

        statItems.forEach((stat, index) => {
            const statCenterX = containerX + (index * statBoxWidth) + (statBoxWidth / 2);
            
            this.ctx.font = '30px Arial'; // Icon
            this.ctx.fillStyle = stat.c;
            this.ctx.textAlign = 'center';
            this.ctx.fillText(stat.i, statCenterX, iconY);
            
            this.ctx.font = '700 30px "Montserrat", sans-serif'; // Value
            this.ctx.fillStyle = isDarkTheme ? '#fff' : '#000';
            this.ctx.fillText(stat.v, statCenterX, valueY + 5); // Value below icon, slightly offset if needed

            this.ctx.fillStyle = isDarkTheme ? 'rgba(255,255,255,0.7)' : 'rgba(0,0,0,0.6)';
            this.ctx.font = '500 16px "Montserrat", sans-serif'; // Label
            this.ctx.fillText(stat.l, statCenterX, labelY);
        });

        this.ctx.restore();
        return currentY + containerHeight + spacingAfter;
    }


    async drawCustomText(yPosition) { /* ... (similar to provided, with minor layout tweaks) ... */ 
        if (!this.options.customText || this.options.customText.trim() === '') return yPosition;
        
        const topMargin = 30;
        const currentY = yPosition + topMargin;
        const containerWidth = this.canvas.width * 0.9;
        const containerX = (this.canvas.width - containerWidth) / 2;
        const spacingAfter = 40;
        const isDarkTheme = ['gradient-blue', 'gradient-red', 'dark'].includes(this.options.colorTheme);
        
        this.ctx.font = 'italic 500 24px "Montserrat", sans-serif'; // Text font
        const words = this.options.customText.split(' ');
        let line = ''; const lines = []; const maxWidth = containerWidth - 100;
        for (let n = 0; n < words.length; n++) {
            const testLine = line + words[n] + ' ';
            if (this.ctx.measureText(testLine).width > maxWidth && n > 0) {
                lines.push(line.trim()); line = words[n] + ' ';
            } else { line = testLine; }
        }
        lines.push(line.trim());
        const textBlockHeight = lines.length * 35; // Line height
        const containerHeight = Math.max(120, textBlockHeight + 70); // Padding

        this.ctx.save();
        this.ctx.shadowColor = 'rgba(0,0,0,0.2)'; this.ctx.shadowBlur = 15; this.ctx.shadowOffsetY = 5;
        this.ctx.fillStyle = isDarkTheme ? 'rgba(255,255,255,0.1)' : 'rgba(255,255,255,0.9)';
        this.roundRect(containerX, currentY, containerWidth, containerHeight, 16);
        this.ctx.shadowColor = 'transparent'; this.ctx.shadowBlur = 0;

        this.ctx.fillStyle = isDarkTheme ? 'rgba(255,255,255,0.2)' : 'rgba(0,0,0,0.1)';
        this.ctx.font = 'bold 90px "Georgia", serif'; // Quotes
        this.ctx.textAlign = 'left'; this.ctx.fillText('“', containerX + 25, currentY + 75); // Adjusted quote pos
        this.ctx.textAlign = 'right'; this.ctx.fillText('”', containerX + containerWidth - 25, currentY + containerHeight - 15); // Adjusted quote pos

        this.ctx.fillStyle = isDarkTheme ? '#fff' : '#333';
        this.ctx.font = 'italic 500 24px "Montserrat", sans-serif'; // Text
        this.ctx.textAlign = 'center';
        let textLineY = currentY + (containerHeight - textBlockHeight) / 2 + 8; // Centered text block + baseline offset
        lines.forEach(l => {
            this.ctx.fillText(l, containerX + containerWidth / 2, textLineY);
            textLineY += 35;
        });

        this.ctx.restore();
        return currentY + containerHeight + spacingAfter;
    }


    async drawFooter() { /* ... (similar to provided, with minor layout tweaks) ... */ 
        const footerHeight = 150; // Increased height
        const footerY = this.canvas.height - footerHeight;
        this.ctx.save();
        this.ctx.fillStyle = 'rgba(0,0,0,0.7)'; // Darker footer
        this.ctx.fillRect(0, footerY, this.canvas.width, footerHeight);

        const profileSize = 80;
        const profileX = 100; // More padding
        const profileY = footerY + footerHeight / 2;

        this.ctx.shadowColor = 'rgba(0,0,0,0.5)'; this.ctx.shadowBlur = 15;
        this.ctx.beginPath(); this.ctx.arc(profileX, profileY, profileSize / 2, 0, Math.PI * 2);
        this.ctx.fillStyle = '#ddd'; this.ctx.fill();
        // TODO: Add logic to draw actual athlete profile picture if available
        this.ctx.strokeStyle = '#fff'; this.ctx.lineWidth = 4; // Thicker border
        this.ctx.stroke();
        this.ctx.shadowColor = 'transparent'; this.ctx.shadowBlur = 0;
        
        // Fallback icon (can be hidden if profile picture is drawn)
        this.ctx.fillStyle = '#555'; this.ctx.font = '40px Arial';
        this.ctx.textAlign = 'center'; this.ctx.textBaseline = 'middle';
        this.ctx.fillText('👤', profileX, profileY);

        const textX = profileX + profileSize / 2 + 30; // More space for text
        this.ctx.fillStyle = '#fff';
        this.ctx.font = '700 30px "Montserrat", sans-serif'; // Larger name
        this.ctx.textAlign = 'left';
        const athleteName = `${this.athlete.firstname || ''} ${this.athlete.lastname || ''}`.trim() || 'Athlete Name';
        this.ctx.fillText(athleteName, textX, profileY - 18); // Adjusted Y

        this.ctx.font = '500 20px "Montserrat", sans-serif'; // Larger username
        if (this.athlete.username) {
            this.ctx.fillText(`@${this.athlete.username}`, textX, profileY + 18); // Adjusted Y
        } else {
            this.ctx.fillText('Strava Activity', textX, profileY + 18);
        }

        this.ctx.font = '500 16px "Montserrat", sans-serif'; // Copyright text
        this.ctx.fillStyle = 'rgba(255,255,255,0.7)';
        this.ctx.textAlign = 'right';
        this.ctx.fillText('Generated by Strava Activity Visualizer', this.canvas.width - 40, this.canvas.height - 30); // Adjusted text & pos
        this.ctx.restore();
    }


    async generateImage() {
        if (!this.ctx || !this.activity || !this.athlete) {
            console.error('Cannot generate image: context, activity, or athlete data is missing.');
            const loadingOverlay = document.getElementById('image-loading');
            if (loadingOverlay) loadingOverlay.style.display = 'none';
            return this.canvas; // Or throw error
        }

        const loadingOverlay = document.getElementById('image-loading');
        if (loadingOverlay) loadingOverlay.style.display = 'flex';
        
        this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);

        try {
            await this.loadFonts(); // Ensure fonts are ready
            await this.drawBackground();
            await this.drawHeader();

            let currentY = await this.drawMetricCards();

            if (this.options.includeMap && this.activity.map?.summary_polyline) {
                currentY = await this.drawMap(currentY);
            }

            if (this.options.includeHeartRate || this.options.includePace) {
                currentY = await this.drawHeartRateAndPaceCharts(currentY);
            }
            
            currentY = await this.drawAdditionalStats(currentY);

            if (this.options.customText && this.options.customText.trim() !== '') {
                currentY = await this.drawCustomText(currentY);
            }

            await this.drawFooter(); // Footer is fixed at the bottom

        } catch (error) {
            console.error('Error generating image:', error);
            this.ctx.fillStyle = 'red';
            this.ctx.font = '24px Arial';
            this.ctx.textAlign = 'center';
            this.ctx.fillText('Error generating image. See console.', this.canvas.width / 2, this.canvas.height / 2);
        } finally {
            if (loadingOverlay) loadingOverlay.style.display = 'none';
        }
        return this.canvas;
    }

    async exportAsImage() {
        return this.canvas.toDataURL('image/png');
    }

    async exportAsBlob() {
        return new Promise(resolve => {
            this.canvas.toBlob(blob => resolve(blob), 'image/png', 1.0);
        });
    }

    updateOptions(newOptions) {
        this.options = { ...this.options, ...newOptions };
        // No need to call loadFonts() again unless fonts change with options
        return this.generateImage();
    }
}

// Example Usage (for testing in browser console if needed):
// Ensure activityData and athleteData are defined globally or passed appropriately.
// const activityData = { ... }; 
// const athleteData = { ... };
// const generator = new EnhancedActivityImageGenerator(activityData, athleteData);
// generator.generateImage().then(canvas => {
//   console.log('Image generated on canvas:', canvas);
// });

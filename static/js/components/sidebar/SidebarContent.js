import { LanguageService } from "../../services/LanguageService.js";
import { stations } from "../station/stations-list.js";

export class SidebarContent {
    constructor(entity, type) {
        this.entity = entity;
        this.type = type;
        this.content = document.createElement('div');
        this.currentLanguage = LanguageService.getCurrentLanguage();
    }

    generateRouteDetailsLink() {
        const baseUrl = '';
        const routeRef = this.entity.ref;
        
        if (this.currentLanguage === 'en') {
            return `${baseUrl}/routes/${routeRef}/`;
        } else {
            return `${baseUrl}/${this.currentLanguage}/routes/${routeRef}/`;
        }
    }

    generateStationDetailsLink() {
        const baseUrl = '';
        const stationCode = this.entity.code;
        
        if (this.currentLanguage === 'en') {
            return `${baseUrl}/stations/${stationCode}/`;
        } else {
            return `${baseUrl}/${this.currentLanguage}/stations/${stationCode}/`;
        }
    }

    getTitle() {
        if (this.type === 'station') {
            return this.entity[`name_${this.currentLanguage}`];
        }
        if (this.type === 'route') {
            return LanguageService.translate('train') + ' ' + this.entity.ref + ': ' + this.entity.routeData[`name:${this.currentLanguage}`];
        }
    }

    getBody() {
        if (this.type === 'station') {
            this.content.innerHTML = '';
            
            // Generate station details link
            const stationDetailsLink = this.generateStationDetailsLink();
            
            // Add station details link at the top
            this.content.innerHTML += `
                <div class="station-details-link-container">
                    <a href="${stationDetailsLink}" class="station-details-link" target="_blank">
                        ${LanguageService.translate('view_station_details')}
                    </a>
                </div>
            `;
            
            // Group routes by categories
            const routeGroups = [
                {
                    key: 'departure',
                    titleKey: 'departures',
                    routes: this.entity.routes.departure || []
                },
                {
                    key: 'arrival', 
                    titleKey: 'arrivals',
                    routes: this.entity.routes.arrival || []
                },
                {
                    key: 'via',
                    titleKey: 'passes_through', 
                    routes: this.entity.routes.via || []
                }
            ];

            // Generate HTML for each group
            routeGroups.forEach(group => {
                if (group.routes.length > 0) {
                    const groupHTML = this.renderRouteGroup(group);
                    this.content.innerHTML += groupHTML;
                }
            });

            return this.content;
        }

        if (this.type === 'route') {
            this.content.innerHTML = '';
            
            // Get start and end stations
            const startStation = this.entity.routeData.stations.find(station => station.role === 'start');
            const endStation = this.entity.routeData.stations.find(station => station.role === 'end');
            
            // Generate route details link
            const routeDetailsLink = this.generateRouteDetailsLink();
            
            let routeHTML = `
                <div class="back-to-train-list-container">
                    <button class="back-to-train-list" data-action="back-to-train-list">
                        ${LanguageService.translate('back_to_train_list')}
                    </button>
                </div>
            `;
            
            // Add timeline with start and end stations
            if (startStation || endStation) {
                routeHTML += `<ul class="route-timeline">`;
                
                // Add start station
                if (startStation) {
                    const startTime = startStation.departure_time !== '-' ? startStation.departure_time : startStation.arrival_time;
                    const startStationInfo = stations[startStation.code] || {};
                    const startStationName = startStationInfo[`name_${this.currentLanguage}`] || startStationInfo.name_en || startStation.code;
                    routeHTML += `
                        <li class="terminal">
                            <span class="station-time">${startTime || ''}</span>
                            <span class="route-station-name">${startStationName}</span>
                        </li>
                    `;
                }
                
                // Add end station  
                if (endStation) {
                    const endTime = endStation.arrival_time && endStation.arrival_time !== '-' ? endStation.arrival_time : endStation.departure_time;
                    const endStationInfo = stations[endStation.code] || {};
                    const endStationName = endStationInfo[`name_${this.currentLanguage}`] || endStationInfo.name_en || endStation.code;
                    routeHTML += `
                        <li class="terminal">
                            <span class="station-time">${endTime || ''}</span>
                            <span class="route-station-name">${endStationName}</span>
                        </li>
                    `;
                }
                
                routeHTML += `</ul>`;
            }
            
            this.content.innerHTML += routeHTML;
            this.content.innerHTML += `
                <div class="route-details-link-container">
                    <a href="${routeDetailsLink}" class="route-details-link" target="_blank">
                        ${LanguageService.translate('view_route_details')}
                    </a>
                </div>
            `;
            return this.content;
        }
    }

    renderRouteGroup(group) {
        const groupTitle = LanguageService.translate(group.titleKey);
        
        // Sort routes by time
        const sortedRoutes = [...group.routes].filter(route => !route.start_date || route.start_date <= Date.now()).sort((a, b) => {
            const timeA = this.getTimeInfo(a, group.key);
            const timeB = this.getTimeInfo(b, group.key);
            
            // If one of the routes has no time, place it at the end
            if (!timeA && !timeB) return 0;
            if (!timeA) return 1;
            if (!timeB) return -1;
            
            // Compare time in HH:MM format
            return timeA.localeCompare(timeB);
        });
        
        const routesHTML = sortedRoutes.map(route => {
            const routeName = route[`name_${this.currentLanguage}`] || route.name_en;
            const timeInfo = this.getTimeInfo(route, group.key);
            
            return `
                <div class="route-line">
                    <div class="route-link" data-route-ref="${route.ref}">
                        <div class="route-header">
                            ${timeInfo ? `<span class="route-time">${timeInfo}</span>` : ''}
                            <div class="route-name">
                                <span class="route-label">${route.ref}</span>
                                <span class="route-destination">${routeName}</span>
                            </div>
                        </div>
                    </div>
                </div>
            `;
        }).join('');

        return `
            <div class="route-group">
                <h4 class="route-group-title">${groupTitle}</h4>
                <div class="route-group-content">
                    ${routesHTML}
                </div>
            </div>
        `;
    }

    getTimeInfo(route, groupType) {
        switch (groupType) {
            case 'departure':
                return route.departure_time && route.departure_time !== '-' ? route.departure_time : null;
            case 'arrival':
                return route.arrival_time && route.arrival_time !== '-' ? route.arrival_time : route.departure_time;
            case 'via':
                return route.arrival_time && route.arrival_time !== '-' ? route.arrival_time : route.departure_time;
            default:
                return null;
        }
    }
}
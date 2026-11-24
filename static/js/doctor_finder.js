/**
 * RuralCare AI - Doctor & Hospital Finder Controller
 * Interactive Leaflet.js OpenStreetMap integration with GPS and rural facility lookup.
 */

let doctorMap = null;
let doctorMarkers = [];
let userLocationMarker = null;
let userCoords = null; // {lat, lon}
let currentDoctors = [];

const DoctorFinder = {
    init: function() {
        this.loadFilters();
        this.initMap();
        this.searchDoctors();
    },

    initMap: function() {
        const mapContainer = document.getElementById("doctorMapContainer");
        if (!mapContainer || doctorMap) return;

        // Default center: Ramanagara rural health belt (12.7209, 77.2799)
        const defaultLat = 12.7209;
        const defaultLon = 77.2799;

        doctorMap = L.map("doctorMapContainer").setView([defaultLat, defaultLon], 10);

        L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
            attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
            maxZoom: 18
        }).addTo(doctorMap);
    },

    loadFilters: async function() {
        try {
            // Load districts
            const distResp = await fetch("/api/doctors/districts");
            const districts = await distResp.json();
            const distSelect = document.getElementById("filterDistrict");
            if (distSelect) {
                distSelect.innerHTML = `<option value="all" data-i18n="filterDistrict">${t("filterDistrict")}</option>`;
                districts.forEach(d => {
                    distSelect.innerHTML += `<option value="${d}">${d}</option>`;
                });
            }

            // Load specializations
            const specResp = await fetch("/api/doctors/specializations");
            const specs = await specResp.json();
            const specSelect = document.getElementById("filterSpecialty");
            if (specSelect) {
                specSelect.innerHTML = `<option value="all" data-i18n="filterSpecialty">${t("filterSpecialty")}</option>`;
                specs.forEach(s => {
                    specSelect.innerHTML += `<option value="${s}">${s}</option>`;
                });
            }
        } catch (e) {
            console.error("Error loading doctor filters:", e);
        }
    },

    getUserLocation: function() {
        if (!navigator.geolocation) {
            alert("Geolocation is not supported by your browser.");
            return;
        }

        const btn = document.getElementById("useLocationBtn");
        if (btn) btn.innerHTML = `<i class="fa-solid fa-spinner fa-spin me-1"></i> Detecting...`;

        navigator.geolocation.getCurrentPosition(
            (pos) => {
                userCoords = {
                    lat: pos.coords.latitude,
                    lon: pos.coords.longitude
                };
                if (btn) btn.innerHTML = `<i class="fa-solid fa-location-crosshairs me-1"></i> ${t("useLocationBtn")}`;
                this.updateUserMapMarker();
                this.searchDoctors();
            },
            (err) => {
                console.warn("Geolocation denied or error:", err.message);
                if (btn) btn.innerHTML = `<i class="fa-solid fa-location-dot me-1"></i> ${t("useLocationBtn")}`;
                alert("Location access denied or unavailable. Using default rural region.");
                this.searchDoctors();
            },
            { timeout: 8000 }
        );
    },

    updateUserMapMarker: function() {
        if (!doctorMap || !userCoords) return;

        if (userLocationMarker) {
            doctorMap.removeLayer(userLocationMarker);
        }

        const userIcon = L.divIcon({
            className: "user-loc-pin",
            html: `<div style="background-color: #2563eb; width: 18px; height: 18px; border-radius: 50%; border: 3px solid white; box-shadow: 0 0 10px rgba(37,99,235,0.8);"></div>`,
            iconSize: [18, 18],
            iconAnchor: [9, 9]
        });

        userLocationMarker = L.marker([userCoords.lat, userCoords.lon], { icon: userIcon })
            .addTo(doctorMap)
            .bindPopup("<b>Your Current Location</b>")
            .openPopup();

        doctorMap.setView([userCoords.lat, userCoords.lon], 11);
    },

    searchDoctors: async function() {
        const district = document.getElementById("filterDistrict")?.value || "all";
        const specialty = document.getElementById("filterSpecialty")?.value || "all";
        const facilityType = document.getElementById("filterFacility")?.value || "all";
        const emergencyOnly = document.getElementById("emergencyOnlyCheck")?.checked || false;

        let url = `/api/doctors/nearby?emergency_only=${emergencyOnly}`;
        if (district !== "all") url += `&district=${encodeURIComponent(district)}`;
        if (specialty !== "all") url += `&specialization=${encodeURIComponent(specialty)}`;
        if (facilityType !== "all") url += `&facility_type=${encodeURIComponent(facilityType)}`;

        if (userCoords) {
            url += `&lat=${userCoords.lat}&lon=${userCoords.lon}`;
        }

        try {
            const resp = await fetch(url);
            const doctors = await resp.json();
            currentDoctors = doctors;
            this.renderDoctorsList(doctors);
            this.plotDoctorsOnMap(doctors);
        } catch (err) {
            console.error("Error searching doctors:", err);
        }
    },

    renderDoctorsList: function(doctors) {
        const container = document.getElementById("doctorsListContainer");
        const countBadge = document.getElementById("doctorCountBadge");
        if (!container) return;

        if (countBadge) countBadge.innerText = `${doctors.length} Found`;

        if (doctors.length === 0) {
            container.innerHTML = `
                <div class="col-12 text-center p-4">
                    <i class="fa-solid fa-user-doctor fs-1 text-muted mb-2"></i>
                    <p class="text-muted">No healthcare facilities matching your criteria. Try changing filters or expanding distance.</p>
                </div>
            `;
            return;
        }

        container.innerHTML = "";
        doctors.forEach(doc => {
            const isGovt = doc.facility_type.includes("PHC") || doc.facility_type.includes("CHC") || doc.facility_type.includes("Hospital");
            const badgeClass = doc.is_emergency_capable ? "bg-danger" : "bg-primary";
            const distHtml = doc.distance_km !== null ? `<span class="badge bg-light text-dark border ms-2"><i class="fa-solid fa-route text-primary me-1"></i>${doc.distance_km} ${t("distanceKm")}</span>` : "";

            const card = document.createElement("div");
            card.className = "col-md-6 col-lg-4 mb-3";
            card.innerHTML = `
                <div class="card h-100 shadow-sm border-0 doctor-card">
                    <div class="card-body d-flex flex-column">
                        <div class="d-flex justify-content-between align-items-start mb-2">
                            <span class="badge ${badgeClass} mb-1">
                                ${doc.is_emergency_capable ? '<i class="fa-solid fa-truck-medical me-1"></i>24x7 Emergency' : doc.facility_type}
                            </span>
                            ${distHtml}
                        </div>
                        <h5 class="card-title fw-bold mb-1 text-dark">${doc.name}</h5>
                        <p class="text-muted small mb-2"><i class="fa-solid fa-stethoscope text-primary me-1"></i>${doc.specialization} (${doc.qualification || 'MBBS'})</p>
                        
                        <div class="facility-info bg-light p-2 rounded mb-3 small">
                            <div class="fw-semibold text-secondary"><i class="fa-solid fa-hospital me-1"></i>${doc.facility_name}</div>
                            <div class="text-muted"><i class="fa-solid fa-map-pin me-1"></i>${doc.address}, ${doc.district}</div>
                            <div class="text-success mt-1"><i class="fa-solid fa-clock me-1"></i>${doc.operating_hours || 'OPD Open'}</div>
                            <div class="text-primary mt-1"><i class="fa-solid fa-wallet me-1"></i>${doc.consultation_fee || t("feeFree")}</div>
                        </div>

                        <div class="mt-auto d-flex gap-2">
                            <a href="tel:${doc.phone}" class="btn btn-primary flex-fill fw-bold py-2">
                                <i class="fa-solid fa-phone me-1"></i> ${t("callNowBtn")}
                            </a>
                            <a href="https://www.google.com/maps/dir/?api=1&destination=${doc.latitude},${doc.longitude}" target="_blank" class="btn btn-outline-secondary py-2" title="Directions">
                                <i class="fa-solid fa-diamond-turn-right"></i>
                            </a>
                        </div>
                    </div>
                </div>
            `;
            container.appendChild(card);
        });
    },

    plotDoctorsOnMap: function(doctors) {
        if (!doctorMap) return;

        // Clear existing doctor markers
        doctorMarkers.forEach(m => doctorMap.removeLayer(m));
        doctorMarkers = [];

        const bounds = [];

        if (userCoords) {
            bounds.push([userCoords.lat, userCoords.lon]);
        }

        doctors.forEach(doc => {
            const markerColor = doc.is_emergency_capable ? "#dc2626" : "#059669";
            const iconHtml = `<div style="background-color: ${markerColor}; width: 28px; height: 28px; border-radius: 50%; color: white; display: flex; align-items: center; justify-content: center; border: 2px solid white; box-shadow: 0 2px 6px rgba(0,0,0,0.3);"><i class="fa-solid fa-hospital text-white" style="font-size: 13px;"></i></div>`;

            const customIcon = L.divIcon({
                className: "doc-map-pin",
                html: iconHtml,
                iconSize: [28, 28],
                iconAnchor: [14, 14]
            });

            const marker = L.marker([doc.latitude, doc.longitude], { icon: customIcon })
                .addTo(doctorMap)
                .bindPopup(`
                    <div style="min-width: 180px;">
                        <h6 style="margin: 0 0 4px; font-weight: bold;">${doc.name}</h6>
                        <div style="font-size: 12px; color: #4b5563;">${doc.specialization}</div>
                        <div style="font-size: 11px; color: #1f2937; margin: 4px 0;"><b>${doc.facility_name}</b></div>
                        <div style="font-size: 11px; color: #6b7280; margin-bottom: 6px;">${doc.address}</div>
                        <a href="tel:${doc.phone}" class="btn btn-sm btn-primary text-white w-100" style="padding: 3px 6px; font-size: 12px; text-decoration: none; display: block; text-align: center;">
                            <i class="fa-solid fa-phone"></i> Call ${doc.phone}
                        </a>
                    </div>
                `);

            doctorMarkers.push(marker);
            bounds.push([doc.latitude, doc.longitude]);
        });

        if (bounds.length > 0) {
            try {
                doctorMap.fitBounds(bounds, { padding: [40, 40], maxZoom: 13 });
            } catch (e) {
                console.warn("Could not fit map bounds:", e);
            }
        }
    }
};

function filterDoctorsBySpecialty(specialty) {
    const select = document.getElementById("filterSpecialty");
    if (!select) return;

    // Check if partial match exists in options
    for (let i = 0; i < select.options.length; i++) {
        if (select.options[i].text.toLowerCase().includes(specialty.toLowerCase())) {
            select.selectedIndex = i;
            break;
        }
    }
    DoctorFinder.searchDoctors();
}

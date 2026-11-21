document.addEventListener("DOMContentLoaded", function () {
  const form = document.getElementById("trip-form");
  const submitBtn = document.getElementById("submit-btn");
  const btnText = submitBtn?.querySelector(".btn-text");
  const btnSpinner = submitBtn?.querySelector(".btn-spinner");
  const loadingOverlay = document.getElementById("loading-overlay");
  const loadingMsg = document.getElementById("loading-msg");
  const timeline = document.getElementById("timeline");
  const weatherBox = document.getElementById("weather");
  const budgetSection = document.getElementById("budget-tracker");
  const suggestionsSection = document.getElementById("suggestions");
  const destInput = document.getElementById("dest");

  let map;

  if (!form) {
    console.error("Form not found.");
    return;
  }

  // ── Helpers ──────────────────────────────────────────────────
  function setLoading(active, message = "") {
    if (loadingOverlay) loadingOverlay.hidden = !active;
    if (loadingMsg && message) loadingMsg.textContent = message;
    if (btnText) btnText.hidden = active;
    if (btnSpinner) btnSpinner.hidden = !active;
    if (submitBtn) submitBtn.disabled = active;
  }

  function clearResults() {
    weatherBox.innerHTML = "";
    timeline.innerHTML = "";
    if (budgetSection) budgetSection.innerHTML = "";
    if (suggestionsSection) suggestionsSection.innerHTML = "";
    if (map) {
      map.off();
      map.remove();
      map = null;
    }
  }

  // ════════════════════════════════════════════════════════════
  // FORM SUBMIT
  // ════════════════════════════════════════════════════════════
  form.addEventListener("submit", async function (e) {
    e.preventDefault();

    const destination = destInput.value.trim();
    const startDate = form.startDate.value;
    const endDate = form.endDate.value;
    const budget = parseInt(form.budget.value) || 0;

    if (!destination || !startDate || !endDate) {
      timeline.innerHTML = `<p class="error-msg">Please fill in destination, start date, and end date.</p>`;
      return;
    }

    const tripStart = new Date(startDate);
    const tripEnd = new Date(endDate);
    const diffMs = tripEnd - tripStart;

    if (Number.isNaN(tripStart.getTime()) || Number.isNaN(tripEnd.getTime())) {
      timeline.innerHTML = `<p class="error-msg">Please enter valid travel dates.</p>`;
      return;
    }

    if (diffMs < 0) {
      timeline.innerHTML = `<p class="error-msg">End date cannot be earlier than start date.</p>`;
      return;
    }

    const numDays = Math.floor(diffMs / 86400000) + 1;

    clearResults();
    setLoading(true, `🔍 Finding attractions in ${destination}…`);

    try {
      // ── /plan-trip ───────────────────────────────────────────
      const planRes = await fetch("http://localhost:5000/plan-trip", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          destination,
          startDate,
          endDate,
          budget,
          numDays,
        }),
      });
      const planData = await planRes.json();
      console.log("✅ /plan-trip:", planData);

      if (planData.error) {
        timeline.innerHTML = `<p class="error-msg">❌ ${planData.error}</p>`;
        setLoading(false);
        return;
      }

      // ── Weather ──────────────────────────────────────────────
      renderWeather(planData.weather, destination, weatherBox);

      // ── Itinerary ────────────────────────────────────────────
      renderItinerary(planData.itinerary, timeline);

      // ── Budget ───────────────────────────────────────────────
      if (budgetSection) {
        const breakdown = planData.budgetBreakdown || {
          accommodation: Math.round(budget * 0.4),
          food: Math.round(budget * 0.2),
          transport: Math.round(budget * 0.15),
          activities: Math.round(budget * 0.15),
          misc: Math.round(budget * 0.1),
        };
        renderBudget(budget, breakdown, budgetSection);
      }

      // ── Map (use coordinates from backend — no extra request) ──
      const coords = planData.coordinates;
      if (coords?.lat && coords?.lon) {
        setLoading(true, "🗺️ Loading map…");
        initMap(
          coords.lat,
          coords.lon,
          destination,
          planData.itinerary,
          planData.attractions,
        );
      }

      setLoading(false);

      // ── Suggestions ──────────────────────────────────────────
      if (suggestionsSection) {
        suggestionsSection.innerHTML = `<p class="warn-msg">Loading nearby hotels and restaurants...</p>`;
      }
      try {
        const sugRes = await fetch("http://localhost:5000/suggestions", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ destination, budget }),
        });
        const sugData = await sugRes.json();
        console.log("✅ /suggestions:", sugData);
        if (suggestionsSection && sugData && !sugData.error) {
          renderSuggestions(sugData, suggestionsSection, map);
        }
      } catch (sugErr) {
        console.warn("Suggestions failed:", sugErr);
        if (suggestionsSection) {
          suggestionsSection.innerHTML = `<p class="warn-msg">⚠️ Could not load hotel/restaurant data. Check that the backend /suggestions endpoint is running.</p>`;
        }
      }
    } catch (err) {
      console.error("Form handler error:", err);
      timeline.innerHTML = `<p class="error-msg">❌ Could not connect to the server. Make sure <code>app.py</code> is running on localhost:5000.</p>`;
    } finally {
      setLoading(false);
    }
  });

  // ════════════════════════════════════════════════════════════
  // MAP — init with backend coords + drop attraction markers
  // ════════════════════════════════════════════════════════════
  function renderSuggestions(data, container, mapRef) {
    const hotels = data.hotels || [];
    const restaurants = data.restaurants || [];
    if (!hotels.length && !restaurants.length) {
      container.innerHTML = `<p class="warn-msg">No nearby hotels or restaurants found in OpenStreetMap for this destination.</p>`;
      return;
    }

    let html = `<h3 class="section-label">Hotels and Restaurants <span class="source-tag">via OpenStreetMap</span></h3><div class="suggestions-grid">`;

    if (hotels.length) {
      html += `
        <div class="sug-column">
          <h4 class="sug-col-title">Nearby Hotels</h4>
          ${hotels
            .map(
              (h) => `
            <div class="sug-card">
              <div class="sug-name">${h.name}</div>
              <div class="sug-meta">
                <span class="sug-badge hotel-badge">${h.type || "Hotel"}</span>
                ${h.rating ? `<span>${h.rating}</span>` : ""}
              </div>
              ${h.address?.trim() ? `<div class="sug-address">${h.address}</div>` : ""}
            </div>`,
            )
            .join("")}
        </div>`;

      if (mapRef) {
        hotels.forEach((h) => {
          if (!h.lat || !h.lon) return;
          const icon = L.divIcon({
            className: "emoji-icon hotel-icon",
            html: "H",
            iconSize: [26, 26],
          });
          L.marker([h.lat, h.lon], { icon })
            .addTo(mapRef)
            .bindPopup(
              `<strong>${h.name}</strong>${h.address ? `<br>${h.address}` : ""}`,
            );
        });
      }
    }

    if (restaurants.length) {
      html += `
        <div class="sug-column">
          <h4 class="sug-col-title">Nearby Restaurants</h4>
          ${restaurants
            .map(
              (r) => `
            <div class="sug-card">
              <div class="sug-name">${r.name}</div>
              <div class="sug-meta">
                <span class="sug-badge rest-badge">${r.cuisine || "Local"}</span>
                ${r.rating ? `<span>${r.rating}</span>` : ""}
                <span>${r.priceRange || "INR"}</span>
              </div>
              ${r.address?.trim() ? `<div class="sug-address">${r.address}</div>` : ""}
            </div>`,
            )
            .join("")}
        </div>`;

      if (mapRef) {
        restaurants.forEach((r) => {
          if (!r.lat || !r.lon) return;
          const icon = L.divIcon({
            className: "emoji-icon rest-icon",
            html: "R",
            iconSize: [26, 26],
          });
          L.marker([r.lat, r.lon], { icon })
            .addTo(mapRef)
            .bindPopup(`<strong>${r.name}</strong><br>${r.cuisine || "Local"}`);
        });
      }
    }

    html += `</div>`;
    container.innerHTML = html;
  }

  function initMap(lat, lon, destination, itinerary, attractions = []) {
    const container = document.getElementById("map");
    if (!container) return;

    map = L.map(container).setView([lat, lon], 12);
    L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
      attribution: "© OpenStreetMap contributors",
    }).addTo(map);

    // Destination pin
    L.marker([lat, lon])
      .addTo(map)
      .bindPopup(`<strong>📍 ${destination}</strong>`)
      .openPopup();

    const seenPlaces = new Set();
    const attractionIcon = L.divIcon({
      className: "emoji-icon",
      html: "ðŸŽ¯",
      iconSize: [24, 24],
    });

    // Attraction markers from itinerary (OpenTripMap coordinates)
    if (Array.isArray(itinerary)) {
      itinerary.forEach((day) => {
        (day.places || []).forEach((place) => {
          if (place.lat && place.lon) {
            const icon = L.divIcon({
              className: "emoji-icon",
              html: "🎯",
              iconSize: [24, 24],
            });
            L.marker([place.lat, place.lon], { icon })
              .addTo(map)
              .bindPopup(
                `🎯 <strong>${place.name}</strong><br>Day ${day.day} — ${day.title}`,
              );
          }
        });
      });
    }
  }

  // ════════════════════════════════════════════════════════════
  // RENDER: WEATHER
  // ════════════════════════════════════════════════════════════
  function renderWeather(weather, destination, container) {
    const hasNumericTemp =
      weather &&
      weather.temp !== undefined &&
      weather.temp !== null &&
      weather.temp !== "N/A" &&
      !Number.isNaN(Number(weather.temp));

    const summary = hasNumericTemp
      ? `🌡️ ${weather.temp}°C &nbsp;•&nbsp; ${weather.condition || "Variable weather"}`
      : `${weather?.condition || "Forecast unavailable"}`;

    container.innerHTML = `
      <div class="weather-card">
        <span class="weather-icon">🌤️</span>
        <div>
          <strong>${destination}</strong>
          <p>${summary}</p>
        </div>
        <div class="weather-source">via Open-Meteo</div>
      </div>`;
  }

  // ════════════════════════════════════════════════════════════
  // RENDER: ITINERARY
  // ════════════════════════════════════════════════════════════
  function renderItinerary(itinerary, container) {
    if (!itinerary?.length) {
      container.innerHTML = `<p class="warn-msg">No itinerary returned. Make sure OPENTRIPMAP_KEY is set in your .env file.</p>`;
      return;
    }

    let html = `<h3 class="section-label">🗺️ Day-by-Day Itinerary</h3><div class="itinerary-timeline">`;

    itinerary.forEach((item, i) => {
      if (typeof item === "string") {
        html += `
          <div class="itinerary-day">
            <div class="day-badge"><span class="day-num">Day ${i + 1}</span></div>
            <div class="day-content"><p>${item}</p></div>
          </div>`;
      } else {
        const activities = (
          Array.isArray(item.activities)
            ? item.activities
            : [item.activities || ""]
        )
          .map((a) => `<li>✅ ${a}</li>`)
          .join("");

        const placeCount = (item.places || []).length;
        const mapNote = placeCount
          ? `<span class="map-note">📍 ${placeCount} place${placeCount > 1 ? "s" : ""} on map</span>`
          : "";

        html += `
          <div class="itinerary-day">
            <div class="day-badge">
              <span class="day-num">Day ${item.day || i + 1}</span>
              ${item.date ? `<span class="day-date">${item.date}</span>` : ""}
            </div>
            <div class="day-content">
              <div class="day-header">
                <h4 class="day-title">${item.title || ""}</h4>
                ${mapNote}
              </div>
              <ul class="activity-list">${activities}</ul>
            </div>
          </div>`;
      }
    });

    html += `</div>`;
    container.innerHTML = html;
  }

  // ════════════════════════════════════════════════════════════
  // RENDER: BUDGET
  // ════════════════════════════════════════════════════════════
  function renderBudget(total, breakdown, container) {
    const cats = [
      { key: "accommodation", label: "🏨 Accommodation", color: "#4f46e5" },
      { key: "food", label: "🍽️ Food & Dining", color: "#06b6d4" },
      { key: "transport", label: "🚗 Transport", color: "#7c3aed" },
      { key: "activities", label: "🎯 Activities", color: "#10b981" },
      { key: "misc", label: "🛍️ Miscellaneous", color: "#f59e0b" },
    ];
    const spend = cats.reduce((s, c) => s + (breakdown[c.key] || 0), 0);
    const remaining = total - spend;

    const bars = cats
      .map((c) => {
        const amt = breakdown[c.key] || 0;
        const pct =
          total > 0 ? Math.min(100, (amt / total) * 100).toFixed(1) : 0;
        return `
        <div class="budget-row">
          <div class="budget-label-row">
            <span>${c.label}</span>
            <span class="budget-amount">₹${amt.toLocaleString("en-IN")}</span>
          </div>
          <div class="budget-bar-bg">
            <div class="budget-bar-fill" style="width:${pct}%;background:${c.color}"></div>
          </div>
        </div>`;
      })
      .join("");

    container.innerHTML = `
      <h3 class="section-label">💰 Budget Breakdown</h3>
      <div class="budget-card">
        <div class="budget-summary">
          <div class="budget-stat">
            <span class="stat-label">Total Budget</span>
            <span class="stat-value">₹${total.toLocaleString("en-IN")}</span>
          </div>
          <div class="budget-stat">
            <span class="stat-label">Estimated Spend</span>
            <span class="stat-value spend">₹${spend.toLocaleString("en-IN")}</span>
          </div>
          <div class="budget-stat">
            <span class="stat-label">Remaining</span>
            <span class="stat-value ${remaining >= 0 ? "positive" : "negative"}">
              ₹${Math.abs(remaining).toLocaleString("en-IN")} ${remaining >= 0 ? "✅" : "⚠️ Over"}
            </span>
          </div>
        </div>
        <div class="budget-bars">${bars}</div>
      </div>`;
  }

  // ════════════════════════════════════════════════════════════
  // RENDER: SUGGESTIONS
  // ════════════════════════════════════════════════════════════
  function renderSuggestions(data, container, mapRef) {
    const hotels = data.hotels || [];
    const restaurants = data.restaurants || [];
    if (!hotels.length && !restaurants.length) {
      container.innerHTML = `<p class="warn-msg">No nearby hotels or restaurants found in OpenStreetMap for this destination.</p>`;
      return;
    }

    let html = `<h3 class="section-label">🏨 Hotels &amp; 🍽️ Restaurants <span class="source-tag">via OpenStreetMap</span></h3>
    <div class="suggestions-grid">`;

    if (hotels.length) {
      html += `
        <div class="sug-column">
          <h4 class="sug-col-title">🏨 Nearby Hotels</h4>
          ${hotels
            .map(
              (h) => `
            <div class="sug-card">
              <div class="sug-name">${h.name}</div>
              <div class="sug-meta">
                <span class="sug-badge hotel-badge">${h.type || "Hotel"}</span>
                ${h.rating ? `<span>⭐ ${h.rating}</span>` : ""}
              </div>
              ${h.address?.trim() ? `<div class="sug-address">📍 ${h.address}</div>` : ""}
            </div>`,
            )
            .join("")}
        </div>`;

      if (mapRef) {
        hotels.forEach((h) => {
          if (h.lat && h.lon) {
            const icon = L.divIcon({
              className: "emoji-icon",
              html: "🏨",
              iconSize: [26, 26],
            });
            L.marker([h.lat, h.lon], { icon })
              .addTo(mapRef)
              .bindPopup(
                `🏨 <strong>${h.name}</strong>${h.address ? `<br>📍 ${h.address}` : ""}`,
              );
          }
        });
      }
    }

    if (restaurants.length) {
      html += `
        <div class="sug-column">
          <h4 class="sug-col-title">🍽️ Nearby Restaurants</h4>
          ${restaurants
            .map(
              (r) => `
            <div class="sug-card">
              <div class="sug-name">${r.name}</div>
              <div class="sug-meta">
                <span class="sug-badge rest-badge">${r.cuisine || "Local"}</span>
                ${r.rating ? `<span>⭐ ${r.rating}</span>` : ""}
                <span>${r.priceRange || "₹₹"}</span>
              </div>
              ${r.address?.trim() ? `<div class="sug-address">📍 ${r.address}</div>` : ""}
            </div>`,
            )
            .join("")}
        </div>`;

      if (mapRef) {
        restaurants.forEach((r) => {
          if (r.lat && r.lon) {
            const icon = L.divIcon({
              className: "emoji-icon",
              html: "🍽️",
              iconSize: [26, 26],
            });
            L.marker([r.lat, r.lon], { icon })
              .addTo(mapRef)
              .bindPopup(
                `🍽️ <strong>${r.name}</strong><br>${r.cuisine || "Local"} • ${r.priceRange || "₹₹"}`,
              );
          }
        });
      }
    }

    html += `</div>`;
    container.innerHTML = html;
  }

  function initMap(lat, lon, destination, itinerary, attractions = []) {
    const container = document.getElementById("map");
    if (!container) return;

    map = L.map(container).setView([lat, lon], 12);
    L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
      attribution: "OpenStreetMap contributors",
    }).addTo(map);

    L.marker([lat, lon])
      .addTo(map)
      .bindPopup(`<strong>Destination: ${destination}</strong>`)
      .openPopup();

    const seenPlaces = new Set();
    const attractionIcon = L.divIcon({
      className: "emoji-icon",
      html: "&#128205;",
      iconSize: [24, 24],
    });

    if (Array.isArray(itinerary)) {
      itinerary.forEach((day) => {
        (day.places || []).forEach((place) => {
          if (!place.lat || !place.lon || !place.name) return;

          const key = `${place.name}|${place.lat}|${place.lon}`;
          seenPlaces.add(key);

          L.marker([place.lat, place.lon], { icon: attractionIcon })
            .addTo(map)
            .bindPopup(
              `<strong>${place.name}</strong><br>Day ${day.day} - ${day.title}`,
            );
        });
      });
    }

    if (Array.isArray(attractions)) {
      attractions.forEach((place) => {
        if (!place.lat || !place.lon || !place.name) return;

        const key = `${place.name}|${place.lat}|${place.lon}`;
        if (seenPlaces.has(key)) return;

        L.marker([place.lat, place.lon], { icon: attractionIcon })
          .addTo(map)
          .bindPopup(
            `<strong>${place.name}</strong>${place.kind ? `<br>${place.kind}` : ""}`,
          );
      });
    }
  }

  function renderSuggestions(data, container, mapRef) {
    const hotels = data.hotels || [];
    const restaurants = data.restaurants || [];
    if (!hotels.length && !restaurants.length) {
      container.innerHTML = `<p class="warn-msg">No nearby hotels or restaurants found in OpenStreetMap for this destination.</p>`;
      return;
    }

    let html = `<h3 class="section-label">Hotels and Restaurants <span class="source-tag">via OpenStreetMap</span></h3><div class="suggestions-grid">`;

    if (hotels.length) {
      html += `
        <div class="sug-column">
          <h4 class="sug-col-title">Nearby Hotels</h4>
          ${hotels
            .map(
              (h) => `
            <div class="sug-card">
              <div class="sug-name">${h.name}</div>
              <div class="sug-meta">
                <span class="sug-badge hotel-badge">${h.type || "Hotel"}</span>
                ${h.rating ? `<span>${h.rating}</span>` : ""}
              </div>
              ${h.address?.trim() ? `<div class="sug-address">${h.address}</div>` : ""}
            </div>`,
            )
            .join("")}
        </div>`;

      if (mapRef) {
        hotels.forEach((h) => {
          if (!h.lat || !h.lon) return;
          const icon = L.divIcon({
            className: "emoji-icon hotel-icon",
            html: "H",
            iconSize: [26, 26],
          });
          L.marker([h.lat, h.lon], { icon })
            .addTo(mapRef)
            .bindPopup(
              `<strong>${h.name}</strong>${h.address ? `<br>${h.address}` : ""}`,
            );
        });
      }
    }

    if (restaurants.length) {
      html += `
        <div class="sug-column">
          <h4 class="sug-col-title">Nearby Restaurants</h4>
          ${restaurants
            .map(
              (r) => `
            <div class="sug-card">
              <div class="sug-name">${r.name}</div>
              <div class="sug-meta">
                <span class="sug-badge rest-badge">${r.cuisine || "Local"}</span>
                ${r.rating ? `<span>${r.rating}</span>` : ""}
                <span>${r.priceRange || "INR"}</span>
              </div>
              ${r.address?.trim() ? `<div class="sug-address">${r.address}</div>` : ""}
            </div>`,
            )
            .join("")}
        </div>`;

      if (mapRef) {
        restaurants.forEach((r) => {
          if (!r.lat || !r.lon) return;
          const icon = L.divIcon({
            className: "emoji-icon rest-icon",
            html: "R",
            iconSize: [26, 26],
          });
          L.marker([r.lat, r.lon], { icon })
            .addTo(mapRef)
            .bindPopup(`<strong>${r.name}</strong><br>${r.cuisine || "Local"}`);
        });
      }
    }

    html += `</div>`;
    container.innerHTML = html;
  }
});

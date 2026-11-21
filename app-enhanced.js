document.addEventListener("DOMContentLoaded", () => {
  const STORAGE_USERS = "planora.users";
  const STORAGE_SESSION = "planora.session";
  const STORAGE_TRIPS = "planora.trips";
  const STORAGE_THEME = "planora.theme";
  const API_BASE = window.location.protocol.startsWith("http") ? "" : "http://localhost:5000";

  const form = document.getElementById("trip-form");
  const submitBtn = document.getElementById("submit-btn");
  const btnText = submitBtn?.querySelector(".btn-text");
  const btnSpinner = submitBtn?.querySelector(".btn-spinner");
  const loadingOverlay = document.getElementById("loading-overlay");
  const loadingMsg = document.getElementById("loading-msg");
  const timeline = document.getElementById("timeline");
  const weatherBox = document.getElementById("weather");
  const insightsPanel = document.getElementById("insights-panel");
  const budgetSection = document.getElementById("budget-tracker");
  const suggestionsSection = document.getElementById("suggestions");
  const destInput = document.getElementById("dest");
  const destinationSuggestions = document.getElementById(
    "destination-suggestions",
  );
  const recentTripsList = document.getElementById("recent-trips-list");
  const recentTripsEmpty = document.getElementById("recent-trips-empty");
  const authSummary = document.getElementById("auth-summary");
  const authAction = document.getElementById("auth-action");
  const authModal = document.getElementById("auth-modal");
  const authForm = document.getElementById("auth-form");
  const authTitle = document.getElementById("auth-title");
  const authNameField = document.getElementById("auth-name-field");
  const authNameInput = document.getElementById("auth-name");
  const authEmailInput = document.getElementById("auth-email");
  const authPasswordInput = document.getElementById("auth-password");
  const authError = document.getElementById("auth-error");
  const authToggle = document.getElementById("auth-toggle");
  const closeAuthBtn = document.getElementById("close-auth");
  const logoutBtn = document.getElementById("logout-btn");
  const myTripsLink = document.getElementById("my-trips-link");
  const loginLink = document.getElementById("login-link");
  const recentTripsSection = document.getElementById("recent-trips");
  const themeToggle = document.getElementById("theme-toggle");
  const tripActionsBar = document.getElementById("trip-actions-bar");
  const printBtn = document.getElementById("print-itinerary-btn");
  const shareBtn = document.getElementById("share-itinerary-btn");
  const packingChecklist = document.getElementById("packing-checklist");
  const mapFilterBar = document.getElementById("map-filter-bar");
  const toast = document.getElementById("toast");

  if (!form) return;

  let map = null;
  let lastPlanData = null;
  let markerGroups = {
    attractions: [],
    hotels: [],
    restaurants: [],
  };
  let authMode = "login";
  let currentUser = getSessionUser();
  let destinationSearchTimer = null;
  let currentTheme = localStorage.getItem(STORAGE_THEME) || "light";

  applyTheme(currentTheme);
  setAuthMode("login");
  refreshAuthUI();
  renderRecentTrips();

  // Set minimum dates to prevent past date errors
  const todayStr = new Date().toISOString().split("T")[0];
  const startInput = form.querySelector('input[name="startDate"]');
  const endInput = form.querySelector('input[name="endDate"]');
  if (startInput) startInput.min = todayStr;
  if (endInput) endInput.min = todayStr;
  startInput?.addEventListener("change", () => {
    if (startInput.value && endInput) {
      endInput.min = startInput.value;
      if (endInput.value && endInput.value < startInput.value) {
        endInput.value = startInput.value;
      }
    }
  });

  // Popular Trending Destination Chips
  document.querySelectorAll(".dest-chip").forEach((chip) => {
    chip.addEventListener("click", () => {
      const dest = chip.dataset.dest;
      const budget = chip.dataset.budget;
      if (destInput) destInput.value = dest;
      if (form.budget) form.budget.value = budget;

      const start = new Date();
      start.setDate(start.getDate() + 3);
      const end = new Date();
      end.setDate(end.getDate() + 7);

      if (form.startDate) form.startDate.value = start.toISOString().split("T")[0];
      if (form.endDate) form.endDate.value = end.toISOString().split("T")[0];

      chip.classList.add("chip-pulse");
      setTimeout(() => chip.classList.remove("chip-pulse"), 400);
      form.scrollIntoView({ behavior: "smooth", block: "center" });
    });
  });

  // Print / PDF Export
  printBtn?.addEventListener("click", () => {
    window.print();
  });

  // Robust Cross-Browser Clipboard Helper
  function copyTextToClipboard(text) {
    return new Promise((resolve, reject) => {
      if (navigator.clipboard && window.isSecureContext) {
        navigator.clipboard.writeText(text).then(resolve).catch(() => {
          fallbackCopyText(text, resolve, reject);
        });
      } else {
        fallbackCopyText(text, resolve, reject);
      }
    });
  }

  function fallbackCopyText(text, resolve, reject) {
    try {
      const textArea = document.createElement("textarea");
      textArea.value = text;
      textArea.style.position = "fixed";
      textArea.style.left = "-9999px";
      textArea.style.top = "-9999px";
      document.body.appendChild(textArea);
      textArea.focus();
      textArea.select();
      const successful = document.execCommand("copy");
      document.body.removeChild(textArea);
      if (successful) resolve();
      else reject(new Error("execCommand copy failed"));
    } catch (err) {
      reject(err);
    }
  }

  // Share / Copy Trip Summary
  shareBtn?.addEventListener("click", () => {
    if (!lastPlanData) {
      showToast("⚠️ Generate a trip plan first before copying summary!");
      return;
    }
    const summary = generateTripSummary(
      lastPlanData,
      destInput.value,
      form.startDate.value,
      form.endDate.value,
      form.budget.value,
    );
    copyTextToClipboard(summary)
      .then(() => {
        showToast("📋 Trip summary copied to clipboard! Share away 🚀");
        const originalHtml = shareBtn.innerHTML;
        shareBtn.innerHTML = "✅ Copied to Clipboard!";
        shareBtn.classList.add("btn-copied");
        setTimeout(() => {
          shareBtn.innerHTML = originalHtml;
          shareBtn.classList.remove("btn-copied");
        }, 2200);
      })
      .catch((err) => {
        console.error("Copy failed:", err);
        showToast("Could not copy automatically. Please try again.");
      });
  });

  // Map Filter Buttons
  document.querySelectorAll(".map-filter-btn").forEach((btn) => {
    btn.addEventListener("click", () => {
      applyMapFilter(btn.dataset.filter);
    });
  });

  // Packing Checklist Interaction
  packingChecklist?.addEventListener("change", (e) => {
    if (e.target.classList.contains("packing-check")) {
      const itemLabel = e.target.closest(".packing-item");
      if (itemLabel) {
        itemLabel.classList.toggle("checked", e.target.checked);
      }
    }
  });

  destInput?.addEventListener("input", () => {
    const query = destInput.value.trim();
    clearTimeout(destinationSearchTimer);

    if (query.length < 3) {
      hideDestinationSuggestions();
      return;
    }

    destinationSearchTimer = setTimeout(async () => {
      try {
        const response = await fetch(
          `${API_BASE}/search-destinations?q=${encodeURIComponent(query)}`,
        );
        const data = await response.json();
        renderDestinationSuggestions(data.results || []);
      } catch {
        hideDestinationSuggestions();
      }
    }, 220);
  });

  document.addEventListener("click", (event) => {
    if (
      !destinationSuggestions?.contains(event.target) &&
      event.target !== destInput
    ) {
      hideDestinationSuggestions();
    }
  });

  loginLink?.addEventListener("click", (event) => {
    event.preventDefault();
    if (currentUser) {
      logoutUser();
      return;
    }
    openAuthModal("login");
  });

  authAction?.addEventListener("click", () => {
    if (currentUser) {
      recentTripsSection?.scrollIntoView({
        behavior: "smooth",
        block: "start",
      });
    } else {
      openAuthModal("login");
    }
  });

  myTripsLink?.addEventListener("click", (event) => {
    event.preventDefault();
    recentTripsSection?.scrollIntoView({ behavior: "smooth", block: "start" });
  });

  closeAuthBtn?.addEventListener("click", closeAuthModal);
  authModal?.addEventListener("click", (event) => {
    if (event.target === authModal) closeAuthModal();
  });

  authToggle?.addEventListener("click", () => {
    setAuthMode(authMode === "login" ? "signup" : "login");
  });

  logoutBtn?.addEventListener("click", logoutUser);
  themeToggle?.addEventListener("click", toggleTheme);

  authForm?.addEventListener("submit", (event) => {
    event.preventDefault();
    authError.textContent = "";

    const name = authNameInput.value.trim();
    const email = authEmailInput.value.trim().toLowerCase();
    const password = authPasswordInput.value;
    const users = readJson(STORAGE_USERS, []);

    if (!email || !password) {
      authError.textContent = "Email and password are required.";
      return;
    }

    if (authMode === "signup") {
      if (!name) {
        authError.textContent = "Please enter your name.";
        return;
      }
      if (users.some((user) => user.email === email)) {
        authError.textContent = "This email is already registered.";
        return;
      }

      const newUser = { name, email, password };
      users.push(newUser);
      localStorage.setItem(STORAGE_USERS, JSON.stringify(users));
      setSession(email);
      currentUser = newUser;
      refreshAuthUI();
      renderRecentTrips();
      closeAuthModal();
      return;
    }

    const existingUser = users.find(
      (user) => user.email === email && user.password === password,
    );
    if (!existingUser) {
      authError.textContent = "Invalid email or password.";
      return;
    }

    setSession(existingUser.email);
    currentUser = existingUser;
    refreshAuthUI();
    renderRecentTrips();
    closeAuthModal();
  });

  form.addEventListener("submit", async (event) => {
    event.preventDefault();

    const destination = destInput.value.trim();
    const startDate = form.startDate.value;
    const endDate = form.endDate.value;
    const budget = parseInt(form.budget.value, 10) || 0;

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
    setLoading(true, `Building your trip for ${destination}...`);

    try {
      const planRes = await fetch(`${API_BASE}/plan-trip`, {
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

      if (planData.error) {
        timeline.innerHTML = `<p class="error-msg">${planData.error}</p>`;
        return;
      }

      renderWeather(planData.weather, destination, weatherBox);
      renderInsights(
        planData.destinationMeta,
        planData.countryInsights,
        insightsPanel,
      );
      renderItinerary(planData.itinerary, timeline);

      lastPlanData = planData;
      if (tripActionsBar) {
        tripActionsBar.hidden = false;
        const hTitle = document.getElementById("trip-header-title");
        const hSub = document.getElementById("trip-header-subtitle");
        if (hTitle) hTitle.textContent = `Trip to ${destination}`;
        if (hSub) {
          const daysCount = planData.itinerary?.length || 0;
          hSub.textContent = `${startDate} to ${endDate} (${daysCount} Day${daysCount > 1 ? "s" : ""}) • ₹${Number(budget).toLocaleString("en-IN")}`;
        }
      }
      renderPackingChecklist(planData.weather, destination, packingChecklist);

      const breakdown = planData.budgetBreakdown || {
        accommodation: Math.round(budget * 0.4),
        food: Math.round(budget * 0.2),
        transport: Math.round(budget * 0.15),
        activities: Math.round(budget * 0.15),
        misc: Math.round(budget * 0.1),
      };
      renderBudget(
        budget,
        breakdown,
        budgetSection,
        planData.currency,
        planData.countryInsights,
      );

      if (planData.coordinates?.lat && planData.coordinates?.lon) {
        initMap(
          planData.coordinates.lat,
          planData.coordinates.lon,
          destination,
          planData.itinerary || [],
          planData.attractions || [],
        );
      }

      if (currentUser) {
        saveRecentTrip({
          destination,
          startDate,
          endDate,
          budget,
          weather: planData.weather,
          itinerary: planData.itinerary || [],
        });
        renderRecentTrips();
      }

      suggestionsSection.innerHTML = `<p class="warn-msg">Loading nearby hotels and restaurants...</p>`;

      try {
        const suggestionsRes = await fetch(
          `${API_BASE}/suggestions`,
          {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ destination, budget }),
          },
        );
        const suggestionsData = await suggestionsRes.json();
        if (!suggestionsData.error) {
          renderSuggestions(suggestionsData, suggestionsSection, map);
        }
      } catch {
        suggestionsSection.innerHTML = `<p class="warn-msg">Could not load hotel or restaurant suggestions.</p>`;
      }
    } catch {
      timeline.innerHTML = `<p class="error-msg">Could not connect to the server. Make sure app.py is running on localhost:5000.</p>`;
    } finally {
      setLoading(false);
    }
  });

  function setLoading(active, message = "") {
    if (loadingOverlay) loadingOverlay.hidden = !active;
    if (loadingMsg && message) loadingMsg.textContent = message;
    if (btnText) btnText.hidden = active;
    if (btnSpinner) btnSpinner.hidden = !active;
    if (submitBtn) submitBtn.disabled = active;
  }

  function clearResults() {
    weatherBox.innerHTML = "";
    insightsPanel.innerHTML = "";
    timeline.innerHTML = "";
    budgetSection.innerHTML = "";
    suggestionsSection.innerHTML = "";
    if (tripActionsBar) tripActionsBar.hidden = true;
    const mapWrapper = document.getElementById("map-wrapper");
    if (mapWrapper) mapWrapper.hidden = true;
    if (packingChecklist) {
      packingChecklist.hidden = true;
      packingChecklist.innerHTML = "";
    }
    if (mapFilterBar) mapFilterBar.hidden = true;
    markerGroups = { attractions: [], hotels: [], restaurants: [] };
    if (map) {
      map.off();
      map.remove();
      map = null;
    }
  }

  function readJson(key, fallback) {
    try {
      return JSON.parse(localStorage.getItem(key)) ?? fallback;
    } catch {
      return fallback;
    }
  }

  function getSessionUser() {
    const session = readJson(STORAGE_SESSION, null);
    const users = readJson(STORAGE_USERS, []);
    return users.find((user) => user.email === session?.email) || null;
  }

  function setSession(email) {
    localStorage.setItem(STORAGE_SESSION, JSON.stringify({ email }));
  }

  function applyTheme(theme) {
    currentTheme = theme === "dark" ? "dark" : "light";
    document.body.classList.toggle("dark-mode", currentTheme === "dark");
    if (themeToggle) {
      const isDark = currentTheme === "dark";
      const icon = isDark ? "☀️" : "🌙";
      const label = isDark ? "Light Mode" : "Dark Mode";
      const iconEl = themeToggle.querySelector(".theme-icon");
      const textEl = themeToggle.querySelector(".theme-text");
      if (iconEl && textEl) {
        iconEl.textContent = icon;
        textEl.textContent = label;
      } else {
        themeToggle.textContent = `${icon} ${label}`;
      }
      themeToggle.setAttribute("aria-pressed", String(isDark));
      themeToggle.setAttribute("aria-label", label);
    }
  }

  function toggleTheme() {
    const nextTheme = currentTheme === "dark" ? "light" : "dark";
    localStorage.setItem(STORAGE_THEME, nextTheme);
    applyTheme(nextTheme);
    if (map) {
      setTimeout(() => map.invalidateSize(), 120);
    }
  }

  function logoutUser() {
    localStorage.removeItem(STORAGE_SESSION);
    currentUser = null;
    refreshAuthUI();
    renderRecentTrips();
    closeAuthModal();
  }

  function setAuthMode(mode) {
    authMode = mode;
    const isSignup = mode === "signup";
    authTitle.textContent = isSignup
      ? "Create your account"
      : "Login to Planora";
    authToggle.textContent = isSignup
      ? "Already have an account? Login"
      : "New here? Create an account";
    authNameField.hidden = !isSignup;
    authNameInput.required = isSignup;
    authForm.querySelector("button[type='submit']").textContent = isSignup
      ? "Create account"
      : "Login";
    authError.textContent = "";
  }

  function openAuthModal(mode) {
    setAuthMode(mode);
    authModal.hidden = false;
  }

  function closeAuthModal() {
    authModal.hidden = true;
    authForm.reset();
    authError.textContent = "";
  }

  function refreshAuthUI() {
    if (currentUser) {
      authSummary.textContent = `Logged in as ${currentUser.name}`;
      authAction.textContent = "View recent trips";
      loginLink.textContent = "Logout";
      logoutBtn.hidden = false;
      recentTripsEmpty.textContent =
        "No recent trips yet. Generate your first trip and it will appear here.";
    } else {
      authSummary.textContent = "Login to save and revisit your recent trips.";
      authAction.textContent = "Login or sign up";
      loginLink.textContent = "Login";
      logoutBtn.hidden = true;
      recentTripsEmpty.textContent =
        "Login to save recent trips to this browser.";
    }
  }

  function saveRecentTrip(trip) {
    const trips = readJson(STORAGE_TRIPS, []);
    trips.unshift({
      id: String(Date.now()),
      owner: currentUser.email,
      ...trip,
      createdAt: new Date().toISOString(),
    });
    localStorage.setItem(STORAGE_TRIPS, JSON.stringify(trips.slice(0, 18)));
  }

  function renderRecentTrips() {
    if (!currentUser) {
      recentTripsList.innerHTML = "";
      recentTripsEmpty.hidden = false;
      return;
    }

    const trips = readJson(STORAGE_TRIPS, []).filter(
      (trip) => trip.owner === currentUser.email,
    );
    if (!trips.length) {
      recentTripsList.innerHTML = "";
      recentTripsEmpty.hidden = false;
      return;
    }

    recentTripsEmpty.hidden = true;
    recentTripsList.innerHTML = trips
      .map((trip) => {
        const weatherLabel =
          trip.weather && trip.weather.temp !== "N/A"
            ? `${trip.weather.temp}°C, ${trip.weather.condition || "Variable weather"}`
            : trip.weather?.condition || "Forecast unavailable";

        return `
          <article class="trip-card" data-id="${trip.id}" style="cursor: pointer;" title="Click to load this trip into planner">
            <div class="trip-card-top">
              <div>
                <h4>${trip.destination}</h4>
                <p>${trip.startDate} to ${trip.endDate}</p>
              </div>
              <span class="trip-budget">₹${Number(trip.budget || 0).toLocaleString("en-IN")}</span>
            </div>
            <p class="trip-weather">${weatherLabel}</p>
            <p class="trip-meta">${trip.itinerary?.length || 0} planned day(s) saved on ${new Date(trip.createdAt).toLocaleDateString("en-IN")}</p>
          </article>`;
      })
      .join("");
  }

  // Restore saved trip to form on click
  recentTripsList?.addEventListener("click", (event) => {
    const card = event.target.closest(".trip-card");
    if (!card) return;
    const tripId = card.dataset.id;
    const trips = readJson(STORAGE_TRIPS, []);
    const trip = trips.find((t) => String(t.id) === String(tripId));
    if (trip) {
      if (destInput) destInput.value = trip.destination || "";
      if (form.startDate) form.startDate.value = trip.startDate || "";
      if (form.endDate) form.endDate.value = trip.endDate || "";
      if (form.budget) form.budget.value = trip.budget || "";
      form.scrollIntoView({ behavior: "smooth", block: "center" });
    }
  });

  function englishText(value, fallback = "Unavailable") {
    if (value === undefined || value === null) return fallback;
    const cleaned = String(value).trim();
    return cleaned.length > 0 ? cleaned : fallback;
  }

  function renderDestinationSuggestions(results) {
    if (!destinationSuggestions) return;
    if (!results.length) {
      hideDestinationSuggestions();
      return;
    }

    destinationSuggestions.hidden = false;
    destinationSuggestions.innerHTML = results
      .map(
        (item) => `
          <button type="button" class="destination-option" data-value="${item.display_name.replace(/"/g, "&quot;")}">
            <strong>${englishText(item.city, englishText(item.country, englishText(item.display_name, "Destination")))}</strong>
            <span>${item.state ? `${englishText(item.state, "")}, ` : ""}${englishText(item.country, "")}</span>
          </button>`,
      )
      .join("");

    destinationSuggestions
      .querySelectorAll(".destination-option")
      .forEach((button) => {
        button.addEventListener("click", () => {
          destInput.value = button.dataset.value || "";
          hideDestinationSuggestions();
        });
      });
  }

  function hideDestinationSuggestions() {
    if (!destinationSuggestions) return;
    destinationSuggestions.hidden = true;
    destinationSuggestions.innerHTML = "";
  }

  function renderInsights(destinationMeta, countryInsights, container) {
    if (!container || (!destinationMeta && !countryInsights)) return;

    const cards = [
      {
        label: "Destination",
        value: englishText(destinationMeta?.display_name, "Unavailable"),
      },
      {
        label: "Country / Region",
        value:
          [
            englishText(
              countryInsights?.country || destinationMeta?.country,
              "",
            ),
            englishText(countryInsights?.region, ""),
          ]
            .filter(Boolean)
            .join(" - ") || "Unavailable",
      },
      {
        label: "Capital",
        value: englishText(countryInsights?.capital, "Unavailable"),
      },
      {
        label: "Currency",
        value:
          [
            englishText(countryInsights?.currencyCode, ""),
            englishText(countryInsights?.currencyName, ""),
          ]
            .filter(Boolean)
            .join(" - ") || "Unavailable",
      },
    ];

    container.innerHTML = `
      <h3 class="section-label">Destination Intel</h3>
      <div class="insights-grid">
        ${cards
          .map(
            (card) => `
              <article class="insight-card">
                <span class="insight-label">${card.label}</span>
                <strong>${card.value}</strong>
              </article>`,
          )
          .join("")}
      </div>`;
  }

  function renderWeather(weather, destination, container) {
    const hasNumericTemp =
      weather &&
      weather.temp !== undefined &&
      weather.temp !== null &&
      weather.temp !== "N/A" &&
      !Number.isNaN(Number(weather.temp));

    const summary = hasNumericTemp
      ? `${weather.temp}°C — ${weather.condition || "Variable weather"}`
      : `${weather?.condition || "Forecast unavailable"}`;

    container.innerHTML = `
      <h3 class="section-label">Live Weather</h3>
      <div class="weather-card">
        <span class="weather-icon">🌤️</span>
        <div>
          <strong>${destination}</strong>
          <p>${summary}</p>
        </div>
        <div class="weather-source">via Open-Meteo</div>
      </div>`;
  }

  function renderItinerary(itinerary, container) {
    if (!Array.isArray(itinerary) || !itinerary.length) {
      container.innerHTML = `<p class="warn-msg">No itinerary returned for this destination.</p>`;
      return;
    }

    let html = `<h3 class="section-label">Day-by-Day Tour Itinerary</h3><div class="itinerary-timeline">`;
    itinerary.forEach((item, index) => {
      const activities = (item.activities || [])
        .map((act) => {
          if (typeof act === "object" && act !== null) {
            const timeIcon =
              act.time === "Morning"
                ? "🌅"
                : act.time === "Afternoon"
                ? "☀️"
                : act.time === "Evening"
                ? "🌙"
                : "📍";
            return `
              <li class="activity-card">
                <div class="act-header">
                  <span class="act-time-pill">${timeIcon} ${englishText(act.time || "Visit", "Visit")}</span>
                  <span class="act-title">${englishText(act.title, "")}</span>
                  ${act.label ? `<span class="act-tag">${englishText(act.label, "")}</span>` : ""}
                </div>
                ${act.desc ? `<p class="act-desc">${englishText(act.desc, "")}</p>` : ""}
                ${act.tip ? `<div class="act-tip">💡 <strong>Tour Guide Tip:</strong> ${englishText(act.tip, "")}</div>` : ""}
              </li>`;
          }
          return `<li class="activity-plain">${englishText(act, "")}</li>`;
        })
        .join("");
      const placeCount = (item.places || []).length;
      const mapNote = placeCount
        ? `<span class="map-note">${placeCount} place${placeCount > 1 ? "s" : ""} on map</span>`
        : "";
      const routeSummary = item.routeSummary
        ? `<span class="route-pill">${item.routeSummary.distanceKm} km - ${item.routeSummary.durationMin} min</span>`
        : "";
      html += `
        <div class="itinerary-day">
          <div class="day-badge">
            <span class="day-num">Day ${item.day || index + 1}</span>
            ${item.date ? `<span class="day-date">${item.date}</span>` : ""}
          </div>
          <div class="day-content">
            <div class="day-header">
              <h4 class="day-title">${item.title || ""}</h4>
              <div class="day-meta">${routeSummary}${mapNote}</div>
            </div>
            <ul class="activity-list">${activities}</ul>
          </div>
        </div>`;
    });
    html += `</div>`;
    container.innerHTML = html;
  }

  function renderBudget(
    total,
    breakdown,
    container,
    currency,
    countryInsights,
  ) {
    const categories = [
      { key: "accommodation", label: "Accommodation", color: "#4f46e5" },
      { key: "food", label: "Food and Dining", color: "#06b6d4" },
      { key: "transport", label: "Transport", color: "#7c3aed" },
      { key: "activities", label: "Activities", color: "#10b981" },
      { key: "misc", label: "Miscellaneous", color: "#f59e0b" },
    ];
    const spend = categories.reduce(
      (sum, category) => sum + (breakdown[category.key] || 0),
      0,
    );
    const remaining = total - spend;
    const bars = categories
      .map((category) => {
        const amount = breakdown[category.key] || 0;
        const width =
          total > 0 ? Math.min(100, (amount / total) * 100).toFixed(1) : 0;
        return `
          <div class="budget-row">
            <div class="budget-label-row">
              <span>${category.label}</span>
              <span class="budget-amount">INR ${amount.toLocaleString("en-IN")}</span>
            </div>
            <div class="budget-bar-bg">
              <div class="budget-bar-fill" style="width:${width}%;background:${category.color}"></div>
            </div>
          </div>`;
      })
      .join("");

    const convertedBudget = currency?.converted
      ? `<div class="budget-note">Approx local budget: ${currency.target} ${Number(currency.converted).toLocaleString("en-US")} ${countryInsights?.currencyName ? `(${countryInsights.currencyName})` : ""}</div>`
      : `<div class="budget-note">Currency conversion unavailable</div>`;

    container.innerHTML = `
      <h3 class="section-label">Budget Breakdown</h3>
      <div class="budget-card">
        <div class="budget-summary">
          <div class="budget-stat">
            <span class="stat-label">Total Budget</span>
            <span class="stat-value">INR ${total.toLocaleString("en-IN")}</span>
          </div>
          <div class="budget-stat">
            <span class="stat-label">Estimated Spend</span>
            <span class="stat-value spend">INR ${spend.toLocaleString("en-IN")}</span>
          </div>
          <div class="budget-stat">
            <span class="stat-label">Remaining</span>
            <span class="stat-value ${remaining >= 0 ? "positive" : "negative"}">INR ${Math.abs(remaining).toLocaleString("en-IN")} ${remaining >= 0 ? "Left" : "Over"}</span>
          </div>
        </div>
        ${convertedBudget}
        <div class="budget-bars">${bars}</div>
      </div>`;
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
              (hotel) => `
            <div class="sug-card">
              <div class="sug-name">${englishText(hotel.name, "Hotel")}</div>
              <div class="sug-meta">
                <span class="sug-badge hotel-badge">${englishText(hotel.type, "Hotel")}</span>
                ${hotel.rating ? `<span>${englishText(String(hotel.rating), "")}</span>` : ""}
              </div>
              ${hotel.address?.trim() ? `<div class="sug-address">${englishText(hotel.address, "Destination area")}</div>` : ""}
            </div>`,
            )
            .join("")}
        </div>`;

      if (mapRef) {
        hotels.forEach((hotel) => {
          if (!hotel.lat || !hotel.lon) return;
          const icon = L.divIcon({
            className: "emoji-icon hotel-icon",
            html: "🏨",
            iconSize: [26, 26],
          });
          const m = L.marker([hotel.lat, hotel.lon], { icon })
            .addTo(mapRef)
            .bindPopup(
              `<strong>${englishText(hotel.name, "Hotel")}</strong>${hotel.address ? `<br>${englishText(hotel.address, "Destination area")}` : ""}`,
            );
          markerGroups.hotels.push(m);
        });
      }
    }

    if (restaurants.length) {
      html += `
        <div class="sug-column">
          <h4 class="sug-col-title">Nearby Restaurants</h4>
          ${restaurants
            .map(
              (restaurant) => `
            <div class="sug-card">
              <div class="sug-name">${englishText(restaurant.name, "Restaurant")}</div>
              <div class="sug-meta">
                <span class="sug-badge rest-badge">${englishText(restaurant.cuisine, "Local")}</span>
                ${restaurant.rating ? `<span>${englishText(String(restaurant.rating), "")}</span>` : ""}
                <span>${englishText(restaurant.priceRange, "Moderate")}</span>
              </div>
              ${restaurant.address?.trim() ? `<div class="sug-address">${englishText(restaurant.address, "Destination area")}</div>` : ""}
            </div>`,
            )
            .join("")}
        </div>`;

      if (mapRef) {
        restaurants.forEach((restaurant) => {
          if (!restaurant.lat || !restaurant.lon) return;
          const icon = L.divIcon({
            className: "emoji-icon rest-icon",
            html: "🍽️",
            iconSize: [26, 26],
          });
          const m = L.marker([restaurant.lat, restaurant.lon], { icon })
            .addTo(mapRef)
            .bindPopup(
              `<strong>${englishText(restaurant.name, "Restaurant")}</strong><br>${englishText(restaurant.cuisine, "Local")}`,
            );
          markerGroups.restaurants.push(m);
        });
      }
    }

    html += `</div>`;
    container.innerHTML = html;
    updateMapFilterCounts();
  }

  function initMap(lat, lon, destination, itinerary, attractions) {
    const container = document.getElementById("map");
    if (!container) return;

    if (map) {
      try {
        map.remove();
      } catch (err) {
        console.warn("Error removing previous map instance:", err);
      }
      map = null;
    }

    const mapWrapper = document.getElementById("map-wrapper");
    if (mapWrapper) mapWrapper.hidden = false;

    markerGroups.attractions = [];
    markerGroups.hotels = [];
    markerGroups.restaurants = [];

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
      className: "emoji-icon attraction-icon",
      html: "📍",
      iconSize: [26, 26],
    });

    (itinerary || []).forEach((day) => {
      (day.places || []).forEach((place) => {
        if (!place.lat || !place.lon || !place.name) return;
        const key = `${place.name}|${place.lat}|${place.lon}`;
        seenPlaces.add(key);
        const m = L.marker([place.lat, place.lon], { icon: attractionIcon })
          .addTo(map)
          .bindPopup(
            `<strong>${englishText(place.name, "Attraction")}</strong><br>${englishText(day.title || "Attraction", "Attraction")}`,
          );
        markerGroups.attractions.push(m);
      });
    });

    (attractions || []).forEach((place) => {
      if (!place.lat || !place.lon || !place.name) return;
      const key = `${place.name}|${place.lat}|${place.lon}`;
      if (seenPlaces.has(key)) return;
      seenPlaces.add(key);
      const m = L.marker([place.lat, place.lon], { icon: attractionIcon })
        .addTo(map)
        .bindPopup(
          `<strong>${englishText(place.name, "Attraction")}</strong>${place.kind ? `<br>${englishText(place.kind, "Attraction")}` : ""}`,
        );
      markerGroups.attractions.push(m);
    });

    updateMapFilterCounts();
    setTimeout(() => {
      if (map) map.invalidateSize();
    }, 250);
  }

  function updateMapFilterCounts() {
    const bar = document.getElementById("map-filter-bar");
    if (!bar) return;
    bar.hidden = false;

    const countAttr = markerGroups.attractions.length;
    const countHotels = markerGroups.hotels.length;
    const countRests = markerGroups.restaurants.length;

    const elAttr = document.getElementById("count-attractions");
    const elHotels = document.getElementById("count-hotels");
    const elRests = document.getElementById("count-restaurants");
    const elAll = document.getElementById("count-all");

    if (elAttr) elAttr.textContent = countAttr;
    if (elHotels) elHotels.textContent = countHotels;
    if (elRests) elRests.textContent = countRests;
    if (elAll) elAll.textContent = countAttr + countHotels + countRests;
  }

  function applyMapFilter(filterType) {
    if (!map) return;
    document.querySelectorAll(".map-filter-btn").forEach((btn) => {
      btn.classList.toggle("active", btn.dataset.filter === filterType);
    });

    const showAttr = filterType === "all" || filterType === "attractions";
    const showHotels = filterType === "all" || filterType === "hotels";
    const showRests = filterType === "all" || filterType === "restaurants";

    markerGroups.attractions.forEach((m) => showAttr ? m.addTo(map) : m.remove());
    markerGroups.hotels.forEach((m) => showHotels ? m.addTo(map) : m.remove());
    markerGroups.restaurants.forEach((m) => showRests ? m.addTo(map) : m.remove());
  }

  let currentPackingItems = [];
  let currentPackingDest = "";
  let currentPackingWeather = null;

  function getIconForCustomItem(text) {
    const t = text.toLowerCase();
    if (t.includes("camera") || t.includes("lens") || t.includes("dslr") || t.includes("tripod")) return "📷";
    if (t.includes("shoe") || t.includes("boot") || t.includes("sneaker") || t.includes("sandal")) return "👟";
    if (t.includes("jacket") || t.includes("coat") || t.includes("fleece") || t.includes("sweater") || t.includes("hoodie")) return "🧥";
    if (t.includes("shirt") || t.includes("dress") || t.includes("top") || t.includes("clothes") || t.includes("tee")) return "👕";
    if (t.includes("pant") || t.includes("jean") || t.includes("shorts") || t.includes("trouser")) return "👖";
    if (t.includes("med") || t.includes("pill") || t.includes("tablet") || t.includes("band") || t.includes("first aid")) return "💊";
    if (t.includes("snack") || t.includes("food") || t.includes("bar") || t.includes("biscuit") || t.includes("chocolate")) return "🍫";
    if (t.includes("water") || t.includes("bottle") || t.includes("drink") || t.includes("sipper")) return "💧";
    if (t.includes("book") || t.includes("kindle") || t.includes("read") || t.includes("novel") || t.includes("guide")) return "📖";
    if (t.includes("laptop") || t.includes("ipad") || t.includes("macbook") || t.includes("computer")) return "💻";
    if (t.includes("headphone") || t.includes("earphone") || t.includes("airpod") || t.includes("audio")) return "🎧";
    if (t.includes("towel") || t.includes("swim") || t.includes("beach")) return "🏖️";
    if (t.includes("umbrella") || t.includes("rain")) return "☂️";
    if (t.includes("sunglass") || t.includes("goggles") || t.includes("shades")) return "🕶️";
    if (t.includes("hat") || t.includes("cap") || t.includes("beanie")) return "🧢";
    if (t.includes("cash") || t.includes("card") || t.includes("wallet") || t.includes("purse")) return "💳";
    if (t.includes("passport") || t.includes("visa") || t.includes("id") || t.includes("ticket") || t.includes("document")) return "🛂";
    if (t.includes("charger") || t.includes("cable") || t.includes("wire") || t.includes("plug")) return "🔌";
    if (t.includes("power bank") || t.includes("battery")) return "🔋";
    if (t.includes("toiletr") || t.includes("brush") || t.includes("paste") || t.includes("soap") || t.includes("shampoo")) return "🧴";
    if (t.includes("scarf") || t.includes("bandana") || t.includes("dupatta") || t.includes("stole")) return "🧣";
    return "🎒";
  }

  function getPackingStorageKey(dest) {
    return `planora_packing_${(dest || "default").toLowerCase().replace(/[^a-z0-9]/g, "_")}`;
  }

  function saveCurrentPacking() {
    if (!currentPackingDest) return;
    try {
      localStorage.setItem(getPackingStorageKey(currentPackingDest), JSON.stringify(currentPackingItems));
    } catch {
      // ignore
    }
  }

  function generateDefaultPackingItems(weather, destination) {
    const condition = (weather?.condition || "").toLowerCase();
    const temp = Number(weather?.temp);
    const dest = destination.toLowerCase();

    const items = [
      { id: "p_id", item: "Passport, Visa & Government Photo ID", icon: "🛂", checked: false },
      { id: "p_adapter", item: "Universal Power Adapter & Phone Cables", icon: "🔌", checked: false },
      { id: "p_powerbank", item: "High-Capacity Power Bank (10,000mAh+)", icon: "🔋", checked: false },
      { id: "p_money", item: "Credit/Debit Cards & Some Local Currency Cash", icon: "💳", checked: false },
      { id: "p_meds", item: "Personal Medications & Travel First-Aid Kit", icon: "💊", checked: false },
      { id: "p_toiletry", item: "Toiletries & Hygiene Essentials", icon: "🧴", checked: false },
    ];

    if (dest.includes("amritsar") || dest.includes("varanasi") || dest.includes("rishikesh") || dest.includes("haridwar")) {
      items.push({ id: "p_scarf", item: "Head Scarf / Bandana (Required for Gurdwaras & Temples)", icon: "🧣", checked: false });
      items.push({ id: "p_slipon", item: "Comfortable Slip-on Footwear (Easy to remove at temples)", icon: "👟", checked: false });
    }

    if (dest.includes("goa") || dest.includes("bali") || dest.includes("beach") || dest.includes("maldives")) {
      items.push({ id: "p_swim", item: "Swimwear, Boardshorts & Beach Towel", icon: "🩳", checked: false });
      items.push({ id: "p_pouch", item: "Waterproof Phone Pouch & Beach Bag", icon: "👜", checked: false });
    }

    if (dest.includes("manali") || dest.includes("shimla") || dest.includes("ladakh") || dest.includes("leh")) {
      items.push({ id: "p_thermals", item: "Thermal Base Layers & Warm Fleece", icon: "🧥", checked: false });
      items.push({ id: "p_boots", item: "Sturdy Trekking Boots & Woolen Socks", icon: "🥾", checked: false });
    }

    if (condition.includes("rain") || condition.includes("drizzle") || condition.includes("shower")) {
      items.push({ id: "p_umbrella", item: "Compact Windproof Travel Umbrella", icon: "☂️", checked: false });
      items.push({ id: "p_raincoat", item: "Waterproof Breathable Rain Jacket", icon: "🧥", checked: false });
    }

    if (!Number.isNaN(temp) && (temp >= 23 || condition.includes("clear") || condition.includes("sun"))) {
      items.push({ id: "p_sunscreen", item: "Broad-Spectrum Sunscreen (SPF 50+)", icon: "☀️", checked: false });
      items.push({ id: "p_shades", item: "UV Polarized Sunglasses & Sun Hat", icon: "🕶️", checked: false });
      items.push({ id: "p_cotton", item: "Breathable Linen & Cotton Outfits", icon: "👕", checked: false });
    }

    if (!Number.isNaN(temp) && temp <= 16) {
      items.push({ id: "p_jacket", item: "Insulated Windbreaker or Down Jacket", icon: "🧥", checked: false });
      items.push({ id: "p_balm", item: "Hydrating Moisturizer & Lip Balm", icon: "💄", checked: false });
    }

    return items;
  }

  function renderPackingChecklist(weather, destination, container) {
    if (!container) return;
    container.hidden = false;
    currentPackingDest = destination;
    currentPackingWeather = weather;

    const saved = readJson(getPackingStorageKey(destination), null);
    if (Array.isArray(saved) && saved.length > 0) {
      currentPackingItems = saved;
    } else {
      currentPackingItems = generateDefaultPackingItems(weather, destination);
      saveCurrentPacking();
    }

    renderPackingDOM(container);
  }

  function renderPackingDOM(container) {
    if (!container) return;
    const total = currentPackingItems.length;
    const packed = currentPackingItems.filter((i) => i.checked).length;
    const pct = total > 0 ? Math.round((packed / total) * 100) : 0;

    container.innerHTML = `
      <div class="packing-header-card">
        <div class="packing-header-top">
          <div>
            <h3 class="section-label">Smart Packing Checklist <span class="checklist-badge">Tailored to ${englishText(currentPackingDest, "Destination")}</span></h3>
            <p class="packing-subtitle">Interactive checklist: check off packed items, add your custom gear, or remove what you don't need.</p>
          </div>
          <div class="packing-header-actions">
            <button type="button" id="packing-reset-btn" class="packing-reset-btn" title="Reset back to suggested defaults">↺ Reset Suggestions</button>
          </div>
        </div>

        <div class="packing-progress-wrap">
          <div class="packing-progress-labels">
            <span class="packing-progress-count"><strong>${packed}</strong> of <strong>${total}</strong> items packed</span>
            <span class="packing-progress-pct">${pct}%</span>
          </div>
          <div class="packing-progress-bar">
            <div class="packing-progress-fill" style="width: ${pct}%"></div>
          </div>
          ${pct === 100 && total > 0 ? `<div class="packing-complete-celebration">🎉 All set! You're 100% packed and ready to go.</div>` : ""}
        </div>
      </div>

      <div class="packing-card">
        <div class="packing-grid" id="packing-grid">
          ${currentPackingItems
            .map(
              (entry) => `
            <div class="packing-item ${entry.checked ? "checked" : ""}" data-id="${entry.id}">
              <label class="packing-item-left">
                <input type="checkbox" class="packing-check" data-id="${entry.id}" ${entry.checked ? "checked" : ""}>
                <span class="packing-icon">${entry.icon || "🎒"}</span>
                <span class="packing-text">${englishText(entry.item, "")}</span>
              </label>
              <button type="button" class="packing-del-btn" data-id="${entry.id}" title="Remove this item">✕</button>
            </div>`,
            )
            .join("")}
        </div>

        <form id="packing-add-form" class="packing-add-form">
          <div class="packing-input-group">
            <input type="text" id="packing-new-input" class="packing-add-input" placeholder="Add custom item (e.g. DSLR camera, power strip, walking shoes)..." maxlength="60" required autocomplete="off">
            <button type="submit" class="packing-add-btn">＋ Add Item</button>
          </div>
        </form>
      </div>`;

    // Event 1: Checkbox toggles
    container.querySelectorAll(".packing-check").forEach((cb) => {
      cb.addEventListener("change", (e) => {
        const id = e.target.dataset.id;
        const item = currentPackingItems.find((i) => String(i.id) === String(id));
        if (item) {
          item.checked = e.target.checked;
          saveCurrentPacking();
          const parentItem = container.querySelector(`.packing-item[data-id="${id}"]`);
          if (parentItem) {
            parentItem.classList.toggle("checked", item.checked);
          }
          updatePackingProgressOnly(container);
        }
      });
    });

    // Event 2: Delete buttons
    container.querySelectorAll(".packing-del-btn").forEach((btn) => {
      btn.addEventListener("click", (e) => {
        e.stopPropagation();
        const id = btn.dataset.id;
        currentPackingItems = currentPackingItems.filter((i) => String(i.id) !== String(id));
        saveCurrentPacking();
        renderPackingDOM(container);
        showToast("Item removed from checklist");
      });
    });

    // Event 3: Add new item
    const addForm = container.querySelector("#packing-add-form");
    if (addForm) {
      addForm.addEventListener("submit", (e) => {
        e.preventDefault();
        const input = container.querySelector("#packing-new-input");
        const val = (input?.value || "").trim();
        if (!val) return;

        const newItem = {
          id: "custom_" + Date.now(),
          item: val,
          icon: getIconForCustomItem(val),
          checked: false,
        };
        currentPackingItems.push(newItem);
        saveCurrentPacking();
        renderPackingDOM(container);
        showToast(`Added "${val}" to packing list!`);
        const newInput = container.querySelector("#packing-new-input");
        if (newInput) newInput.focus();
      });
    }

    // Event 4: Reset suggestions
    const resetBtn = container.querySelector("#packing-reset-btn");
    if (resetBtn) {
      resetBtn.addEventListener("click", () => {
        currentPackingItems = generateDefaultPackingItems(currentPackingWeather, currentPackingDest);
        saveCurrentPacking();
        renderPackingDOM(container);
        showToast("Checklist reset to destination defaults");
      });
    }
  }

  function updatePackingProgressOnly(container) {
    const total = currentPackingItems.length;
    const packed = currentPackingItems.filter((i) => i.checked).length;
    const pct = total > 0 ? Math.round((packed / total) * 100) : 0;

    const countEl = container.querySelector(".packing-progress-count");
    if (countEl) countEl.innerHTML = `<strong>${packed}</strong> of <strong>${total}</strong> items packed`;

    const pctEl = container.querySelector(".packing-progress-pct");
    if (pctEl) pctEl.textContent = `${pct}%`;

    const fillEl = container.querySelector(".packing-progress-fill");
    if (fillEl) fillEl.style.width = `${pct}%`;

    const celebrationWrap = container.querySelector(".packing-progress-wrap");
    let celEl = container.querySelector(".packing-complete-celebration");
    if (pct === 100 && total > 0) {
      if (!celEl && celebrationWrap) {
        celEl = document.createElement("div");
        celEl.className = "packing-complete-celebration";
        celEl.textContent = "🎉 All set! You're 100% packed and ready to go.";
        celebrationWrap.appendChild(celEl);
      }
    } else if (celEl) {
      celEl.remove();
    }
  }

  function generateTripSummary(planData, destination, startDate, endDate, budget) {
    const weatherStr = planData.weather && planData.weather.temp !== "N/A"
      ? `${planData.weather.temp}°C, ${planData.weather.condition || "Pleasant"}`
      : planData.weather?.condition || "Forecast available";

    const currencyStr = planData.currency?.converted
      ? `${planData.currency.target} ${Number(planData.currency.converted).toLocaleString("en-US")}`
      : `₹${Number(budget).toLocaleString("en-IN")}`;

    let text = `🌍 Planora Trip: ${destination}\n`;
    text += `📅 Dates: ${startDate} to ${endDate} (${planData.itinerary?.length || 0} Days)\n`;
    text += `🌤️ Weather: ${weatherStr}\n`;
    text += `💰 Budget: ₹${Number(budget).toLocaleString("en-IN")} (~${currencyStr})\n\n`;
    text += `📍 DAY-BY-DAY ITINERARY:\n`;

    (planData.itinerary || []).forEach((day) => {
      text += `\nDay ${day.day} (${day.date}): ${day.title}\n`;
      if (day.routeSummary) {
        text += `  🚗 Route: ~${day.routeSummary.distanceKm} km (${day.routeSummary.durationMin} mins drive)\n`;
      }
      (day.activities || []).forEach((act) => {
        if (typeof act === "object" && act !== null) {
          text += `  • [${act.time || "Visit"}] ${act.title}${act.desc ? ` — ${act.desc}` : ""}\n`;
          if (act.tip) text += `    💡 Tour Tip: ${act.tip}\n`;
        } else {
          text += `  • ${act}\n`;
        }
      });
    });

    if (currentPackingItems.length > 0) {
      const packedCount = currentPackingItems.filter((i) => i.checked).length;
      text += `\n🎒 PACKING STATUS (${packedCount}/${currentPackingItems.length} packed):\n`;
      currentPackingItems.forEach((i) => {
        text += `  [${i.checked ? "x" : " "}] ${i.icon || "•"} ${i.item}\n`;
      });
    }

    text += `\n✈️ Planned with Planora • Smart Travel Planner`;
    return text;
  }

  function showToast(msg) {
    const toastEl = document.getElementById("toast");
    if (!toastEl) return;
    toastEl.textContent = msg;
    toastEl.hidden = false;
    toastEl.classList.add("toast-show");
    setTimeout(() => {
      toastEl.classList.remove("toast-show");
      setTimeout(() => {
        toastEl.hidden = true;
      }, 300);
    }, 3200);
  }

  // ── MOBILE BOTTOM NAVIGATION ──────────────────────────────
  const mobileNavItems = document.querySelectorAll(".mobile-nav-item");

  function scrollToMobileSection(targetId) {
    const targetEl = document.getElementById(targetId);
    if (!targetEl) return;

    if (targetId === "map-wrapper" && targetEl.hidden) {
      targetEl.hidden = false;
    }

    const navOffset = 64;
    const elementPosition = targetEl.getBoundingClientRect().top;
    const offsetPosition = elementPosition + window.pageYOffset - navOffset;

    window.scrollTo({
      top: Math.max(0, offsetPosition),
      behavior: "smooth",
    });

    if (targetId === "map-wrapper" && map) {
      setTimeout(() => map.invalidateSize(), 300);
    }
  }

  mobileNavItems.forEach((btn) => {
    btn.addEventListener("click", () => {
      const targetId = btn.dataset.target;
      mobileNavItems.forEach((b) => b.classList.remove("active"));
      btn.classList.add("active");
      scrollToMobileSection(targetId);
    });
  });

  // Scroll Spy for Mobile Nav Bar
  let scrollThrottleTimer = null;
  window.addEventListener(
    "scroll",
    () => {
      if (window.innerWidth > 768) return;
      if (scrollThrottleTimer) return;
      scrollThrottleTimer = setTimeout(() => {
        scrollThrottleTimer = null;
        const sectionIds = [
          "budget-tracker",
          "packing-checklist",
          "map-wrapper",
          "timeline",
          "trip-form",
        ];
        for (const id of sectionIds) {
          const el = document.getElementById(id);
          if (el && !el.hidden) {
            const rect = el.getBoundingClientRect();
            if (rect.top <= 250 && rect.bottom >= 120) {
              mobileNavItems.forEach((btn) => {
                btn.classList.toggle("active", btn.dataset.target === id);
              });
              break;
            }
          }
        }
      }, 100);
    },
    { passive: true },
  );

  // Invalidate Leaflet map size on screen resize & orientation change
  window.addEventListener("resize", () => {
    if (map) map.invalidateSize();
  });
  window.addEventListener("orientationchange", () => {
    setTimeout(() => {
      if (map) map.invalidateSize();
    }, 280);
  });
});

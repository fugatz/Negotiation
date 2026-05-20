const DATA_URLS = [
  "/simulation/reports/sample-runs/latest.json",
  "../simulation/reports/sample-runs/latest.json",
];

const STORAGE_KEY = "distinkt-pricing-admin-actions";

const state = {
  report: null,
  filter: "all",
  view: "all",
  search: "",
  selectedProjectId: null,
  selectedQuoteId: null,
  actions: loadActions(),
};

const els = {
  policyPill: document.querySelector("#policyPill"),
  refreshButton: document.querySelector("#refreshButton"),
  metrics: document.querySelector("#metrics"),
  projectCount: document.querySelector("#projectCount"),
  searchInput: document.querySelector("#searchInput"),
  projectList: document.querySelector("#projectList"),
  projectSummary: document.querySelector("#projectSummary"),
  slateTitle: document.querySelector("#slateTitle"),
  slateList: document.querySelector("#slateList"),
  detailPane: document.querySelector("#detailPane"),
};

function loadActions() {
  try {
    return JSON.parse(localStorage.getItem(STORAGE_KEY) || "{}");
  } catch {
    return {};
  }
}

function saveActions() {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(state.actions));
}

function html(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function compact(value) {
  return String(value ?? "")
    .replaceAll("_", " ")
    .replace(/\b\w/g, (letter) => letter.toUpperCase());
}

function formatMoney(value, currency = "USD") {
  const amount = Number(value || 0);
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency,
    maximumFractionDigits: amount < 1000 ? 0 : 0,
  }).format(amount);
}

function formatPct(value, signed = false) {
  const number = Number(value || 0) * 100;
  const sign = signed && number > 0 ? "+" : "";
  return `${sign}${number.toFixed(1)}%`;
}

function traceRecommendations(trace) {
  const groups = [
    ["recommended", trace.recommendedSlate || []],
    ["stress", trace.stressShortlist || []],
    ["override", trace.adminOverrideSlate || []],
  ];
  return groups.flatMap(([group, records]) =>
    records.map((rec, index) => ({
      ...rec,
      __group: group,
      __quoteId:
        rec.quoteLifecycle?.quoteId ||
        `${trace.projectId}-${group}-${rec.talent}-${index}`.toLowerCase().replace(/\W+/g, "-"),
    })),
  );
}

function allRecommendations() {
  return (state.report?.traces || []).flatMap((trace) =>
    traceRecommendations(trace).map((rec) => ({ trace, rec })),
  );
}

function actionFor(rec) {
  return state.actions[rec.__quoteId]?.action || "pending";
}

function reviewCount(trace) {
  return traceRecommendations(trace).filter(
    (rec) => (rec.adminGovernance?.exceptionTriggers || []).length > 0,
  ).length;
}

function hasPaidActual(trace) {
  return traceRecommendations(trace).some(
    (rec) => rec.budgetContext?.marketCostContext?.paidRateActual,
  );
}

function traceMatchesSearch(trace) {
  if (!state.search) return true;
  const haystack = [
    trace.project,
    trace.client,
    trace.outcome,
    ...traceRecommendations(trace).map((rec) => `${rec.talent} ${rec.role} ${rec.lane}`),
  ]
    .join(" ")
    .toLowerCase();
  return haystack.includes(state.search.toLowerCase());
}

function traceMatchesFilter(trace) {
  if (state.filter === "review") {
    return reviewCount(trace) > 0 || !trace.readinessGate?.bindingQuoteAllowed;
  }
  if (state.filter === "actuals") {
    return hasPaidActual(trace);
  }
  if (state.filter === "blocked") {
    return !trace.readinessGate?.bindingQuoteAllowed || String(trace.outcome).includes("scope");
  }
  return true;
}

function filteredTraces() {
  return (state.report?.traces || []).filter(
    (trace) => traceMatchesFilter(trace) && traceMatchesSearch(trace),
  );
}

function selectedTrace() {
  return (
    (state.report?.traces || []).find((trace) => trace.projectId === state.selectedProjectId) ||
    filteredTraces()[0] ||
    state.report?.traces?.[0]
  );
}

function selectedRecommendation(trace = selectedTrace()) {
  const recs = trace ? traceRecommendations(trace) : [];
  return recs.find((rec) => rec.__quoteId === state.selectedQuoteId) || recs[0] || null;
}

function chipClass(kind) {
  if (kind === "booked" || kind === "ready" || kind === "approved") return "good";
  if (kind === "pending" || kind === "review" || kind === "hold") return "warn";
  if (kind === "risk" || kind === "reopened" || kind === "blocked") return "risk";
  if (kind === "actuals" || kind === "ratecard") return "info";
  return "neutral";
}

function chip(label, kind = "neutral") {
  return `<span class="chip ${chipClass(kind)}">${html(label)}</span>`;
}

function renderMetrics() {
  const metrics = state.report?.metrics || {};
  const tiles = [
    ["Scenarios", metrics.scenarioCount],
    ["Approvals", metrics.adminApprovalRequiredCount],
    ["Mature", metrics.matureAutonomyCandidateCount],
    ["Paid Actuals", metrics.paidRateActualRecommendationCount],
    ["Warnings", state.report?.validation?.warningCount],
    ["Audit Events", metrics.quoteAuditEventCount],
  ];
  els.metrics.innerHTML = tiles
    .map(([label, value]) => {
      return `
        <div class="metric-tile">
          <span>${html(label)}</span>
          <strong>${html(value ?? 0)}</strong>
        </div>
      `;
    })
    .join("");
}

function renderProjectList() {
  const traces = filteredTraces();
  els.projectCount.textContent = traces.length;
  if (!traces.length) {
    els.projectList.innerHTML = emptyState();
    return;
  }
  els.projectList.innerHTML = traces
    .map((trace) => {
      const active = trace.projectId === selectedTrace()?.projectId ? "active" : "";
      const recs = traceRecommendations(trace);
      const reviews = reviewCount(trace);
      const statusKind = !trace.readinessGate?.bindingQuoteAllowed
        ? "blocked"
        : reviews > 0
          ? "review"
          : "ready";
      return `
        <button class="project-button ${active}" type="button" data-project-id="${html(trace.projectId)}">
          <span class="project-title">${html(trace.project)}</span>
          <span class="project-meta">
            ${chip(compact(trace.outcome), statusKind)}
            ${chip(`${recs.length} quotes`)}
            ${hasPaidActual(trace) ? chip("Paid actual", "actuals") : ""}
          </span>
        </button>
      `;
    })
    .join("");
}

function renderProjectSummary(trace) {
  if (!trace) {
    els.projectSummary.innerHTML = emptyState();
    return;
  }

  const ctx = trace.projectContext || {};
  const trust = trace.clientCredibility || {};
  els.projectSummary.innerHTML = `
    <div class="row-between">
      <div>
        <p class="eyebrow">${html(trace.client)}</p>
        <h2>${html(trace.project)}</h2>
      </div>
      ${chip(compact(trace.outcome), trace.outcome === "booked" ? "booked" : "review")}
    </div>
    <div class="summary-grid">
      <div class="summary-item">
        <span>All In</span>
        <strong>${formatMoney(ctx.allInBudget, ctx.currency || "USD")}</strong>
      </div>
      <div class="summary-item">
        <span>Talent Budget</span>
        <strong>${formatMoney(ctx.talentBudget, ctx.currency || "USD")}</strong>
      </div>
      <div class="summary-item">
        <span>Readiness</span>
        <strong>${html(compact(trace.readinessGate?.projectReadinessTier || "unknown"))}</strong>
      </div>
      <div class="summary-item">
        <span>Client Trust</span>
        <strong>${html(compact(trust.clientTrustTier || "unknown"))} ${html(trust.clientTrustScore ?? "")}</strong>
      </div>
    </div>
  `;
}

function recommendationMatchesView(rec) {
  if (state.view === "exceptions") {
    return (rec.adminGovernance?.exceptionTriggers || []).length > 0;
  }
  if (state.view === "actors") {
    return rec.talentClass === "actor";
  }
  return true;
}

function renderSlate(trace) {
  if (!trace) {
    els.slateList.innerHTML = emptyState();
    return;
  }
  const recs = traceRecommendations(trace).filter(recommendationMatchesView);
  els.slateTitle.textContent = `${traceRecommendations(trace).length} Recommendations`;
  if (!recs.length) {
    els.slateList.innerHTML = emptyState();
    return;
  }
  els.slateList.innerHTML = recs.map((rec) => slateCard(trace, rec)).join("");
}

function slateCard(trace, rec) {
  const currency = rec.expectedBookingRange?.currency || trace.projectContext?.currency || "USD";
  const exceptions = rec.adminGovernance?.exceptionTriggers || [];
  const active = rec.__quoteId === selectedRecommendation(trace)?.__quoteId ? "active" : "";
  const action = actionFor(rec);
  const market = rec.budgetContext?.marketCostContext || {};
  return `
    <article class="slate-card ${active}" data-quote-id="${html(rec.__quoteId)}">
      <div class="slate-main">
        <h3>${html(rec.talent)}</h3>
        <div class="chip-row">
          ${chip(rec.lane)}
          ${chip(compact(rec.clientVisiblePriceState), rec.clientVisiblePriceState === "outside stated budget" ? "risk" : "neutral")}
          ${exceptions.length ? chip(`${exceptions.length} exceptions`, "review") : chip("Clean", "ready")}
          ${market.paidRateActual ? chip("Paid actual", "actuals") : ""}
          ${market.actorRateCard ? chip("Rate card", "ratecard") : ""}
          ${chip(compact(action), action)}
        </div>
        <div class="quote-line">
          <span class="quote">${formatMoney(rec.quote, currency)}</span>
          <span class="quote-sub">v${html(rec.quoteLifecycle?.quoteVersion || 1)} ${html(compact(rec.quoteLifecycle?.quoteState || "locked"))}</span>
        </div>
      </div>
      <div class="mini-stat-grid">
        <div class="mini-stat"><span>Creative</span><strong>${formatPct(rec.creativeFit)}</strong></div>
        <div class="mini-stat"><span>Price Fit</span><strong>${formatPct(rec.priceFit)}</strong></div>
        <div class="mini-stat"><span>Accept</span><strong>${formatPct(rec.acceptanceProbability)}</strong></div>
      </div>
    </article>
  `;
}

function renderDetail(trace, rec) {
  if (!trace || !rec) {
    els.detailPane.innerHTML = emptyState();
    return;
  }
  const range = rec.expectedBookingRange || {};
  const currency = range.currency || trace.projectContext?.currency || "USD";
  const exceptions = rec.adminGovernance?.exceptionTriggers || [];
  const market = rec.budgetContext?.marketCostContext || {};
  const prior = market.actorMarketRatePrior;
  const paid = market.paidRateActual;
  const rateCard = market.actorRateCard;
  const admin = rec.aiRationales?.adminPricingRationale || {};
  const action = state.actions[rec.__quoteId];

  els.detailPane.innerHTML = `
    <p class="eyebrow">${html(rec.role || rec.talentClass)}</p>
    <h2>${html(rec.talent)}</h2>
    <div class="chip-row">
      ${chip(rec.talentClass)}
      ${chip(compact(rec.candidateSource))}
      ${chip(compact(actionFor(rec)), actionFor(rec))}
    </div>
    <div class="quote-line">
      <span class="quote">${formatMoney(rec.quote, currency)}</span>
      <span class="quote-sub">${html(compact(rec.availabilityCheck?.status || "pending"))}</span>
    </div>
    <div class="detail-actions">
      <button class="action-button primary" type="button" data-action="approved" data-quote-id="${html(rec.__quoteId)}">
        <i data-lucide="check"></i> Approve
      </button>
      <button class="action-button warn" type="button" data-action="hold" data-quote-id="${html(rec.__quoteId)}">
        <i data-lucide="pause"></i> Hold
      </button>
      <button class="action-button danger" type="button" data-action="reopened" data-quote-id="${html(rec.__quoteId)}">
        <i data-lucide="rotate-ccw"></i> Reopen
      </button>
    </div>
    ${action ? `<p class="quote-sub">Last action: ${html(compact(action.action))} at ${html(new Date(action.at).toLocaleString())}</p>` : ""}

    <section class="detail-section">
      <h3>Expected Range</h3>
      ${rangeBar(range, rec.quote, currency)}
    </section>

    <section class="detail-section">
      <h3>Review Triggers</h3>
      ${list(exceptions.length ? exceptions.map(compact) : ["No exception triggers"], "exception-list")}
    </section>

    <section class="detail-section">
      <h3>Pricing Inputs</h3>
      ${rows([
        ["Timing", `${formatPct(rec.timing?.rateDelta, true)} rate, ${formatPct(rec.timing?.confidenceDelta, true)} confidence`],
        ["Behavior", formatPct(rec.behavior?.combinedBehaviorRateDelta, true)],
        ["Advocacy", rec.talentAdvocacy?.applies ? formatPct(rec.talentAdvocacy.rateDelta, true) : "Not applied"],
        ["AI Discretion", `${formatPct(admin.discretionDelta, true)} ${html(admin.discretionMode || "shadow")}`],
        ["Legal Floor", `${formatMoney(rec.legalFloor?.effectiveFloor, currency)} ${compact(rec.legalFloor?.basis)}`],
      ])}
    </section>

    <section class="detail-section">
      <h3>Market Evidence</h3>
      ${marketEvidence(market, prior, paid, rateCard, currency)}
    </section>

    <section class="detail-section">
      <h3>Admin Rationale</h3>
      ${list(admin.reasons || ["No rationale generated"], "rationale-list")}
    </section>

    <section class="detail-section">
      <h3>Assumptions</h3>
      ${list(range.assumptionsIncluded || [], "assumption-list")}
    </section>

    <section class="detail-section">
      <h3>Audit</h3>
      ${auditRows(rec.quoteLifecycle?.auditEvents || [])}
    </section>

    ${settingsPanel()}
  `;
}

function rangeBar(range, quote, currency) {
  const low = Number(range.low || quote || 0);
  const high = Number(range.high || quote || 0);
  const spread = Math.max(high - low, 1);
  const marker = Math.min(100, Math.max(0, ((Number(quote || 0) - low) / spread) * 100));
  return `
    <div class="range-track">
      <div class="range-fill"></div>
      <div class="range-marker" style="left: ${marker}%"></div>
    </div>
    <div class="range-labels">
      <span>${formatMoney(low, currency)}</span>
      <span>${formatMoney(quote, currency)}</span>
      <span>${formatMoney(high, currency)}</span>
    </div>
  `;
}

function rows(items) {
  return items
    .map(
      ([label, value]) => `
        <div class="row-between evidence-row">
          <span>${html(label)}</span>
          <strong>${html(value)}</strong>
        </div>
      `,
    )
    .join("");
}

function marketEvidence(market, prior, paid, rateCard, currency) {
  if (!market?.available) {
    return rows([["Source", "No market evidence matched"]]);
  }
  if (paid) {
    return rows([
      ["Source", paid.sourceName],
      ["Country", paid.country],
      ["Observed Day", formatMoney(paid.observedHighDayRate, paid.currency || currency)],
      ["Buyout", formatMoney(paid.observedBuyout, paid.currency || currency)],
      ["One Day Total", formatMoney(paid.observedOneShootDayTotal, paid.currency || currency)],
      ["Confidence", compact(paid.confidence)],
    ]);
  }
  if (rateCard) {
    return rows([
      ["Source", rateCard.agreement],
      ["Country", rateCard.country],
      ["Agreement Floor", formatMoney(rateCard.standardDayTotalWithHolidayPay, rateCard.currency || currency)],
      ["Authority", compact(prior?.calibrationAuthority || "published rate card")],
    ]);
  }
  return rows([
    ["Source", "Cost proxy"],
    ["Country", market.country],
    ["Pressure", compact(market.expectedLocalRatePressure)],
    ["Prior", `${market.talentCostPriorVsBaseline}x France`],
    ["Leverage", `${market.localBudgetLeverageVsBaseline}x`],
  ]);
}

function auditRows(events) {
  const visible = events.slice(-6);
  return visible
    .map(
      (event) => `
        <div class="audit-row">
          <strong>${html(compact(event.eventType))}</strong>
          <div class="quote-sub">${html(event.actor)} · ${html(compact(event.reasonCode))}</div>
        </div>
      `,
    )
    .join("");
}

function list(items, className) {
  const records = items.length ? items : ["None"];
  return `<ul class="${className}">${records.map((item) => `<li>${html(item)}</li>`).join("")}</ul>`;
}

function settingsPanel() {
  const controls = [
    ["timingCap", "Timing Cap", 0, 10, 8],
    ["behaviorCap", "Behavior Cap", 0, 8, 5],
    ["advocacyCap", "Advocacy Cap", 0, 10, 8],
    ["aiCap", "AI Shadow", 0, 3, 1],
  ];
  return `
    <section class="settings-panel">
      <p class="eyebrow">Policy Knobs</p>
      ${controls
        .map(
          ([id, label, min, max, value]) => `
            <div class="setting-row">
              <label for="${id}">${label}</label>
              <output id="${id}Output">${value}%</output>
              <input id="${id}" type="range" min="${min}" max="${max}" value="${value}" />
            </div>
          `,
        )
        .join("")}
    </section>
  `;
}

function emptyState() {
  const template = document.querySelector("#emptyStateTemplate");
  return template.innerHTML;
}

function render() {
  const trace = selectedTrace();
  if (trace && !state.selectedProjectId) {
    state.selectedProjectId = trace.projectId;
  }
  const rec = selectedRecommendation(trace);
  if (rec && !state.selectedQuoteId) {
    state.selectedQuoteId = rec.__quoteId;
  }

  els.policyPill.textContent = state.report?.policy || "No policy";
  renderMetrics();
  renderProjectList();
  renderProjectSummary(trace);
  renderSlate(trace);
  renderDetail(trace, rec);
  bindSettingOutputs();
  refreshIcons();
}

function bindSettingOutputs() {
  document.querySelectorAll(".setting-row input").forEach((input) => {
    const output = document.querySelector(`#${input.id}Output`);
    if (!output) return;
    input.addEventListener("input", () => {
      output.textContent = `${input.value}%`;
    });
  });
}

function refreshIcons() {
  if (window.lucide) {
    window.lucide.createIcons();
  }
}

async function loadReport() {
  els.policyPill.textContent = "Loading";
  let lastError;
  for (const url of DATA_URLS) {
    try {
      const response = await fetch(`${url}?t=${Date.now()}`);
      if (!response.ok) throw new Error(`${response.status} ${response.statusText}`);
      state.report = await response.json();
      const firstTrace = state.report.traces?.[0];
      state.selectedProjectId = state.selectedProjectId || firstTrace?.projectId;
      state.selectedQuoteId = null;
      render();
      return;
    } catch (error) {
      lastError = error;
    }
  }
  els.policyPill.textContent = "Load failed";
  els.projectSummary.innerHTML = `
    <div class="empty-state">
      <i data-lucide="circle-alert"></i>
      <h3>${html(lastError?.message || "Unable to load report")}</h3>
    </div>
  `;
  refreshIcons();
}

document.addEventListener("click", (event) => {
  const projectButton = event.target.closest("[data-project-id]");
  if (projectButton) {
    state.selectedProjectId = projectButton.dataset.projectId;
    state.selectedQuoteId = null;
    render();
    return;
  }

  const slateCard = event.target.closest(".slate-card[data-quote-id]");
  if (slateCard) {
    state.selectedQuoteId = slateCard.dataset.quoteId;
    render();
    return;
  }

  const filterButton = event.target.closest(".filter-button[data-filter]");
  if (filterButton) {
    state.filter = filterButton.dataset.filter;
    document.querySelectorAll(".filter-button").forEach((button) => {
      button.classList.toggle("active", button === filterButton);
    });
    state.selectedProjectId = null;
    state.selectedQuoteId = null;
    render();
    return;
  }

  const segment = event.target.closest(".segment[data-view]");
  if (segment) {
    state.view = segment.dataset.view;
    document.querySelectorAll(".segment").forEach((button) => {
      button.classList.toggle("active", button === segment);
    });
    state.selectedQuoteId = null;
    render();
    return;
  }

  const actionButton = event.target.closest(".action-button[data-action]");
  if (actionButton) {
    const quoteId = actionButton.dataset.quoteId;
    state.actions[quoteId] = {
      action: actionButton.dataset.action,
      at: new Date().toISOString(),
    };
    saveActions();
    render();
  }
});

els.searchInput.addEventListener("input", (event) => {
  state.search = event.target.value.trim();
  state.selectedProjectId = null;
  state.selectedQuoteId = null;
  render();
});

els.refreshButton.addEventListener("click", () => {
  state.selectedQuoteId = null;
  loadReport();
});

loadReport();

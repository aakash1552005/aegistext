/**
 * AegisText Web Application Controller
 */

document.addEventListener("DOMContentLoaded", () => {
  const inputText = document.getElementById("inputText");
  const charCountLabel = document.getElementById("charCountLabel");
  const wordCountLabel = document.getElementById("wordCountLabel");
  const toggleSanitize = document.getElementById("toggleSanitize");
  const btnAnalyze = document.getElementById("btnAnalyze");
  const btnClear = document.getElementById("btnClear");

  const emptyStateView = document.getElementById("emptyStateView");
  const resultsContentView = document.getElementById("resultsContentView");
  const classificationBadge = document.getElementById("classificationBadge");
  const confidenceBandText = document.getElementById("confidenceBandText");
  const aiProbabilityValue = document.getElementById("aiProbabilityValue");
  const gaugeBarFill = document.getElementById("gaugeBarFill");

  const securityBanner = document.getElementById("securityBanner");
  const securityTitle = document.getElementById("securityTitle");
  const securityDesc = document.getElementById("securityDesc");

  const sentenceHeatmapContainer = document.getElementById("sentenceHeatmapContainer");
  const attributionsTableBody = document.getElementById("attributionsTableBody");
  const diagnosticsList = document.getElementById("diagnosticsList");

  const btnExportJson = document.getElementById("btnExportJson");
  const btnPrintReport = document.getElementById("btnPrintReport");
  const btnOpenBenchmarks = document.getElementById("btnOpenBenchmarks");
  const btnCloseBenchmarks = document.getElementById("btnCloseBenchmarks");
  const benchmarksModal = document.getElementById("benchmarksModal");

  let currentAnalysisData = null;

  // Preset Samples
  const PRESETS = {
    human: (
      "Recent investigations into distributed consensus algorithms reveal fundamental " +
      "trade-offs between latency and partition tolerance. In asynchronous networks, deterministic " +
      "consensus cannot be guaranteed in the presence of even a single unannounced crash failure. " +
      "Empirical benchmarks across geo-distributed nodes demonstrate that speculative execution mitigates " +
      "tail latency by up to thirty-four percent without violating linearizability guarantees."
    ),
    ai: (
      "In conclusion, distributed consensus mechanisms represent a pivotal foundation of modern decentralized architecture. " +
      "Furthermore, it is crucial to recognize that latency and fault tolerance must be carefully balanced to achieve optimal throughput. " +
      "Moreover, empirical evaluations clearly demonstrate that speculative execution plays an essential role in improving overall " +
      "system reliability and cryptographic security in contemporary digital ecosystems."
    ),
    humanized: (
      "Honestly, when looking at distributed consensus, there are some pretty major trade-offs between speed and network partition tolerance. " +
      "As it turns out, in asynchronous setups, you just can't guarantee consensus if even a single node crashes unexpectedly. " +
      "To be fair, testing across multiple cloud regions shows that running speculative execution cuts tail latency by almost thirty-five percent."
    ),
  };

  // Text metrics updater
  function updateTextCounters() {
    const text = inputText.value;
    charCountLabel.textContent = `${text.length} characters`;
    const words = text.trim() ? text.trim().split(/\s+/).length : 0;
    wordCountLabel.textContent = `${words} words`;
  }

  inputText.addEventListener("input", updateTextCounters);

  // Preset button handlers
  document.getElementById("btnPresetHuman").addEventListener("click", () => {
    inputText.value = PRESETS.human;
    updateTextCounters();
  });

  document.getElementById("btnPresetAi").addEventListener("click", () => {
    inputText.value = PRESETS.ai;
    updateTextCounters();
  });

  document.getElementById("btnPresetHumanized").addEventListener("click", () => {
    // Add an adversarial zero-width space and Cyrillic homoglyph to show defense in action
    inputText.value = PRESETS.humanized.replace("consensus", "c\u200bonsensus").replace("network", "nеtwork");
    updateTextCounters();
  });

  btnClear.addEventListener("click", () => {
    inputText.value = "";
    updateTextCounters();
    emptyStateView.classList.remove("hidden");
    resultsContentView.classList.add("hidden");
  });

  // Modal handlers
  btnOpenBenchmarks.addEventListener("click", () => {
    benchmarksModal.classList.remove("hidden");
  });

  btnCloseBenchmarks.addEventListener("click", () => {
    benchmarksModal.classList.add("hidden");
  });

  benchmarksModal.addEventListener("click", (e) => {
    if (e.target === benchmarksModal) {
      benchmarksModal.classList.add("hidden");
    }
  });

  // Tab Switching
  document.querySelectorAll(".tab-btn").forEach((btn) => {
    btn.addEventListener("click", () => {
      document.querySelectorAll(".tab-btn").forEach((b) => b.classList.remove("active"));
      document.querySelectorAll(".tab-pane").forEach((p) => p.classList.remove("active"));
      btn.classList.add("active");
      const targetPane = document.getElementById(btn.dataset.tab);
      if (targetPane) targetPane.classList.add("active");
    });
  });

  // Analyze Action
  btnAnalyze.addEventListener("click", async () => {
    const text = inputText.value.trim();
    if (!text || text.length < 10) {
      alert("Please enter at least 10 characters to analyze.");
      return;
    }

    btnAnalyze.disabled = true;
    btnAnalyze.innerHTML = "Analyzing...";

    try {
      const response = await fetch("/api/v1/explain", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          text: text,
          sanitize_adversarial: toggleSanitize.checked,
        }),
      });

      if (!response.ok) {
        throw new Error(`API error: ${response.status}`);
      }

      const data = await response.json();
      currentAnalysisData = data;
      renderResults(data);
    } catch (err) {
      console.error(err);
      alert("Analysis failed. Please verify the AegisText engine is running.");
    } finally {
      btnAnalyze.disabled = false;
      btnAnalyze.innerHTML = `
        <span class="btn-icon">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2"><path d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"/></svg>
        </span>
        Analyze Text
      `;
    }
  });

  function renderResults(data) {
    emptyStateView.classList.add("hidden");
    resultsContentView.classList.remove("hidden");

    const det = data.detection;
    const prob = det.ai_probability;
    const pct = Math.round(prob * 1000) / 10;

    // Verdict Badge
    classificationBadge.textContent = det.classification;
    if (det.classification === "AI_GENERATED") {
      classificationBadge.className = "classification-badge ai";
      gaugeBarFill.style.background = "var(--color-ai)";
    } else {
      classificationBadge.className = "classification-badge human";
      gaugeBarFill.style.background = "var(--color-human)";
    }

    confidenceBandText.textContent = `Confidence: ${det.confidence_band.replace(/_/g, " ")} (${det.processing_time_ms} ms)`;
    aiProbabilityValue.textContent = `${pct}%`;
    gaugeBarFill.style.width = `${pct}%`;

    // Security Alert
    const audit = det.tampering_report || {};
    if (audit.adversarial_markers_present) {
      securityBanner.classList.remove("hidden");
      securityTitle.textContent = "Adversarial Evasion Markers Intercepted";
      securityDesc.textContent = (
        `Sanitized ${audit.zero_width_count || 0} zero-width invisible character(s) and ` +
        `${audit.homoglyph_count || 0} confusable character(s). The model evaluated canonical text.`
      );
    } else {
      securityBanner.classList.add("hidden");
    }

    // Sentence Heatmap
    sentenceHeatmapContainer.innerHTML = "";
    (data.sentence_heatmap || []).forEach((s) => {
      const span = document.createElement("span");
      span.className = `heat-sent ${s.suspicion_level.toLowerCase()}`;
      span.textContent = s.text + " ";
      span.title = `Sentence #${s.sentence_index + 1}: ${Math.round(s.ai_probability * 100)}% AI suspicion (${s.suspicion_level})`;
      sentenceHeatmapContainer.appendChild(span);
    });

    // Attributions Table
    attributionsTableBody.innerHTML = "";
    (data.feature_attributions || []).forEach((f) => {
      const tr = document.createElement("tr");
      const dirBadge = f.ai_indicative === "high"
        ? '<span class="badge-tag red">AI Indicator (High)</span>'
        : '<span class="badge-tag green">Human Indicator (High)</span>';

      tr.innerHTML = `
        <td><strong>${f.display_name}</strong><br><small style="color:var(--text-dim)">${f.explanation}</small></td>
        <td><code>${f.value}</code></td>
        <td>${dirBadge}</td>
        <td><code>${f.weight_impact}</code></td>
      `;
      attributionsTableBody.appendChild(tr);
    });

    // Diagnostics List
    diagnosticsList.innerHTML = "";
    const diags = data.linguistic_diagnostics || [];
    if (diags.length === 0) {
      diagnosticsList.innerHTML = '<p class="section-hint">No structural anomalies or severe stylistic red flags detected.</p>';
    } else {
      diags.forEach((d) => {
        const item = document.createElement("div");
        item.className = "diagnostic-item";
        item.innerHTML = `
          <div class="diag-title">[${d.severity}] ${d.title}</div>
          <div class="diag-desc">${d.description}</div>
        `;
        diagnosticsList.appendChild(item);
      });
    }
  }

  // Export JSON
  btnExportJson.addEventListener("click", () => {
    if (!currentAnalysisData) return;
    const blob = new Blob([JSON.stringify(currentAnalysisData, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `aegistext_audit_${Date.now()}.json`;
    a.click();
    URL.revokeObjectURL(url);
  });

  // Print Report
  btnPrintReport.addEventListener("click", () => {
    window.print();
  });
});

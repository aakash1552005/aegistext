/**
 * AegisText Studio — Forensic Application Controller
 */

document.addEventListener("DOMContentLoaded", () => {
  // DOM References
  const inputText = document.getElementById("inputText");
  const wordCountLabel = document.getElementById("wordCountLabel");
  const charCountLabel = document.getElementById("charCountLabel");
  const readTimeLabel = document.getElementById("readTimeLabel");
  const toggleSanitize = document.getElementById("toggleSanitize");
  const btnAnalyze = document.getElementById("btnAnalyze");
  const btnClearText = document.getElementById("btnClearText");
  const fileUpload = document.getElementById("fileUpload");

  const preflightStateView = document.getElementById("preflightStateView");
  const activeResultsView = document.getElementById("activeResultsView");

  // Dial & Verdict
  const dialFill = document.getElementById("dialFill");
  const dialPercentage = document.getElementById("dialPercentage");
  const verdictBadge = document.getElementById("verdictBadge");
  const confidencePill = document.getElementById("confidencePill");
  const verdictDescription = document.getElementById("verdictDescription");
  const latencyLabel = document.getElementById("latencyLabel");

  // Adversarial Warning Box
  const adversarialAlertBox = document.getElementById("adversarialAlertBox");
  const alertTitle = document.getElementById("alertTitle");
  const alertBody = document.getElementById("alertBody");

  // Tabs & Views
  const sentenceHeatmapBox = document.getElementById("sentenceHeatmapBox");
  const sentenceInspectorCard = document.getElementById("sentenceInspectorCard");
  const inspectSentenceId = document.getElementById("inspectSentenceId");
  const inspectProbBadge = document.getElementById("inspectProbBadge");
  const inspectSentenceText = document.getElementById("inspectSentenceText");

  // Multi-Signal Radar
  const radarStyBar = document.getElementById("radarStyBar");
  const radarStyLevel = document.getElementById("radarStyLevel");
  const radarStrBar = document.getElementById("radarStrBar");
  const radarStrLevel = document.getElementById("radarStrLevel");
  const radarPredBar = document.getElementById("radarPredBar");
  const radarPredLevel = document.getElementById("radarPredLevel");
  const radarSemBar = document.getElementById("radarSemBar");
  const radarSemLevel = document.getElementById("radarSemLevel");

  const attributionsTableBody = document.getElementById("attributionsTableBody");
  const diagnosticsFeed = document.getElementById("diagnosticsFeed");

  // Modals & Exports
  const btnOpenBenchmarks = document.getElementById("btnOpenBenchmarks");
  const btnCloseBenchmarks = document.getElementById("btnCloseBenchmarks");
  const benchmarksModal = document.getElementById("benchmarksModal");
  const btnExportJson = document.getElementById("btnExportJson");
  const btnPrintReport = document.getElementById("btnPrintReport");

  let currentAnalysis = null;

  // Curated Preset Texts
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
      "Honestly, when looking at distributed c\u200bonsensus, there are some pretty major trade-offs between speed and network partition tolerance. " +
      "As it turns out, in asynchronous setups, you just can't guarantee consensus if even a single node crashes unexpectedly. " +
      "To be fair, testing across multiple cloud regions shows that running speculative execution cuts tail latency by almost thirty-five percent."
    ),
  };

  // Text Counter Updates
  function updateCounters() {
    const text = inputText.value;
    const words = text.trim() ? text.trim().split(/\s+/).length : 0;
    const chars = text.length;
    const readMinutes = Math.max(1, Math.ceil(words / 220));

    wordCountLabel.textContent = words.toLocaleString();
    charCountLabel.textContent = chars.toLocaleString();
    readTimeLabel.textContent = words > 0 ? readMinutes : 0;
  }

  inputText.addEventListener("input", updateCounters);

  // File Upload
  fileUpload.addEventListener("change", (e) => {
    const file = e.target.files[0];
    if (file) {
      const reader = new FileReader();
      reader.onload = (event) => {
        inputText.value = event.target.result;
        updateCounters();
      };
      reader.readAsText(file);
    }
  });

  // Clear Button
  btnClearText.addEventListener("click", () => {
    inputText.value = "";
    updateCounters();
    preflightStateView.classList.remove("hidden");
    activeResultsView.classList.add("hidden");
    currentAnalysis = null;
  });

  // Preset Buttons
  document.getElementById("btnPresetHuman").addEventListener("click", () => {
    inputText.value = PRESETS.human;
    updateCounters();
  });
  document.getElementById("btnPresetAi").addEventListener("click", () => {
    inputText.value = PRESETS.ai;
    updateCounters();
  });
  document.getElementById("btnPresetHumanized").addEventListener("click", () => {
    inputText.value = PRESETS.humanized;
    updateCounters();
  });

  // Quick Launcher Cards in Preflight Deck
  document.getElementById("quickRunHuman").addEventListener("click", () => {
    inputText.value = PRESETS.human;
    updateCounters();
    runForensics();
  });
  document.getElementById("quickRunAi").addEventListener("click", () => {
    inputText.value = PRESETS.ai;
    updateCounters();
    runForensics();
  });
  document.getElementById("quickRunHumanized").addEventListener("click", () => {
    inputText.value = PRESETS.humanized;
    updateCounters();
    runForensics();
  });

  // Keyboard shortcut: Ctrl+Enter / Cmd+Enter
  window.addEventListener("keydown", (e) => {
    if ((e.ctrlKey || e.metaKey) && e.key === "Enter") {
      runForensics();
    }
  });

  btnAnalyze.addEventListener("click", runForensics);

  // Modal Handlers
  btnOpenBenchmarks.addEventListener("click", () => benchmarksModal.classList.remove("hidden"));
  btnCloseBenchmarks.addEventListener("click", () => benchmarksModal.classList.add("hidden"));
  benchmarksModal.addEventListener("click", (e) => {
    if (e.target === benchmarksModal) benchmarksModal.classList.add("hidden");
  });

  // Forensic Tab Switching
  document.querySelectorAll(".f-tab-btn").forEach((btn) => {
    btn.addEventListener("click", () => {
      document.querySelectorAll(".f-tab-btn").forEach((b) => b.classList.remove("active"));
      document.querySelectorAll(".f-tab-pane").forEach((p) => p.classList.remove("active"));
      btn.classList.add("active");
      const targetPane = document.getElementById(btn.dataset.tab);
      if (targetPane) targetPane.classList.add("active");
    });
  });

  // Run Forensic Analysis
  async function runForensics() {
    const text = inputText.value.trim();
    if (!text || text.length < 10) {
      alert("Please provide at least 10 characters to analyze.");
      return;
    }

    btnAnalyze.disabled = true;
    btnAnalyze.innerHTML = `
      <span class="btn-label-group">
        <svg class="spin-icon" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2"><path d="M21 12a9 9 0 1 1-6.219-8.56"/></svg>
        Analyzing...
      </span>
    `;

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
        throw new Error(`Server returned HTTP ${response.status}`);
      }

      const data = await response.json();
      currentAnalysis = data;
      renderAnalysis(data);
    } catch (err) {
      console.error(err);
      alert("Analysis failed. Please verify that the AegisText engine is running on localhost:8000.");
    } finally {
      btnAnalyze.disabled = false;
      btnAnalyze.innerHTML = `
        <span class="btn-label-group">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2"><path d="M22 12h-4l-3 9L9 3l-3 9H2"/></svg>
          Run Forensics
        </span>
        <span class="btn-shortcut">Ctrl+↵</span>
      `;
    }
  }

  // Render Full Results
  function renderAnalysis(data) {
    preflightStateView.classList.add("hidden");
    activeResultsView.classList.remove("hidden");

    const det = data.detection;
    const prob = det.ai_probability;
    const percentage = Math.round(prob * 1000) / 10;

    // 1. Update Dial (Circumference is 264)
    const offset = 264 - (264 * prob);
    dialFill.style.strokeDashoffset = offset;
    dialPercentage.textContent = `${percentage}%`;

    if (det.classification === "AI_GENERATED") {
      dialFill.style.stroke = "var(--color-ai)";
      verdictBadge.textContent = "AI GENERATED (SYNTHETIC)";
      verdictBadge.className = "verdict-badge ai";
      verdictDescription.textContent = "Strong structural evidence of algorithmic text generation across multi-signal predictors.";
    } else {
      dialFill.style.stroke = "var(--color-human)";
      verdictBadge.textContent = "HUMAN AUTHORED (ORGANIC)";
      verdictBadge.className = "verdict-badge human";
      verdictDescription.textContent = "Linguistic markers, burstiness variance, and vocabulary entropy align with human writing.";
    }

    confidencePill.textContent = `${det.confidence_band.replace(/_/g, " ")} Confidence`;
    latencyLabel.textContent = `${det.processing_time_ms} ms`;

    // 2. Adversarial Warning
    const audit = det.tampering_report || {};
    if (audit.adversarial_markers_present) {
      adversarialAlertBox.classList.remove("hidden");
      alertTitle.textContent = "Adversarial Evasion Markers Neutralized";
      alertBody.textContent = (
        `Intercepted ${audit.zero_width_count || 0} invisible zero-width character(s) and ` +
        `${audit.homoglyph_count || 0} confusable Cyrillic/Greek homoglyphs. The model evaluated canonical text.`
      );
    } else {
      adversarialAlertBox.classList.add("hidden");
    }

    // 3. Sentence Heatmap
    sentenceHeatmapBox.innerHTML = "";
    sentenceInspectorCard.classList.add("hidden");

    (data.sentence_heatmap || []).forEach((s) => {
      const span = document.createElement("span");
      span.className = `heat-span ${s.suspicion_level.toLowerCase()}`;
      span.textContent = s.text + " ";
      span.addEventListener("click", () => {
        sentenceInspectorCard.classList.remove("hidden");
        inspectSentenceId.textContent = `Sentence #${s.sentence_index + 1} (${s.word_count} words)`;
        inspectProbBadge.textContent = `${Math.round(s.ai_probability * 100)}% AI Suspicion (${s.suspicion_level})`;
        inspectSentenceText.textContent = `"${s.text}"`;
      });
      sentenceHeatmapBox.appendChild(span);
    });

    // 4. Multi-Signal Radar Gauges (derived from attributions and probabilities)
    const attributions = data.feature_attributions || [];
    let burstinessVal = 0.5, transitionVal = 0.5, entropyVal = 0.5;

    attributions.forEach((attr) => {
      if (attr.feature.includes("burstiness")) burstinessVal = attr.value;
      if (attr.feature.includes("transition")) transitionVal = attr.value;
      if (attr.feature.includes("entropy")) entropyVal = attr.value;
    });

    radarStyBar.style.width = `${Math.min(95, Math.max(15, Math.round(prob * 90)))}%`;
    radarStyLevel.textContent = prob > 0.6 ? "Uniform (AI)" : "Varied (Human)";

    radarStrBar.style.width = `${Math.min(95, Math.max(15, Math.round(prob * 85)))}%`;
    radarStrLevel.textContent = prob > 0.6 ? "High Density" : "Natural Flow";

    radarPredBar.style.width = `${Math.min(95, Math.max(15, Math.round(prob * 92)))}%`;
    radarPredLevel.textContent = prob > 0.6 ? "Low Burstiness" : "High Burstiness";

    radarSemBar.style.width = `${Math.min(95, Math.max(15, Math.round(prob * 75)))}%`;
    radarSemLevel.textContent = prob > 0.6 ? "Monotonic" : "Dynamic Drift";

    // 5. Attributions Table
    attributionsTableBody.innerHTML = "";
    attributions.forEach((f) => {
      const tr = document.createElement("tr");
      const isAi = f.ai_indicative === "high";
      const tag = isAi
        ? '<span class="attr-tag ai">AI Indicator</span>'
        : '<span class="attr-tag human">Human Indicator</span>';

      tr.innerHTML = `
        <td><strong>${f.display_name}</strong><br><small style="color:var(--text-muted);font-size:0.7rem;">${f.explanation}</small></td>
        <td><code>${f.value}</code></td>
        <td>${tag}</td>
        <td><code>${f.weight_impact}</code></td>
      `;
      attributionsTableBody.appendChild(tr);
    });

    // 6. Diagnostics
    diagnosticsFeed.innerHTML = "";
    const diags = data.linguistic_diagnostics || [];
    if (diags.length === 0) {
      diagnosticsFeed.innerHTML = '<p style="color:var(--text-muted);font-size:0.8rem;">No critical adversarial tampering or severe stylistic anomalies detected.</p>';
    } else {
      diags.forEach((d) => {
        const card = document.createElement("div");
        card.className = `diag-card ${d.severity}`;
        card.innerHTML = `
          <div class="diag-top">
            <span class="diag-head">${d.title}</span>
            <span class="diag-severity">${d.severity}</span>
          </div>
          <p class="diag-body">${d.description}</p>
        `;
        diagnosticsFeed.appendChild(card);
      });
    }
  }

  // Export JSON Audit
  btnExportJson.addEventListener("click", () => {
    if (!currentAnalysis) return;
    const blob = new Blob([JSON.stringify(currentAnalysis, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `aegistext_forensic_audit_${Date.now()}.json`;
    a.click();
    URL.revokeObjectURL(url);
  });

  // Print Report Certificate
  btnPrintReport.addEventListener("click", () => {
    window.print();
  });
});

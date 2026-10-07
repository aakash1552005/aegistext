/**
 * AegisText — Document Intelligence & Authorship Analysis Controller
 * UI Reset & Design Freeze Edition: Clean, Modular, and Robust
 */

document.addEventListener("DOMContentLoaded", () => {
  // DOM Elements: Navigation
  const navTabs = document.querySelectorAll(".nav-tab");
  const pageViews = document.querySelectorAll(".page-view");

  // DOM Elements: Document Input
  const inputText = document.getElementById("inputText");
  const fileUpload = document.getElementById("fileUpload");
  const btnClearText = document.getElementById("btnClearText");
  const wordCountLabel = document.getElementById("wordCountLabel");
  const charCountLabel = document.getElementById("charCountLabel");
  const readTimeLabel = document.getElementById("readTimeLabel");
  const toggleSanitize = document.getElementById("toggleSanitize");
  const btnAnalyze = document.getElementById("btnAnalyze");
  const btnAnalyzeText = document.getElementById("btnAnalyzeText");

  // DOM Elements: Sample Presets
  const btnPresetHuman = document.getElementById("btnPresetHuman");
  const btnPresetAi = document.getElementById("btnPresetAi");
  const btnPresetHumanized = document.getElementById("btnPresetHumanized");

  // DOM Elements: Results
  const resultContainer = document.getElementById("resultContainer");
  const latencyTag = document.getElementById("latencyTag");
  const verdictTitle = document.getElementById("verdictTitle");
  const verdictDesc = document.getElementById("verdictDesc");
  const probNumber = document.getElementById("probNumber");
  const probProgressFill = document.getElementById("probProgressFill");
  const evidenceStrength = document.getElementById("evidenceStrength");
  const confidenceDetail = document.getElementById("confidenceDetail");

  const defenseNotice = document.getElementById("defenseNotice");
  const defenseNoticeText = document.getElementById("defenseNoticeText");

  // DOM Elements: Detailed Analysis
  const sentenceHeatmapBox = document.getElementById("sentenceHeatmapBox");
  const sentenceDetailBox = document.getElementById("sentenceDetailBox");
  const detailSentenceIndex = document.getElementById("detailSentenceIndex");
  const detailSentenceProb = document.getElementById("detailSentenceProb");
  const detailSentenceText = document.getElementById("detailSentenceText");

  const signalsTableBody = document.getElementById("signalsTableBody");
  const diagnosticsList = document.getElementById("diagnosticsList");

  // DOM Elements: Actions & History
  const btnExportJson = document.getElementById("btnExportJson");
  const btnPrintReport = document.getElementById("btnPrintReport");
  const historyTableBody = document.getElementById("historyTableBody");
  const btnClearHistory = document.getElementById("btnClearHistory");

  // App State
  let currentAnalysis = null;
  let sessionHistory = [];

  // Sample Documents
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

  // =========================================================================
  // 1. Navigation Switching
  // =========================================================================
  navTabs.forEach((tab) => {
    tab.addEventListener("click", () => {
      const targetId = tab.dataset.target;

      navTabs.forEach((t) => t.classList.remove("active"));
      pageViews.forEach((view) => view.classList.add("hidden"));

      tab.classList.add("active");
      const targetView = document.getElementById(targetId);
      if (targetView) {
        targetView.classList.remove("hidden");
      }
    });
  });

  // =========================================================================
  // 2. Document Metrics & Input Listeners
  // =========================================================================
  function updateDocumentMetrics() {
    const text = inputText.value;
    const words = text.trim() ? text.trim().split(/\s+/).length : 0;
    const chars = text.length;
    const readMinutes = Math.max(1, Math.ceil(words / 220));

    wordCountLabel.textContent = words.toLocaleString();
    charCountLabel.textContent = chars.toLocaleString();
    readTimeLabel.textContent = words > 0 ? readMinutes : 0;
  }

  inputText.addEventListener("input", updateDocumentMetrics);

  // File Upload
  fileUpload.addEventListener("change", (e) => {
    const file = e.target.files[0];
    if (file) {
      const reader = new FileReader();
      reader.onload = (event) => {
        inputText.value = event.target.result;
        updateDocumentMetrics();
      };
      reader.readAsText(file);
    }
  });

  // Clear Document
  btnClearText.addEventListener("click", () => {
    inputText.value = "";
    updateDocumentMetrics();
    resultContainer.classList.add("hidden");
    currentAnalysis = null;
  });

  // Preset Buttons
  btnPresetHuman.addEventListener("click", () => {
    inputText.value = PRESETS.human;
    updateDocumentMetrics();
  });

  btnPresetAi.addEventListener("click", () => {
    inputText.value = PRESETS.ai;
    updateDocumentMetrics();
  });

  btnPresetHumanized.addEventListener("click", () => {
    inputText.value = PRESETS.humanized;
    updateDocumentMetrics();
  });

  // Keyboard shortcut: Ctrl+Enter / Cmd+Enter
  window.addEventListener("keydown", (e) => {
    if ((e.ctrlKey || e.metaKey) && e.key === "Enter") {
      runAnalysis();
    }
  });

  btnAnalyze.addEventListener("click", runAnalysis);

  // =========================================================================
  // 3. Analysis Pipeline
  // =========================================================================
  async function runAnalysis() {
    const text = inputText.value.trim();
    if (!text || text.length < 10) {
      alert("Please provide at least 10 characters to analyze.");
      return;
    }

    btnAnalyze.disabled = true;
    btnAnalyzeText.textContent = "Analyzing Document...";

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
        throw new Error(`Inference engine returned HTTP ${response.status}`);
      }

      const data = await response.json();
      currentAnalysis = data;
      renderResults(data, text);
      addToHistory(data, text);
    } catch (err) {
      console.error(err);
      alert("Analysis failed. Please verify that the AegisText engine is running on localhost:8000.");
    } finally {
      btnAnalyze.disabled = false;
      btnAnalyzeText.textContent = "Analyze Document";
    }
  }

  // =========================================================================
  // 4. Render Simple Assessment with Progressive Disclosure
  // =========================================================================
  function renderResults(data, originalText) {
    resultContainer.classList.remove("hidden");

    const det = data.detection;
    const prob = det.ai_probability;
    const percentage = Math.round(prob * 100);

    latencyTag.textContent = `${det.processing_time_ms} ms`;
    probNumber.textContent = `${percentage}%`;
    probProgressFill.style.width = `${percentage}%`;

    // High Level Verdict
    if (det.classification === "AI_GENERATED") {
      verdictTitle.textContent = "AI-Generated Likely";
      verdictTitle.className = "verdict-title ai";
      verdictDesc.textContent = "Linguistic and discourse markers indicate synthetic text generation.";
      probProgressFill.className = "progress-bar-fill ai";
    } else {
      verdictTitle.textContent = "Human-Authored Likely";
      verdictTitle.className = "verdict-title human";
      verdictDesc.textContent = "Vocabulary entropy and burstiness patterns align with human authorship.";
      probProgressFill.className = "progress-bar-fill human";
    }

    // Evidence Strength
    if (prob >= 0.85 || prob <= 0.15) {
      evidenceStrength.textContent = "Strong";
    } else if (prob >= 0.65 || prob <= 0.35) {
      evidenceStrength.textContent = "Moderate";
    } else {
      evidenceStrength.textContent = "Inconclusive";
    }

    confidenceDetail.textContent = `Calibrated confidence: ${det.confidence_band.replace(/_/g, " ")}`;

    // Adversarial Defense Warning
    const audit = det.tampering_report || {};
    if (audit.adversarial_markers_present) {
      defenseNotice.classList.remove("hidden");
      defenseNoticeText.textContent = (
        `Found ${audit.zero_width_count || 0} invisible unicode character(s) and ` +
        `${audit.homoglyph_count || 0} confusable homoglyph(s). Normalized before evaluation.`
      );
    } else {
      defenseNotice.classList.add("hidden");
    }

    // 4A. Sentence Heatmap
    sentenceHeatmapBox.innerHTML = "";
    sentenceDetailBox.classList.add("hidden");

    (data.sentence_heatmap || []).forEach((s) => {
      const span = document.createElement("span");
      span.className = `heat-span ${s.suspicion_level.toLowerCase()}`;
      span.textContent = s.text + " ";
      span.title = `Suspicion: ${s.suspicion_level} (${Math.round(s.ai_probability * 100)}%)`;

      span.addEventListener("click", () => {
        sentenceDetailBox.classList.remove("hidden");
        detailSentenceIndex.textContent = `Sentence #${s.sentence_index + 1} (${s.word_count} words)`;
        detailSentenceProb.textContent = `${Math.round(s.ai_probability * 100)}% AI Suspicion (${s.suspicion_level})`;
        detailSentenceText.textContent = `"${s.text}"`;
      });

      sentenceHeatmapBox.appendChild(span);
    });

    // 4B. Signals Table
    signalsTableBody.innerHTML = "";
    (data.feature_attributions || []).forEach((f) => {
      const tr = document.createElement("tr");
      const isAi = f.ai_indicative === "high";
      const tag = isAi
        ? '<span class="badge-tag ai">AI Indicator</span>'
        : '<span class="badge-tag human">Human Indicator</span>';

      tr.innerHTML = `
        <td><strong>${escapeHtml(f.display_name)}</strong><br><small style="color:var(--text-muted);">${escapeHtml(f.explanation)}</small></td>
        <td><code>${f.value}</code></td>
        <td>${tag}</td>
        <td><code>${f.weight_impact}</code></td>
      `;
      signalsTableBody.appendChild(tr);
    });

    // 4C. Technical Diagnostics
    diagnosticsList.innerHTML = "";
    const diags = data.linguistic_diagnostics || [];
    if (diags.length === 0) {
      diagnosticsList.innerHTML = '<p class="sub-instruction">No anomalous structural or adversarial markers detected.</p>';
    } else {
      diags.forEach((d) => {
        const item = document.createElement("div");
        item.className = `diag-item ${d.severity.toLowerCase()}`;
        item.innerHTML = `
          <div class="diag-header">
            <span>${escapeHtml(d.title)}</span>
            <span class="badge-tag">${escapeHtml(d.severity)}</span>
          </div>
          <p class="diag-body">${escapeHtml(d.description)}</p>
        `;
        diagnosticsList.appendChild(item);
      });
    }

    // Scroll smoothly to results
    resultContainer.scrollIntoView({ behavior: "smooth", block: "start" });
  }

  // =========================================================================
  // 5. Session History
  // =========================================================================
  function addToHistory(data, text) {
    const snippet = text.slice(0, 75).trim() + (text.length > 75 ? "..." : "");
    const words = text.trim().split(/\s+/).length;
    const timestamp = new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", second: "2-digit" });

    sessionHistory.unshift({
      timestamp,
      snippet,
      words,
      text,
      data,
      classification: data.detection.classification,
      probability: Math.round(data.detection.ai_probability * 100),
    });

    renderHistory();
  }

  function renderHistory() {
    if (sessionHistory.length === 0) {
      historyTableBody.innerHTML = `
        <tr>
          <td colspan="6" class="empty-cell">No documents analyzed yet in this session.</td>
        </tr>
      `;
      return;
    }

    historyTableBody.innerHTML = "";
    sessionHistory.forEach((item, index) => {
      const tr = document.createElement("tr");
      const isAi = item.classification === "AI_GENERATED";
      const badge = isAi
        ? '<span class="badge-tag ai">AI Likely</span>'
        : '<span class="badge-tag human">Human Likely</span>';

      tr.innerHTML = `
        <td><small style="color:var(--text-muted);">${item.timestamp}</small></td>
        <td>${escapeHtml(item.snippet)}</td>
        <td>${item.words.toLocaleString()}</td>
        <td>${badge}</td>
        <td><strong>${item.probability}%</strong></td>
        <td><button class="btn-secondary btn-reload-hist" data-index="${index}">View</button></td>
      `;
      historyTableBody.appendChild(tr);
    });

    document.querySelectorAll(".btn-reload-hist").forEach((btn) => {
      btn.addEventListener("click", () => {
        const item = sessionHistory[btn.dataset.index];
        if (item) {
          inputText.value = item.text;
          updateDocumentMetrics();
          renderResults(item.data, item.text);
          // Switch to analyze view
          document.querySelector('[data-target="viewAnalyze"]').click();
        }
      });
    });
  }

  btnClearHistory.addEventListener("click", () => {
    sessionHistory = [];
    renderHistory();
  });

  // =========================================================================
  // 6. Export & Print
  // =========================================================================
  btnExportJson.addEventListener("click", () => {
    if (!currentAnalysis) return;
    const blob = new Blob([JSON.stringify(currentAnalysis, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `aegistext_analysis_${Date.now()}.json`;
    a.click();
    URL.revokeObjectURL(url);
  });

  btnPrintReport.addEventListener("click", () => {
    window.print();
  });

  function escapeHtml(str) {
    if (!str) return "";
    return str
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#039;");
  }
});

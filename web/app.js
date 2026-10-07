/**
 * AegisText — Document Intelligence & Authorship Analysis
 * Controller for the Figma-Matched Landing Page
 */

document.addEventListener("DOMContentLoaded", () => {
  // Navigation: Sidebar
  const navNewAnalysis = document.getElementById("navNewAnalysis");
  const navLibrary = document.getElementById("navLibrary");
  const navOrganization = document.getElementById("navOrganization");
  const workspacePages = document.querySelectorAll(".workspace-page");

  // Document Tabs
  const tabUpload = document.getElementById("tabUpload");
  const tabPaste = document.getElementById("tabPaste");

  // Dropzone Elements
  const dropzoneArea = document.getElementById("dropzoneArea");
  const fileInput = document.getElementById("fileInput");
  const btnChooseFile = document.getElementById("btnChooseFile");

  // Excerpt Textarea Elements
  const excerptTextarea = document.getElementById("excerptTextarea");
  const wordCountNotice = document.getElementById("wordCountNotice");
  const btnReviewText = document.getElementById("btnReviewText");

  // Preset Sample Links
  const presetAcademic = document.getElementById("presetAcademic");
  const presetSynthetic = document.getElementById("presetSynthetic");
  const presetHumanized = document.getElementById("presetHumanized");

  // Modal: Review & Assessment
  const analysisModal = document.getElementById("analysisModal");
  const btnCloseAnalysis = document.getElementById("btnCloseAnalysis");
  const btnCloseReview = document.getElementById("btnCloseReview");

  // Modal Assessment Elements
  const reviewDocTitle = document.getElementById("reviewDocTitle");
  const assessmentState = document.getElementById("assessmentState");
  const assessmentExplanation = document.getElementById("assessmentExplanation");
  const assessmentProb = document.getElementById("assessmentProb");
  const assessmentProbFill = document.getElementById("assessmentProbFill");
  const assessmentConfidence = document.getElementById("assessmentConfidence");
  const assessmentLatency = document.getElementById("assessmentLatency");

  const adversarialNotice = document.getElementById("adversarialNotice");
  const adversarialNoticeText = document.getElementById("adversarialNoticeText");

  const sentencesProseBox = document.getElementById("sentencesProseBox");
  const selectedSentenceBox = document.getElementById("selectedSentenceBox");
  const selSentenceId = document.getElementById("selSentenceId");
  const selSentenceScore = document.getElementById("selSentenceScore");
  const selSentenceText = document.getElementById("selSentenceText");

  const signalsTableBody = document.getElementById("signalsTableBody");
  const libraryTableBody = document.getElementById("libraryTableBody");

  // Actions: Export & Print
  const btnExportJson = document.getElementById("btnExportJson");
  const btnPrintReport = document.getElementById("btnPrintReport");
  const toggleShield = document.getElementById("toggleShield");

  // State
  let currentAnalysis = null;
  let sessionAnalyses = [];

  // Curated Preset Texts
  const PRESETS = {
    academic: (
      "Recent investigations into distributed consensus algorithms reveal fundamental " +
      "trade-offs between latency and partition tolerance. In asynchronous networks, deterministic " +
      "consensus cannot be guaranteed in the presence of even a single unannounced crash failure. " +
      "Empirical benchmarks across geo-distributed nodes demonstrate that speculative execution mitigates " +
      "tail latency by up to thirty-four percent without violating linearizability guarantees. " +
      "We formalize these empirical boundaries within an asynchronous state-machine replication model, " +
      "evaluating worst-case Byzantine fault configurations under high packet-drop regimes."
    ),
    synthetic: (
      "In conclusion, distributed consensus mechanisms represent a pivotal foundation of modern decentralized architecture. " +
      "Furthermore, it is crucial to recognize that latency and fault tolerance must be carefully balanced to achieve optimal throughput. " +
      "Moreover, empirical evaluations clearly demonstrate that speculative execution plays an essential role in improving overall " +
      "system reliability and cryptographic security in contemporary digital ecosystems. " +
      "Consequently, architects must adopt a holistic framework to navigate complex trade-offs across asynchronous cloud clusters."
    ),
    humanized: (
      "Honestly, when looking at distributed c\u200bonsensus, there are some pretty major trade-offs between speed and network partition tolerance. " +
      "As it turns out, in asynchronous setups, you just can't guarantee consensus if even a single node crashes unexpectedly. " +
      "To be fair, testing across multiple cloud regions shows that running speculative execution cuts tail latency by almost thirty-five percent " +
      "without messing with linearizability guarantees."
    ),
  };

  // =========================================================================
  // 1. Sidebar Page Switching
  // =========================================================================
  function switchPage(pageId, activeBtn) {
    workspacePages.forEach((p) => p.classList.add("hidden"));
    [navNewAnalysis, navLibrary, navOrganization].forEach((b) => b.classList.remove("active"));

    const targetPage = document.getElementById(pageId);
    if (targetPage) targetPage.classList.remove("hidden");
    if (activeBtn) activeBtn.classList.add("active");
  }

  navNewAnalysis.addEventListener("click", () => switchPage("viewNewAnalysis", navNewAnalysis));
  navLibrary.addEventListener("click", () => {
    switchPage("viewLibrary", navLibrary);
    renderLibrary();
  });
  navOrganization.addEventListener("click", () => switchPage("viewOrganization", navOrganization));

  // =========================================================================
  // 2. Tabs: Upload Document vs Paste Text
  // =========================================================================
  tabUpload.addEventListener("click", () => {
    tabUpload.classList.add("active");
    tabPaste.classList.remove("active");
  });

  tabPaste.addEventListener("click", () => {
    tabPaste.classList.add("active");
    tabUpload.classList.remove("active");
    excerptTextarea.focus();
  });

  // =========================================================================
  // 3. Excerpt Word Counter
  // =========================================================================
  function updateExcerptStats() {
    const text = excerptTextarea.value.trim();
    const words = text ? text.split(/\s+/).length : 0;
    wordCountNotice.textContent = `${words} words · Minimum 150 words`;
  }

  excerptTextarea.addEventListener("input", updateExcerptStats);

  // Preset Loaders
  presetAcademic.addEventListener("click", () => {
    excerptTextarea.value = PRESETS.academic;
    updateExcerptStats();
  });

  presetSynthetic.addEventListener("click", () => {
    excerptTextarea.value = PRESETS.synthetic;
    updateExcerptStats();
  });

  presetHumanized.addEventListener("click", () => {
    excerptTextarea.value = PRESETS.humanized;
    updateExcerptStats();
  });

  // =========================================================================
  // 4. File Dropzone & Selection
  // =========================================================================
  btnChooseFile.addEventListener("click", () => fileInput.click());

  fileInput.addEventListener("change", (e) => {
    const file = e.target.files[0];
    if (file) handleFile(file);
  });

  dropzoneArea.addEventListener("dragover", (e) => {
    e.preventDefault();
    dropzoneArea.classList.add("dragover");
  });

  dropzoneArea.addEventListener("dragleave", () => {
    dropzoneArea.classList.remove("dragover");
  });

  dropzoneArea.addEventListener("drop", (e) => {
    e.preventDefault();
    dropzoneArea.classList.remove("dragover");
    const file = e.dataTransfer.files[0];
    if (file) handleFile(file);
  });

  function handleFile(file) {
    const reader = new FileReader();
    reader.onload = (event) => {
      const content = event.target.result;
      excerptTextarea.value = content;
      updateExcerptStats();
      analyzeText(content, file.name);
    };
    reader.readAsText(file);
  }

  // =========================================================================
  // 5. Review Text & ML Analysis Pipeline
  // =========================================================================
  btnReviewText.addEventListener("click", () => {
    const text = excerptTextarea.value.trim();
    if (!text || text.length < 10) {
      alert("Please provide at least 10 characters to evaluate.");
      return;
    }
    analyzeText(text, "Document Excerpt");
  });

  async function analyzeText(text, docTitle = "Document Review") {
    btnReviewText.disabled = true;
    btnReviewText.textContent = "Analyzing...";

    try {
      const response = await fetch("/api/v1/explain", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          text: text,
          sanitize_adversarial: toggleShield ? toggleShield.checked : true,
        }),
      });

      if (!response.ok) {
        throw new Error(`Inference engine returned HTTP ${response.status}`);
      }

      const data = await response.json();
      currentAnalysis = data;
      renderAnalysisModal(data, docTitle, text);
      recordAnalysis(data, docTitle, text);
    } catch (err) {
      console.error(err);
      alert("Inference request failed. Please ensure the AegisText engine is running on localhost:8000.");
    } finally {
      btnReviewText.disabled = false;
      btnReviewText.textContent = "Review text";
    }
  }

  // =========================================================================
  // 6. Render Modal Assessment (Considered Review)
  // =========================================================================
  function renderAnalysisModal(data, title, fullText) {
    reviewDocTitle.textContent = title;
    const det = data.detection;
    const prob = det.ai_probability;
    const percentage = Math.round(prob * 100);

    // 1. Overall Assessment
    assessmentProb.textContent = `${percentage}%`;
    assessmentProbFill.style.width = `${percentage}%`;
    assessmentLatency.textContent = `Latency: ${det.processing_time_ms} ms`;

    if (det.classification === "AI_GENERATED") {
      assessmentState.textContent = "AI-Generated Likely";
      assessmentState.className = "verdict-state ai";
      assessmentProbFill.className = "stat-fill ai";
      assessmentExplanation.textContent = (
        "Linguistic markers, transition predictability, and vocabulary entropy patterns are consistent with synthetic generation."
      );
    } else {
      assessmentState.textContent = "Human-Authored Likely";
      assessmentState.className = "verdict-state human";
      assessmentProbFill.className = "stat-fill human";
      assessmentExplanation.textContent = (
        "Burstiness variance, lexical diversity, and transition entropy align closely with organic human composition."
      );
    }

    assessmentConfidence.textContent = `${det.confidence_band.replace(/_/g, " ")} Confidence`;

    // 2. Adversarial Tampering Alert
    const audit = det.tampering_report || {};
    if (audit.adversarial_markers_present) {
      adversarialNotice.classList.remove("hidden");
      adversarialNoticeText.textContent = (
        `Found ${audit.zero_width_count || 0} invisible zero-width unicode character(s) and ` +
        `${audit.homoglyph_count || 0} confusable homoglyph(s). Text was normalized prior to analysis.`
      );
    } else {
      adversarialNotice.classList.add("hidden");
    }

    // 3. Sentences Heatmap
    sentencesProseBox.innerHTML = "";
    selectedSentenceBox.classList.add("hidden");

    (data.sentence_heatmap || []).forEach((s) => {
      const span = document.createElement("span");
      span.className = `heat-span ${s.suspicion_level.toLowerCase()}`;
      span.textContent = s.text + " ";
      span.title = `Passage: ${s.suspicion_level} (${Math.round(s.ai_probability * 100)}% AI likelihood)`;

      span.addEventListener("click", () => {
        selectedSentenceBox.classList.remove("hidden");
        selSentenceId.textContent = `Sentence #${s.sentence_index + 1} (${s.word_count} words)`;
        selSentenceScore.textContent = `${Math.round(s.ai_probability * 100)}% AI Suspicion (${s.suspicion_level})`;
        selSentenceText.textContent = `"${s.text}"`;
      });

      sentencesProseBox.appendChild(span);
    });

    // 4. Signals Table
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

    // Show Modal
    analysisModal.classList.remove("hidden");
  }

  // Close Modal Handlers
  btnCloseAnalysis.addEventListener("click", () => analysisModal.classList.add("hidden"));
  btnCloseReview.addEventListener("click", () => analysisModal.classList.add("hidden"));
  analysisModal.addEventListener("click", (e) => {
    if (e.target === analysisModal) analysisModal.classList.add("hidden");
  });

  // =========================================================================
  // 7. Library Archive
  // =========================================================================
  function recordAnalysis(data, title, text) {
    const snippet = text.slice(0, 80).trim() + (text.length > 80 ? "..." : "");
    const words = text.trim().split(/\s+/).length;
    const time = new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });

    sessionAnalyses.unshift({
      time,
      title,
      snippet,
      words,
      text,
      data,
      classification: data.detection.classification,
      probability: Math.round(data.detection.ai_probability * 100),
    });
  }

  function renderLibrary() {
    if (sessionAnalyses.length === 0) {
      libraryTableBody.innerHTML = `
        <tr><td colspan="6" class="empty-state-cell">No documents evaluated in this session yet.</td></tr>
      `;
      return;
    }

    libraryTableBody.innerHTML = "";
    sessionAnalyses.forEach((item, index) => {
      const tr = document.createElement("tr");
      const isAi = item.classification === "AI_GENERATED";
      const badge = isAi
        ? '<span class="badge-tag ai">AI Likely</span>'
        : '<span class="badge-tag human">Human Likely</span>';

      tr.innerHTML = `
        <td><small style="color:var(--text-muted);">${item.time}</small></td>
        <td><strong>${escapeHtml(item.title)}</strong><br><small style="color:var(--text-muted);">${escapeHtml(item.snippet)}</small></td>
        <td>${item.words.toLocaleString()}</td>
        <td>${badge}</td>
        <td><strong>${item.probability}%</strong></td>
        <td><button class="btn-action-ghost btn-lib-view" data-index="${index}">Open Review</button></td>
      `;
      libraryTableBody.appendChild(tr);
    });

    document.querySelectorAll(".btn-lib-view").forEach((btn) => {
      btn.addEventListener("click", () => {
        const item = sessionAnalyses[btn.dataset.index];
        if (item) {
          renderAnalysisModal(item.data, item.title, item.text);
        }
      });
    });
  }

  // =========================================================================
  // 8. Export & Print
  // =========================================================================
  btnExportJson.addEventListener("click", () => {
    if (!currentAnalysis) return;
    const blob = new Blob([JSON.stringify(currentAnalysis, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `aegistext_assessment_${Date.now()}.json`;
    a.click();
    URL.revokeObjectURL(url);
  });

  btnPrintReport.addEventListener("click", () => window.print());

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

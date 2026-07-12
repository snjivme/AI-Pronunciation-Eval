const audioInput = document.getElementById("audioFile");
const audioPlayer = document.getElementById("audioPlayer");

const fileName = document.getElementById("fileName");
const fileSize = document.getElementById("fileSize");
const fileDuration = document.getElementById("fileDuration");

const analyzeBtn = document.getElementById("analyzeBtn");

const loading = document.getElementById("loading");
const results = document.getElementById("results");

// Stop Analysis Elements
const stopAnalyzeBtn = document.getElementById("stopAnalyzeBtn");

// Privacy Policy Modal Elements
const privacyModal = document.getElementById("privacyModal");
const privacyPolicyLink = document.getElementById("privacyPolicyLink");
const closePrivacyModal = document.getElementById("closePrivacyModal");
const acceptPrivacyBtn = document.getElementById("acceptPrivacyBtn");
const consentCheckbox = document.getElementById("dpdpConsent");

// Deletion Button Elements
const deleteDataBtn = document.getElementById("deleteDataBtn");

let lastReportFilename = "";
let currentAnalysisController = null;

const BACKEND_URL = window.location.hostname === "localhost" || window.location.hostname === "127.0.0.1" || window.location.protocol === "file:"
  ? "http://127.0.0.1:8000"
  : "https://pronunciation-ai.onrender.com";

analyzeBtn.disabled = true;

// --------------------
// Full-Screen Loading Helpers
// --------------------

function showLoading() {
  loading.style.display = "flex";
  document.body.classList.add("no-scroll");
}

function hideLoading() {
  loading.style.display = "none";
  document.body.classList.remove("no-scroll");
}

// --------------------
// Privacy Modal Events
// --------------------

privacyPolicyLink.addEventListener("click", function (e) {
  e.preventDefault();
  privacyModal.style.display = "block";
});

closePrivacyModal.addEventListener("click", function () {
  privacyModal.style.display = "none";
});

acceptPrivacyBtn.addEventListener("click", function () {
  consentCheckbox.checked = true;
  privacyModal.style.display = "none";
});

window.addEventListener("click", function (e) {
  if (e.target === privacyModal) {
    privacyModal.style.display = "none";
  }
});

// --------------------
// File Selection
// --------------------

audioInput.addEventListener("change", function () {
  const file = this.files[0];

  if (!file) return;

  fileName.textContent = file.name;

  fileSize.textContent =
    "Size : " + (file.size / (1024 * 1024)).toFixed(2) + " MB";

  const url = URL.createObjectURL(file);

  audioPlayer.src = url;

  const audio = new Audio(url);

  audio.addEventListener("loadedmetadata", () => {
    const duration = Math.floor(audio.duration);

    fileDuration.textContent = "Duration : " + duration + " seconds";

    if (duration < 30 || duration > 45) {
      alert("Audio duration must be between 30 and 45 seconds.");
      analyzeBtn.disabled = true;
      return;
    }

    analyzeBtn.disabled = false;
  });
});

// --------------------
// Text Highlighting Function
// --------------------

function highlightTranscript(transcriptText, mispronouncedWords) {
  if (!mispronouncedWords || mispronouncedWords.length === 0) {
    return transcriptText;
  }

  // Map of lowercased mispronounced words for easy lookup (removing punctuation)
  const mistakesMap = {};
  mispronouncedWords.forEach(item => {
    const cleanKey = item.word.toLowerCase().replace(/[.,\/#!$%\^&\*;:{}=\-_`~()?"']/g, "").trim();
    if (cleanKey) {
      mistakesMap[cleanKey] = item;
    }
  });

  // Split transcript by whitespace to process token by token
  const tokens = transcriptText.split(/(\s+)/);
  const processedTokens = tokens.map(token => {
    if (token.trim() === "") {
      return token; // whitespace
    }

    // Clean word for key lookup
    const cleanWord = token.toLowerCase().replace(/[.,\/#!$%\^&\*;:{}=\-_`~()?"']/g, "").trim();

    if (mistakesMap[cleanWord]) {
      const item = mistakesMap[cleanWord];
      // Keep punctuation outside the highlighted word tag
      const match = token.match(/^(['"\s]*)(.*?)(['"\s.,\/#!$%\^&\*;:{}=\-_`~()?]*)$/);
      if (match) {
        const before = match[1];
        const wordPart = match[2];
        const after = match[3];

        return `${before}<span class="mispronounced-word">
          ${wordPart}
          <span class="pron-tooltip">
            <span class="tooltip-header">
              <span>${wordPart}</span>
              <span class="tooltip-severity ${item.severity}">${item.severity}</span>
            </span>
            <div class="tooltip-body">${item.issue}</div>
            <div class="tooltip-tip">💡 ${item.tip}</div>
          </span>
        </span>${after}`;
      }
    }
    return token;
  });

  return processedTokens.join("");
}

// --------------------
// Score Ring Helper
// --------------------

function setScoreRing(score) {
  const scoreCircle = document.querySelector(".score-circle");
  const clamped = Math.max(0, Math.min(100, Number(score) || 0));
  if (scoreCircle) {
    scoreCircle.style.setProperty("--score", clamped);
  }
}

// --------------------
// Upload & Analyze
// --------------------

analyzeBtn.addEventListener("click", async () => {
  // DPDP Consent Check
  if (!consentCheckbox.checked) {
    alert("Under India's Digital Personal Data Protection Act 2023, we require your explicit consent to process your voice recording. Please review the Privacy Notice and check the consent box.");
    return;
  }

  const file = audioInput.files[0];

  if (!file) {
    alert("Please select an audio file.");
    return;
  }

  const formData = new FormData();
  formData.append("file", file);

  currentAnalysisController = new AbortController();

  showLoading();
  results.style.display = "none";
  analyzeBtn.disabled = true;

  try {
    const response = await fetch(
      `${BACKEND_URL}/upload-audio`,
      {
        method: "POST",
        body: formData,
        signal: currentAnalysisController.signal,
      },
    );
    const data = await response.json();

    hideLoading();
    analyzeBtn.disabled = false;

    if (!response.ok) {
      alert(data.detail || "Something went wrong.");
      return;
    }

    results.style.display = "grid";

    // Extract filename for potential deletion
    if (data.pdf_download_url) {
      const urlParts = data.pdf_download_url.split("/");
      lastReportFilename = urlParts[urlParts.length - 1];
    }

    // --------------------
    // Score
    // --------------------
    document.getElementById("score").textContent = data.evaluation.overall_score;
    setScoreRing(data.evaluation.overall_score);

    // --------------------
    // Transcript with Highlights
    // --------------------
    const highlightedHtml = highlightTranscript(data.transcript, data.evaluation.mispronounced_words);
    document.getElementById("transcript").innerHTML = highlightedHtml;

    document.getElementById("correctedTranscript").textContent = data.corrected_transcript;

    // --------------------
    // Detailed Scores
    // --------------------
    document.getElementById("pronunciationScore").textContent = data.evaluation.pronunciation_score;
    document.getElementById("fluencyScore").textContent = data.evaluation.fluency_score;
    document.getElementById("clarityScore").textContent = data.evaluation.clarity_score;
    document.getElementById("pace").textContent = data.evaluation.pace;

    // --------------------
    // Mistakes List
    // --------------------
    const mistakes = document.getElementById("mistakes");
    mistakes.innerHTML = "";

    if (data.evaluation.mispronounced_words.length === 0) {
      mistakes.innerHTML = "<li>No pronunciation mistakes detected.</li>";
    } else {
      data.evaluation.mispronounced_words.forEach((item) => {
        mistakes.innerHTML += `
          <li>
            <strong>${item.word}</strong><br>
            <b>Severity:</b> <span class="tooltip-severity ${item.severity}" style="display:inline-block; font-size:0.75rem; padding:1px 5px;">${item.severity}</span><br>
            <b>Issue:</b> ${item.issue}<br>
            <b>Tip:</b> ${item.tip}
          </li>
        `;
      });
    }

    // --------------------
    // Strengths
    // --------------------
    const strengths = document.getElementById("strengths");
    strengths.innerHTML = "";
    data.evaluation.strengths.forEach((item) => {
      strengths.innerHTML += `<li>${item}</li>`;
    });

    // --------------------
    // Suggestions
    // --------------------
    const suggestions = document.getElementById("suggestions");
    suggestions.innerHTML = "";
    data.evaluation.suggestions.forEach((item) => {
      suggestions.innerHTML += `<li>${item}</li>`;
    });

    // --------------------
    // Overall Feedback
    // --------------------
    document.getElementById("overallFeedback").textContent = data.evaluation.overall_feedback;

    // --------------------
    // PDF Download
    // --------------------
    document.getElementById("downloadPdf").href = data.pdf_download_url;

  } catch (error) {
    hideLoading();
    analyzeBtn.disabled = false;

    if (error.name === "AbortError") {
      // User intentionally stopped the analysis; no error alert needed.
      console.log("Analysis stopped by user.");
    } else {
      alert("Unable to connect to backend.");
      console.error(error);
    }
  } finally {
    currentAnalysisController = null;
  }
});

// --------------------
// Stop Analysis
// --------------------

stopAnalyzeBtn.addEventListener("click", () => {
  if (currentAnalysisController) {
    currentAnalysisController.abort();
  }
});

// --------------------
// Data Deletion (DPDP Erasure Request)
// --------------------

deleteDataBtn.addEventListener("click", async () => {
  if (!lastReportFilename) {
    alert("No report found to delete.");
    return;
  }

  const confirmDelete = confirm("Are you sure you want to withdraw consent and delete all your assessment data from the server? This action is irreversible.");
  if (!confirmDelete) return;

  try {
    deleteDataBtn.disabled = true;
    deleteDataBtn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Deleting...';

    const response = await fetch(
      `${BACKEND_URL}/delete-report/${lastReportFilename}`,
      {
        method: "DELETE"
      }
    );

    if (response.ok) {
      alert("Your voice report data has been successfully deleted from the server in compliance with India's DPDP Act 2023.");

      // Reset UI state
      results.style.display = "none";
      audioInput.value = "";
      fileName.textContent = "No file selected";
      fileSize.textContent = "";
      fileDuration.textContent = "";
      audioPlayer.src = "";
      analyzeBtn.disabled = true;
      consentCheckbox.checked = false;
      lastReportFilename = "";
    } else {
      const errData = await response.json();
      alert(`Error deleting data: ${errData.detail || "Unknown error"}`);
    }
  } catch (error) {
    console.error(error);
    alert("Failed to connect to backend to request data deletion.");
  } finally {
    deleteDataBtn.disabled = false;
    deleteDataBtn.innerHTML = '<i class="fa-solid fa-trash-can"></i> Delete All My Data';
  }
});
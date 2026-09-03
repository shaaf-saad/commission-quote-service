const form = document.getElementById("quote-form");
const submitBtn = document.getElementById("submit-btn");
const formError = document.getElementById("form-error");
const idle = document.getElementById("result-idle");
const loading = document.getElementById("result-loading");
const errorBox = document.getElementById("result-error");
const success = document.getElementById("result-success");

function setState(name) {
  idle.hidden = name !== "idle";
  loading.hidden = name !== "loading";
  errorBox.hidden = name !== "error";
  success.hidden = name !== "success";
}

function showFormError(message) {
  formError.hidden = !message;
  formError.textContent = message || "";
}

function formatMoney(value) {
  return new Intl.NumberFormat("en-AU", {
    style: "currency",
    currency: "AUD",
  }).format(Number(value));
}

function formatRate(value) {
  return `${(Number(value) * 100).toFixed(2)}%`;
}

function validate(payload) {
  if (!Number.isFinite(payload.loanAmount) || payload.loanAmount <= 0) {
    return "Loan amount must be a number greater than 0.";
  }
  if (payload.loanAmount > 10_000_000) {
    return "Loan amount cannot exceed 10,000,000.";
  }
  if (!Number.isInteger(payload.loanTermInMonths) || payload.loanTermInMonths < 1) {
    return "Loan term must be a whole number of months (1–360).";
  }
  if (payload.loanTermInMonths > 360) {
    return "Loan term cannot exceed 360 months.";
  }
  if (!payload.riskBand) {
    return "Please select a risk band.";
  }
  return null;
}

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  showFormError("");

  const payload = {
    loanAmount: Number(form.loanAmount.value),
    loanTermInMonths: Number(form.loanTermInMonths.value),
    riskBand: form.riskBand.value,
  };

  const clientError = validate(payload);
  if (clientError) {
    showFormError(clientError);
    return;
  }

  submitBtn.disabled = true;
  setState("loading");

  try {
    const response = await fetch("/api/quotes", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });

    const data = await response.json().catch(() => ({}));
    if (!response.ok) {
      const detail = Array.isArray(data.detail)
        ? data.detail.map((item) => item.msg || JSON.stringify(item)).join(" ")
        : data.detail || "Quote generation failed.";
      errorBox.textContent = detail;
      setState("error");
      return;
    }

    document.getElementById("out-quoteId").textContent = data.quoteId;
    document.getElementById("out-commissionRate").textContent = formatRate(data.commissionRate);
    document.getElementById("out-totalCommission").textContent = formatMoney(data.totalCommission);
    document.getElementById("out-loanSummary").textContent =
      `${formatMoney(data.loanAmount)} · ${data.loanTermInMonths} months · band ${data.riskBand}`;
    setState("success");
  } catch {
    errorBox.textContent = "Could not reach the application server. Please try again.";
    setState("error");
  } finally {
    submitBtn.disabled = false;
  }
});

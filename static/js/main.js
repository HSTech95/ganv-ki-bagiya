/**
 * Ganv Ki Bagiya — Frontend Scripts
 */

document.addEventListener("DOMContentLoaded", function () {
  // 1. Amount selection buttons on Donate page
  const presetButtons = document.querySelectorAll(".donation-preset-btn");
  const amountInput = document.querySelector("#id_amount");

  if (presetButtons.length > 0 && amountInput) {
    // If input already has a preset value (e.g. from URL ?amount=...), highlight matching button
    if (amountInput.value) {
      presetButtons.forEach((btn) => {
        if (btn.getAttribute("data-amount") === String(parseInt(amountInput.value, 10))) {
          btn.classList.remove("btn-outline-success");
          btn.classList.add("btn-success", "active");
        }
      });
    }

    presetButtons.forEach((btn) => {
      btn.addEventListener("click", function () {
        const val = this.getAttribute("data-amount");
        amountInput.value = val;
        presetButtons.forEach((b) => b.classList.remove("active", "btn-success"));
        presetButtons.forEach((b) => b.classList.add("btn-outline-success"));
        this.classList.remove("btn-outline-success");
        this.classList.add("btn-success", "active");
      });
    });
  }

  // 2. Clipboard copy helper
  const copyButtons = document.querySelectorAll(".btn-copy");
  copyButtons.forEach((btn) => {
    btn.addEventListener("click", function () {
      const targetText = this.getAttribute("data-copy");
      if (targetText) {
        navigator.clipboard.writeText(targetText).then(() => {
          const originalHtml = this.innerHTML;
          this.innerHTML = '<i class="bi bi-check2"></i> Copied!';
          this.classList.add("btn-success");
          setTimeout(() => {
            this.innerHTML = originalHtml;
            this.classList.remove("btn-success");
          }, 2000);
        });
      }
    });
  });

  // 3. Auto-dismiss alerts after 6 seconds
  const autoAlerts = document.querySelectorAll(".alert-dismissible");
  autoAlerts.forEach((alert) => {
    setTimeout(() => {
      const bsAlert = bootstrap.Alert.getOrCreateInstance(alert);
      if (bsAlert) {
        bsAlert.close();
      }
    }, 6000);
  });
});

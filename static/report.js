(function () {
  var form = document.getElementById("report-form");
  if (!form) return;
  var status = document.getElementById("report-status");
  var contactWrap = document.getElementById("contact-wrap");
  var button = form.querySelector("button[type=submit]");

  form.addEventListener("change", function (e) {
    if (e.target.name === "contact_ok") contactWrap.hidden = e.target.value !== "yes";
  });

  form.addEventListener("submit", function (e) {
    e.preventDefault();
    status.className = "status-msg";
    if (!form.what.value.trim()) {
      status.textContent = "Add a description of what happened before sending.";
      status.className = "status-msg error";
      form.what.focus();
      return;
    }
    if (!form.consent.checked) {
      status.textContent = "Check the box to confirm you understand where this report goes.";
      status.className = "status-msg error";
      form.consent.focus();
      return;
    }
    button.disabled = true;
    status.textContent = "Sending your report…";
    var data = {};
    new FormData(form).forEach(function (v, k) { data[k] = v; });
    fetch("/api/report", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data)
    }).then(function (r) {
      if (!r.ok) throw new Error("send failed");
      form.reset();
      contactWrap.hidden = true;
      form.hidden = true;
      var done = document.createElement("div");
      done.className = "note sent";
      done.innerHTML = "<h2>Your report was sent</h2><p>Thank you for trusting us with this. It has been " +
        "delivered confidentially to the Hollywood Council for Restorative Justice. Nothing was saved on this site.</p>" +
        "<p>If you'd like to talk to someone now, RAINN's hotline is free and confidential at 800-656-4673.</p>";
      form.parentNode.insertBefore(done, form);
      done.setAttribute("tabindex", "-1");
      done.focus();
    }).catch(function () {
      button.disabled = false;
      status.textContent = "Your report didn't send. Nothing was saved. Check your connection and try again.";
      status.className = "status-msg error";
    });
  });
})();

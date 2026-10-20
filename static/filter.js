(function () {
  var q = document.getElementById("q");
  var status = document.getElementById("status");
  var chips = Array.prototype.slice.call(document.querySelectorAll(".chip"));
  var entries = Array.prototype.slice.call(document.querySelectorAll(".entry"));
  var months = Array.prototype.slice.call(document.querySelectorAll(".month"));
  var count = document.getElementById("count");
  var empty = document.getElementById("empty");
  var cat = "all";

  function apply() {
    var terms = q.value.toLowerCase().trim().split(/\s+/).filter(Boolean);
    var st = status.value;
    var shown = 0;
    entries.forEach(function (el) {
      var ok = (cat === "all" || el.dataset.cat === cat) &&
        (!st || el.dataset.status === st) &&
        terms.every(function (t) { return el.dataset.q.indexOf(t) !== -1; });
      el.hidden = !ok;
      if (ok) shown++;
    });
    months.forEach(function (m) {
      m.hidden = !m.querySelector(".entry:not([hidden])");
    });
    var filtered = terms.length || st || cat !== "all";
    count.textContent = filtered ? shown + " of " + entries.length + " entries" : "";
    empty.hidden = shown !== 0;
  }

  chips.forEach(function (c) {
    c.addEventListener("click", function () {
      cat = c.dataset.filter;
      chips.forEach(function (o) { o.setAttribute("aria-pressed", String(o === c)); });
      apply();
    });
  });
  q.addEventListener("input", apply);
  status.addEventListener("change", apply);
})();

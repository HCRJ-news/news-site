// Receives anonymous reports from /report/ and emails them to the
// Hollywood Council for Restorative Justice. Nothing is stored or logged.
//
// Requires (Cloudflare Pages project settings):
//   - send_email binding named EMAIL (Cloudflare Email Service)
//   - environment variable REPORT_TO = the Council's inbox
//   - environment variable REPORT_FROM = reports@sexabuselitigation.org (domain onboarded to Email Sending)

const LIMITS = { what: 10000, org: 300, when: 120, where: 200, reported: 120, contact: 200 };

function clean(v, max) {
  return String(v ?? "").replace(/\r\n?/g, "\n").trim().slice(0, max);
}

function escapeHtml(s) {
  return s.replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
}

export async function onRequestPost({ request, env }) {
  let body;
  try {
    body = await request.json();
  } catch {
    return Response.json({ ok: false, error: "invalid" }, { status: 400 });
  }

  // Honeypot: bots fill hidden fields. Pretend success so they don't retry.
  if (clean(body.website, 200)) return Response.json({ ok: true });

  const r = {};
  for (const [k, max] of Object.entries(LIMITS)) r[k] = clean(body[k], max);
  const wantsContact = body.contact_ok === "yes" && r.contact;

  if (!r.what || body.consent !== "on") {
    return Response.json({ ok: false, error: "missing" }, { status: 400 });
  }
  if (!env.EMAIL || !env.REPORT_TO || !env.REPORT_FROM) {
    return Response.json({ ok: false, error: "not_configured" }, { status: 503 });
  }

  const rows = [
    ["Organization involved", r.org],
    ["When", r.when],
    ["Where", r.where],
    ["Reported elsewhere", r.reported || "Prefer not to say"],
    ["Contact", wantsContact ? r.contact : "None — reporter chose to stay anonymous"],
  ];
  const text =
    "New anonymous report submitted through sexabuselitigation.org\n\n" +
    rows.map(([k, v]) => `${k}: ${v || "—"}`).join("\n") +
    "\n\nWhat happened:\n" + r.what +
    "\n\n---\nThis report was not stored on the website. The sender's IP address was not recorded.";
  const html =
    "<p>New anonymous report submitted through sexabuselitigation.org</p><table>" +
    rows.map(([k, v]) => `<tr><th align="left">${k}</th><td>${escapeHtml(v || "—")}</td></tr>`).join("") +
    `</table><h3>What happened</h3><p style="white-space:pre-wrap">${escapeHtml(r.what)}</p>` +
    "<hr><p><small>This report was not stored on the website. The sender's IP address was not recorded.</small></p>";

  try {
    await env.EMAIL.send({
      from: { email: env.REPORT_FROM, name: "Anonymous report form" },
      to: env.REPORT_TO,
      subject: "New confidential report",
      text,
      html,
    });
  } catch {
    return Response.json({ ok: false, error: "send_failed" }, { status: 502 });
  }
  return Response.json({ ok: true });
}

export function onRequest() {
  return new Response("Method not allowed", { status: 405, headers: { Allow: "POST" } });
}

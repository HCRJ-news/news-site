// Cloudflare Worker "report-form": receives anonymous reports from /report/ and emails them to the
// Hollywood Council for Restorative Justice via Email Routing. Nothing is stored or logged.
// Deployed in the Cloudflare dashboard with:
//   - Send Email binding named REPORTS (destination: report@hollywoodjustice.org)
//   - Routes: sexabuselitigation.org/api/report and www.sexabuselitigation.org/api/report
import { EmailMessage } from "cloudflare:email";

const FROM = "reports@sexabuselitigation.org";
const TO = "report@hollywoodjustice.org";
const LIMITS = { what: 10000, org: 300, when: 120, where: 200, reported: 120, contact: 200 };
const clean = (v, max) => String(v ?? "").replace(/\r\n?/g, "\n").trim().slice(0, max);
const json = (obj, status = 200) =>
  new Response(JSON.stringify(obj), { status, headers: { "Content-Type": "application/json" } });

export default {
  async fetch(request, env) {
    if (request.method !== "POST") return new Response("Method not allowed", { status: 405 });
    let body;
    try { body = await request.json(); } catch { return json({ ok: false }, 400); }
    if (clean(body.website, 200)) return json({ ok: true }); // honeypot
    const r = {};
    for (const [k, max] of Object.entries(LIMITS)) r[k] = clean(body[k], max);
    if (!r.what || body.consent !== "on") return json({ ok: false, error: "missing" }, 400);
    const contact = body.contact_ok === "yes" && r.contact ? r.contact : "None (reporter chose to stay anonymous)";
    const text = [
      "New anonymous report submitted through sexabuselitigation.org",
      "",
      "Organization involved: " + (r.org || "-"),
      "When: " + (r.when || "-"),
      "Where: " + (r.where || "-"),
      "Reported elsewhere: " + (r.reported || "Prefer not to say"),
      "Contact: " + contact,
      "",
      "What happened:",
      r.what,
      "",
      "---",
      "This report was not stored on the website. The sender's IP address was not recorded.",
    ].join("\r\n");
    const raw = [
      `From: Anonymous report form <${FROM}>`,
      `To: <${TO}>`,
      "Subject: New confidential report",
      `Message-ID: <${crypto.randomUUID()}@sexabuselitigation.org>`,
      `Date: ${new Date().toUTCString()}`,
      "MIME-Version: 1.0",
      "Content-Type: text/plain; charset=utf-8",
      "Content-Transfer-Encoding: 8bit",
      "",
      text,
    ].join("\r\n");
    try {
      await env.REPORTS.send(new EmailMessage(FROM, TO, raw));
    } catch {
      return json({ ok: false, error: "send_failed" }, 502);
    }
    return json({ ok: true });
  },
};

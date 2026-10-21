// Hero's Junk Removal site worker.
// Serves the static site (ASSETS) and one API route: POST /api/quote for the contact form.
// The visitor gets an answer immediately: the lead is saved to KV first (so it can never be lost),
// then the notification email goes out in the background (ctx.waitUntil).
// Email: Resend when RESEND_API_KEY is set (FormSubmit as fallback), plus a confirmation to the customer.
// A cron re-sends any lead whose email failed.
// GET /api/leads?key=LEADS_KEY lists the most recent leads with their delivery status.

const JSON_HEADERS = { 'content-type': 'application/json; charset=utf-8', 'cache-control': 'no-store' };
const FIELDS = ['full_name', 'phone', 'email', 'city', 'service', 'message', 'source'];

function reply(body, status = 200) {
  return new Response(JSON.stringify(body), { status, headers: JSON_HEADERS });
}

function clean(v, max = 2000) {
  return String(v == null ? '' : v).replace(/[\u0000-\u001f\u007f]/g, ' ').trim().slice(0, max);
}

async function readBody(request) {
  const type = request.headers.get('content-type') || '';
  if (type.includes('application/json')) return await request.json();
  const form = await request.formData();
  const out = {};
  for (const [k, v] of form.entries()) out[k] = typeof v === 'string' ? v : '';
  return out;
}

function leadText(lead) {
  return [
    'New website lead for Hero\'s Junk Removal',
    '',
    `Name: ${lead.full_name}`,
    `Phone: ${lead.phone}`,
    `Email: ${lead.email || '-'}`,
    `City: ${lead.city || '-'}`,
    `What needs to go: ${lead.service || '-'}`,
    `Details: ${lead.message || '-'}`,
    '',
    `Page: ${lead.source || '-'}`,
    `Received: ${lead.received}`,
  ].join('\n');
}

function customerText(lead) {
  const first = (lead.full_name || '').split(' ')[0] || 'there';
  return [
    `Hi ${first},`,
    '',
    'Thanks for reaching out to Hero\'s Junk Removal. We got your request and Nash will call or text you soon with a price.',
    '',
    'Need us faster? Call or text (214) 277-9069.',
    '',
    'What you sent us:',
    `Phone: ${lead.phone}`,
    `City: ${lead.city || '-'}`,
    `What needs to go: ${lead.service || '-'}`,
    `Details: ${lead.message || '-'}`,
    '',
    'Hero\'s Junk Removal',
    'herosjunkremovaltx.com',
  ].join('\n');
}

async function resend(env, msg) {
  const r = await fetch('https://api.resend.com/emails', {
    method: 'POST',
    headers: { authorization: `Bearer ${env.RESEND_API_KEY}`, 'content-type': 'application/json' },
    body: JSON.stringify({ from: env.RESEND_FROM, ...msg }),
  });
  return { via: 'resend', ok: r.ok, status: r.status, body: (await r.text()).slice(0, 300) };
}

async function formsubmit(env, lead) {
  const url = env.NOTIFY_URL || 'https://formsubmit.co/ajax/herosjunkremovaltx@gmail.com';
  const r = await fetch(url, {
    method: 'POST',
    headers: {
      'content-type': 'application/json',
      accept: 'application/json',
      origin: 'https://herosjunkremovaltx.com',
      referer: 'https://herosjunkremovaltx.com/contact',
    },
    body: JSON.stringify({
      _subject: `New Hero's Junk Removal lead (website): ${lead.full_name}`,
      _template: 'table',
      _captcha: 'false',
      ...Object.fromEntries(FIELDS.map((k) => [k, lead[k] || ''])),
      received: lead.received,
    }),
  });
  const body = (await r.text()).slice(0, 300);
  let ok = r.ok;
  try { ok = ok && String(JSON.parse(body).success) === 'true'; } catch { ok = false; }
  return { via: 'formsubmit', ok, status: r.status, body };
}

// Email Nash about the lead. Resend first; if that fails, try FormSubmit so a single outage can't drop it.
async function notify(env, lead) {
  if (lead.test) {
    return resend(env, { to: (env.TEST_TO || 'wingdigital26@gmail.com').split(','), subject: `TEST lead: ${lead.full_name}`, text: leadText(lead) });
  }
  if (env.RESEND_API_KEY && env.RESEND_FROM) {
    const cc = (env.LEAD_CC || '').split(',').map((x) => x.trim()).filter(Boolean);
    const r = await resend(env, {
      to: (env.LEAD_TO || 'herosjunkremovaltx@gmail.com').split(','),
      cc: cc.length ? cc : undefined,
      reply_to: lead.email || undefined,
      subject: `New lead: ${lead.full_name}, ${lead.phone} (${lead.city || 'no city'})`,
      text: leadText(lead),
    });
    if (r.ok) return r;
    const fb = await formsubmit(env, lead).catch((e) => ({ via: 'formsubmit', ok: false, error: String(e).slice(0, 200) }));
    return fb.ok ? fb : { ...r, fallback: fb };
  }
  return formsubmit(env, lead);
}

// Confirmation to the person who filled out the form, so they know it went through.
async function confirmCustomer(env, lead) {
  if (!env.RESEND_API_KEY || !env.RESEND_FROM || !/^[^@\s]+@[^@\s]+\.[a-z]{2,}$/i.test(lead.email || '')) return { skipped: true };
  return resend(env, {
    to: [lead.email],
    reply_to: (env.LEAD_TO || 'herosjunkremovaltx@gmail.com').split(',')[0],
    subject: 'We got your junk removal request',
    text: customerText(lead),
  });
}

async function deliver(env, id, lead, prev = {}) {
  let result = prev.delivery && prev.delivery.ok ? prev.delivery : null;
  if (!result) {
    try { result = await notify(env, lead); } catch (e) { result = { ok: false, error: String(e).slice(0, 200) }; }
  }
  let confirm = prev.confirm && (prev.confirm.ok || prev.confirm.skipped) ? prev.confirm : null;
  if (!confirm) {
    try { confirm = await confirmCustomer(env, lead); } catch (e) { confirm = { ok: false, error: String(e).slice(0, 200) }; }
  }
  const attempts = (prev.attempts || 0) + 1;
  try { if (env.LEADS) await env.LEADS.put(id, JSON.stringify({ ...lead, delivery: result, confirm, attempts })); } catch (e) { console.error('lead status save failed', e); }
  console.log('lead', id, attempts, JSON.stringify(result), JSON.stringify(confirm));
}

// Cron: re-send any lead whose email to Nash failed (up to 24 tries, then it stays flagged in /api/leads).
async function retryFailed(env) {
  if (!env.LEADS) return;
  const list = await env.LEADS.list({ prefix: 'lead:', limit: 1000 });
  for (const { name } of list.keys) {
    const rec = JSON.parse((await env.LEADS.get(name)) || '{}');
    if (rec.no_resend || rec.test) continue;
    const pending = !rec.delivery || rec.delivery === 'pending' || !rec.delivery.ok;
    if (!pending || (rec.attempts || 0) >= 24) continue;
    if (Date.now() - Date.parse(rec.received) < 5 * 60 * 1000) continue;
    const { delivery, confirm, attempts, ...lead } = rec;
    await deliver(env, name, lead, { delivery: rec.delivery, confirm, attempts });
  }
}

async function handleQuote(request, env, ctx) {
  let data;
  try { data = await readBody(request); } catch { return reply({ success: 'false', message: 'Bad request' }, 400); }
  // Honeypot: bots fill the hidden "company" field. Pretend success, store nothing.
  if (clean(data.company)) return reply({ success: 'true' });

  const lead = Object.fromEntries(FIELDS.map((k) => [k, clean(data[k], k === 'message' ? 4000 : 200)]));
  if (!lead.full_name || !lead.phone) return reply({ success: 'false', message: 'Name and phone are required.' }, 422);
  lead.received = new Date().toISOString();
  lead.ip_country = request.cf && request.cf.country ? request.cf.country : '';
  // ?test=<LEADS_KEY>: Nash's copy goes to TEST_TO instead of Nash.
  const testKey = new URL(request.url).searchParams.get('test');
  if (testKey && env.LEADS_KEY && testKey === env.LEADS_KEY) { lead.test = true; lead.no_resend = true; }

  const id = `lead:${lead.received}:${crypto.randomUUID().slice(0, 8)}`;
  // Saving must never block the lead: if storage hiccups, the email still goes out.
  try { if (env.LEADS) await env.LEADS.put(id, JSON.stringify({ ...lead, delivery: 'pending' })); } catch (e) { console.error('lead save failed', e); }

  ctx.waitUntil(deliver(env, id, lead));

  return reply({ success: 'true', message: 'Received' });
}

async function handleLeads(request, env) {
  const url = new URL(request.url);
  if (!env.LEADS_KEY || url.searchParams.get('key') !== env.LEADS_KEY) return reply({ error: 'not found' }, 404);
  if (!env.LEADS) return reply({ leads: [] });
  const list = await env.LEADS.list({ prefix: 'lead:', limit: 1000 });
  const keys = list.keys.map((k) => k.name).sort().reverse().slice(0, 100);
  const leads = await Promise.all(keys.map(async (k) => JSON.parse((await env.LEADS.get(k)) || '{}')));
  return reply({ count: leads.length, leads });
}

export default {
  async fetch(request, env, ctx) {
    const { pathname } = new URL(request.url);
    if (pathname === '/api/quote') {
      if (request.method !== 'POST') return reply({ error: 'method not allowed' }, 405);
      return handleQuote(request, env, ctx);
    }
    if (pathname === '/api/leads') return handleLeads(request, env);
    return env.ASSETS.fetch(request);
  },
  async scheduled(event, env, ctx) {
    ctx.waitUntil(retryFailed(env));
  },
};

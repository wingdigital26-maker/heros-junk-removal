// Hero's Junk Removal site worker.
// Serves the static site (ASSETS) and one API route: POST /api/quote for the contact form.
// The visitor gets an answer immediately: the lead is saved to KV first (so it can never be lost),
// then the notification email goes out in the background (ctx.waitUntil).
// Email: Resend when RESEND_API_KEY is set, otherwise forwarded to FormSubmit (NOTIFY_URL).
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

async function notify(env, lead) {
  if (env.RESEND_API_KEY && env.RESEND_FROM) {
    const r = await fetch('https://api.resend.com/emails', {
      method: 'POST',
      headers: { authorization: `Bearer ${env.RESEND_API_KEY}`, 'content-type': 'application/json' },
      body: JSON.stringify({
        from: env.RESEND_FROM,
        to: (env.LEAD_TO || 'herosjunkremovaltx@gmail.com').split(','),
        reply_to: lead.email || undefined,
        subject: `New lead: ${lead.full_name} (${lead.city || 'no city'})`,
        text: leadText(lead),
      }),
    });
    return { via: 'resend', ok: r.ok, status: r.status, body: (await r.text()).slice(0, 300) };
  }
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

async function handleQuote(request, env, ctx) {
  let data;
  try { data = await readBody(request); } catch { return reply({ success: 'false', message: 'Bad request' }, 400); }
  // Honeypot: bots fill the hidden "company" field. Pretend success, store nothing.
  if (clean(data.company)) return reply({ success: 'true' });

  const lead = Object.fromEntries(FIELDS.map((k) => [k, clean(data[k], k === 'message' ? 4000 : 200)]));
  if (!lead.full_name || !lead.phone) return reply({ success: 'false', message: 'Name and phone are required.' }, 422);
  lead.received = new Date().toISOString();
  lead.ip_country = request.cf && request.cf.country ? request.cf.country : '';

  const id = `lead:${lead.received}:${crypto.randomUUID().slice(0, 8)}`;
  // Saving must never block the lead: if storage hiccups, the email still goes out.
  try { if (env.LEADS) await env.LEADS.put(id, JSON.stringify({ ...lead, delivery: 'pending' })); } catch (e) { console.error('lead save failed', e); }

  ctx.waitUntil((async () => {
    let result;
    try { result = await notify(env, lead); } catch (e) { result = { ok: false, error: String(e).slice(0, 200) }; }
    try { if (env.LEADS) await env.LEADS.put(id, JSON.stringify({ ...lead, delivery: result })); } catch (e) { console.error('lead status save failed', e); }
    console.log('lead', id, JSON.stringify(result));
  })());

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
};

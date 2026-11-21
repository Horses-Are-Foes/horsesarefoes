// ===========================================================================
// Horses Are Foes — Decap CMS GitHub OAuth proxy
// -----------------------------------------------------------------------------
// A tiny, dependency-free Cloudflare Worker that speaks Decap's github-backend
// auth protocol. Decap opens /auth in a popup, then finishes a postMessage
// handshake on /callback. Without that handshake the editor's "Login" button
// never signs you in (the popup just hangs / stays blank).
//
// DEPLOY (no wrangler, no build — just paste):
//   1. Workers & Pages  ->  Create Application  ->  Worker  ->  Quick start
//   2. Replace the starter code with this whole file.
//   3. Settings  ->  Variables & Secrets  (type = "Secret")  ->  add:
//          GITHUB_OAUTH_ID     your GitHub OAuth app CLIENT ID
//          GITHUB_OAUTH_SECRET your GitHub OAuth app CLIENT SECRET
//      (optional) GITHUB_REPO_PRIVATE = 1   (set only if the repo is private)
//   4. Save and Deploy.
//
// In the GitHub OAuth app settings set the Authorization redirect URI to:
//          https://<your-worker>/callback
//
// The Worker serves two paths used by Decap:
//   /auth     -> 302-redirects the popup to GitHub's authorize page.
//   /callback -> once GitHub redirects back with an auth code, we exchange it
//                for an access token and postMessage() the result back to the
//                Decap editor using the exact handshake Decap expects.
// ===========================================================================

export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    const id = env.GITHUB_OAUTH_ID;
    const secret = env.GITHUB_OAUTH_SECRET;

    // /auth — Decap opens this in a popup to start GitHub login.
    // We don't hand the client any secret here; the token is fetched
    // server-side from /callback, so the client stays out of the way.
    if (url.pathname === '/auth') {
      if (!id || !secret) {
        return new Response('Set GITHUB_OAUTH_ID and GITHUB_OAUTH_SECRET secrets first.', { status: 500 });
      }
      if (url.searchParams.get('provider') !== 'github') {
        return new Response('Only the github provider is supported.', { status: 400 });
      }
      // The repo scope is fixed here so the caller can't widen it.
      const isPrivate = env.GITHUB_REPO_PRIVATE === '1' || env.GITHUB_REPO_PRIVATE === 'true';
      const scope = isPrivate ? 'repo,user' : 'public_repo,user';
      const authorize = new URL('https://github.com/login/oauth/authorize');
      authorize.searchParams.set('client_id', id);
      authorize.searchParams.set('redirect_uri', `${url.protocol}//${url.host}/callback`);
      authorize.searchParams.set('scope', scope);
      const state = randomState();
      authorize.searchParams.set('state', state);
      // Remember the state in an HttpOnly cookie so /callback can reject a
      // mismatched (CSRF) state. Exposed only to the Worker, never the page.
      const cookie = `decap_cms_state=${state}; Path=/; Secure; HttpOnly; SameSite=Lax; Max-Age=300`;
      return new Response(null, {
        status: 302,
        headers: {
          Location: authorize.toString(),
          'Set-Cookie': cookie,
          'Cache-Control': 'no-store',
        },
      });
    }

    // /callback — GitHub redirects here with ?code=...&state=...
    // (GitHub does NOT echo the `provider` param here; only /auth needs it.)
    if (url.pathname === '/callback') {
      const code = url.searchParams.get('code');
      if (!code) {
        return new Response('Missing authorization code. Sign in again from the editor.', { status: 400 });
      }
      if (!id || !secret) {
        return new Response('The proxy needs GITHUB_OAUTH_ID and GITHUB_OAUTH_SECRET secrets.', { status: 500 });
      }

      // CSRF: compare the state GitHub echoed against the one we stored at /auth.
      const cookieState = readCookie(request, 'decap_cms_state');
      const returnedState = url.searchParams.get('state');
      if (!cookieState || !returnedState || !safeEqual(cookieState, returnedState)) {
        return new Response(
          'OAuth state mismatch. Sign in again from the editor.',
          {
            status: 400,
            headers: { 'Content-Type': 'text/html;charset=UTF-8', 'Cache-Control': 'no-store' },
          },
        );
      }

      // Exchange the one-time code for an access token.
      const { token, error } = await exchangeCode(code, id, secret);

      // Render the handshake page that hands the token back to the Decap editor.
      return new Response(renderCallbackPage(token, error), {
        status: token ? 200 : 400,
        headers: {
          'Content-Type': 'text/html;charset=UTF-8',
          'Cache-Control': 'no-store',
          'Referrer-Policy': 'no-referrer',
        },
      });
    }

    return new Response('Horses Are Foes Decap OAuth proxy. Use /auth to sign in.', {
      status: 200,
      headers: { 'Content-Type': 'text/plain;charset=UTF-8' },
    });
  },
};

// -----------------------------------------------------------------------------
// Helpers
// -----------------------------------------------------------------------------

function readCookie(request, name) {
  const header = request.headers.get('cookie') || '';
  for (const part of header.split(';')) {
    const eq = part.trim().indexOf('=');
    if (eq === -1) continue;
    const key = part.trim().slice(0, eq);
    if (key === name) {
      try {
        return decodeURIComponent(part.trim().slice(eq + 1));
      } catch {
        return part.trim().slice(eq + 1);
      }
    }
  }
  return null;
}

function safeEqual(a, b) {
  const len = Math.max(a.length, b.length);
  let diff = a.length ^ b.length;
  for (let i = 0; i < len; i++) {
    diff |= (a.charCodeAt(i) || 0) ^ (b.charCodeAt(i) || 0);
  }
  return diff === 0;
}

function randomState() {
  const bytes = new Uint8Array(32);
  crypto.getRandomValues(bytes);
  let out = '';
  for (let i = 0; i < 32; i++) out += bytes[i].toString(16).padStart(2, '0');
  return out;
}

// Exchange the one-time code for an access token. Returns { token, error }.
async function exchangeCode(code, id, secret) {
  let resp, json;
  try {
    resp = await fetch('https://github.com/login/oauth/access_token', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', Accept: 'application/json' },
      body: JSON.stringify({ client_id: id, client_secret: secret, code }),
    });
    json = await resp.json();
  } catch (e) {
    return { token: null, error: 'network error: ' + String(e) };
  }
  if (json && json.access_token) {
    return { token: json.access_token, error: null };
  }
  return {
    token: null,
    error:
      json.error ||
      json.error_description ||
      'GitHub token exchange failed (unknown error).',
  };
}

// -----------------------------------------------------------------------------
// The popup page the editor finishes the handshake from.
// -----------------------------------------------------------------------------
// The popup is a top-level window, so `window.opener` is the Decap editor.
// We talk ONLY to window.opener (never to a wildcard origin), and only with the
// exact grammar Decap's client accepts (decap-cms-lib-auth):
//     1. 'authorizing:github'          <- editor waits for this
//     2. editor replies to us          <- then we post the token back
//     3. 'authorization:github:success:<json>'   { token }
// -----------------------------------------------------------------------------

function renderCallbackPage(token, error) {
  const errPayload = JSON.stringify({ message: error || 'Authentication failed.' });

  const errScript = `
    function fail(e) {
      if (!window.opener || e.source !== window.opener) return;
      if (e.origin !== window.opener.origin) return;
      window.opener.postMessage('authorization:github:error:' + ${errPayload}, window.opener.origin);
      window.removeEventListener('message', fail);
    }
    window.addEventListener('message', fail, false);
    window.opener.postMessage('authorizing:github', window.opener.origin);
  `;

  // Token success: announce readiness, then (once the editor confirms) post the
  // token. Decap's client reads exactly this { token } shape.
  const successPayload = JSON.stringify({ token });
  const successScript = `
    function reply(e) {
      if (!window.opener || e.source !== window.opener) return;
      if (e.origin !== window.opener.origin) return;
      window.opener.postMessage('authorization:github:success:${successPayload}', window.opener.origin);
      window.removeEventListener('message', reply);
    }
    window.addEventListener('message', reply, false);
    window.opener.postMessage('authorizing:github', window.opener.origin);
  `;

  const body = token ? successScript : errScript;
  return `<!doctype html><html><body><h1 style="font-family:sans-serif">Authorizing…</h1><script>${body}</script></body></html>`;
}

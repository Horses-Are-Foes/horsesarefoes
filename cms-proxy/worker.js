// Horses Are Foes — Decap CMS GitHub sign-in proxy (Cloudflare Worker)
//
// A tiny, dependency-free worker that stands in for a GitHub OAuth token
// server so the Decap CMS editor can sign in with "Login with GitHub".
// Decap opens /auth in a popup, then finishes a postMessage handshake on
// /callback. Without that handshake the editor's "Login" button never signs
// you in (the popup just hangs / stays blank).
//
// DEPLOY (no wrangler, no build — just paste into a fresh Worker's code box):
//   1. Workers & Pages  ->  Create Application  ->  Worker  ->  Quick start
//   2. Replace the starter code with this whole file.
//   3. Settings  ->  Variables & Secrets  (type = "Secret")  ->  add:
//          GITHUB_OAUTH_ID     your GitHub OAuth app CLIENT ID
//          GITHUB_OAUTH_SECRET your GitHub OAuth app CLIENT SECRET
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

// ---------------------------------------------------------------------------
// 16 bytes of crypto-strength randomness, hex-encoded, as the CSRF state token.
function generateState() {
  const bytes = new Uint8Array(16);
  crypto.getRandomValues(bytes);
  let out = '';
  for (let i = 0; i < 16; i++) out += bytes[i].toString(16).padStart(2, '0');
  return out;
}

// Read the `state` cookie value from the incoming request, or null if absent.
function readStateCookie(request) {
  const header = request.headers.get('cookie') || request.headers.get('Cookie') || '';
  for (const pair of header.split(';')) {
    if (pair.trim().startsWith('state=')) {
      return pair.trim().slice(6);
    }
  }
  return null;
}

// Constant-time string comparison, to avoid timing attacks on the state token.
function safeEqual(a, b) {
  const len = Math.max(a.length, b.length);
  let diff = a.length ^ b.length;
  for (let i = 0; i < len; i++) {
    diff |= (a.charCodeAt(i) || 0) ^ (b.charCodeAt(i) || 0);
  }
  return diff === 0;
}

// Step 1 — send the popup to GitHub's authorize page, remembering the state.
function handleAuth(url, env) {
  const GITHUB_OAUTH_ID = env.GITHUB_OAUTH_ID;
  const authState = generateState();
  const scope = url.searchParams.get('scope') || 'repo';

  const authUrl = new URL('https://github.com/login/oauth/authorize');
  authUrl.searchParams.set('client_id', GITHUB_OAUTH_ID);
  authUrl.searchParams.set('redirect_uri', `${url.protocol}//${url.host}/callback`);
  authUrl.searchParams.set('scope', scope);
  authUrl.searchParams.set('state', authState);

  // HttpOnly (the client never reads it; the Worker checks it server-side),
  // Secure, and Lax so GitHub's back-redirect (a top-level GET) still carries
  // the cookie back to /callback.
  const cookie = `state=${authState}; Path=/; Secure; SameSite=Lax; Max-Age=300; HttpOnly`;
  return new Response('', {
    status: 302,
    headers: {
      Location: authUrl.toString(),
      'Set-Cookie': cookie,
      'Cache-Control': 'no-store',
    },
  });
}

// Step 2 — exchange the one-time code for a token and render the handshake page.
async function handleCallback(url, code, state, env, request) {
  const secret = env.GITHUB_OAUTH_SECRET;
  const GITHUB_OAUTH_ID = env.GITHUB_OAUTH_ID;
  const cookieState = readStateCookie(request);

  if (!code) {
    return renderError('Could not sign you in', 'Missing authorization code. Sign in again.');
  }
  if (!secret) {
    return renderError(
      'Could not sign you in',
      'The proxy is missing its GITHUB_OAUTH_SECRET secret. Tell Andrew.',
    );
  }
  if (!cookieState || !state || !safeEqual(cookieState, state)) {
    return renderError(
      'Could not sign you in',
      'Session state mismatch. Please start over and sign in again.',
    );
  }

  // Exchange the one-time code for a long-lived access token.
  let data;
  try {
    const exchange = await fetch('https://github.com/login/oauth/access_token', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', Accept: 'application/json' },
      body: JSON.stringify({ client_id: GITHUB_OAUTH_ID, client_secret: secret, code }),
    });
    data = await exchange.json();
  } catch (e) {
    return renderError('Could not sign you in', 'Network error talking to GitHub.');
  }

  if (!data || !data.access_token) {
    const reason = data && data.error_description
      ? data.error_description
      : (data && data.error)
        ? data.error
        : 'GitHub rejected the token request.';
    return renderError('Could not sign you in', `GitHub said: ${reason}`);
  }

  const token = data.access_token;

  // Hand the token back to the Decap editor over postMessage. The editor
  // (window.opener) asks for our handshake with 'authorizing:github', we
  // acknowledge, then reply with 'authorization:github:...:success:<JSON>'.
  // The editor parses the JSON and reads the .token field.
  const script = `
    const token = ${JSON.stringify(token)};
    window.opener.postMessage('authorizing:github', '*');
    function reply(event) {
      if (event.data !== 'authorizing:github') return;
      window.removeEventListener('message', reply);
      window.opener.postMessage(
        'authorization:github:success:' + JSON.stringify({ token: token, provider: 'github' }),
        '*'
      );
    }
    window.addEventListener('message', reply);
  `;

  const body = `<!doctype html>
<html>
<head><title>Signing you in…</title></head>
<body style="font-family: system-ui, sans-serif; text-align: center; padding-top: 3rem;">
  <p>Signing you in…</p>
  <script>${script}</script>
</body>
</html>`;

  return new Response(body, {
    status: 200,
    headers: { 'Content-Type': 'text/html; charset=utf-8' },
  });
}

// Small error page shown when the OAuth dance can't finish.
function renderError(title, message) {
  const body = `<!doctype html>
<html>
<head><title>${title}</title></head>
<body style="font-family: system-ui, sans-serif; text-align: center; padding-top: 3rem;">
  <p>${message}</p>
</body>
</html>`;
  return new Response(body, {
    status: 200,
    headers: { 'Content-Type': 'text/html; charset=utf-8' },
  });
}

// Cloudflare injects the OAuth client id + secret via the `env` parameter.
export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    const GITHUB_OAUTH_ID = env.GITHUB_OAUTH_ID;
    const GITHUB_OAUTH_SECRET = env.GITHUB_OAUTH_SECRET;

    if (url.pathname === '/auth') {
      if (!GITHUB_OAUTH_ID || !GITHUB_OAUTH_SECRET) {
        return new Response('Set GITHUB_OAUTH_ID and GITHUB_OAUTH_SECRET secrets first.', {
          status: 500,
        });
      }
      return handleAuth(url, env);
    }

    if (url.pathname === '/callback') {
      if (!GITHUB_OAUTH_ID || !GITHUB_OAUTH_SECRET) {
        return new Response('The proxy needs its GITHUB_OAUTH_ID / GITHUB_OAUTH_SECRET secrets.', {
          status: 500,
        });
      }
      return handleCallback(
        url,
        url.searchParams.get('code'),
        url.searchParams.get('state'),
        env,
        request,
      );
    }

    return new Response('Horses Are Foes Decap OAuth proxy. Use /auth to sign in.', {
      status: 200,
      headers: { 'Content-Type': 'text/plain; charset=utf-8' },
    });
  },
};

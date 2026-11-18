// ===========================================================================
// Horses Are Foes — Decap CMS GitHub OAuth proxy
// -----------------------------------------------------------------------------
// A tiny, dependency-free Cloudflare Worker that speaks Decap's github-backend
// auth protocol. Without it the editor's "Sign in" button never renders.
//
// DEPLOY (no wrangler, no build — just paste):
//   1. Workers & Pages  ->  Create Application  ->  Worker  ->  Quick start
//   2. Delete the starter code, PASTE this whole file.
//   3. Settings  ->  Variables & Secrets  (type = "Secret")  ->  add:
//          GITHUB_OAUTH_ID     your GitHub OAuth app CLIENT ID
//          GITHUB_OAUTH_SECRET your GitHub OAuth app CLIENT SECRET
//      (optional) GITHUB_REPO_PRIVATE = 1   (set only if the repo is private)
//   4. Save and Deploy.
//
// In the GitHub OAuth app settings set the Authorization redirect URI to:
//          https://<your-worker>/callback
// (the Worker handles both /auth and /callback — see below).
// ===========================================================================

export default {
  // request / env / ctx — secrets live in `env`.
  async fetch(request, env) {
    const url = new URL(request.url);
    const id = env.GITHUB_OAUTH_ID;
    const secret = env.GITHUB_OAUTH_SECRET;

    if (!id || !secret) {
      return new Response('Set GITHUB_OAUTH_ID and GITHUB_OAUTH_SECRET secrets first.', {
        status: 500,
      });
    }

    // /auth — Decap calls this to start login. Send the popup to GitHub.
    if (url.pathname === '/auth') {
      const scope = env.GITHUB_REPO_PRIVATE === '1' ? 'repo,user' : 'public_repo,user';
      const redirectUri = `${url.protocol}//${url.host}/callback`;
      const authUrl = new URL('https://github.com/login/oauth/authorize');
      authUrl.searchParams.set('client_id', id);
      authUrl.searchParams.set('redirect_uri', redirectUri);
      authUrl.searchParams.set('scope', scope);
      authUrl.searchParams.set('state', randomState(16));
      return Response.redirect(authUrl.toString(), 301);
    }

    // /callback — GitHub sends ?code=... here; exchange it for an access token.
    if (url.pathname === '/callback') {
      const code = url.searchParams.get('code');
      if (!code) {
        return new Response('Missing authorization code. Sign in again from the editor.', {
          status: 400,
        });
      }
      let resp;
      let data = null;
      try {
        resp = await fetch('https://github.com/login/oauth/access_token', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json', Accept: 'application/json' },
          body: JSON.stringify({ client_id: id, client_secret: secret, code }),
        });
        // Read raw text first so we can surface it even if the body isn't JSON.
        const text = await resp.text();
        try {
          data = JSON.parse(text);
        } catch {
          data = { _raw: text };
        }
      } catch (err) {
        return new Response(
          `<pre>network error: ${String(err)}</pre>`,
          { headers: { 'Content-Type': 'text/html;charset=UTF-8' } }
        );
      }

      if (data && data.access_token) {
        // Hand the token back to the editor, hidden, via postMessage.
        return new Response(
          `<html><body><script>window.parent.postMessage(${JSON.stringify(
            data.access_token,
          )}, '*');</script></body></html>`,
          { headers: { 'Content-Type': 'text/html;charset=UTF-8' } }
        );
      }

      // Failure: echo back GitHub's exact reason so the popup is self-diagnosing.
      const parts = [];
      if (data && data.error) parts.push(`error: ${data.error}`);
      if (data && data.error_description) parts.push(`description: ${data.error_description}`);
      if (data && data.error_uri) parts.push(`info: ${data.error_uri}`);
      if (data && data._raw) parts.push(`raw: ${data._raw}`);
      if (!parts.length) parts.push('Token exchange failed (GitHub returned nothing useful).');
      return new Response(`<pre>${parts.join('\n')}</pre>`, {
        headers: { 'Content-Type': 'text/html;charset=UTF-8' },
      });
    }

    return new Response('Horses Are Foes Decap OAuth proxy. Use /auth to sign in.', {
      status: 200,
      headers: { 'Content-Type': 'text/plain;charset=UTF-8' },
    });
  },
};

function randomState(n) {
  const bytes = new Uint8Array(n);
  crypto.getRandomValues(bytes);
  let out = '';
  for (let i = 0; i < n; i++) out += bytes[i].toString(16).padStart(2, '0');
  return out;
}

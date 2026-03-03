/**
 * Cloudflare Worker proxy for treningscoach-backend.
 * Single source of truth for Cloudflare deploy behavior lives in wrangler.toml.
 * Backend runtime source of truth remains Render (main.py).
 */

const DEFAULT_ORIGIN = "https://treningscoach-backend.onrender.com";

export default {
  async fetch(request, env) {
    const originBase = (env.ORIGIN_URL || DEFAULT_ORIGIN).replace(/\/+$/, "");
    const reqUrl = new URL(request.url);
    const upstreamUrl = `${originBase}${reqUrl.pathname}${reqUrl.search}`;

    const headers = new Headers(request.headers);
    headers.set("x-forwarded-host", reqUrl.host);
    headers.set("x-forwarded-proto", reqUrl.protocol.replace(":", ""));
    headers.delete("host");

    const init = {
      method: request.method,
      headers,
      redirect: "manual",
    };

    if (request.method !== "GET" && request.method !== "HEAD") {
      init.body = request.body;
    }

    const upstream = await fetch(upstreamUrl, init);
    const responseHeaders = new Headers(upstream.headers);
    responseHeaders.set("x-coachi-edge", "cloudflare-worker");

    return new Response(upstream.body, {
      status: upstream.status,
      statusText: upstream.statusText,
      headers: responseHeaders,
    });
  },
};

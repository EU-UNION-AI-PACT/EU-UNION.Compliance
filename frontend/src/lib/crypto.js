/**
 * Browser-native holder-binding helpers using SubtleCrypto.
 * Generates a P-256 ECDSA keypair, exports the public JWK, and signs the
 * OpenID4VCI proof JWT for the issuer's nonce challenge.
 */

function b64u(bytes) {
  let s = "";
  const arr = new Uint8Array(bytes);
  for (let i = 0; i < arr.byteLength; i++) s += String.fromCharCode(arr[i]);
  return btoa(s).replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/, "");
}

function b64uJson(obj) {
  const s = JSON.stringify(obj);
  return b64u(new TextEncoder().encode(s));
}

export async function generateHolderKey() {
  const pair = await crypto.subtle.generateKey(
    { name: "ECDSA", namedCurve: "P-256" },
    true,
    ["sign", "verify"]
  );
  const jwk = await crypto.subtle.exportKey("jwk", pair.publicKey);
  const pubJwk = { kty: "EC", crv: "P-256", x: jwk.x, y: jwk.y };
  return { privateKey: pair.privateKey, publicJwk: pubJwk };
}

export async function signProofJwt(privateKey, publicJwk, { audience, nonce }) {
  const header = { alg: "ES256", typ: "openid4vci-proof+jwt", jwk: publicJwk };
  const payload = { iss: "holder", aud: audience, iat: Math.floor(Date.now() / 1000), nonce };
  const h = b64uJson(header);
  const p = b64uJson(payload);
  const signingInput = new TextEncoder().encode(`${h}.${p}`);
  const sig = await crypto.subtle.sign(
    { name: "ECDSA", hash: "SHA-256" },
    privateKey,
    signingInput
  );
  return `${h}.${p}.${b64u(sig)}`;
}

export async function signKbJwt(privateKey, { audience, nonce, sd_hash }) {
  const header = { alg: "ES256", typ: "kb+jwt" };
  const payload = { aud: audience, nonce, iat: Math.floor(Date.now() / 1000), sd_hash };
  const h = b64uJson(header);
  const p = b64uJson(payload);
  const signingInput = new TextEncoder().encode(`${h}.${p}`);
  const sig = await crypto.subtle.sign(
    { name: "ECDSA", hash: "SHA-256" },
    privateKey,
    signingInput
  );
  return `${h}.${p}.${b64u(sig)}`;
}

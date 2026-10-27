/**
 * Client-side SHA-256 verification using browser Web Crypto API.
 */
export async function sha256Browser(content) {
  const enc = new TextEncoder();
  const data = typeof content === "string" ? enc.encode(content) : content;
  const hashBuffer = await window.crypto.subtle.digest("SHA-256", data);
  const hashArray = Array.from(new Uint8Array(hashBuffer));
  return hashArray.map(b => b.toString(16).padStart(2, "0")).join("");
}
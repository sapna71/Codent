export function isValidGithubUrl(url: string): boolean {
  try {
    const parsed = new URL(url.trim());
    if (!["github.com", "www.github.com"].includes(parsed.hostname)) return false;
    const parts = parsed.pathname.split("/").filter(Boolean);
    return parts.length >= 2;
  } catch {
    return false;
  }
}

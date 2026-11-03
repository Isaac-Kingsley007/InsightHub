export async function api<T>(path: string, options?: RequestInit): Promise<T> {
  let response: Response;
  try { response = await fetch(`/api${path}`, options); }
  catch { throw new Error("Could not reach InsightHub. Check your connection and try again."); }
  const data = await response.json().catch(() => null);
  if (!response.ok) {
    const detail = data?.detail;
    throw new Error(typeof detail === "string" ? detail : response.status === 422 ? "Please check the required fields and try again." : "The service is unavailable. Make sure the Python API is running, then try again.");
  }
  if (data === null) throw new Error("The service returned an empty response. Please try again.");
  return data as T;
}

export function postJson<T>(path: string, value: unknown) {
  return api<T>(path, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(value) });
}

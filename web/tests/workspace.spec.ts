import { expect, test } from "@playwright/test";

test("agent chat supports follow-ups and new conversations", async ({ page }) => {
  const sessions: string[] = [];
  await page.route("**/api/agent", async route => {
    sessions.push(route.request().postDataJSON().session_id);
    await route.fulfill({ json: { answer: "There are 42 churned customers. [chunk-1]", tools_used: ["run_safe_query", "search_documents"] } });
  });
  await page.goto("/chat");
  await expect(page.getByRole("heading", { name: "What would you like to understand?" })).toBeVisible();
  await page.getByRole("textbox", { name: "Your question" }).fill("How many customers churned?");
  await page.getByRole("button", { name: "Send question" }).click();
  await expect(page.getByText("There are 42 churned customers. [chunk-1]")).toBeVisible();
  await page.getByRole("textbox", { name: "Your question" }).fill("What about policies?");
  await page.getByRole("button", { name: "Send question" }).click();
  await expect(page.getByText("There are 42 churned customers. [chunk-1]")).toHaveCount(2);
  expect(sessions[0]).toBe(sessions[1]);
  await page.getByRole("button", { name: "New conversation" }).click();
  await expect(page.getByRole("heading", { name: "What would you like to understand?" })).toBeVisible();
});

test("document upload uses multipart and refreshes the library", async ({ page }) => {
  let uploaded = false;
  await page.route("**/api/documents", route => route.fulfill({ json: uploaded ? [{ id: "doc", filename: "policy.txt", created_at: "2026-11-03T10:00:00Z", chunk_count: 2 }] : [] }));
  await page.route("**/api/ingest", async route => {
    expect(route.request().headers()["content-type"]).toContain("multipart/form-data");
    uploaded = true;
    await route.fulfill({ json: { id: "doc", filename: "policy.txt", chunk_count: 2, created: true } });
  });
  await page.goto("/documents");
  await page.getByLabel("Choose policy document").setInputFiles({ name: "policy.txt", mimeType: "text/plain", buffer: Buffer.from("Refunds within 30 days.") });
  await page.getByRole("button", { name: "Upload & add to knowledge base" }).click();
  await expect(page.getByText("Added to your knowledge base.", { exact: true })).toBeVisible();
  await expect(page.getByText("Ready for search")).toBeVisible();
});

test("churn form reaches the real saved-model API through the proxy", async ({ page }) => {
  await page.goto("/predictions");
  await page.getByRole("button", { name: "Predict churn risk" }).click();
  await expect(page.getByText("Estimated churn probability")).toBeVisible();
  await expect(page.getByRole("heading", { name: "Recent predictions" })).toBeVisible();
  await expect(page.getByText(/Predicted to (stay|churn)/)).toBeVisible();
});

test("mobile navigation and service errors are usable", async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await page.route("**/api/documents", route => route.fulfill({ status: 503, json: { detail: "Document storage unavailable." } }));
  await page.goto("/chat");
  await page.getByRole("link", { name: "Knowledge base", exact: true }).click();
  await expect(page.getByRole("alert").filter({ hasText: "Document storage unavailable." })).toBeVisible();
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(true);
});

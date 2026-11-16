// Browser QA: responsive, interactions, console/CSP errors, keyboard focus, axe accessibility.
// node e2e.js <base> <password> <outdir>
const { chromium, firefox, webkit } = require("playwright");
const fs = require("fs");
const path = require("path");
const AXE = fs.readFileSync(require.resolve("axe-core/axe.min.js"), "utf8");

const [BASE, PW, OUT] = [process.argv[2], process.argv[3], process.argv[4]];
fs.mkdirSync(OUT, { recursive: true });
const results = [];
const check = (area, name, ok, detail = "") => {
  results.push({ area, name, ok: !!ok, detail: String(detail).slice(0, 300) });
  console.log(`${ok ? "PASS" : "FAIL"}  [${area}] ${name}  ${ok ? "" : detail}`);
};
const PAGES = ["/", "/changes/new", "/requests", "/action-items", "/audit", "/search?q=chargeback", "/setup", "/evaluation"];
const WIDTHS = [320, 375, 390, 430, 768, 820, 1024, 1280, 1366, 1440, 1920, 2560];
const SHOTS = { 375: 1, 768: 1, 1366: 1, 1920: 1 };

async function newPage(browser, width, extra = {}) {
  const ctx = await browser.newContext({ viewport: { width, height: 900 }, httpCredentials: { username: "qa", password: PW },
                                         ...extra });
  const page = await ctx.newPage();
  page.problems = [];
  page.on("console", (m) => { if (m.type() === "error") page.problems.push("console: " + m.text()); });
  page.on("pageerror", (e) => page.problems.push("js: " + e.message));
  page.on("response", (r) => { if (r.status() >= 400 && r.status() !== 401 && !r.url().includes("/nope")) page.problems.push(r.status() + " " + r.url()); });
  return { ctx, page };
}

async function responsive(name, browser) {
  for (const width of WIDTHS) {
    const { ctx, page } = await newPage(browser, width);
    for (const p of PAGES) {
      await page.goto(BASE + p, { waitUntil: "networkidle" });
      const m = await page.evaluate(() => {
        const doc = document.documentElement;
        const clipped = (el) => { for (let a = el.parentElement; a && a !== document.body; a = a.parentElement) {
          if (["auto", "scroll", "hidden"].includes(getComputedStyle(a).overflowX)) return true; } return false; };
        const over = [...document.querySelectorAll("body *")].filter((el) => {
          const r = el.getBoundingClientRect();
          return r.width > 0 && r.right > doc.clientWidth + 1 && getComputedStyle(el).position !== "fixed"
                 && !el.closest(".sidebar") && !el.closest("[hidden]") && !clipped(el);
        }).slice(0, 3).map((el) => el.tagName + "." + el.className);
        return { scroll: doc.scrollWidth - doc.clientWidth, over, h1: !!document.querySelector("h1"),
                 small: [...document.querySelectorAll("body *")].some((el) => el.childNodes.length && el.offsetParent &&
                   [...el.childNodes].some((n) => n.nodeType === 3 && n.textContent.trim()) && parseFloat(getComputedStyle(el).fontSize) < 11) };
      });
      check("responsive", `${name} ${width}px ${p} no horizontal scroll`, m.scroll <= 0 && m.over.length === 0,
            `scroll=${m.scroll} ${m.over.join(",")}`);
      check("responsive", `${name} ${width}px ${p} text >= 11px`, !m.small, "tiny text");
      if (name === "chromium" && SHOTS[width] && ["/", "/requests", "/changes/new", "/setup"].includes(p)) {
        await page.screenshot({ path: path.join(OUT, `${width}${p.replace(/[\/?=]/g, "_")}.png`), fullPage: true });
      }
    }
    check("errors", `${name} ${width}px no console/JS/HTTP errors on all pages`, page.problems.length === 0,
          page.problems.slice(0, 3).join(" | "));
    await ctx.close();
  }
}

async function interactions(name, browser) {
  // Mobile menu
  {
    const { ctx, page } = await newPage(browser, 375);
    await page.goto(BASE + "/", { waitUntil: "networkidle" });
    const sidebar = page.locator(".sidebar");
    const hiddenBefore = await sidebar.evaluate((el) => el.getBoundingClientRect().right <= 0);
    await page.locator(".menu-btn").click();
    await page.waitForTimeout(400);
    const shown = await sidebar.evaluate((el) => el.getBoundingClientRect().left >= 0);
    await page.keyboard.press("Escape"); await page.waitForTimeout(400);
    const closed = await sidebar.evaluate((el) => el.getBoundingClientRect().right <= 0);
    check("navigation", `${name} mobile menu opens and closes (Escape)`, hiddenBefore && shown && closed,
          `${hiddenBefore} ${shown} ${closed}`);
    await page.locator(".menu-btn").click(); await page.waitForTimeout(300);
    await page.locator(".sidebar a[href='/requests']").click(); await page.waitForURL("**/requests");
    check("navigation", `${name} mobile menu link navigates`, page.url().endsWith("/requests"));
    await ctx.close();
  }
  const { ctx, page } = await newPage(browser, 1366);
  // Every sidebar link
  await page.goto(BASE + "/", { waitUntil: "networkidle" });
  const links = await page.locator(".sidebar nav a").evaluateAll((as) => as.map((a) => a.getAttribute("href")));
  for (const href of links) {
    const r = await page.goto(BASE + href); check("navigation", `${name} sidebar link ${href} 200`, r.status() === 200, r.status());
  }
  // Template switcher (auto-submit select, no inline handler)
  await page.goto(BASE + "/requests", { waitUntil: "networkidle" });
  await page.selectOption("[data-testid=template-switcher]", "university"); await page.waitForLoadState("networkidle");
  const uni = await page.locator("[data-testid=template-switcher]").inputValue();
  check("navigation", `${name} organization switcher works`, uni === "university", uni);
  await page.selectOption("[data-testid=template-switcher]", "payments"); await page.waitForLoadState("networkidle");
  // Reviewer switcher
  const opts = await page.locator("select[name=name] option").evaluateAll((o) => o.map((x) => x.value));
  await page.selectOption("select[name=name]", opts[opts.length - 1]); await page.waitForLoadState("networkidle");
  check("navigation", `${name} reviewer switcher works`, (await page.locator("select[name=name]").inputValue()) === opts[opts.length - 1]);
  // Table filters
  await page.goto(BASE + "/requests", { waitUntil: "networkidle" });
  const visible = () => page.locator("#request-table tbody tr[data-status]:visible").count();
  const all = await visible();
  await page.click("[data-table-filter=request-table] button[data-status=open]");
  const open = await visible();
  await page.fill("[data-table-filter=request-table] input[type=search]", "zzzz-no-match");
  const none = await visible(); const emptyShown = await page.locator("#request-table-empty").isVisible();
  await page.fill("[data-table-filter=request-table] input[type=search]", "");
  await page.click("[data-table-filter=request-table] button[data-status=all]");
  check("filters", `${name} request filters (all/open/search/empty state)`, all > 0 && open <= all && none === 0 && emptyShown && (await visible()) === all,
        `${all}/${open}/${none}/${emptyShown}`);
  // Investigate -> task page -> reject without comment -> approve
  const rowId = await page.locator("#request-table tbody tr[data-status=open] form").first().getAttribute("action");
  await page.locator(`form[action='${rowId}'] button`).click();
  await page.waitForURL("**/tasks/**");
  await page.waitForSelector(".review", { timeout: 60000 });
  check("requests", `${name} investigate opens task page with review box`, true);
  await page.locator(".review button[data-toggle=reject]").first().click();
  await page.locator(".review .reject-form button[data-decision=reject]").first().click();
  const err = await page.locator(".review-error").first().textContent();
  check("review", `${name} reject without comment shows message`, /comment/i.test(err || ""), err);
  await page.locator(".review button[data-decision=approve]").first().click();
  await page.waitForLoadState("networkidle"); await page.waitForTimeout(800);
  const status = await page.locator("#task-status").textContent();
  check("review", `${name} approve closes task (Approved badge)`, /approved/i.test(status), status);
  // Change: analyze -> task page -> edit + approve, or close summary
  await page.goto(BASE + "/changes/new", { waitUntil: "networkidle" });
  await page.locator("#change-table tbody form button").first().click();
  await page.waitForURL("**/tasks/**");
  await page.waitForSelector("#task-status", { timeout: 60000 });
  check("changes", `${name} analyze opens change task`, true);
  // Paste form: empty -> error
  await page.goto(BASE + "/changes/new#paste", { waitUntil: "networkidle" });
  const pasteForm = page.locator("#paste form");
  if (await pasteForm.count()) {
    await pasteForm.locator("button[type=submit]").click(); await page.waitForLoadState("networkidle");
    check("changes", `${name} empty paste shows error`, (await page.locator(".notice, .alert, [role=alert]").count()) > 0);
  } else check("changes", `${name} paste form present`, false, "no #paste form");
  // Search form
  await page.goto(BASE + "/search", { waitUntil: "networkidle" });
  await page.fill("main input[name=q]", "refund deadline");
  await Promise.all([page.waitForURL("**/search?q=refund*"), page.keyboard.press("Enter")]);
  check("search", `${name} search form shows results`, (await page.locator("main").textContent()).length > 500 && page.url().includes("q=refund"));
  // Top search box
  await page.fill(".topsearch input", "chargeback");
  await Promise.all([page.waitForURL("**/search?q=chargeback*"), page.keyboard.press("Enter")]);
  check("search", `${name} header search works`, page.url().includes("/search?q=chargeback"));
  // Audit filter
  await page.goto(BASE + "/audit", { waitUntil: "networkidle" });
  check("audit", `${name} audit log lists events`, (await page.locator("table tbody tr").count()) > 0);
  // Setup rebuild button (moved from inline script to ui.js)
  if (name === "chromium") {
    await page.goto(BASE + "/setup", { waitUntil: "networkidle" });
    await page.click("#rebuild");
    await page.locator("#rebuild-status", { hasText: /Done:|Failed:/ }).waitFor({ timeout: 120000 });
    const txt = await page.locator("#rebuild-status").textContent();
    check("setup", `${name} rebuild index button works`, txt.startsWith("Done:"), txt);
  }
  // Keyboard: skip to first focusable and see a visible focus ring
  await page.goto(BASE + "/requests", { waitUntil: "networkidle" });
  let ring = false; let reached = [];
  for (let i = 0; i < 6; i++) {
    await page.keyboard.press("Tab");
    const f = await page.evaluate(() => { const e = document.activeElement; const s = getComputedStyle(e);
      return { tag: e.tagName, ring: (s.outlineStyle !== "none" && parseFloat(s.outlineWidth) > 0) || s.boxShadow !== "none" }; });
    reached.push(f.tag); ring = ring || f.ring;
  }
  check("a11y", `${name} keyboard Tab reaches controls with visible focus`, ring && reached.some((t) => ["A", "BUTTON", "INPUT", "SELECT"].includes(t)), reached.join(","));
  check("errors", `${name} no console/JS errors during interactions`, page.problems.filter((p) => !p.includes(" 400 ") && !p.includes("/review")).length === 0,
        page.problems.slice(0, 4).join(" | "));
  await ctx.close();
}

async function a11y(browser) {
  const { ctx, page } = await newPage(browser, 1366);
  const pages = [...PAGES];
  await page.goto(BASE + "/", { waitUntil: "networkidle" });
  const taskHref = await page.locator("a[href^='/tasks/']").first().getAttribute("href").catch(() => null);
  if (taskHref) pages.push(taskHref);
  const all = {};
  for (const p of pages) {
    await page.goto(BASE + p, { waitUntil: "networkidle" });
    await page.addScriptTag({ content: AXE }).catch(() => page.evaluate(AXE));
    const res = await page.evaluate(async () => (await axe.run(document, { runOnly: ["wcag2a", "wcag2aa", "wcag21a", "wcag21aa", "wcag22aa", "best-practice"] })).violations
      .map((v) => ({ id: v.id, impact: v.impact, n: v.nodes.length, sample: v.nodes[0].target.join(" ") })));
    all[p] = res;
    const serious = res.filter((v) => ["serious", "critical"].includes(v.impact));
    check("a11y", `axe ${p} no serious/critical violations`, serious.length === 0, serious.map((v) => `${v.id}(${v.n}) ${v.sample}`).join("; "));
    check("a11y", `axe ${p} no moderate/minor violations`, res.length === serious.length, res.filter((v) => !serious.includes(v)).map((v) => `${v.id}(${v.n}) ${v.sample}`).join("; "));
  }
  fs.writeFileSync(path.join(OUT, "axe.json"), JSON.stringify(all, null, 1));
  // Dark mode: page must stay readable (explicit background, text colour differs)
  const { ctx: dctx, page: dp } = await newPage(browser, 1366, { colorScheme: "dark" });
  await dp.goto(BASE + "/requests", { waitUntil: "networkidle" });
  const c = await dp.evaluate(() => { const s = getComputedStyle(document.body); return [s.backgroundColor, s.color]; });
  check("ui", "dark-mode OS setting: page keeps explicit readable colours", c[0] !== "rgba(0, 0, 0, 0)" && c[0] !== c[1], c.join(" / "));
  await dp.screenshot({ path: path.join(OUT, "dark_requests.png") });
  await dctx.close(); await ctx.close();
}

(async () => {
  const engines = { chromium: () => chromium.launch({ channel: "msedge" }), firefox: () => firefox.launch(), webkit: () => webkit.launch() };
  for (const [name, launch] of Object.entries(engines)) {
    let browser;
    try { browser = await launch(); } catch (e) { check("compat", `${name} launch`, false, e.message); continue; }
    try {
      await responsive(name, browser);
      await interactions(name, browser);
      if (name === "chromium") await a11y(browser);
    } catch (e) { check("compat", `${name} suite crashed`, false, e.message.split("\n")[0]); }
    await browser.close();
  }
  const pass = results.filter((r) => r.ok).length;
  console.log(`\nTOTAL ${results.length}  PASS ${pass}  FAIL ${results.length - pass}`);
  fs.writeFileSync(path.join(OUT, "e2e_results.json"), JSON.stringify(results, null, 1));
})();

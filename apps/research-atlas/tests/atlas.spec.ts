import { test, expect, type Page } from '@playwright/test';
import AxeBuilder from '@axe-core/playwright';
import { mkdirSync, readFileSync } from 'node:fs';
import { resolve } from 'node:path';
const routes = [
  ['/', /What if/], ['/journey', /A journey/], ['/experiment/1', /Can causal relationships reveal time/],
  ['/experiment/2', /Can causal relationships reveal dimensions/], ['/experiment/3', /Can fake universes/],
  ['/experiment/4', /Does local structure/], ['/experiment/5', /Can geometry emerge/],
  ['/evidence', /actually disprove/], ['/data', /Explore the evidence/], ['/learn', /Build your intuition/], ['/sources', /Trace every claim/],
] as const;
async function goto(page: Page, path: string) {
  const response = await page.goto(`./#${path}`);
  // Hash-only transitions have no new document response.
  if (response) expect(response.ok()).toBeTruthy();
  await expect(page.locator('main h1')).toBeVisible();
  await expect(page.getByText('Loading the archived evidence…', { exact: true })).toHaveCount(0);
}
async function setRange(page: Page, label: string, value: number) {
  const slider = page.getByLabel(label);
  const limits = await slider.evaluate(el => ({ min: +(el as HTMLInputElement).min, step: +(el as HTMLInputElement).step || 1 }));
  await slider.focus(); await slider.press('Home');
  for (let i = 0; i < Math.round((value - limits.min) / limits.step); i++) await slider.press('ArrowRight');
}
async function noOverflow(page: Page) { expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth + 1)).toBeTruthy(); }
async function screenshot(page: Page, name: string) {
  mkdirSync(resolve('docs/screenshots'), { recursive: true });
  await page.evaluate(() => { (document.activeElement as HTMLElement)?.blur(); window.scrollTo({ top: 0, behavior: 'instant' }); });
  await page.screenshot({ path: resolve(`docs/screenshots/${name}.png`), fullPage: true, animations: 'disabled' });
}
for (const [route, heading] of routes) {
  test(`accessible responsive route: ${route}`, async ({ page }, testInfo) => {
    const errors: string[] = [];
    page.on('pageerror', error => errors.push(error.message));
    await goto(page, route);
    await expect(page.getByRole('heading', { level: 1 })).toHaveText(heading);
    await noOverflow(page);
    const accessibility = await new AxeBuilder({ page }).withTags(['wcag2a', 'wcag2aa', 'wcag21aa']).analyze();
    expect(accessibility.violations, JSON.stringify(accessibility.violations.map(v => ({ id: v.id, help: v.help, nodes: v.nodes.map(n => ({ target: n.target, summary: n.failureSummary })) })), null, 2)).toEqual([]);
    expect(errors).toEqual([]);
    if (route === '/') await screenshot(page, `${testInfo.project.name}-home`);
    if (testInfo.project.name === 'desktop' && route === '/evidence') await screenshot(page, 'desktop-evidence');
    if (testInfo.project.name === 'desktop' && route === '/experiment/5') {
      for (let i = 1; i < 24; i++) await page.getByRole('button', { name: '+ One event' }).click();
      await screenshot(page, 'desktop-growth');
    }
  });
}
test('complete narrative navigation and materially different explanation levels', async ({ page }, testInfo) => {
  await goto(page, '/');
  await page.getByRole('button', { name: 'Micro', exact: true }).click();
  await expect(page.getByText('SPECULATIVE DEPICTION', { exact: true })).toBeVisible();
  await page.getByRole('button', { name: 'Water', exact: true }).click();
  await expect(page.getByText(/Molecules and their interactions/)).toBeVisible();
  await page.getByRole('link', { name: 'Follow the research' }).click();
  await expect(page).toHaveURL(/#\/journey/);
  await page.getByRole('link', { name: 'Open experiment', exact: true }).first().click();
  const original = await page.getByTestId('level-explanation').innerText();
  await page.getByRole('button', { name: 'researcher', exact: true }).click();
  await expect(page.getByTestId('level-explanation')).not.toHaveText(original);
  await expect(page.locator('.technical-section details').first()).toHaveAttribute('open', '');
  for (const n of [2, 3, 4, 5]) {
    await page.getByRole('navigation', { name: 'Five experiments' }).getByRole('link').nth(n - 1).click();
    await expect(page).toHaveURL(new RegExp(`#/experiment/${n}$`));
    await expect(page.getByRole('heading', { level: 1 })).toBeVisible();
  }
  await page.locator('.next-experiment').getByRole('link', { name: 'The evidence map' }).click();
  await expect(page.getByRole('heading', { level: 1 })).toContainText('actually disprove');
  if (testInfo.project.name === 'mobile') {
    await page.getByRole('button', { name: 'Open navigation' }).click();
    await expect(page.getByRole('dialog')).toBeVisible();
    await page.getByRole('navigation', { name: 'Mobile navigation' }).getByRole('link', { name: 'Data explorer' }).click();
    await expect(page.getByRole('dialog')).not.toBeVisible();
  } else await page.getByRole('navigation', { name: 'Main navigation' }).getByRole('link', { name: 'Data explorer' }).click();
  await expect(page).toHaveURL(/#\/data/);
});
test('five miniature experiments respond to real inputs', async ({ page }) => {
  await goto(page, '/experiment/1');
  await setRange(page, 'Sampling density', 128);
  await expect(page.getByText('Poisson mean λ = ρ/2 = 64')).toBeVisible();
  await page.getByLabel('Show generating coordinates').uncheck();
  await expect(page.getByText(/ABSTRACT ORDER LAYOUT/)).toBeVisible();
  await page.getByLabel('Time model').selectOption('antichain');
  await expect(page.getByText('Not physical', { exact: true })).toBeVisible();
  await goto(page, '/experiment/2');
  await page.getByRole('button', { name: '3 dimensions', exact: true }).click();
  await page.getByRole('button', { name: 'Reveal the model' }).click();
  await expect(page.locator('.lab-reveal')).toContainText('Minkowski sampling');
  await page.getByLabel('Reveal a time / first-space-coordinate projection').check();
  await expect(page.getByText(/Projection only/)).toBeVisible();
  await goto(page, '/experiment/3');
  await page.getByLabel('Adversarial family').selectOption('rank');
  await expect(page.getByText(/positive equivalence control/)).toBeVisible();
  await page.getByRole('button', { name: 'F Interval abundance' }).click();
  await expect(page.getByText(/Different orders can still share that complete histogram/)).toBeVisible();
  await goto(page, '/experiment/4');
  await page.getByLabel('Show the disconnected interior').check();
  await expect(page.locator('.lab-stat').filter({ hasText: 'Induced 2+2 count' }).locator('strong')).toHaveText('16');
  await page.getByLabel('Exact counterexample').selectOption('extended');
  await expect(page.locator('.lab-stat').filter({ hasText: 'Induced 2+2 count' }).locator('strong')).toHaveText('42');
  await page.getByLabel('Sampling region').selectOption('box');
  await expect(page.getByText(/A spatial box can clip/)).toBeVisible();
  await goto(page, '/experiment/5');
  await page.getByRole('button', { name: '+ One event' }).click();
  await expect(page.getByText('2 / 48', { exact: true })).toBeVisible();
  await page.getByRole('button', { name: 'Auto-play growth' }).click();
  await expect(page.getByText('3 / 48', { exact: true })).toBeVisible();
  await page.getByRole('button', { name: 'Pause growth' }).click();
  await page.getByRole('button', { name: 'Reset history' }).click();
  await expect(page.getByText('1 / 48', { exact: true })).toBeVisible();
  await page.getByLabel('Growth probability').selectOption('0.3');
  await page.getByRole('button', { name: '+ One event' }).click();
  await page.getByLabel('Inspect growth event').selectOption('1');
  await expect(page.getByText(/Event 2 selected/)).toBeVisible();
});
test('filters, chart points, numerical tables and full-precision exports', async ({ page }) => {
  await goto(page, '/data');
  await page.getByRole('combobox', { name: 'Experiment', exact: true }).selectOption('5');
  await page.getByRole('combobox', { name: 'Archived dataset', exact: true }).selectOption('growth-global');
  const family = page.getByLabel('family', { exact: true });
  await expect(family).toBeVisible();
  const options = await family.locator('option').evaluateAll(nodes => nodes.map(n => ({ value: (n as HTMLOptionElement).value, label: n.textContent })));
  const percolation = options.find(o => /percolation/.test(o.value))?.value;
  expect(percolation).toBeTruthy();
  await family.selectOption(percolation!);
  await page.getByLabel('parameter', { exact: true }).selectOption('0.1');
  const points = page.locator('.scientific-chart circle[role="button"]');
  await expect(points.first()).toBeVisible();
  await points.first().focus();
  await page.keyboard.press('Enter');
  await expect(page.getByText('Selected record', { exact: true })).toBeVisible();
  await page.getByRole('button', { name: 'Numerical table', exact: true }).click();
  await expect(page.getByRole('table')).toBeVisible();
  const downloadPromise = page.waitForEvent('download');
  await page.getByRole('button', { name: 'Export filtered JSON with provenance' }).click();
  const download = await downloadPromise;
  expect(download.suggestedFilename()).toBe('growth-global-filtered.json');
  const exported = JSON.parse(readFileSync((await download.path())!, 'utf8'));
  expect(exported.rows.length).toBeGreaterThan(0);
  expect(exported.rows.every((row: Record<string, unknown>) => row.family === percolation && row.parameter === .1)).toBeTruthy();
  expect(exported.sha256).toMatch(/^[a-f0-9]{64}$/);
  expect(exported.sourceUrl).toMatch(/github.com\/raghammer1\/causal-spacetime-lab\/blob\/[a-f0-9]{40}\//);
  const csvPromise = page.waitForEvent('download');
  await page.getByRole('button', { name: 'Export filtered CSV' }).click();
  const csv = await csvPromise;
  expect(readFileSync((await csv.path())!, 'utf8').split('\r\n').length).toBe(exported.rows.length + 1);
  await page.getByRole('searchbox', { name: 'Find a record' }).fill('no-record-can-match-this-query');
  await expect(page.getByText(/No archived rows match these filters/)).toBeVisible();
  await page.getByRole('button', { name: 'Reset data filters' }).click();
  await expect(page.getByRole('table')).toBeVisible();
  await noOverflow(page);
});
test('evidence scope, archived source links and concept navigation remain explicit', async ({ page }) => {
  await goto(page, '/evidence');
  await page.getByRole('button', { name: /All possible emergent-spacetime theories are impossible/ }).click();
  await expect(page.locator('.claim-detail')).toContainText('Not tested by this lab');
  await expect(page.locator('.claim-detail')).toContainText(/not test|does not|cannot/i);
  await page.getByRole('button', { name: /studied classical growth route/ }).click();
  await expect(page.locator('.claim-detail')).toContainText('Falsified within scope');
  await goto(page, '/sources');
  const sources = await page.locator('main a[href*="github.com/raghammer1/causal-spacetime-lab/blob/"]').evaluateAll(nodes => nodes.map(n => (n as HTMLAnchorElement).href));
  expect(sources.length).toBeGreaterThan(25);
  expect(sources.every(url => /\/blob\/9bc5984c656271c247354e0079fd900702642064\//.test(url))).toBeTruthy();
  await goto(page, '/learn');
  await page.getByRole('button', { name: /Induced 2\+2/ }).click();
  await page.getByLabel('Use 3+1 instead of 2+2').check();
  await expect(page.locator('.lab-stat').filter({ hasText: 'Pattern' }).locator('strong')).toHaveText('3+1');
  await page.getByRole('button', { name: /Why singularities/ }).click();
  await setRange(page, 'Radius relative to event horizon', 1);
  await expect(page.getByText('At horizon', { exact: true })).toBeVisible();
  await expect(page.getByText(/horizon is not a curvature singularity/)).toBeVisible();
});
test('keyboard and reduced-motion journeys have usable focus and no auto-start', async ({ page }, testInfo) => {
  await goto(page, '/');
  await page.locator('.skip-link').focus();
  await page.keyboard.press('Enter');
  await expect(page.locator('main')).toBeFocused();
  expect(await page.evaluate(() => matchMedia('(prefers-reduced-motion: reduce)').matches)).toBeTruthy();
  if (testInfo.project.name === 'mobile') {
    await page.getByRole('button', { name: 'Open navigation' }).focus();
    await page.keyboard.press('Enter');
    await expect(page.getByRole('dialog')).toBeVisible();
    await page.keyboard.press('Escape');
    await expect(page.getByRole('dialog')).not.toBeVisible();
    await expect(page.getByRole('button', { name: 'Open navigation' })).toBeFocused();
  }
  await goto(page, '/experiment/5');
  await expect(page.getByText('1 / 48', { exact: true })).toBeVisible();
  await page.getByRole('button', { name: '+ One event' }).focus();
  await page.keyboard.press('Enter');
  await page.getByRole('button', { name: 'Inspect event 2', exact: true }).focus();
  await page.keyboard.press('Space');
  await expect(page.getByLabel('Inspect growth event')).toHaveValue('1');
  await expect(page.getByRole('button', { name: 'Auto-play growth' })).toBeVisible();
});

test('every archived dataset loads with pinned provenance and a usable data view', async ({ page }) => {
  await goto(page, '/data');
  let visited = 0;
  for (const experiment of ['1', '2', '3', '4', '5']) {
    await page.getByRole('combobox', { name: 'Experiment', exact: true }).selectOption(experiment);
    const selector = page.getByRole('combobox', { name: 'Archived dataset', exact: true });
    const choices = await selector.locator('option').evaluateAll(nodes => nodes.map(n => ({ value: (n as HTMLOptionElement).value, title: n.textContent || '' })));
    for (const choice of choices) {
      await selector.selectOption(choice.value);
      const panel = page.getByRole('region', { name: choice.title, exact: true });
      await expect(panel).toBeVisible();
      await expect(panel.getByRole('link', { name: 'Exact source' })).toHaveAttribute('href', /\/blob\/9bc5984c656271c247354e0079fd900702642064\//);
      await expect(panel.locator('.record-count')).toContainText(/\d[\d,]* \/ \d[\d,]* records/);
      await panel.getByRole('button', { name: 'Numerical table', exact: true }).click();
      await expect(panel.getByRole('table')).toBeVisible();
      await noOverflow(page);
      visited++;
    }
  }
  expect(visited).toBeGreaterThanOrEqual(13);
});

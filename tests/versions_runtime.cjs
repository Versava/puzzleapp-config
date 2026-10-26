'use strict';
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const test = require('node:test');

const script = fs.readFileSync(process.argv[2], 'utf8');
const fallbackHtml = fs.readFileSync(process.argv[3], 'utf8');
const clone = value => JSON.parse(JSON.stringify(value));
const unescape = value => value.replace(/&quot;/g, '"').replace(/&#x27;/g, "'")
  .replace(/&lt;/g, '<').replace(/&gt;/g, '>').replace(/&amp;/g, '&');
const initialAttributes = Object.fromEntries([...fallbackHtml.matchAll(/data-([a-z-]+)="([^"]*)"/g)]
  .map(([, key, value]) => [key.replace(/-([a-z])/g, (_, letter) => letter.toUpperCase()), unescape(value)]));
const baseline = JSON.parse(initialAttributes.releaseSnapshot);
const indexPath = '/releases/index.json', betaPath = '/releases/beta.json', publicPath = '/releases/public.json';
class Element {
  constructor(tag, text = '') { this.tagName = tag; this.textContent = text; this.children = []; this.attributes = {}; }
  append(...children) { this.children.push(...children); }
  setAttribute(name, value) { this.attributes[name] = value; }
  replaceChildren(...children) { this.children = children; this.replacements = (this.replacements || 0) + 1; }
}
const descendants = element => [element, ...element.children.flatMap(descendants)];
const text = element => descendants(element).map(item => item.textContent).filter(Boolean).join(' ');
const advanced = () => {
  const documents = clone(baseline);
  Object.values(documents).forEach(document => document.revision++);
  return documents;
};
async function runtime(documents = baseline, options = {}) {
  const target = new Element('div', 'GENERATED FALLBACK');
  target.dataset = {...initialAttributes, ...options.dataset};
  const state = {target, documents: clone(documents), raw: {}, requests: [], refresh: null};
  const document = {
    hidden: false, getElementById: () => target,
    createElement: tag => new Element(tag), createDocumentFragment: () => new Element('fragment'),
    addEventListener: (_, callback) => { state.visibilityChanged = callback; },
  };
  vm.runInNewContext(script, {
    URL, TextEncoder, AbortController, setTimeout, clearTimeout,
    setInterval: callback => { state.refresh = callback; }, document,
    fetch: async (path, request) => {
      state.requests.push({path, request});
      return {ok: options.ok !== false, text: async () => state.raw[path] ?? JSON.stringify(state.documents[path])};
    },
  });
  await new Promise(resolve => setImmediate(resolve));
  return state;
}
async function refresh(state, documents, raw = {}) {
  state.documents = clone(documents); state.raw = raw;
  await state.refresh();
}

for (const [name, mutate] of [
  ['minimum greater than latest', documents => {
    documents[betaPath].ios.minimumVersion = '9.0.0'; documents[indexPath].beta.minimumVersion = '9.0.0';
  }],
  ['duplicate blocked ranges', documents => {
    const point = documents[betaPath].ios.minimumVersion;
    documents[betaPath].ios.blockedRanges = [
      {fromVersion: point, throughVersion: point, reason: 'security'},
      {fromVersion: point, throughVersion: point, reason: 'compatibility'},
    ];
  }],
  ['overlapping blocked ranges', documents => {
    documents[betaPath].ios.blockedRanges = [
      {fromVersion: '2.0.0', throughVersion: '2.2.0', reason: 'security'},
      {fromVersion: '2.1.0', throughVersion: '2.2.1', reason: 'compatibility'},
    ];
  }],
  ['blocked range includes the latest obtainable version', documents => {
    const latest = documents[betaPath].ios.latestVersion;
    documents[betaPath].ios.blockedRanges = [{fromVersion: latest, throughVersion: latest, reason: 'security'}];
  }],
  ['Public ordinary updates marked required', documents => {
    const item = documents[indexPath].public;
    item.status = 'available';
    documents[publicPath].ios = {latestVersion: item.version, minimumVersion: item.minimumVersion,
      updateUrl: 'https://apps.apple.com/app/id123456789', blockedRanges: [], updatePolicy: 'required'};
  }],
  ['unavailable state with non-null versions', documents => { documents[indexPath].beta.status = 'unavailable'; }],
  ['unavailable state with a non-null minimum', documents => {
    documents[indexPath].beta.status = 'unavailable'; documents[indexPath].beta.version = null;
  }],
  ['testing state with null versions', documents => {
    documents[indexPath].beta.version = null; documents[indexPath].beta.minimumVersion = null;
  }],
  ['wrong track', documents => { documents[betaPath].track = 'public'; }],
  ['unknown policy field', documents => { documents[betaPath].ios.surprise = true; }],
  ['unknown index field', documents => { documents[indexPath].beta.surprise = true; }],
  ['build authority in a version-only range', documents => {
    documents[betaPath].ios.blockedRanges = [{fromVersion: '2.0.0', throughVersion: '2.0.1', reason: 'security', fromBuild: 4}];
  }],
  ['untrusted update URL', documents => { documents[betaPath].ios.updateUrl = 'https://example.invalid/join/AbCdEf12'; }],
  ['malformed Android channel', documents => { documents[betaPath].android = {latestVersion: '2.3.0'}; }],
  ['version component exceeds the supported integer range', documents => {
    documents[betaPath].ios.latestVersion = '2147483648.0.0'; documents[indexPath].beta.version = '2147483648.0.0';
  }],
]) {
  test(`invalid ${name} preserves the generated fallback`, async () => {
    const documents = advanced(); mutate(documents);
    const state = await runtime(documents);
    assert.equal(state.target.replacements || 0, 0);
    assert.equal(text(state.target), 'GENERATED FALLBACK');
  });
}

test('first fetch rejects changed content under an already generated revision', async () => {
  const documents = clone(baseline);
  documents[indexPath].revision++;
  documents[indexPath].beta.minimumVersion = '2.2.0'; documents[betaPath].ios.minimumVersion = '2.2.0';
  const state = await runtime(documents);
  assert.equal(state.target.replacements || 0, 0);
});

test('lower revisions cannot replace the generated baseline', async () => {
  const documents = advanced(); documents[betaPath].revision = baseline[betaPath].revision - 1;
  const state = await runtime(documents);
  assert.equal(state.target.replacements || 0, 0);
});

test('equal-revision formatting changes retain the same semantic authority', async () => {
  const state = await runtime();
  await refresh(state, baseline, {[betaPath]: JSON.stringify(baseline[betaPath], null, 2)});
  assert.equal(state.target.replacements, 2);
});

test('JSON-only updates replace old fallback details with a minimal Release-first display', async () => {
  const state = await runtime();
  const documents = advanced();
  documents[betaPath].ios.latestVersion = '9.4.0'; documents[betaPath].ios.minimumVersion = '9.1.0';
  documents[indexPath].beta.version = '9.4.0'; documents[indexPath].beta.minimumVersion = '9.1.0';
  documents[betaPath].ios.blockedRanges = [{fromVersion: '9.2.0', throughVersion: '9.3.0', reason: 'security'}];
  await refresh(state, documents);
  const content = text(state.target), elements = descendants(state.target);
  assert.deepEqual(elements.filter(item => item.tagName === 'h2').map(item => item.textContent), ['Release', 'Beta']);
  assert.deepEqual(elements.filter(item => item.tagName === 'dt').map(item => item.textContent),
    ['Latest version', 'Minimum supported version', 'Latest version', 'Minimum supported version']);
  assert.match(content, /9\.4\.0/); assert.match(content, /9\.1\.0/); assert.match(content, /9\.2\.0 through 9\.3\.0/);
  assert.doesNotMatch(content, /Status|In review|Testing|Policy JSON|Upgrade required|Open App Store|invitation|before continuing/);
  assert.equal(elements.some(item => item.tagName === 'a'), false);
  assert.equal(state.target.replacements, 2);
  assert.match(fallbackHtml, /2\.3\.0/); assert.doesNotMatch(fallbackHtml, /9\.4\.0/);
  for (const request of state.requests) {
    assert.equal(request.path.startsWith('/releases/'), true);
    assert.equal(request.request.cache, 'no-store'); assert.equal(request.request.redirect, 'error');
  }
});

test('higher revisions cannot lower an accepted latest/minimum or unpublish its policy', async () => {
  const state = await runtime();
  for (const documents of [
    (() => { const value = advanced(); value[betaPath].ios.latestVersion = '1.0.0'; value[betaPath].ios.minimumVersion = '1.0.0';
      value[indexPath].beta.version = '1.0.0'; value[indexPath].beta.minimumVersion = '1.0.0'; return value; })(),
    (() => { const value = advanced(); value[betaPath].ios.minimumVersion = '2.0.0'; value[indexPath].beta.minimumVersion = '2.0.0'; return value; })(),
    (() => { const value = advanced(); value[betaPath].ios = null; value[indexPath].beta = {version: null, minimumVersion: null, status: 'unavailable'}; return value; })(),
  ]) {
    await refresh(state, documents);
    assert.equal(state.target.replacements, 1);
  }
});

test('a partially invalid multi-document refresh preserves the last complete display', async () => {
  const state = await runtime();
  const documents = advanced(); documents[indexPath].beta.version = '9.4.0';
  await refresh(state, documents);
  assert.equal(state.target.replacements, 1);
  assert.match(text(state.target), /2\.3\.0/);
  await refresh(state, advanced());
  assert.equal(state.target.replacements, 2);
});

test('duplicate JSON keys and oversized bodies cannot replace the last display', async () => {
  const state = await runtime();
  const documents = advanced(), raw = JSON.stringify(documents[betaPath]);
  await refresh(state, documents, {[betaPath]: raw.replace(/"revision":\d+/, match => `${match},${match}`)});
  assert.equal(state.target.replacements, 1);
  await refresh(state, documents, {[betaPath]: ' '.repeat(16385) + raw});
  assert.equal(state.target.replacements, 1);
});

test('bad generated snapshots and failed requests keep the HTML fallback intact', async () => {
  for (const dataset of [{releaseSnapshot: ''}, {betaRevision: '999'}, {releaseSnapshot: '{'}]) {
    const state = await runtime(baseline, {dataset});
    assert.equal(state.target.replacements || 0, 0); assert.equal(state.requests.length, 0);
  }
  const failed = await runtime(baseline, {ok: false});
  assert.equal(failed.target.replacements || 0, 0);
});

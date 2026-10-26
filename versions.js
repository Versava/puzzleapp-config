(() => {
  'use strict';
  const target = document.getElementById('release-details');
  if (!target) return;
  const paths = ['/releases/index.json', '/releases/beta.json', '/releases/public.json'];
  const maximum = 2147483647;
  const revisions = new Map();
  const floors = new Map([[paths[0], Number(target.dataset.indexRevision)],
    [paths[1], Number(target.dataset.betaRevision)], [paths[2], Number(target.dataset.publicRevision)]]);
  let pending = false;
  const record = value => value !== null && typeof value === 'object' && !Array.isArray(value);
  function exact(value, names) {
    if (!record(value) || Object.keys(value).length !== names.length || names.some(name => !Object.hasOwn(value, name))) {
      throw new Error('Invalid release fields');
    }
  }
  function number(value) {
    if (!Number.isInteger(value) || value < 1 || value > maximum) throw new Error('Invalid revision');
    return value;
  }
  function version(value) {
    if (typeof value !== 'string' || !/^(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)$/.test(value)) throw new Error('Invalid version');
    const parts = value.split('.').map(Number);
    if (parts.some(part => part > maximum)) throw new Error('Invalid version');
    return parts;
  }
  function compare(left, right) {
    const a = version(left), b = version(right);
    for (let index = 0; index < a.length; index++) if (a[index] !== b[index]) return a[index] < b[index] ? -1 : 1;
    return 0;
  }
  const canonical = value => Array.isArray(value) ? `[${value.map(canonical).join(',')}]` : record(value) ?
    `{${Object.keys(value).sort().map(key => `${JSON.stringify(key)}:${canonical(value[key])}`).join(',')}}` : JSON.stringify(value);
  function uniqueJson(text) {
    const parsed = JSON.parse(text);
    let offset = 0;
    const whitespace = () => { while (/\s/.test(text[offset] || '!')) offset++; };
    const string = () => {
      const start = offset++;
      while (text[offset] !== '"') { if (text[offset] === '\\') offset++; offset++; }
      offset++;
      return JSON.parse(text.slice(start, offset));
    };
    function value(depth) {
      if (depth > 32) throw new Error('Release config is too deeply nested');
      whitespace();
      if (text[offset] === '{') {
        offset++; whitespace();
        const seen = new Set();
        if (text[offset] === '}') { offset++; return; }
        for (;;) {
          whitespace(); const key = string();
          if (seen.has(key)) throw new Error('Duplicate release key');
          seen.add(key); whitespace(); offset++; value(depth + 1); whitespace();
          if (text[offset++] === '}') return;
        }
      }
      if (text[offset] === '[') {
        offset++; whitespace();
        if (text[offset] === ']') { offset++; return; }
        for (;;) { value(depth + 1); whitespace(); if (text[offset++] === ']') return; }
      }
      if (text[offset] === '"') { string(); return; }
      while (offset < text.length && !/[\s,}\]]/.test(text[offset])) offset++;
    }
    value(0);
    return parsed;
  }
  function updateUrl(value, track) {
    if (typeof value !== 'string') throw new Error('Invalid update URL');
    const url = new URL(value);
    const publicTrack = track === 'public';
    const path = publicTrack ? /^\/(?:[a-z]{2}\/)?app\/(?:[a-zA-Z0-9-]+\/)?id[0-9]+$/ : /^\/join\/[A-Za-z0-9]{8}$/;
    if (url.protocol !== 'https:' || url.hostname !== (publicTrack ? 'apps.apple.com' : 'testflight.apple.com') ||
        url.href !== value || url.username || url.password || url.port || url.search || url.hash || !path.test(url.pathname)) {
      throw new Error('Invalid update URL');
    }
  }
  function channel(value, track) {
    if (value === null) return;
    exact(value, ['latestVersion', 'minimumVersion', 'updateUrl', 'blockedRanges', 'updatePolicy']);
    if (compare(value.minimumVersion, value.latestVersion) > 0 || value.updatePolicy !== (track === 'public' ? 'optional' : 'required') ||
        !Array.isArray(value.blockedRanges) || value.blockedRanges.length > 32) throw new Error('Invalid version-only policy');
    updateUrl(value.updateUrl, track);
    let previous;
    for (const range of value.blockedRanges) {
      exact(range, ['fromVersion', 'throughVersion', 'reason']);
      if (compare(range.fromVersion, range.throughVersion) > 0 || compare(range.throughVersion, value.latestVersion) >= 0 ||
          previous !== undefined && compare(range.fromVersion, previous) <= 0 || !['security', 'compatibility'].includes(range.reason)) {
        throw new Error('Invalid blocked range');
      }
      previous = range.throughVersion;
    }
  }
  function policy(value, track) {
    exact(value, ['schemaVersion', 'revision', 'track', 'ios', 'android']);
    if (value.schemaVersion !== 3 || value.track !== track) throw new Error('Invalid release track');
    number(value.revision); channel(value.ios, track); channel(value.android, track);
  }
  function validate(documents) {
    const [index, beta, publicPolicy] = documents;
    exact(index, ['schemaVersion', 'revision', 'beta', 'public']);
    if (index.schemaVersion !== 1) throw new Error('Invalid release index');
    number(index.revision); policy(beta, 'beta'); policy(publicPolicy, 'public');
    for (const [track, selected] of [['beta', beta], ['public', publicPolicy]]) {
      const item = index[track];
      exact(item, ['version', 'minimumVersion', 'status']);
      const statuses = track === 'public' ? ['inReview', 'available', 'unavailable'] : ['testing', 'unavailable'];
      if (!statuses.includes(item.status)) throw new Error('Invalid release status');
      if (item.status === 'unavailable') {
        if (item.version !== null || item.minimumVersion !== null) throw new Error('Unavailable release advertises versions');
      } else if (compare(item.minimumVersion, item.version) > 0) throw new Error('Invalid release index boundary');
      if (['testing', 'available'].includes(item.status) && (!selected.ios || item.version !== selected.ios.latestVersion ||
          item.minimumVersion !== selected.ios.minimumVersion)) throw new Error('Release is not obtainable');
    }
  }
  function acceptsSuccessor(previous, following, path) {
    if (!previous) return;
    if (following.revision < previous.revision || following.revision === previous.revision && canonical(following) !== canonical(previous)) {
      throw new Error('Stale release config');
    }
    const entries = path === paths[0] ? ['beta', 'public'] : ['ios', 'android'];
    for (const name of entries) {
      const before = previous[name], after = following[name];
      if (path === paths[0]) {
        if (before.version !== null && (after.version === null || compare(after.version, before.version) < 0 ||
            compare(after.minimumVersion, before.minimumVersion) < 0)) throw new Error('Release index moved backwards');
      } else if (before !== null && (after === null || compare(after.latestVersion, before.latestVersion) < 0 ||
          compare(after.minimumVersion, before.minimumVersion) < 0)) throw new Error('Release policy moved backwards');
    }
  }
  // Generated snapshots establish content authority for the first fetch too.
  // An older cached HTML page without this baseline safely retains its fallback.
  try {
    const snapshot = JSON.parse(target.dataset.releaseSnapshot);
    exact(snapshot, paths);
    const documents = paths.map(path => snapshot[path]);
    validate(documents);
    documents.forEach((value, index) => {
      if (number(floors.get(paths[index])) !== value.revision) throw new Error('Invalid generated baseline');
      revisions.set(paths[index], value);
    });
  } catch (_) { return; }
  function node(tag, text, className) {
    const result = document.createElement(tag);
    if (text !== undefined) result.textContent = text;
    if (className) result.className = className;
    return result;
  }
  function fact(list, name, value) {
    const row = node('div'); row.append(node('dt', name), node('dd', value)); list.append(row);
  }
  async function read(path, signal) {
    const response = await fetch(path, {cache: 'no-store', redirect: 'error', signal});
    if (!response.ok) throw new Error('Release config unavailable');
    const text = await response.text();
    if (new TextEncoder().encode(text).length > 16384) throw new Error('Release config too large');
    const value = uniqueJson(text);
    if (!record(value) || number(value.revision) < floors.get(path)) throw new Error('Stale release config');
    return value;
  }
  function section(track, item, selected) {
    const channel = selected.ios;
    const result = node('section', undefined, 'support-section');
    const heading = node('h2', track === 'public' ? 'Release' : 'Beta');
    heading.id = track === 'public' ? 'release-versions' : 'beta-versions';
    result.setAttribute('aria-labelledby', heading.id); result.append(heading);
    const card = node('section', undefined, 'contact-card version-card');
    const facts = node('dl', undefined, 'version-facts');
    fact(facts, 'Latest version', (channel ? channel.latestVersion : item.version) || 'Not listed');
    fact(facts, 'Minimum supported version', (channel ? channel.minimumVersion : item.minimumVersion) || 'Not listed');
    card.append(facts);
    if (channel && channel.blockedRanges.length) {
      card.append(node('h4', 'Blocked versions'));
      const list = node('ul');
      for (const range of channel.blockedRanges) {
        list.append(node('li', `${range.fromVersion} through ${range.throughVersion}, inclusive — ${range.reason === 'security' ? 'Security' : 'Compatibility'}`));
      }
      card.append(list);
    }
    result.append(card); return result;
  }
  async function refresh() {
    if (pending || document.hidden) return;
    pending = true;
    const abort = new AbortController();
    const timer = setTimeout(() => abort.abort(), 8000);
    try {
      const documents = await Promise.all(paths.map(path => read(path, abort.signal)));
      validate(documents);
      documents.forEach((value, index) => acceptsSuccessor(revisions.get(paths[index]), value, paths[index]));
      const [index, beta, publicPolicy] = documents;
      const fragment = document.createDocumentFragment();
      fragment.append(section('public', index.public, publicPolicy), section('beta', index.beta, beta));
      target.replaceChildren(fragment);
      documents.forEach((value, index) => revisions.set(paths[index], value));
    } catch (_) {
      // Keep the validated generated page or most recent successful refresh.
    } finally { clearTimeout(timer); pending = false; }
  }
  refresh();
  setInterval(refresh, 60000);
  document.addEventListener('visibilitychange', refresh);
})();

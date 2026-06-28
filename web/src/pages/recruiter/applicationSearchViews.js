export const APPLICATION_FILTER_DEFAULTS = {
  search: '',
  status: 'all',
  fit: 'all',
  sort: 'newest',
};

export const APPLICATION_FIT_FILTERS = {
  all: {},
  strong: { min_score: 75 },
  possible: { min_score: 50, max_score: 74.99 },
  low: { max_score: 49.99 },
  unscored: {},
};

const storageKey = (scope) => `hrrecruit.recruiter.savedViews.${scope}`;

export const buildApplicationQueryParams = (filters = {}) => {
  const merged = { ...APPLICATION_FILTER_DEFAULTS, ...filters };
  const params = {};
  if (merged.search?.trim()) params.search = merged.search.trim();
  if (merged.status && merged.status !== 'all') params.status = merged.status;
  if (merged.sort && merged.sort !== 'newest') params.sort = merged.sort;
  const fitParams = APPLICATION_FIT_FILTERS[merged.fit] ?? {};
  Object.assign(params, fitParams);
  return params;
};

export const describeApplicationFilters = (filters = {}) => {
  const merged = { ...APPLICATION_FILTER_DEFAULTS, ...filters };
  const active = [];
  if (merged.search?.trim()) active.push(`Search: ${merged.search.trim()}`);
  if (merged.status !== 'all') active.push(`Status: ${merged.status.replaceAll('_', ' ')}`);
  if (merged.fit !== 'all') active.push(`AI fit: ${merged.fit}`);
  if (merged.sort !== 'newest') active.push(`Sort: ${merged.sort.replaceAll('_', ' ')}`);
  return active;
};

export const loadSavedApplicationViews = (scope) => {
  try {
    const parsed = JSON.parse(window.localStorage.getItem(storageKey(scope)) || '[]');
    return Array.isArray(parsed) ? parsed : [];
  } catch (_error) {
    return [];
  }
};

export const saveApplicationView = (scope, name, filters) => {
  const trimmedName = name.trim();
  if (!trimmedName) return loadSavedApplicationViews(scope);
  const existing = loadSavedApplicationViews(scope).filter((view) => view.name !== trimmedName);
  const nextViews = [{ name: trimmedName, filters: { ...APPLICATION_FILTER_DEFAULTS, ...filters } }, ...existing].slice(0, 8);
  window.localStorage.setItem(storageKey(scope), JSON.stringify(nextViews));
  return nextViews;
};

export const deleteApplicationView = (scope, name) => {
  const nextViews = loadSavedApplicationViews(scope).filter((view) => view.name !== name);
  window.localStorage.setItem(storageKey(scope), JSON.stringify(nextViews));
  return nextViews;
};

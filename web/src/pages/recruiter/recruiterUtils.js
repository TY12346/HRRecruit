export const formatDateTime = (value) => {
  if (!value) return '—';
  return new Intl.DateTimeFormat(undefined, {
    dateStyle: 'medium',
    timeStyle: 'short',
  }).format(new Date(value));
};

export const formatDate = (value) => {
  if (!value) return '';
  return new Date(value).toISOString().slice(0, 16);
};

export const titleize = (value) => {
  if (!value) return '—';
  return String(value)
    .replaceAll('_', ' ')
    .replace(/\b\w/g, (letter) => letter.toUpperCase());
};

export const getApiErrorMessage = (error, fallback = 'Something went wrong.') => {
  const data = error?.response?.data;
  if (!data) return error?.message ?? fallback;
  if (typeof data === 'string') return data;
  if (data.detail) return data.detail;
  const [firstKey] = Object.keys(data);
  const firstValue = data[firstKey];
  if (Array.isArray(firstValue)) return `${titleize(firstKey)}: ${firstValue.join(' ')}`;
  if (typeof firstValue === 'string') return `${titleize(firstKey)}: ${firstValue}`;
  return fallback;
};

export const scoreText = (value) => (value === null || value === undefined || value === '' ? 'Not screened' : `${value}`);

export const applicationName = (application) => application?.applicant?.full_name ?? application?.applicant_profile?.full_name ?? 'Candidate';

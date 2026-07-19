export function getApiErrorMessage(error, fallback = 'Something went wrong. Please try again.') {
  const data = error.response?.data;

  if (!data) {
    return fallback;
  }

  if (typeof data.detail === 'string') {
    if (Array.isArray(data.blockers) && data.blockers.length > 0) {
      return `${data.detail} ${data.blockers.join(' ')}`;
    }
    return data.detail;
  }

  if (typeof data.message === 'string') {
    return data.message;
  }

  if (typeof data === 'string') {
    return data;
  }

  if (typeof data === 'object') {
    return Object.entries(data)
      .map(([field, messages]) => {
        if (Array.isArray(messages)) {
          return `${field}: ${messages.join(' ')}`;
        }
        if (typeof messages === 'object' && messages !== null) {
          return `${field}: ${JSON.stringify(messages)}`;
        }
        return `${field}: ${messages}`;
      })
      .join(' ');
  }

  return fallback;
}

export function formatDateTime(value) {
  if (!value) {
    return '—';
  }
  return new Intl.DateTimeFormat(undefined, {
    dateStyle: 'medium',
    timeStyle: 'short',
  }).format(new Date(value));
}

export function formatCurrency(value, currency = 'MYR') {
  const numericValue = Number(value ?? 0);
  return new Intl.NumberFormat(undefined, {
    style: 'currency',
    currency,
  }).format(numericValue);
}

export function titleize(value) {
  if (!value) {
    return '—';
  }
  return String(value)
    .replaceAll('_', ' ')
    .replace(/\b\w/g, (character) => character.toUpperCase());
}

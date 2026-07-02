export function formatJobDescriptionText(value) {
  if (!value) {
    return '';
  }

  return String(value)
    .replace(/\r\n?/g, '\n')
    .replace(/\s+(#{1,6}\s+)/g, '\n\n$1')
    .replace(/([^\n])\s+(\*\s+[A-Z0-9])/g, '$1\n$2')
    .replace(/([^\n])\s+([•-]\s+[A-Z0-9])/g, '$1\n$2')
    .replace(/\n{3,}/g, '\n\n')
    .trim();
}

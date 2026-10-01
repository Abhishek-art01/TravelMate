export function formatDate(value: Date | string, locale = 'en-IN') {
  return new Intl.DateTimeFormat(locale, { dateStyle: 'medium' }).format(new Date(value))
}

export function formatNumber(value: number, locale = 'en-IN') {
  return new Intl.NumberFormat(locale).format(value)
}

export function getTimeZone() {
  return Intl.DateTimeFormat().resolvedOptions().timeZone
}

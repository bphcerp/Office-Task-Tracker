/** Shared formatting helpers for task views. */

export function statusTone(status: string): 'todo' | 'progress' | 'done' {
  const normalized = status.toLowerCase().replace(/[\s-]+/g, '_');
  if (normalized === 'done' || normalized === 'completed' || normalized === 'complete') {
    return 'done';
  }
  if (
    normalized === 'in_progress' ||
    normalized === 'doing' ||
    normalized === 'active' ||
    normalized === 'working'
  ) {
    return 'progress';
  }
  return 'todo';
}

export function formatStatusLabel(status: string): string {
  return status.replace(/[_-]+/g, ' ');
}

export function formatDateTime(value: string | null | undefined): string {
  if (!value) return '—';
  return new Date(value).toLocaleString(undefined, {
    dateStyle: 'medium',
    timeStyle: 'short',
  });
}

export function formatRelativeTime(value: string | null | undefined): string {
  if (!value) return '';
  const date = new Date(value);
  const diffMs = date.getTime() - Date.now();
  const absSec = Math.round(Math.abs(diffMs) / 1000);
  const rtf = new Intl.RelativeTimeFormat(undefined, { numeric: 'auto' });

  if (absSec < 60) return rtf.format(Math.round(diffMs / 1000), 'second');
  if (absSec < 3600) return rtf.format(Math.round(diffMs / 60_000), 'minute');
  if (absSec < 86_400) return rtf.format(Math.round(diffMs / 3_600_000), 'hour');
  if (absSec < 2_592_000) return rtf.format(Math.round(diffMs / 86_400_000), 'day');
  return formatDateTime(value);
}

export function truncate(text: string, max = 160): string {
  if (text.length <= max) return text;
  return `${text.slice(0, max).trimEnd()}…`;
}

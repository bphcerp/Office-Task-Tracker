import type { IngestionSettings } from './types';

export type IngestionSettingsPatch = Partial<
  Pick<IngestionSettings, 'mode' | 'mark_as_read' | 'poll_hours' | 'batch_limit'>
>;

export async function updateIngestionSettings(
  patch: IngestionSettingsPatch,
): Promise<IngestionSettings> {
  const res = await fetch('/api/settings/ingestion', {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(patch),
  });

  if (!res.ok) {
    throw new Error(`Failed to save settings (HTTP ${res.status})`);
  }

  return res.json();
}

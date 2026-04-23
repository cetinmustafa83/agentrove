import { check, type Update } from '@tauri-apps/plugin-updater';
import { relaunch } from '@tauri-apps/plugin-process';
import { useDesktopUpdateStore } from '@/store/updateStore';

// Silently check for an update and stage it in the store. Does NOT download —
// download+install runs only when the user clicks the menu item, so we don't
// waste bandwidth re-downloading on every app launch.
export async function checkDesktopUpdate(): Promise<void> {
  const update = await check();
  if (!update) return;

  useDesktopUpdateStore.getState().setAvailable(
    {
      version: update.version,
      currentVersion: update.currentVersion,
      body: update.body ?? null,
      date: update.date ?? null,
    },
    () => downloadAndInstall(update),
  );
}

async function downloadAndInstall(update: Update): Promise<void> {
  const store = useDesktopUpdateStore.getState();
  store.setDownloading();
  try {
    await update.download((event) => {
      const s = useDesktopUpdateStore.getState();
      if (event.event === 'Started') {
        s.setDownloadStarted(event.data.contentLength ?? null);
      } else if (event.event === 'Progress') {
        s.addDownloadChunk(event.data.chunkLength);
      }
    });
    useDesktopUpdateStore.getState().setInstalling();
    await update.install();
    // On Windows install() exits the current process; on macOS/Linux it
    // replaces the bundle in place and requires an explicit relaunch.
    await relaunch();
  } catch (error) {
    useDesktopUpdateStore
      .getState()
      .setError(error instanceof Error ? error.message : 'Update failed');
  }
}

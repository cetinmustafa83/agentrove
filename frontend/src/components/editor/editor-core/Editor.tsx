import { memo, useState, useCallback } from 'react';
import { logger } from '@/utils/logger';
import { CodeView } from '../code-view/CodeView';
import type { FileStructure } from '@/types/file-system.types';
import type { Chat } from '@/types/chat.types';
import { useResolvedTheme } from '@/hooks/useResolvedTheme';
import { sandboxService } from '@/services/sandboxService';

export interface EditorProps {
  files: FileStructure[];
  selectedFile: FileStructure | null;
  onFileSelect: (file: FileStructure | null) => void;
  currentChat?: Chat | null;
  isSandboxSyncing?: boolean;
  onRefresh?: () => void;
  isRefreshing?: boolean;
}

export const Editor = memo(function Editor({
  files,
  onFileSelect,
  selectedFile,
  currentChat,
  isSandboxSyncing = false,
  onRefresh,
  isRefreshing = false,
}: EditorProps) {
  const theme = useResolvedTheme();
  const [isDownloading, setIsDownloading] = useState(false);

  const handleDownload = useCallback(async () => {
    try {
      if (!currentChat?.sandbox_id) {
        return false;
      }

      setIsDownloading(true);

      const zipBlob = await sandboxService.downloadZip(currentChat.sandbox_id);

      const url = URL.createObjectURL(zipBlob);
      const link = document.createElement('a');
      link.href = url;
      const fileName = `sandbox_${currentChat.sandbox_id}_${crypto.randomUUID()}.zip`;
      link.download = fileName;

      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      URL.revokeObjectURL(url);

      return true;
    } catch (error) {
      logger.error('Sandbox download failed', 'Editor', error);
      return false;
    } finally {
      setIsDownloading(false);
    }
  }, [currentChat?.sandbox_id]);

  return (
    <div className="flex h-full w-full flex-col overflow-hidden bg-surface-secondary dark:bg-surface-dark-secondary">
      <CodeView
        files={files}
        selectedFile={selectedFile}
        onFileSelect={onFileSelect}
        theme={theme}
        sandboxId={currentChat?.sandbox_id}
        chatId={currentChat?.id}
        cwd={currentChat?.worktree_cwd ?? undefined}
        onDownload={handleDownload}
        isDownloading={isDownloading}
        isSandboxSyncing={isSandboxSyncing}
        onRefresh={onRefresh}
        isRefreshing={isRefreshing}
      />
    </div>
  );
});

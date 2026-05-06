import { useEffect } from 'react';
import { useUIStore } from '@/store/uiStore';
import { findFileByToolPath } from '@/utils/file';
import type { FileStructure } from '@/types/file-system.types';

export function usePendingFileOpen(
  fileStructure: FileStructure[],
  setSelectedFile: (file: FileStructure | null) => void,
) {
  const pendingFilePath = useUIStore((s) => s.pendingFilePath);

  useEffect(() => {
    if (!pendingFilePath || fileStructure.length === 0) return;
    const file = findFileByToolPath(fileStructure, pendingFilePath);
    setSelectedFile(file ?? { path: pendingFilePath, type: 'file', content: '' });
    useUIStore.setState({ pendingFilePath: null });
  }, [pendingFilePath, setSelectedFile, fileStructure]);
}

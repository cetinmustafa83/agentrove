import {
  memo,
  useEffect,
  useImperativeHandle,
  useMemo,
  useRef,
  type ReactNode,
  type Ref,
} from 'react';
import { FolderOpen } from 'lucide-react';
import { FileTree as PierreFileTree, useFileTree } from '@pierre/trees/react';
import { Spinner } from '@/components/ui/primitives/Spinner';
import type { FileStructure } from '@/types/file-system.types';
import {
  findFileInStructure,
  getAncestorFolderPaths,
  hasActualFiles,
  traverseFileStructure,
} from '@/utils/file';
import '@/styles/pierre-tree-theme.css';

const UNSAFE_CSS = `
  [data-file-tree-search-input] {
    --trees-focus-ring-width: 1px;
  }
`;

export interface TreeHandle {
  expandAncestors: (path: string) => void;
  focusPath: (path: string) => void;
  openSearch: () => void;
}

export interface TreeProps {
  files: FileStructure[];
  selectedFile: FileStructure | null;
  onFileSelect: (file: FileStructure) => void;
  isSandboxSyncing?: boolean;
  modifiedPaths?: Set<string>;
  header?: ReactNode;
  ref?: Ref<TreeHandle>;
}

export const Tree = memo(function Tree({
  files,
  selectedFile,
  onFileSelect,
  isSandboxSyncing = false,
  modifiedPaths,
  header,
  ref,
}: TreeProps) {
  // Snapshot the latest files/handlers so the pierre callbacks can look up the
  // current FileStructure without recreating the model on every render.
  const filesRef = useRef(files);
  filesRef.current = files;
  const onFileSelectRef = useRef(onFileSelect);
  onFileSelectRef.current = onFileSelect;

  const paths = useMemo(
    () => traverseFileStructure(files, (item) => (item.type === 'file' ? item.path : null)),
    [files],
  );
  const initialPathsRef = useRef(paths);

  const { model } = useFileTree({
    paths: initialPathsRef.current,
    initialExpansion: 'open',
    initialSelectedPaths: selectedFile ? [selectedFile.path] : [],
    search: true,
    icons: 'complete',
    itemHeight: 26,
    unsafeCSS: UNSAFE_CSS,
    onSelectionChange: (selectedPaths) => {
      const path = selectedPaths[0];
      if (!path) return;
      // Folder clicks arrive here too — only surface file selections upstream.
      const item = model.getItem(path);
      if (!item || item.isDirectory()) return;
      const file = findFileInStructure(filesRef.current, path);
      if (file) onFileSelectRef.current(file);
    },
  });

  useEffect(() => {
    // useFileTree already consumed the initial paths; skip re-applying on mount.
    if (paths === initialPathsRef.current) return;
    model.resetPaths(paths);
  }, [paths, model]);

  useEffect(() => {
    const entries = modifiedPaths
      ? Array.from(modifiedPaths, (path) => ({ path, status: 'modified' as const }))
      : [];
    model.setGitStatus(entries);
  }, [modifiedPaths, model]);

  // Apply external selection changes (e.g. CommandMenu jump) imperatively.
  useEffect(() => {
    const current = model.getSelectedPaths()[0] ?? null;
    const next = selectedFile?.path ?? null;
    if (current === next) return;
    if (next) {
      model.getItem(next)?.select();
    } else {
      const item = current ? model.getItem(current) : null;
      item?.deselect();
    }
  }, [selectedFile, model]);

  useImperativeHandle(
    ref,
    () => ({
      expandAncestors: (path: string) => {
        for (const ancestor of getAncestorFolderPaths(path)) {
          const item = model.getItem(ancestor);
          if (item && item.isDirectory()) item.expand();
        }
      },
      focusPath: (path: string) => {
        model.focusPath(path);
      },
      openSearch: () => {
        model.openSearch();
      },
    }),
    [model],
  );

  useEffect(() => {
    const handler = (event: KeyboardEvent) => {
      if (!(event.ctrlKey || event.metaKey) || event.key !== 'f') return;
      const active = document.activeElement;
      const isInInput =
        active?.tagName === 'INPUT' ||
        active?.tagName === 'TEXTAREA' ||
        (active as HTMLElement | null)?.contentEditable === 'true';
      if (isInInput) return;
      // offsetParent null when the tree lives in a hidden tab — yield the shortcut to siblings.
      const container = model.getFileTreeContainer();
      if (!container?.offsetParent) return;
      event.preventDefault();
      model.openSearch();
    };
    window.addEventListener('keydown', handler);
    return () => window.removeEventListener('keydown', handler);
  }, [model]);

  if (!hasActualFiles(files)) {
    return (
      <div className="flex h-full select-none flex-col items-center justify-center gap-2 px-4 py-12">
        {isSandboxSyncing ? (
          <Spinner size="md" className="text-text-quaternary dark:text-text-dark-quaternary" />
        ) : (
          <FolderOpen className="h-5 w-5 text-text-quaternary dark:text-text-dark-quaternary" />
        )}
        <p className="text-xs text-text-quaternary dark:text-text-dark-quaternary">
          {isSandboxSyncing ? 'Loading files...' : 'No files yet'}
        </p>
      </div>
    );
  }

  return <PierreFileTree model={model} header={header} className="h-full select-none" />;
});

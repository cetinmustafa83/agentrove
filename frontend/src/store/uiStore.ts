import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import type {
  ThemeState,
  UIState,
  UIActions,
  SplitViewState,
  SplitViewActions,
  ViewType,
} from '@/types/ui.types';
import { MOBILE_BREAKPOINT } from '@/config/constants';
import { getLeaves, isMosaicSplitNode, removeTileFromLayout } from '@/utils/mosaicHelpers';

type UIStoreState = ThemeState &
  Pick<UIState, 'sidebarOpen'> &
  Pick<UIActions, 'setSidebarOpen'> &
  SplitViewState &
  SplitViewActions & {
    commandMenuOpen: boolean;
    setCommandMenuOpen: (open: boolean) => void;
    subThreadDialogOpen: boolean;
    setSubThreadDialogOpen: (open: boolean) => void;
    createPRDialogOpen: boolean;
    setCreatePRDialogOpen: (open: boolean) => void;
    createBranchDialogOpen: boolean;
    setCreateBranchDialogOpen: (open: boolean) => void;
    createCommitDialogOpen: boolean;
    setCreateCommitDialogOpen: (open: boolean) => void;
    pendingFilePath: string | null;
    // Nonce lets the consumer re-jump even when path+line repeat, so that clicking
    // the same search result after scrolling away still reveals it.
    pendingFileJump: { path: string; line: number; nonce: number } | null;
    openFileInEditor: (path: string, line?: number) => void;
    consumeFileJump: () => void;
    pendingDiffFile: string | null;
    openInDiffView: (path: string) => void;
    consumeDiffFileJump: () => void;
    pendingChatMessage: string | null;
    setPendingChatMessage: (message: string | null) => void;
  };

const getInitialSidebarState = (): boolean => {
  if (typeof window === 'undefined') return false;
  return window.innerWidth >= MOBILE_BREAKPOINT;
};

// Mobile switches the sole view; desktop appends a tile to the mosaic
// unless the view is already present.
function ensureViewVisible(
  set: (partial: Partial<UIStoreState>) => void,
  get: () => UIStoreState,
  view: ViewType,
): void {
  const isMobile = typeof window !== 'undefined' && window.innerWidth < MOBILE_BREAKPOINT;
  if (isMobile) {
    set({ currentView: view, mosaicLayout: view });
    return;
  }
  const state = get();
  const layout = state.mosaicLayout;
  if (layout && isMosaicSplitNode(layout)) {
    if (!getLeaves(layout).includes(view)) {
      set({ mosaicLayout: { direction: 'row', first: layout, second: view } });
    }
    return;
  }
  const currentView = (layout ?? state.currentView) as ViewType;
  if (currentView !== view) {
    set({ mosaicLayout: { direction: 'row', first: currentView, second: view } });
  }
}

export const useUIStore = create<UIStoreState>()(
  persist(
    (set, get) => ({
      theme: 'dark',
      toggleTheme: () =>
        set((state) => {
          const next =
            state.theme === 'dark' ? 'light' : state.theme === 'light' ? 'system' : 'dark';
          return { theme: next };
        }),
      setTheme: (theme) => set({ theme }),
      sidebarOpen: getInitialSidebarState(),
      setSidebarOpen: (isOpen) => set({ sidebarOpen: isOpen }),

      commandMenuOpen: false,
      setCommandMenuOpen: (open) => set({ commandMenuOpen: open }),
      subThreadDialogOpen: false,
      setSubThreadDialogOpen: (open) => set({ subThreadDialogOpen: open }),
      createPRDialogOpen: false,
      setCreatePRDialogOpen: (open) => set({ createPRDialogOpen: open }),
      createBranchDialogOpen: false,
      setCreateBranchDialogOpen: (open) => set({ createBranchDialogOpen: open }),
      createCommitDialogOpen: false,
      setCreateCommitDialogOpen: (open) => set({ createCommitDialogOpen: open }),

      pendingChatMessage: null,
      setPendingChatMessage: (message) => set({ pendingChatMessage: message }),

      pendingFilePath: null,
      pendingFileJump: null,
      consumeFileJump: () => set({ pendingFileJump: null }),
      pendingDiffFile: null,
      consumeDiffFileJump: () => set({ pendingDiffFile: null }),
      openFileInEditor: (path, line) => {
        set({
          pendingFilePath: path,
          pendingFileJump:
            line != null ? { path, line, nonce: (get().pendingFileJump?.nonce ?? 0) + 1 } : null,
        });
        ensureViewVisible(set, get, 'editor');
      },
      openInDiffView: (path) => {
        set({ pendingDiffFile: path });
        ensureViewVisible(set, get, 'diff');
      },

      currentView: 'agent',
      splitDirection: 'row',
      mosaicLayout: null,

      setCurrentView: (view) =>
        set({
          currentView: view,
          mosaicLayout: view,
        }),

      exitSplitMode: () => {
        const state = get();
        set({ mosaicLayout: state.currentView });
      },

      setSplitDirection: (direction) => set({ splitDirection: direction }),

      setMosaicLayout: (layout) => {
        if (layout === null) {
          set({ mosaicLayout: null });
          return;
        }
        if (typeof layout === 'string') {
          set({
            mosaicLayout: layout,
            currentView: layout as ViewType,
          });
        } else {
          const leaves = getLeaves(layout);
          set({
            mosaicLayout: layout,
            currentView: leaves[0] as ViewType,
          });
        }
      },

      addTileToMosaic: (view, direction) => {
        const state = get();
        const currentLayout = state.mosaicLayout ?? state.currentView;

        const leaves =
          typeof currentLayout === 'string' ? [currentLayout] : getLeaves(currentLayout);
        if (leaves.includes(view)) return;

        set({
          mosaicLayout: {
            direction,
            first: currentLayout,
            second: view,
          },
          currentView: leaves[0] as ViewType,
        });
      },

      removeTileFromMosaic: (view) => {
        const layout = get().mosaicLayout;
        if (!layout || typeof layout === 'string') return;
        const remaining = getLeaves(layout).filter((v) => v !== view);
        if (remaining.length === 0) return;
        if (remaining.length === 1) {
          set({ currentView: remaining[0], mosaicLayout: remaining[0] });
        } else {
          const newLayout = removeTileFromLayout(layout, view);
          if (newLayout) get().setMosaicLayout(newLayout);
        }
      },

      // Shift-click adds the view as a new tile in the mosaic (split mode);
      // regular click switches to it as the sole view.
      handleViewClick: (view, isShiftClick) => {
        if (
          isShiftClick &&
          typeof window !== 'undefined' &&
          window.innerWidth >= MOBILE_BREAKPOINT
        ) {
          get().addTileToMosaic(view, get().splitDirection);
        } else {
          set({
            currentView: view,
            mosaicLayout: view,
          });
        }
      },
    }),
    {
      name: 'ui-storage',
      version: 6,
      partialize: (state) => ({
        theme: state.theme,
        currentView: state.currentView,
        splitDirection: state.splitDirection,
        sidebarOpen: state.sidebarOpen,
      }),
      migrate: (persisted) => {
        const state = persisted as Record<string, unknown>;
        delete state.isSplitMode;
        delete state.secondaryView;
        delete state.permissionMode;
        delete state.thinkingMode;
        delete state.mosaicLayout;
        if (state.splitDirection === 'horizontal') state.splitDirection = 'row';
        if (state.splitDirection === 'vertical') state.splitDirection = 'column';
        return state;
      },
      merge: (persisted, current) => ({
        ...current,
        ...(persisted || {}),
      }),
    },
  ),
);

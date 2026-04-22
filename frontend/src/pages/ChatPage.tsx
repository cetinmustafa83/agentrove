import { useEffect, useMemo, useCallback, useRef, ReactNode, lazy, Suspense } from 'react';
import { useParams, Navigate, useNavigate } from 'react-router-dom';
import { Sidebar } from '@/components/layout/Sidebar';
import { useLayoutSidebar } from '@/components/layout/layoutState';
import { useUIStore } from '@/store/uiStore';
import { useChatStore } from '@/store/chatStore';
import { SplitViewContainer } from '@/components/ui/SplitViewContainer';
import { CommandMenu } from '@/components/ui/CommandMenu';
import { useCommandMenu } from '@/hooks/useCommandMenu';
import { useActiveViews } from '@/hooks/useActiveViews';
import { Spinner } from '@/components/ui/primitives/Spinner';
import type { ViewType } from '@/types/ui.types';
import { Chat as ChatComponent } from '@/components/chat/chat-window/Chat';
import { ChatSessionOrchestrator } from '@/components/chat/chat-window/ChatSessionOrchestrator';
import { useEditorState } from '@/hooks/useEditorState';
import { useChatData } from '@/hooks/useChatData';
import { useSandboxFiles } from '@/hooks/useSandboxFiles';
import {
  useWorkspacesQuery,
  useWorkspaceResourcesQuery,
} from '@/hooks/queries/useWorkspaceQueries';
import { useSettingsQuery } from '@/hooks/queries/useSettingsQueries';
import { findFileByToolPath } from '@/utils/file';
import { ChatProvider } from '@/contexts/ChatContext';
import { CreateSubThreadDialog } from '@/components/chat/sub-threads/CreateSubThreadDialog';

const Editor = lazy(() =>
  import('@/components/editor/editor-core/Editor').then((m) => ({ default: m.Editor })),
);
const SecretsView = lazy(() =>
  import('@/components/sandbox/secrets/SecretsView').then((m) => ({ default: m.SecretsView })),
);
const DiffView = lazy(() =>
  import('@/components/sandbox/git/DiffView').then((m) => ({ default: m.DiffView })),
);
const TerminalContainer = lazy(() =>
  import('@/components/sandbox/terminal/Container').then((m) => ({ default: m.Container })),
);
const PRReviewView = lazy(() =>
  import('@/components/sandbox/git/PRReviewView').then((m) => ({ default: m.PRReviewView })),
);
const CreateBranchDialog = lazy(() =>
  import('@/components/chat/github/CreateBranchDialog').then((m) => ({
    default: m.CreateBranchDialog,
  })),
);
const CreateCommitDialog = lazy(() =>
  import('@/components/chat/github/CreateCommitDialog').then((m) => ({
    default: m.CreateCommitDialog,
  })),
);
const CreatePRDialog = lazy(() =>
  import('@/components/chat/github/CreatePRDialog').then((m) => ({ default: m.CreatePRDialog })),
);

const viewLoadingFallback = (
  <div className="flex h-full w-full items-center justify-center bg-surface-secondary dark:bg-surface-dark-secondary">
    <Spinner size="md" className="text-text-quaternary dark:text-text-dark-quaternary" />
  </div>
);

export function ChatPage() {
  const { chatId } = useParams();
  const navigate = useNavigate();
  useCommandMenu();
  const subThreadDialogOpen = useUIStore((s) => s.subThreadDialogOpen);
  const createCommitDialogOpen = useUIStore((s) => s.createCommitDialogOpen);
  const createPRDialogOpen = useUIStore((s) => s.createPRDialogOpen);
  const createBranchDialogOpen = useUIStore((s) => s.createBranchDialogOpen);

  const activeViews = useActiveViews();

  const { currentChat, fetchedMessages, hasFetchedMessages, messagesQuery } = useChatData(chatId);

  const { fileStructure, isFileMetadataLoading, refetchFilesMetadata } = useSandboxFiles(
    currentChat,
    chatId,
  );

  const worktreeCwd = currentChat?.worktree_cwd ?? undefined;

  const prevViewsRef = useRef<{
    views: ViewType[];
    sandboxId: string | null;
  }>({
    views: [],
    sandboxId: null,
  });

  useEffect(() => {
    if (!currentChat?.sandbox_id) return;

    const prev = prevViewsRef.current;
    const editorNowActive = activeViews.includes('editor');
    const editorWasActive = prev.views.includes('editor');
    const switchedSandbox = prev.sandboxId !== currentChat.sandbox_id;

    if ((editorNowActive && !editorWasActive) || (editorNowActive && switchedSandbox)) {
      refetchFilesMetadata();
    }

    prevViewsRef.current = {
      views: activeViews,
      sandboxId: currentChat.sandbox_id,
    };
  }, [activeViews, currentChat?.sandbox_id, refetchFilesMetadata]);

  const { data: workspacesData } = useWorkspacesQuery();
  const workspaces = workspacesData?.items ?? [];
  const { data: settings } = useSettingsQuery();

  const { data: workspaceResources } = useWorkspaceResourcesQuery(currentChat?.workspace_id);

  const { selectedFile, setSelectedFile, isRefreshing, handleRefresh, handleFileSelect } =
    useEditorState(refetchFilesMetadata);

  const prevChatIdForResetRef = useRef(chatId);

  useEffect(() => {
    useChatStore.getState().setCurrentChat(currentChat || null);
  }, [currentChat]);

  if (prevChatIdForResetRef.current !== chatId) {
    prevChatIdForResetRef.current = chatId;
    setSelectedFile(null);
    useUIStore.getState().setCurrentView('agent');
    useUIStore.setState({
      pendingFilePath: null,
      pendingFileJump: null,
      subThreadDialogOpen: false,
      createCommitDialogOpen: false,
      createPRDialogOpen: false,
      createBranchDialogOpen: false,
    });
  }

  const pendingFilePath = useUIStore((s) => s.pendingFilePath);

  useEffect(() => {
    if (!pendingFilePath || fileStructure.length === 0) return;

    const file = findFileByToolPath(fileStructure, pendingFilePath);
    setSelectedFile(file ?? { path: pendingFilePath, type: 'file', content: '' });
    useUIStore.setState({ pendingFilePath: null });
  }, [pendingFilePath, setSelectedFile, fileStructure]);

  const handleChatSelect = useCallback(
    (selectedChatId: string) => {
      navigate(`/chat/${selectedChatId}`);
    },
    [navigate],
  );

  // Auto-close sidebar when switching to non-agent views (editor-only, terminal-only, etc.)
  // to reclaim the 300px. Users can re-open via the TitleBar toggle.
  const agentVisible = activeViews.includes('agent');
  useEffect(() => {
    if (!agentVisible) {
      useUIStore.getState().setSidebarOpen(false);
    }
  }, [agentVisible]);

  // Sidebar is always available on chat pages — it holds navigation, settings, and logout
  const sidebarContent = useMemo(() => {
    return (
      <Sidebar
        workspaces={workspaces}
        selectedChatId={chatId || null}
        selectedChatWorkspaceId={currentChat?.workspace_id}
        selectedChatParentId={currentChat?.parent_chat_id}
        onChatSelect={handleChatSelect}
      />
    );
  }, [
    workspaces,
    chatId,
    currentChat?.workspace_id,
    currentChat?.parent_chat_id,
    handleChatSelect,
  ]);

  useLayoutSidebar(sidebarContent);

  const renderNonTerminalView = useCallback(
    (view: ViewType): ReactNode => {
      switch (view) {
        case 'agent':
          return <ChatComponent />;
        case 'editor':
          return (
            <Suspense fallback={viewLoadingFallback}>
              <Editor
                files={fileStructure}
                selectedFile={selectedFile}
                onFileSelect={handleFileSelect}
                currentChat={currentChat}
                isSandboxSyncing={isFileMetadataLoading}
                onRefresh={handleRefresh}
                isRefreshing={isRefreshing}
              />
            </Suspense>
          );
        case 'secrets':
          return (
            <Suspense fallback={viewLoadingFallback}>
              <SecretsView sandboxId={currentChat?.sandbox_id} />
            </Suspense>
          );
        case 'diff':
          return (
            <Suspense fallback={viewLoadingFallback}>
              <DiffView sandboxId={currentChat?.sandbox_id} cwd={worktreeCwd} />
            </Suspense>
          );
        case 'prReview':
          return (
            <Suspense fallback={viewLoadingFallback}>
              <PRReviewView />
            </Suspense>
          );
        default:
          return null;
      }
    },
    [
      chatId,
      currentChat,
      fileStructure,
      selectedFile,
      handleFileSelect,
      isFileMetadataLoading,
      handleRefresh,
      isRefreshing,
      worktreeCwd,
    ],
  );

  const renderView = useCallback(
    (view: ViewType, slot: string): ReactNode => {
      const isTerminal = view === 'terminal';
      return (
        <div className="relative flex h-full w-full">
          <div className={isTerminal ? 'flex h-full w-full' : 'hidden'}>
            <Suspense fallback={viewLoadingFallback}>
              <TerminalContainer
                sandboxId={currentChat?.sandbox_id}
                chatId={currentChat?.id}
                isVisible={isTerminal}
                panelKey={slot}
              />
            </Suspense>
          </div>
          <div className={isTerminal ? 'hidden' : 'flex h-full w-full'}>
            {renderNonTerminalView(view)}
          </div>
        </div>
      );
    },
    [currentChat, renderNonTerminalView],
  );

  if (!chatId) return <Navigate to="/" />;

  return (
    <ChatProvider
      chatId={chatId}
      sandboxId={currentChat?.sandbox_id}
      parentChatId={currentChat?.parent_chat_id ?? undefined}
      fileStructure={fileStructure}
      customSkills={workspaceResources?.skills}
      builtinSlashCommands={workspaceResources?.builtin_slash_commands}
      personas={settings?.personas}
    >
      <ChatSessionOrchestrator
        chatId={chatId}
        currentChat={currentChat}
        fetchedMessages={fetchedMessages}
        hasFetchedMessages={hasFetchedMessages}
        messagesQuery={messagesQuery}
        refetchFilesMetadata={refetchFilesMetadata}
      >
        <div className="relative flex h-full">
          <div className="flex h-full flex-1 overflow-hidden bg-surface text-text-primary dark:bg-surface-dark dark:text-text-dark-primary">
            <SplitViewContainer renderView={renderView} />
          </div>
          <CommandMenu />
          {subThreadDialogOpen && currentChat && !currentChat.parent_chat_id && (
            <CreateSubThreadDialog
              parentChat={currentChat}
              onClose={() => useUIStore.getState().setSubThreadDialogOpen(false)}
            />
          )}
          {createCommitDialogOpen && (
            <Suspense fallback={null}>
              <CreateCommitDialog
                onClose={() => useUIStore.getState().setCreateCommitDialogOpen(false)}
              />
            </Suspense>
          )}
          {createPRDialogOpen && (
            <Suspense fallback={null}>
              <CreatePRDialog onClose={() => useUIStore.getState().setCreatePRDialogOpen(false)} />
            </Suspense>
          )}
          {createBranchDialogOpen && (
            <Suspense fallback={null}>
              <CreateBranchDialog
                onClose={() => useUIStore.getState().setCreateBranchDialogOpen(false)}
              />
            </Suspense>
          )}
        </div>
      </ChatSessionOrchestrator>
    </ChatProvider>
  );
}

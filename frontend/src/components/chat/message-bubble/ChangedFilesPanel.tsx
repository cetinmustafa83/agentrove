import { memo, useState } from 'react';
import { ChevronDown, Files } from 'lucide-react';
import { Button } from '@/components/ui/primitives/Button';
import { useMessageChangesQuery } from '@/hooks/queries/useChatQueries';
import { useUIStore } from '@/store/uiStore';
import type { ChangedFile, ChangedFileStatus } from '@/types/sandbox.types';

interface ChangedFilesPanelProps {
  messageId: string;
}

const STATUS_LABEL: Record<ChangedFileStatus, string> = {
  M: 'Modified',
  A: 'Added',
  D: 'Deleted',
};

const STATUS_COLOR: Record<ChangedFileStatus, string> = {
  M: 'text-text-quaternary dark:text-text-dark-quaternary',
  A: 'text-success-600 dark:text-success-400',
  D: 'text-error-600 dark:text-error-400',
};

const ChangedFilesPanelInner: React.FC<ChangedFilesPanelProps> = ({ messageId }) => {
  const [expanded, setExpanded] = useState(true);
  const { data } = useMessageChangesQuery(messageId);

  const files = data?.files ?? [];
  const cwd = data?.cwd ?? '';
  if (files.length === 0) return null;

  const { totalAdditions, totalDeletions } = files.reduce(
    (acc, f) => {
      acc.totalAdditions += f.additions;
      acc.totalDeletions += f.deletions;
      return acc;
    },
    { totalAdditions: 0, totalDeletions: 0 },
  );

  return (
    <div className="mt-3 overflow-hidden rounded-lg border border-border/50 bg-surface-secondary dark:border-border-dark/50 dark:bg-surface-dark-secondary">
      <Button
        type="button"
        variant="unstyled"
        onClick={() => setExpanded((prev) => !prev)}
        aria-expanded={expanded}
        className="flex w-full items-center gap-2 px-3 py-2 text-left transition-colors duration-150 hover:bg-surface-hover dark:hover:bg-surface-dark-hover"
      >
        <Files className="h-3.5 w-3.5 flex-shrink-0 text-text-tertiary dark:text-text-dark-tertiary" />
        <span className="text-xs font-medium text-text-secondary dark:text-text-dark-secondary">
          {files.length} {files.length === 1 ? 'file' : 'files'} changed
        </span>
        <span className="text-text-quaternary dark:text-text-dark-quaternary">·</span>
        <span className="font-mono text-xs tabular-nums text-success-600 dark:text-success-400">
          +{totalAdditions}
        </span>
        <span className="font-mono text-xs tabular-nums text-error-600 dark:text-error-400">
          −{totalDeletions}
        </span>
        <div className="flex-1" />
        <ChevronDown
          className={`h-3.5 w-3.5 flex-shrink-0 text-text-quaternary transition-transform duration-300 ease-out dark:text-text-dark-quaternary ${expanded ? 'rotate-180' : ''}`}
        />
      </Button>

      {expanded && (
        <div className="border-t border-border/50 dark:border-border-dark/50">
          {files.map((file, index) => (
            <ChangedFileRow
              key={file.path}
              file={file}
              cwd={cwd}
              isLast={index === files.length - 1}
            />
          ))}
        </div>
      )}
    </div>
  );
};

const ChangedFileRow: React.FC<{ file: ChangedFile; cwd: string; isLast: boolean }> = ({
  file,
  cwd,
  isLast,
}) => {
  const isDeleted = file.status === 'D';
  const editorPath = cwd ? `${cwd}/${file.path}` : file.path;
  const borderClass = isLast ? '' : 'border-b border-border/50 dark:border-border-dark/50';
  const interactiveClass = isDeleted
    ? 'cursor-default'
    : 'transition-colors duration-150 hover:bg-surface-hover dark:hover:bg-surface-dark-hover';
  return (
    <Button
      type="button"
      variant="unstyled"
      disabled={isDeleted}
      onClick={isDeleted ? undefined : () => useUIStore.getState().openFileInEditor(editorPath)}
      className={`flex w-full items-center gap-2.5 px-3 py-2 text-left ${interactiveClass} ${borderClass}`}
    >
      <span
        className={`w-3.5 flex-shrink-0 text-center font-mono text-2xs ${STATUS_COLOR[file.status]}`}
        title={STATUS_LABEL[file.status]}
      >
        {file.status}
      </span>
      <span
        className="min-w-0 flex-1 truncate font-mono text-xs text-text-secondary dark:text-text-dark-secondary"
        title={file.path}
      >
        {file.path}
      </span>
      <span className="min-w-[28px] flex-shrink-0 text-right font-mono text-2xs tabular-nums text-success-600 dark:text-success-400">
        +{file.additions}
      </span>
      <span className="min-w-[24px] flex-shrink-0 text-right font-mono text-2xs tabular-nums text-error-600 dark:text-error-400">
        −{file.deletions}
      </span>
    </Button>
  );
};

export const ChangedFilesPanel = memo(ChangedFilesPanelInner);

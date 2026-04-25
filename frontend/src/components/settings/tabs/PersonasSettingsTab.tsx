import { ListManagementTab } from '@/components/ui/ListManagementTab';
import type { Persona } from '@/types/user.types';
import { UserCircle } from 'lucide-react';

interface PersonasSettingsTabProps {
  personas: Persona[] | null;
  onAddPersona: () => void;
  onEditPersona: (index: number) => void;
  onDeletePersona: (index: number) => void | Promise<void>;
}

export const PersonasSettingsTab: React.FC<PersonasSettingsTabProps> = ({
  personas,
  onAddPersona,
  onEditPersona,
  onDeletePersona,
}) => {
  return (
    <ListManagementTab<Persona>
      title="Personas"
      description="Create personas with custom system prompts. Select from the persona dropdown in the input bar. Claude, Codex, and OpenCode support replacing the system prompt; the persona selector is hidden for Cursor and Copilot."
      items={personas}
      emptyIcon={UserCircle}
      emptyText="No personas configured yet"
      emptyButtonText="Create Your First Persona"
      addButtonText="Add Persona"
      deleteConfirmTitle="Delete Persona"
      deleteConfirmMessage={(persona) =>
        `Are you sure you want to delete "${persona.name}"? This action cannot be undone.`
      }
      getItemKey={(persona) => persona.name}
      onAdd={onAddPersona}
      onEdit={onEditPersona}
      onDelete={onDeletePersona}
      renderItem={(persona) => (
        <>
          <h3 className="mb-2 truncate text-xs font-medium text-text-primary dark:text-text-dark-primary">
            {persona.name}
          </h3>
          <p className="line-clamp-3 font-mono text-2xs leading-relaxed text-text-quaternary dark:text-text-dark-quaternary">
            {persona.content}
          </p>
        </>
      )}
      logContext="PersonasSettingsTab"
    />
  );
};

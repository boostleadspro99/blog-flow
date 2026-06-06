interface PromptFormProps {
  value: string;
  onChange: (value: string) => void;
  disabled: boolean;
}

const MAX_LENGTH = 1000;

export default function PromptForm({ value, onChange, disabled }: PromptFormProps) {
  return (
    <div>
      <label htmlFor="prompt" className="block text-sm font-medium text-slate-300 mb-2">
        Prompt
      </label>
      <textarea
        id="prompt"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        disabled={disabled}
        maxLength={MAX_LENGTH}
        rows={4}
        placeholder="Describe the image you want to generate..."
        className="w-full resize-none rounded-lg border border-slate-700 bg-slate-800 px-4 py-3 text-sm text-white placeholder-slate-500 focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500 disabled:opacity-50"
      />
      <p className="mt-1 text-right text-xs text-slate-500">
        {value.length} / {MAX_LENGTH}
      </p>
    </div>
  );
}

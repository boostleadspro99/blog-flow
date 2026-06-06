import { IMAGE_MODELS } from '../lib/models';

interface ModelSelectProps {
  value: string;
  onChange: (value: string) => void;
  disabled: boolean;
}

export default function ModelSelect({ value, onChange, disabled }: ModelSelectProps) {
  return (
    <div>
      <label htmlFor="model" className="block text-sm font-medium text-slate-300 mb-2">
        Model
      </label>
      <select
        id="model"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        disabled={disabled}
        className="w-full rounded-lg border border-slate-700 bg-slate-800 px-4 py-3 text-sm text-white focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500 disabled:opacity-50"
      >
        {IMAGE_MODELS.map((m) => (
          <option key={m.id} value={m.id}>
            {m.label} — {m.provider}
          </option>
        ))}
      </select>
      {value && (
        <p className="mt-1 text-xs text-slate-500">
          {IMAGE_MODELS.find((m) => m.id === value)?.recommendedFor}
        </p>
      )}
    </div>
  );
}

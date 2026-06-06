import { useState } from 'react';
import { Link } from 'react-router-dom';
import PromptForm from '../components/PromptForm';
import ModelSelect from '../components/ModelSelect';
import ImagePreview from '../components/ImagePreview';
import ErrorMessage from '../components/ErrorMessage';
import { generateImage, GeminiError } from '../lib/geminiClient';
import { useAuth } from '../contexts/AuthContext';

export default function Home() {
  const { user } = useAuth();
  const [prompt, setPrompt] = useState('');
  const [model, setModel] = useState('gemini-3-pro-image');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [imageUrl, setImageUrl] = useState<string | null>(null);

  const handleGenerate = async () => {
    if (!prompt.trim()) {
      setError('Please enter a prompt to generate an image.');
      return;
    }
    setError(null);
    setImageUrl(null);
    setLoading(true);
    try {
      const url = await generateImage({ prompt, model });
      setImageUrl(url);
    } catch (err) {
      const message =
        err instanceof GeminiError
          ? err.message
          : 'An unexpected error occurred. Please try again.';
      setError(message);
      console.error('Image generation error:', err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="mx-auto max-w-6xl px-4 py-8 lg:py-12">
      <div className="mb-8">
        <h1 className="text-3xl font-bold tracking-tight text-white">
          PuterImage Studio
        </h1>
        <p className="mt-1 text-sm text-slate-400">
          Generate images with AI — powered by Gemini-Free-API
        </p>
      </div>

      {!user && (
        <div className="mb-6 rounded-xl border border-amber-800 bg-amber-900/20 p-4 flex items-center justify-between">
          <p className="text-sm text-amber-300">
            <span className="font-semibold">Sign in</span> to generate images with your own Gemini account.
          </p>
          <Link
            to="/login"
            className="rounded-lg bg-amber-600 px-4 py-2 text-sm font-medium text-white hover:bg-amber-700 transition-colors"
          >
            Sign In
          </Link>
        </div>
      )}

      <div className="grid gap-8 lg:grid-cols-2">
        <div className="flex flex-col gap-6">
          <div className="rounded-xl border border-slate-800 bg-slate-900/50 p-6">
            <h2 className="text-lg font-semibold text-white mb-4">
              Configuration
            </h2>
            <div className="flex flex-col gap-5">
              <PromptForm
                value={prompt}
                onChange={setPrompt}
                disabled={loading}
              />
              <ModelSelect
                value={model}
                onChange={setModel}
                disabled={loading}
              />
              <button
                onClick={handleGenerate}
                disabled={loading}
                className="w-full rounded-lg bg-blue-600 px-4 py-3 text-sm font-medium text-white hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 focus:ring-offset-slate-950 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                {loading ? 'Generating...' : 'Generate Image'}
              </button>
              {error && (
                <ErrorMessage
                  message={error}
                  onDismiss={() => setError(null)}
                />
              )}
            </div>
          </div>
        </div>

        <div>
          <h2 className="text-lg font-semibold text-white mb-4">Preview</h2>
          <ImagePreview imageUrl={imageUrl} loading={loading} error={null} />
        </div>
      </div>

      <p className="mt-12 text-center text-xs text-slate-600">
        Powered by{' '}
        <a
          href="https://github.com/eaveszen/Gemini-Free-API"
          className="underline hover:text-slate-400"
          target="_blank"
          rel="noopener noreferrer"
        >
          Gemini-Free-API
        </a>
        {' — '}Runs locally, no API keys.
      </p>
    </div>
  );
}

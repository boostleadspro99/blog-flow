import { useCallback, useEffect, useState, type FormEvent } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { authRequest, ApiError } from '../lib/api';
import type { CookieResponse } from '../lib/types';

export default function Settings() {
  const { user, token, refreshUser } = useAuth();
  const [psid, setPsid] = useState('');
  const [psidts, setPsidts] = useState('');
  const [cookies, setCookies] = useState<CookieResponse | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);

  const loadCookies = useCallback(async () => {
    try {
      const data = await authRequest<CookieResponse>('/user/cookies');
      setCookies(data);
    } catch {
      // No cookies yet
    }
  }, []);

  useEffect(() => {
    loadCookies();
  }, [loadCookies]);

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setMessage(null);
    if (!psid.trim() || !psidts.trim()) {
      setMessage({ type: 'error', text: 'Both cookie values are required.' });
      return;
    }
    setSubmitting(true);
    try {
      const data = await authRequest<CookieResponse>('/user/cookies', {
        method: 'POST',
        body: JSON.stringify({
          secure_1psid: psid,
          secure_1psidts: psidts,
        }),
      });
      setCookies(data);
      if (data.is_valid) {
        setMessage({ type: 'success', text: 'Cookies validated successfully! Your Gemini client is ready.' });
      } else {
        setMessage({ type: 'error', text: `Cookies saved but validation failed: ${data.error_message || 'Unknown error'}` });
      }
      setPsid('');
      setPsidts('');
      await refreshUser();
    } catch (err) {
      setMessage({ type: 'error', text: err instanceof ApiError ? err.message : 'Failed to save cookies.' });
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="mx-auto max-w-2xl px-4 py-12">
      <h2 className="text-2xl font-bold text-white mb-6">Settings</h2>

      {/* Browser Extension token */}
      {user && token && (
        <div className="mb-8 rounded-xl border border-blue-800 bg-blue-900/20 p-6">
          <h3 className="text-lg font-semibold text-white mb-2">
            🔑 Browser Extension Token
          </h3>
          <p className="text-sm text-slate-400 mb-3">
            Copy this token into the Chrome extension to automatically extract your Gemini cookies.
          </p>
          <div className="flex gap-2">
            <input
              type="text"
              readOnly
              value={token}
              className="flex-1 rounded-lg border border-slate-700 bg-slate-800 px-3 py-2 text-xs text-slate-300 font-mono truncate focus:outline-none"
            />
            <button
              onClick={() => {
                navigator.clipboard.writeText(token);
                setMessage({ type: 'success', text: 'Token copied!' });
                setTimeout(() => setMessage(null), 2000);
              }}
              className="rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 transition-colors whitespace-nowrap"
            >
              Copy
            </button>
          </div>
          {message && message.text === 'Token copied!' && (
            <p className="mt-2 text-xs text-green-400">{message.text}</p>
          )}
        </div>
      )}

      {/* User info */}
      {user && (
        <div className="mb-8 rounded-xl border border-slate-800 bg-slate-900/50 p-6">
          <h3 className="text-lg font-semibold text-white mb-3">Account</h3>
          <dl className="grid grid-cols-2 gap-2 text-sm">
            <dt className="text-slate-400">Email</dt>
            <dd className="text-white">{user.email}</dd>
            <dt className="text-slate-400">Username</dt>
            <dd className="text-white">{user.username}</dd>
            <dt className="text-slate-400">Member since</dt>
            <dd className="text-white">
              {new Date(user.created_at).toLocaleDateString()}
            </dd>
          </dl>
        </div>
      )}

      {/* Cookie status */}
      <div className="mb-8 rounded-xl border border-slate-800 bg-slate-900/50 p-6">
        <h3 className="text-lg font-semibold text-white mb-3">
          Gemini Cookies
        </h3>
        {cookies ? (
          <div className="flex items-center gap-3 mb-4">
            <div
              className={`h-2.5 w-2.5 rounded-full ${
                cookies.is_valid ? 'bg-green-500' : 'bg-red-500'
              }`}
            />
            <span className="text-sm text-slate-300">
              {cookies.is_valid
                ? 'Cookies configured and valid'
                : 'Cookies need attention'}
            </span>
            {cookies.last_validated_at && (
              <span className="text-xs text-slate-500">
                Last checked:{' '}
                {new Date(cookies.last_validated_at).toLocaleString()}
              </span>
            )}
          </div>
        ) : (
          <p className="text-sm text-slate-400 mb-4">
            No cookies configured yet. Add your Gemini cookies to start
            generating images.
          </p>
        )}
        {cookies?.error_message && (
          <div className="mb-4 rounded-lg border border-red-800 bg-red-900/30 px-4 py-2.5 text-sm text-red-400">
            {cookies.error_message}
          </div>
        )}

        {/* Cookie form */}
        <form onSubmit={handleSubmit} className="flex flex-col gap-3">
          <div>
            <label className="block text-xs text-slate-400 mb-1">
              __Secure-1PSID
            </label>
            <input
              type="text"
              value={psid}
              onChange={(e) => setPsid(e.target.value)}
              placeholder="Paste your __Secure-1PSID cookie..."
              className="w-full rounded-lg border border-slate-700 bg-slate-800 px-4 py-2.5 text-white text-sm font-mono focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
          <div>
            <label className="block text-xs text-slate-400 mb-1">
              __Secure-1PSIDTS
            </label>
            <input
              type="text"
              value={psidts}
              onChange={(e) => setPsidts(e.target.value)}
              placeholder="Paste your __Secure-1PSIDTS cookie..."
              className="w-full rounded-lg border border-slate-700 bg-slate-800 px-4 py-2.5 text-white text-sm font-mono focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
          <p className="text-xs text-slate-500">
            Get these from gemini.google.com → F12 → Application → Cookies.
            They are encrypted before storage.
          </p>
          {message && (
            <div
              className={`rounded-lg border px-4 py-2.5 text-sm ${
                message.type === 'success'
                  ? 'border-green-800 bg-green-900/30 text-green-400'
                  : 'border-red-800 bg-red-900/30 text-red-400'
              }`}
            >
              {message.text}
            </div>
          )}
          <button
            type="submit"
            disabled={submitting}
            className="rounded-lg bg-blue-600 px-4 py-3 text-sm font-medium text-white hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50 transition-colors"
          >
            {submitting ? 'Validating...' : 'Save & Validate Cookies'}
          </button>
        </form>
      </div>
    </div>
  );
}

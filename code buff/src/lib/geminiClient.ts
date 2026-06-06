// In production (Vercel), use the backend URL. In dev, use the Vite proxy.
const API_BASE = import.meta.env.VITE_API_BASE || '/v1';

export interface GenerateOptions {
  prompt: string;
  model: string;
}

export class GeminiError extends Error {
  constructor(message: string) {
    super(message);
    this.name = 'GeminiError';
  }
}

/**
 * Generate an image using Gemini-Free-API (local server).
 * Calls POST /v1/images/generations (OpenAI-compatible format).
 * Returns the image URL on success.
 */
export async function generateImage({ prompt, model }: GenerateOptions): Promise<string> {
  if (!prompt.trim()) {
    throw new GeminiError('Please enter a prompt to generate an image.');
  }

  if (prompt.length > 1000) {
    throw new GeminiError('Prompt must be 1000 characters or fewer.');
  }

  const token = localStorage.getItem('token');
  const headers: Record<string, string> = { 'Content-Type': 'application/json' };
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  let response: Response;
  try {
    response = await fetch(`${API_BASE}/images/generations`, {
      method: 'POST',
      headers,
      body: JSON.stringify({
        model,
        prompt,
        n: 1,
        size: '1024x1024',
      }),
    });
  } catch {
    throw new GeminiError(
      'Cannot reach Gemini-Free-API server. Make sure it is running on http://localhost:3897.',
    );
  }

  if (!response.ok) {
    const text = await response.text().catch(() => '');
    throw new GeminiError(
      `Gemini API error (${response.status}): ${text || response.statusText}`,
    );
  }

  const data = await response.json().catch(() => null);
  if (!data?.data?.[0]?.url) {
    throw new GeminiError('Unexpected response format from Gemini API.');
  }

  return data.data[0].url;
}

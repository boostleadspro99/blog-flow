interface ImagePreviewProps {
  imageUrl: string | null;
  loading: boolean;
  error: string | null;
}

export default function ImagePreview({ imageUrl, loading, error }: ImagePreviewProps) {
  if (loading) {
    return (
      <div className="flex items-center justify-center rounded-xl border border-slate-800 bg-slate-900/50 p-8">
        <div className="flex flex-col items-center gap-4">
          <div className="relative h-10 w-10">
            <div className="absolute inset-0 animate-spin rounded-full border-3 border-slate-700 border-t-blue-500" />
          </div>
          <p className="text-sm text-slate-400">Generating image...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="rounded-xl border border-red-800/50 bg-red-950/30 p-8">
        <div className="flex flex-col items-center gap-3 text-center">
          <svg className="h-8 w-8 text-red-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M12 9v2m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <p className="text-sm text-red-300">{error}</p>
        </div>
      </div>
    );
  }

  if (imageUrl) {
    return (
      <div className="overflow-hidden rounded-xl border border-slate-800">
        <img
          src={imageUrl}
          alt="Generated"
          className="w-full h-auto object-cover"
        />
      </div>
    );
  }

  return (
    <div className="flex items-center justify-center rounded-xl border border-dashed border-slate-700 bg-slate-900/30 p-8">
      <div className="flex flex-col items-center gap-3 text-center">
        <svg className="h-10 w-10 text-slate-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
        </svg>
        <p className="text-sm text-slate-500">Your generated image will appear here.</p>
      </div>
    </div>
  );
}

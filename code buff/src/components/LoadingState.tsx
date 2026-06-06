export default function LoadingState() {
  return (
    <div className="flex flex-col items-center justify-center gap-4 py-16">
      <div className="relative h-12 w-12">
        <div className="absolute inset-0 animate-spin rounded-full border-4 border-slate-700 border-t-blue-500" />
      </div>
      <p className="text-sm text-slate-400">Generating image...</p>
    </div>
  );
}

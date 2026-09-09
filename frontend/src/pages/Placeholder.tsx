
export function Placeholder({ title, phase }: { title: string; phase: string }) {
  return (
    <div className="flex min-h-screen items-center justify-center bg-bg text-ink">
      <div className="flex flex-col gap-2 text-center">
        <span className="text-lg font-semibold">{title}</span>
        <span className="text-sm text-ink-3">{phase}</span>
      </div>
    </div>
  );
}

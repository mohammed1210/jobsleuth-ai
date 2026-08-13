export default function CompletenessBar({ value }: { value: number }) {
  const width = Math.max(0, Math.min(100, value));
  return (
    <div>
      <div className="flex justify-between text-xs text-gray-500 mb-1">
        <span>Evidence completeness</span>
        <span>{width}%</span>
      </div>
      <div className="h-2 rounded-full bg-gray-100 overflow-hidden">
        <div className="h-full bg-brand-600" style={{ width: `${width}%` }} />
      </div>
    </div>
  );
}

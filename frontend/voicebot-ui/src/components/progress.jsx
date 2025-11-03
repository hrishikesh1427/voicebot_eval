export function Progress({ value, className = "" }) {
  return (
    <div className={`w-full h-2 bg-gray-200 rounded-full overflow-hidden ${className}`}>
      <div
        className="bg-blue-500 h-full transition-all duration-700"
        style={{ width: `${value}%` }}
      />
    </div>
  );
}

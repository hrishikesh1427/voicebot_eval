export function Badge({ children, className = "" }) {
  return (
    <span className={`px-2 py-1 rounded-full text-xs bg-gray-200 font-medium ${className}`}>
      {children}
    </span>
  );
}

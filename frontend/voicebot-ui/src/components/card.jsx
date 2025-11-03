export function Card({ children, className = "" }) {
  return <div className={`rounded-2xl bg-white border p-2 shadow-sm ${className}`}>{children}</div>;
}

export function CardContent({ children, className = "" }) {
  return <div className={className}>{children}</div>;
}

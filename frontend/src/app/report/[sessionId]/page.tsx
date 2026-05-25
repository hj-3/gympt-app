import ReportPageClient from './ReportPageClient';

// Required for static export with dynamic routes
export function generateStaticParams() {
  // Return empty array - client-side routing will handle dynamic routes
  return [];
}

// Server component wrapper
export default function ReportPage() {
  return <ReportPageClient />;
}

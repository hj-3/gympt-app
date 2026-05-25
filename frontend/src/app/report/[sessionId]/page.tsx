import ReportPageClient from './ReportPageClient';

// Required for static export with dynamic routes
// Returns empty array to skip static generation
// Client-side routing will handle all [sessionId] values
export async function generateStaticParams() {
  return [];
}

// Server component wrapper
export default function ReportPage() {
  return <ReportPageClient />;
}

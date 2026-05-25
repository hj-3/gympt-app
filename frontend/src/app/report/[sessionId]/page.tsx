import ReportPageClient from './ReportPageClient';

// Required for static export with dynamic routes
export async function generateStaticParams() {
  // Return empty array - client-side routing will handle dynamic routes
  return [];
}

// Mark as dynamic to ensure it's not statically generated
export const dynamic = 'force-dynamic';
export const dynamicParams = true;

// Server component wrapper
export default function ReportPage() {
  return <ReportPageClient />;
}

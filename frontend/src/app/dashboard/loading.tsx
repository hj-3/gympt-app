export default function DashboardLoading() {
  return (
    <div className="min-h-screen bg-gray-50 p-4">
      <div className="max-w-4xl mx-auto space-y-4 animate-pulse">
        <div className="h-8 bg-gray-200 rounded w-48" />
        <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
          {[...Array(4)].map((_, i) => (
            <div key={i} className="bg-white rounded-2xl p-6 h-28" />
          ))}
        </div>
        <div className="bg-white rounded-2xl h-64" />
        <div className="bg-white rounded-2xl h-48" />
      </div>
    </div>
  );
}

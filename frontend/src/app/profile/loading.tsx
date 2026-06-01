export default function ProfileLoading() {
  return (
    <div className="min-h-screen bg-gray-50 p-4">
      <div className="max-w-md mx-auto space-y-4 animate-pulse">
        <div className="flex items-center gap-4">
          <div className="w-16 h-16 bg-gray-200 rounded-full" />
          <div className="space-y-2">
            <div className="h-5 bg-gray-200 rounded w-32" />
            <div className="h-4 bg-gray-200 rounded w-48" />
          </div>
        </div>
        {[...Array(4)].map((_, i) => (
          <div key={i} className="bg-white rounded-2xl h-14" />
        ))}
      </div>
    </div>
  );
}

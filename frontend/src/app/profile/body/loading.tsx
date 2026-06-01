export default function BodyLoading() {
  return (
    <div className="min-h-screen bg-gray-50 p-4">
      <div className="max-w-md mx-auto space-y-4 animate-pulse">
        <div className="h-8 bg-gray-200 rounded w-32" />
        <div className="bg-white rounded-2xl p-6 space-y-4">
          {[...Array(5)].map((_, i) => (
            <div key={i} className="flex justify-between items-center">
              <div className="h-4 bg-gray-200 rounded w-24" />
              <div className="h-4 bg-gray-200 rounded w-16" />
            </div>
          ))}
        </div>
        <div className="bg-white rounded-2xl h-32" />
      </div>
    </div>
  );
}

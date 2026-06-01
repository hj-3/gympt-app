export default function WorkoutLoading() {
  return (
    <div className="min-h-screen bg-gray-50 p-4">
      <div className="max-w-2xl mx-auto space-y-4 animate-pulse">
        <div className="h-8 bg-gray-200 rounded w-40" />
        {[...Array(3)].map((_, i) => (
          <div key={i} className="bg-white rounded-2xl h-24" />
        ))}
      </div>
    </div>
  );
}

import { Card } from '@/components/ui/Card';

interface StatsCardProps {
  title: string;
  value: number | string;
  unit?: string;
  icon?: string;
  trend?: {
    value: number;
    isPositive: boolean;
  };
}

export function StatsCard({ title, value, unit, icon, trend }: StatsCardProps) {
  return (
    <Card>
      <div className="flex items-start justify-between">
        <div>
          <p className="text-sm text-gray-600 mb-1">{title}</p>
          <div className="flex items-baseline space-x-1">
            <span className="text-3xl font-bold">{value}</span>
            {unit && <span className="text-gray-600">{unit}</span>}
          </div>
          {trend && (
            <p className={`text-sm mt-2 ${trend.isPositive ? 'text-green-600' : 'text-red-600'}`}>
              {trend.isPositive ? '↑' : '↓'} {Math.abs(trend.value)}%
            </p>
          )}
        </div>
        {icon && <span className="text-3xl">{icon}</span>}
      </div>
    </Card>
  );
}

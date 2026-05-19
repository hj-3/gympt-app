'use client';

import { Card } from '@/components/ui/Card';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';

interface WeeklyData {
  day: string;
  minutes: number;
  sessions: number;
}

interface WeeklyChartProps {
  data: WeeklyData[];
}

export function WeeklyChart({ data }: WeeklyChartProps) {
  return (
    <Card>
      <h3 className="text-lg font-semibold mb-4">Weekly Activity</h3>

      {data.length === 0 ? (
        <p className="text-gray-500 text-center py-8">No activity data</p>
      ) : (
        <ResponsiveContainer width="100%" height={300}>
          <BarChart data={data}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="day" />
            <YAxis />
            <Tooltip />
            <Bar dataKey="minutes" fill="#3B82F6" name="Minutes" />
          </BarChart>
        </ResponsiveContainer>
      )}
    </Card>
  );
}

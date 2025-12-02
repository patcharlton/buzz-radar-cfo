import React from 'react';
import { AreaChart, Area, ResponsiveContainer } from 'recharts';

/**
 * A minimal sparkline chart for showing trends.
 *
 * @param {Array} data - Array of {value: number} objects
 * @param {string} color - Stroke color (default emerald)
 * @param {string} fillColor - Fill color (default same as stroke with opacity)
 * @param {number} height - Chart height in pixels (default 40)
 * @param {boolean} showGradient - Whether to show gradient fill (default true)
 */
export function Sparkline({
  data,
  color = '#10b981',
  fillColor,
  height = 40,
  showGradient = true,
}) {
  if (!data || data.length === 0) {
    return (
      <div
        style={{ height }}
        className="flex items-center justify-center text-xs text-muted-foreground"
      >
        No data
      </div>
    );
  }

  // Normalize data to have 'value' key
  const chartData = data.map((d, i) => ({
    value: typeof d === 'number' ? d : d.value || 0,
    index: i,
  }));

  const gradientId = `sparkline-gradient-${Math.random().toString(36).substr(2, 9)}`;
  const actualFillColor = fillColor || color;

  return (
    <ResponsiveContainer width="100%" height={height}>
      <AreaChart data={chartData} margin={{ top: 2, right: 2, bottom: 2, left: 2 }}>
        <defs>
          {showGradient && (
            <linearGradient id={gradientId} x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor={actualFillColor} stopOpacity={0.3} />
              <stop offset="95%" stopColor={actualFillColor} stopOpacity={0} />
            </linearGradient>
          )}
        </defs>
        <Area
          type="monotone"
          dataKey="value"
          stroke={color}
          strokeWidth={1.5}
          fill={showGradient ? `url(#${gradientId})` : 'none'}
          dot={false}
          isAnimationActive={false}
        />
      </AreaChart>
    </ResponsiveContainer>
  );
}

export default Sparkline;

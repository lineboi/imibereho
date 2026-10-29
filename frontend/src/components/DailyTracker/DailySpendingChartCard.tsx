import React, { useState } from 'react';
import type { Language } from '../../types';
import { TRACKER_TRANSLATIONS } from '../../data/mockTrackerData';
import type { TrackerBurnRateResponse, TrackerDailyTrendPoint } from '../../services/api';
import { BarChart2, TrendingUp, CheckCircle2, Zap } from 'lucide-react';

interface DailySpendingChartCardProps {
  language: Language;
  idealDailyLimit?: number;
  todaySpent: number;
  dailyTrendPoints?: TrackerDailyTrendPoint[];
  burnRate?: TrackerBurnRateResponse | null;
}

interface DaySpending {
  dayLabel: string;
  dateStr: string;
  amount: number;
  isToday?: boolean;
}

export const DailySpendingChartCard: React.FC<DailySpendingChartCardProps> = ({
  language,
  idealDailyLimit = 5000,
  todaySpent,
  dailyTrendPoints,
  burnRate,
}) => {
  const t = TRACKER_TRANSLATIONS[language];
  const [hoveredIndex, setHoveredIndex] = useState<number | null>(null);

  // Generate the past 7 days strictly from database dailyTrendPoints (0 if no spend recorded)
  const today = new Date();
  const daysData: DaySpending[] = Array.from({ length: 7 }, (_, i) => {
    const d = new Date(today);
    d.setDate(today.getDate() - (6 - i));
    const isoDate = d.toISOString().slice(0, 10);
    const isToday = i === 6;
    const dayNum = d.getDate();
    const monthShort = new Intl.DateTimeFormat(language === 'RW' ? 'rw-RW' : 'en-US', { month: 'short' }).format(d);
    const monthLong = new Intl.DateTimeFormat(language === 'RW' ? 'rw-RW' : 'en-US', { month: 'long' }).format(d);
    const dayLabel = isToday
      ? language === 'RW'
        ? 'Uyu munsi'
        : 'Today'
      : `${dayNum} ${monthShort}`;
    const dateStr = `${dayNum} ${monthLong}`;

    // Read recorded spend from backend database points
    const dbPoint = dailyTrendPoints?.find((p) => p.date === isoDate);
    const amount = isToday
      ? todaySpent > 0
        ? todaySpent
        : dbPoint?.total || 0
      : dbPoint?.total || 0;

    return {
      dayLabel,
      dateStr,
      amount,
      isToday,
    };
  });

  // Graph geometry - expanded width gives dedicated right-side margin for the ideal badge
  const chartWidth = 540;
  const chartHeight = 210;
  const axisLeft = 55;
  const axisRight = 445; // Bars end cleanly at 445
  const axisTop = 25;
  const axisBottom = 165;
  const plotHeight = axisBottom - axisTop; // 140px

  const yCeiling = 8000;
  const getY = (val: number) => axisBottom - (val / yCeiling) * plotHeight;

  const yTicks = [
    { val: 8000, label: '8k' },
    { val: 6000, label: '6k' },
    { val: 4000, label: '4k' },
    { val: 2000, label: '2k' },
    { val: 0, label: '0' },
  ];

  const idealY = getY(idealDailyLimit);
  const slotWidth = (axisRight - axisLeft) / daysData.length;
  const barWidth = 26;

  const daysUnderIdeal = daysData.filter((d) => d.amount <= idealDailyLimit).length;

  return (
    <section
      aria-label="Daily Spending Graph"
      className="w-full bg-white rounded-2xl border border-[#E3DED4] p-4 sm:p-5 shadow-xs flex flex-col gap-3.5"
    >
      {/* Header Row */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-1.5 pb-2 border-b border-[#F0ECE4]">
        <div className="flex items-center gap-2">
          <div className="w-7 h-7 rounded-lg bg-[#E8F2EC] flex items-center justify-center text-[#1E5E45] shrink-0 border border-[#CFE4D7]">
            <BarChart2 className="w-3.5 h-3.5" />
          </div>
          <div>
            <h3 className="font-serif text-base sm:text-lg font-medium text-[#133A29] leading-tight">
              {t.chartTitle}
            </h3>
            <p className="text-[11px] text-[#697B71] mt-0.5">
              {t.chartSubtitle}
            </p>
          </div>
        </div>

        {/* Legend indicator */}
        <div className="flex items-center gap-3 text-xs self-start sm:self-auto">
          <div className="flex items-center gap-1.5 text-[11px] font-semibold text-[#B91C1C] bg-red-50 px-2.5 py-1 rounded-md border border-red-200/80">
            <span className="w-3.5 h-0.5 border-t-2 border-dashed border-[#B91C1C]" />
            <span>{idealDailyLimit.toLocaleString()} RWF Ideal Line</span>
          </div>
        </div>
      </div>

      {/* SVG Graph Area with Crisp X and Y Axes */}
      <div className="w-full relative">
        <svg
          viewBox={`0 0 ${chartWidth} ${chartHeight}`}
          className="w-full h-auto overflow-visible select-none"
        >
          {/* Horizontal Gridlines & Y-Axis Labels */}
          {yTicks.map((tick) => {
            const y = getY(tick.val);
            return (
              <g key={tick.val}>
                <line
                  x1={axisLeft}
                  y1={y}
                  x2={axisRight}
                  y2={y}
                  stroke="#E8E3D8"
                  strokeWidth="1"
                  strokeDasharray={tick.val === 0 ? '' : '3 3'}
                />
                <text
                  x={axisLeft - 8}
                  y={y + 3.5}
                  textAnchor="end"
                  fontSize="11"
                  fill="#687A71"
                  fontFamily="monospace"
                >
                  {tick.label}
                </text>
              </g>
            );
          })}

          {/* Y-Axis Line */}
          <line
            x1={axisLeft}
            y1={axisTop - 5}
            x2={axisLeft}
            y2={axisBottom}
            stroke="#657A6E"
            strokeWidth="1.5"
          />

          {/* X-Axis Line (Solid Baseline) */}
          <line
            x1={axisLeft}
            y1={axisBottom}
            x2={axisRight + 6}
            y2={axisBottom}
            stroke="#657A6E"
            strokeWidth="1.5"
          />

          {/* Ideal Benchmark Dashed Line across the plot */}
          <line
            x1={axisLeft}
            y1={idealY}
            x2={axisRight + 4}
            y2={idealY}
            stroke="#B91C1C"
            strokeWidth="1.75"
            strokeDasharray="5 3"
          />

          {/* Ideal Benchmark Badge positioned OUTSIDE the bars in dedicated right margin */}
          <g transform={`translate(${axisRight + 8}, ${idealY - 9})`}>
            <rect
              width="78"
              height="18"
              fill="#B91C1C"
              rx="2"
            />
            <text
              x="39"
              y="12.5"
              textAnchor="middle"
              fill="#FFFFFF"
              fontSize="9"
              fontWeight="bold"
            >
              Ideal: {idealDailyLimit.toLocaleString()}
            </text>
          </g>

          {/* Flat-Top Bars (Solid Colors, Zero Gradients, Zero Rounded Tops) */}
          {daysData.map((day, idx) => {
            const centerX = axisLeft + slotWidth * idx + slotWidth / 2;
            const barX = centerX - barWidth / 2;
            const barHeightVal = (Math.min(day.amount, yCeiling) / yCeiling) * plotHeight;
            const barY = axisBottom - barHeightVal;
            const isOver = day.amount > idealDailyLimit;
            const isHovered = hoveredIndex === idx;

            // Solid Flat Colors: Forest Green within ideal, Solid Amber above ideal
            const barColor = isOver ? '#D97706' : '#1E5E45';

            return (
              <g
                key={day.dayLabel}
                className="cursor-pointer"
                onMouseEnter={() => setHoveredIndex(idx)}
                onMouseLeave={() => setHoveredIndex(null)}
              >
                {/* Flat-Top Rectangular Bar */}
                <rect
                  x={barX}
                  y={barY}
                  width={barWidth}
                  height={barHeightVal}
                  fill={barColor}
                  opacity={isHovered ? 0.85 : 1}
                  className="transition-opacity duration-150"
                />

                {/* Amount on top of bar */}
                <text
                  x={centerX}
                  y={barY - 5}
                  textAnchor="middle"
                  fontSize="9.5"
                  fontWeight="bold"
                  fill={isOver ? '#B45309' : '#143B2A'}
                >
                  {(day.amount / 1000).toFixed(1)}k
                </text>

                {/* X-Axis Tick Mark */}
                <line
                  x1={centerX}
                  y1={axisBottom}
                  x2={centerX}
                  y2={axisBottom + 4}
                  stroke="#657A6E"
                  strokeWidth="1.5"
                />

                {/* X-Axis Day Label */}
                <text
                  x={centerX}
                  y={axisBottom + 16}
                  textAnchor="middle"
                  fontSize={day.isToday ? '11' : '10'}
                  fontWeight={day.isToday ? 'bold' : 'normal'}
                  fill={day.isToday ? '#143B2A' : '#5E7065'}
                >
                  {day.dayLabel}
                </text>
              </g>
            );
          })}
        </svg>

        {/* Hover Tooltip Box */}
        {hoveredIndex !== null && (
          <div className="absolute top-1 right-2 bg-[#132A1F] text-white text-[11px] py-1 px-2.5 rounded-md shadow-md border border-[#254636] pointer-events-none">
            <span className="font-semibold">{daysData[hoveredIndex].dateStr}: </span>
            <span className="font-bold">{daysData[hoveredIndex].amount.toLocaleString()} RWF </span>
            <span className={daysData[hoveredIndex].amount > idealDailyLimit ? 'text-amber-300' : 'text-emerald-300'}>
              ({daysData[hoveredIndex].amount > idealDailyLimit
                ? `+${(daysData[hoveredIndex].amount - idealDailyLimit).toLocaleString()} above ideal`
                : `${(idealDailyLimit - daysData[hoveredIndex].amount).toLocaleString()} within ideal`})
            </span>
          </div>
        )}
      </div>

      {/* Axis Unit Sub-label */}
      <div className="flex items-center justify-between text-[10.5px] text-[#788A80] -mt-1 pt-1 border-t border-[#F2EEE7]">
        <span>{language === 'RW' ? 'Y-axis: Amafaranga (RWF)' : 'Y-axis: Amounts in Rwandan Francs (RWF)'}</span>
        <span>{language === 'RW' ? 'X-axis: Iminsi 7 ishize (19 - 25 Ukw 2026)' : 'X-axis: Past 7 Days (19 - 25 Oct 2026)'}</span>
      </div>

      {/* Bottom Summary Insight */}
      <div className="bg-[#FAF8F4] border border-[#E9E3D6] rounded-xl p-2.5 sm:p-3 flex items-center justify-between gap-2 text-xs">
        <div className="flex items-center gap-2 text-[#465A4E]">
          <CheckCircle2 className="w-4 h-4 text-[#1E5E45] shrink-0" />
          <span className="text-[11.5px] sm:text-xs">
            {t.chartFooterPraise.replace('4 of 7', `${daysUnderIdeal} of 7`)}
          </span>
        </div>
        <div className="flex items-center gap-1 font-bold text-[#1E5E45] text-xs shrink-0">
          <TrendingUp className="w-3.5 h-3.5" />
          <span>Disciplined Pace</span>
        </div>
      </div>

      {/* Burn Rate Metric */}
      {burnRate && (
        <div className="bg-[#FAFDFB] border border-[#CEE4D5] rounded-xl p-2.5 flex items-center justify-between text-xs text-[#1E5E45]">
          <div className="flex items-center gap-1.5 font-semibold">
            <Zap className="w-3.5 h-3.5" />
            <span>Avg. Daily Spend: {burnRate.averageDailySpend?.toLocaleString() || 0} RWF</span>
          </div>
          <span className="text-[11px] text-[#55695D]">
            Projected Month Spend: <strong>{burnRate.projectedMonthSpend?.toLocaleString() || 0} RWF</strong>
          </span>
        </div>
      )}
    </section>
  );
};

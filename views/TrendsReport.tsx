
import React from 'react';
import { AreaChart, Area, XAxis, YAxis, ResponsiveContainer, Tooltip, CartesianGrid } from 'recharts';
import { PetInfo } from '../types';

interface TrendsReportProps {
  pet: PetInfo;
  onBack: () => void;
}

const mockTrendsData = [
  { day: 'Mon', steps: 6400, health: 95, sleep: 7.2 },
  { day: 'Tue', steps: 7200, health: 96, sleep: 7.8 },
  { day: 'Wed', steps: 8100, health: 94, sleep: 6.5 },
  { day: 'Thu', steps: 5800, health: 92, sleep: 8.1 },
  { day: 'Fri', steps: 9400, health: 98, sleep: 7.4 },
  { day: 'Sat', steps: 11200, health: 99, sleep: 8.5 },
  { day: 'Sun', steps: 8432, health: 98, sleep: 8.2 },
];

const TrendsReportView: React.FC<TrendsReportProps> = ({ pet, onBack }) => {
  return (
    <div className="flex flex-col min-h-full bg-white relative pb-10">
      {/* Header */}
      <header className="sticky top-0 z-50 bg-white/90 backdrop-blur-md px-6 py-4 flex items-center justify-between border-b border-gray-50">
        <button 
          onClick={onBack}
          className="size-10 flex items-center justify-center rounded-2xl bg-gray-50 text-gray-600 hover:bg-gray-100 transition-all active:scale-90"
        >
          <span className="material-symbols-outlined">arrow_back</span>
        </button>
        <h1 className="text-lg font-black text-[#111814] tracking-tight">趋势分析报告</h1>
        <button className="size-10 flex items-center justify-center rounded-2xl bg-gray-50 text-gray-600">
          <span className="material-symbols-outlined text-[20px]">ios_share</span>
        </button>
      </header>

      <main className="flex-1 px-6 pt-6 flex flex-col gap-8">
        {/* 1. AI Summary Card */}
        <section className="relative animate-in fade-in slide-in-from-bottom-4 duration-500">
          <div className="bg-[#111814] rounded-[2.5rem] p-8 text-white relative overflow-hidden shadow-2xl shadow-black/20">
            <div className="absolute top-0 right-0 w-40 h-40 bg-[#31d2e8]/10 rounded-full blur-3xl -mr-20 -mt-20"></div>
            <div className="flex items-center gap-3 mb-6">
              <div className="p-2 bg-[#31d2e8] rounded-xl">
                <span className="material-symbols-outlined text-white text-[20px] fill-icon">auto_awesome</span>
              </div>
              <span className="text-xs font-bold text-[#31d2e8] uppercase tracking-[0.2em]">AI 智能周结</span>
            </div>
            <h2 className="text-2xl font-bold mb-4 leading-tight">本周活跃度较上周提升了 <span className="text-[#31d2e8]">15.4%</span></h2>
            <p className="text-gray-400 text-sm leading-relaxed mb-6">
              {pet.name} 在周末表现出极高的探索欲。平均心率维持在 72bpm，处于非常理想的平稳期。建议在下周二增加 20 分钟的间歇性运动。
            </p>
            <div className="grid grid-cols-2 gap-4">
              <div className="bg-white/5 border border-white/10 rounded-2xl p-4">
                <p className="text-[10px] text-gray-500 font-bold uppercase mb-1">平均睡眠</p>
                <p className="text-xl font-black">7.8h</p>
              </div>
              <div className="bg-white/5 border border-white/10 rounded-2xl p-4">
                <p className="text-[10px] text-gray-500 font-bold uppercase mb-1">健康趋势</p>
                <p className="text-xl font-black text-green-400">稳步上升</p>
              </div>
            </div>
          </div>
        </section>

        {/* 2. Comparative Analysis Chart */}
        <section className="flex flex-col gap-4 animate-in fade-in slide-in-from-bottom-4 duration-700">
          <div className="flex items-center justify-between">
            <h3 className="text-xl font-black text-[#111814] tracking-tight">活动与健康对比</h3>
            <div className="flex gap-2">
              <div className="flex items-center gap-1">
                <div className="size-2 bg-[#31d2e8] rounded-full"></div>
                <span className="text-[10px] font-bold text-gray-400">步数</span>
              </div>
              <div className="flex items-center gap-1">
                <div className="size-2 bg-orange-400 rounded-full"></div>
                <span className="text-[10px] font-bold text-gray-400">健康分</span>
              </div>
            </div>
          </div>
          
          <div className="bg-gray-50 rounded-[2rem] p-6 h-[280px]">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={mockTrendsData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                <defs>
                  <linearGradient id="colorSteps" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#31d2e8" stopOpacity={0.1}/>
                    <stop offset="95%" stopColor="#31d2e8" stopOpacity={0}/>
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e2e8f0" />
                <XAxis 
                  dataKey="day" 
                  axisLine={false} 
                  tickLine={false} 
                  tick={{fontSize: 10, fill: '#94a3b8', fontWeight: 'bold'}}
                />
                <YAxis axisLine={false} tickLine={false} hide />
                <Tooltip 
                  contentStyle={{ borderRadius: '16px', border: 'none', boxShadow: '0 10px 15px -3px rgba(0,0,0,0.1)' }}
                />
                <Area type="monotone" dataKey="steps" stroke="#31d2e8" strokeWidth={3} fillOpacity={1} fill="url(#colorSteps)" />
                <Area type="monotone" dataKey="health" stroke="#fb923c" strokeWidth={2} fillOpacity={0} />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </section>

        {/* 3. Deep Insights Heatmap Simulation */}
        <section className="flex flex-col gap-4 mb-8">
          <h3 className="text-xl font-black text-[#111814] tracking-tight">24h 行为热力分布</h3>
          <div className="grid grid-cols-6 gap-2">
            {Array.from({ length: 24 }).map((_, i) => {
              const opacity = Math.random() * 0.8 + 0.1;
              return (
                <div 
                  key={i} 
                  className="aspect-square rounded-lg flex items-center justify-center text-[8px] font-bold text-gray-400 transition-all hover:scale-105"
                  style={{ backgroundColor: `rgba(49, 210, 232, ${opacity})` }}
                >
                  {i}h
                </div>
              );
            })}
          </div>
          <p className="text-[10px] text-gray-400 font-medium italic text-center">颜色越深代表该时段活动频率越高</p>
        </section>

        {/* 4. Action Plan */}
        <section className="bg-emerald-50 rounded-[2rem] p-6 border border-emerald-100">
          <div className="flex items-center gap-3 mb-4">
            <span className="material-symbols-outlined text-emerald-600">health_and_safety</span>
            <h3 className="text-lg font-bold text-emerald-900">下周行动计划</h3>
          </div>
          <ul className="space-y-3">
            <PlanItem icon="check_circle" text="保持周六的高强度户外社交" />
            <PlanItem icon="check_circle" text="周二、周四增加 10% 蛋白质摄入" />
            <PlanItem icon="check_circle" text="监控夜间呼吸频率波动" />
          </ul>
        </section>
      </main>
    </div>
  );
};

const PlanItem: React.FC<{ icon: string; text: string }> = ({ icon, text }) => (
  <li className="flex items-center gap-2 text-sm text-emerald-800 font-medium">
    <span className="material-symbols-outlined text-emerald-500 text-[18px]">{icon}</span>
    {text}
  </li>
);

export default TrendsReportView;

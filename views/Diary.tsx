
import React, { useState } from 'react';
import { AreaChart, Area, ResponsiveContainer } from 'recharts';
import { PetInfo, DiaryEntry } from '../types';

const entries: (DiaryEntry & { activityTrend: {v: number}[] })[] = [
  {
    id: '1',
    time: '今天, 14:00',
    status: '精力充沛',
    title: '公园奇遇',
    content: '今天的公园太棒了！我遇到了一只叫麦克斯的金毛猎犬。我们一直转圈跑，直到我都晕了。',
    imageUrl: 'https://lh3.googleusercontent.com/aida-public/AB6AXuD8aCJEZBl-xr6GYUIxiRY37BGvvKo1RqtbS_0cMl14Qn-sudYG2dOm9YCRVhvsgWSKfFmI1KufQnYwh1ivxs8kREy80MBYHCheAN0oHTZDIX-8WhyElEeICmBoQlyWWh1Os8vG2oFsqjr6DWXfpvnhM-OSp2fBgzsOCOd0DXF1-okVcWgXysd8B_FdwqdTIO7CWXOGGzlNfW3Kmw95_gfPApghBA6_kUh9L8zjChcuEdByFfXCUOD8mZ-1ZEEKTQlo8TdBTimcqtA',
    isVideo: true,
    duration: '0:15',
    type: 'activity',
    activityTrend: [{v: 10}, {v: 40}, {v: 35}, {v: 90}, {v: 85}, {v: 100}, {v: 60}, {v: 20}]
  },
  {
    id: '2',
    time: '今天, 10:30',
    status: '进食',
    title: '美食时刻',
    content: '人类终于喂我了。这可是我生命中最美好的30秒。',
    imageUrl: 'https://lh3.googleusercontent.com/aida-public/AB6AXuD9y4_BzhL5e2NAm4fMR1ixhiN09nbe0qIyKEyVdzzPDQ_8pxC2zWEIeYY1Ri61zuKRXpU3FW8rjEk6ist0YUN81Zu7AAv0-KuUSQugw5bB_zxEnVc3xuy8hQAlXsg0a1nyPBUFDD0qzG0KBSdS0GFuqHktvLo7R6ECWZHGOXTPUp2zd6tdDFVYr5JfO-4tMhGVLORGCqU_GWP74VV9thvq_jYicKgQHU-liP0fKyzeGNv8mLDLCgqjojoNrOMeXTJZsdNbjDaVHH8',
    type: 'feeding',
    activityTrend: [{v: 5}, {v: 10}, {v: 15}, {v: 80}, {v: 95}, {v: 85}, {v: 10}, {v: 5}]
  }
];

const DiaryView: React.FC<{ pet: PetInfo; onGoToRegister?: () => void }> = ({ pet, onGoToRegister }) => {
  const [showSettings, setShowSettings] = useState(false);
  const [filter, setFilter] = useState<'all' | 'activity' | 'feeding'>('all');

  // 检查宠物是否已注册
  const isPetRegistered = !!pet.id;

  // 如果宠物未注册，显示引导界面
  if (!isPetRegistered && onGoToRegister) {
    return (
      <div className="flex flex-col h-full bg-[#f6f8f8] items-center justify-center px-8 pb-32">
        <div className="bg-white rounded-3xl p-8 shadow-lg max-w-sm w-full text-center">
          <div className="w-20 h-20 bg-gradient-to-br from-[#31d2e8] to-[#28c566] rounded-full flex items-center justify-center mx-auto mb-6">
            <span className="material-symbols-outlined text-white text-3xl">book_2</span>
          </div>
          
          <h2 className="text-2xl font-bold text-[#111814] mb-4">完成宠物档案注册</h2>
          <p className="text-gray-500 text-sm mb-6 leading-relaxed">
            您需要先完成宠物档案注册，才能查看和记录宠物日记。
          </p>
          
          <div className="space-y-3">
            <button 
              onClick={onGoToRegister}
              className="w-full py-4 bg-[#31d2e8] text-white font-bold rounded-2xl hover:bg-[#2bb8cc] transition-colors flex items-center justify-center gap-2"
            >
              <span className="material-symbols-outlined">add_reaction</span>
              <span>立即注册宠物档案</span>
            </button>
            
            <p className="text-xs text-gray-400">
              注册后即可享受完整的日记功能
            </p>
          </div>
        </div>
      </div>
    );
  }

  const filteredEntries = filter === 'all' 
    ? entries 
    : entries.filter(e => e.type === filter);

  return (
    <div className="flex flex-col min-h-full bg-[#f6f8f8] pb-32">
      <header className="sticky top-0 z-30 bg-white/90 backdrop-blur-md border-b border-gray-100 p-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="relative">
              <div className="bg-center bg-no-repeat aspect-square bg-cover rounded-full size-10 ring-2 ring-[#31d2e8]/50" style={{backgroundImage: `url(${pet.avatar || 'https://lh3.googleusercontent.com/aida-public/AB6AXuBL8hWh1zN4HXT8Xny9U_4fKeIGwQuMObOqzh9UHslNo-Z6PubizNF157nzuMkApk_7eOtZE21P6FEKx44-5kVqK7u4PzOuY4WkBaSSJoLj6mlPUnzTSXXtZAuCOfCmwN_PIQu9II2p-igr8_M5fXZoQRT0A25O1q3N4grb5yEKWVrJXOucd0n7eOPqeOKsJiXgYhIkudttsmuKjRphyPE2-BjRglitID_yrW0IQCIN5XenKppBt_-0ZkUPfaY0P04wvpKrPsWtsNA'})`}}></div>
              <div className="absolute bottom-0 right-0 size-3 bg-[#31d2e8] rounded-full border-2 border-white"></div>
            </div>
            <div>
              <h1 className="text-xl font-bold leading-tight">{pet.name}的日记</h1>
              <p className="text-xs text-gray-500 font-medium">在线 • 电量 {pet.battery}%</p>
            </div>
          </div>
          <div className="relative">
            <button 
              onClick={() => setShowSettings(!showSettings)}
              className="flex items-center justify-center size-10 rounded-full hover:bg-gray-100 active:scale-90 transition-all"
            >
              <span className="material-symbols-outlined">tune</span>
            </button>
            {showSettings && (
              <div className="absolute right-0 top-12 w-48 bg-white rounded-2xl shadow-2xl border border-gray-100 p-2 animate-in zoom-in-95 duration-200">
                <p className="px-3 py-2 text-[10px] font-bold text-gray-400 uppercase tracking-widest">筛选视图</p>
                <button onClick={() => {setFilter('all'); setShowSettings(false)}} className={`w-full text-left px-3 py-2 rounded-xl text-sm font-bold ${filter === 'all' ? 'bg-[#31d2e8]/10 text-[#31d2e8]' : 'text-gray-700'}`}>全部动态</button>
                <button onClick={() => {setFilter('activity'); setShowSettings(false)}} className={`w-full text-left px-3 py-2 rounded-xl text-sm font-bold ${filter === 'activity' ? 'bg-[#31d2e8]/10 text-[#31d2e8]' : 'text-gray-700'}`}>仅看户外</button>
                <button onClick={() => {setFilter('feeding'); setShowSettings(false)}} className={`w-full text-left px-3 py-2 rounded-xl text-sm font-bold ${filter === 'feeding' ? 'bg-[#31d2e8]/10 text-[#31d2e8]' : 'text-gray-700'}`}>仅看进食</button>
                <div className="h-px bg-gray-50 my-1"></div>
                <button className="w-full text-left px-3 py-2 rounded-xl text-sm font-bold text-[#31d2e8] flex items-center gap-2">
                  <span className="material-symbols-outlined text-sm">summarize</span> 生成本周总结
                </button>
              </div>
            )}
          </div>
        </div>
      </header>

      <main className="px-4 pt-6 relative">
        <div className="absolute left-[31px] top-6 bottom-0 w-0.5 bg-gray-200 z-0"></div>

        <div className="flex flex-col gap-8">
          {filteredEntries.map((entry) => (
            <div key={entry.id} className="relative z-10 flex gap-4">
              <div className="flex flex-col items-center">
                <div className={`size-8 rounded-full flex items-center justify-center shadow-lg ring-4 ring-[#f6f8f8] ${entry.type === 'activity' ? 'bg-[#31d2e8]' : 'bg-white border-2 border-[#31d2e8]'}`}>
                  <span className={`material-symbols-outlined text-[18px] ${entry.type === 'activity' ? 'text-white' : 'text-[#31d2e8]'}`}>
                    {entry.type === 'activity' ? 'pets' : 'restaurant'}
                  </span>
                </div>
              </div>
              <div className="flex-1 min-w-0">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-sm font-bold text-gray-900">{entry.time}</span>
                  <span className={`inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-xs font-bold ${entry.type === 'activity' ? 'bg-[#31d2e8]/20 text-green-800' : 'bg-orange-100 text-orange-700'}`}>
                    <span className="material-symbols-outlined text-[14px]">{entry.type === 'activity' ? 'bolt' : 'nutrition'}</span>
                    {entry.status}
                  </span>
                </div>
                <div className="bg-white rounded-2xl p-3 shadow-sm border border-gray-100">
                  <div className="relative w-full aspect-video rounded-xl overflow-hidden mb-3 bg-gray-100">
                    <img src={entry.imageUrl} alt={entry.title} className="w-full h-full object-cover" />
                    {entry.isVideo && (
                      <div className="absolute bottom-2 right-2 bg-black/50 backdrop-blur-sm text-white text-xs px-2 py-1 rounded-md flex items-center gap-1">
                        <span className="material-symbols-outlined text-[14px]">videocam</span> {entry.duration}
                      </div>
                    )}
                  </div>
                  
                  {/* Activity Sparkline */}
                  <div className="mb-3 px-1">
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-[10px] font-bold text-gray-400 uppercase tracking-wider">活动强度分析</span>
                      <span className="text-[10px] text-[#31d2e8] font-bold">AI 实时监测</span>
                    </div>
                    <div className="h-8 w-full block">
                      <ResponsiveContainer width="100%" height={32} minWidth={0}>
                        <AreaChart data={entry.activityTrend}>
                          <Area 
                            type="monotone" 
                            dataKey="v" 
                            stroke={entry.type === 'activity' ? '#31d2e8' : '#fb923c'} 
                            fill={entry.type === 'activity' ? '#31d2e8' : '#fb923c'} 
                            fillOpacity={0.1}
                            strokeWidth={2}
                            isAnimationActive={false}
                          />
                        </AreaChart>
                      </ResponsiveContainer>
                    </div>
                  </div>

                  <div className="flex gap-3">
                    <div className={`w-1 rounded-full shrink-0 h-auto ${entry.type === 'activity' ? 'bg-[#31d2e8]' : 'bg-orange-400'}`}></div>
                    <div>
                      <p className="text-base text-gray-700 leading-relaxed">{entry.content}</p>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          ))}

          {filteredEntries.length === 0 && (
            <div className="flex flex-col items-center justify-center py-20 text-gray-400">
              <span className="material-symbols-outlined text-6xl mb-2">event_busy</span>
              <p className="font-bold">暂无相关日记</p>
            </div>
          )}

          <div className="relative z-10 flex gap-4">
            <div className="flex flex-col items-center w-8">
              <div className="size-2 rounded-full bg-gray-300"></div>
            </div>
            <div className="flex-1 pt-1">
              <p className="text-xs text-gray-400 font-bold uppercase tracking-wider">日记起点</p>
            </div>
          </div>
        </div>
      </main>

      <button className="fixed bottom-28 right-4 z-40 flex items-center justify-center gap-2 rounded-full bg-[#31d2e8] text-white px-5 py-4 shadow-xl shadow-[#31d2e8]/30 hover:scale-105 active:scale-95 transition-transform duration-200">
        <span className="material-symbols-outlined">auto_awesome</span>
        <span className="font-bold text-sm">生成日记</span>
      </button>
    </div>
  );
};

export default DiaryView;

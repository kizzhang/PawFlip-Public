
import React, { useState, useRef, useEffect, useMemo } from 'react';
import { AreaChart, Area, XAxis, ResponsiveContainer, Tooltip, CartesianGrid } from 'recharts';
import { PetInfo, ChatMessage } from '../types';
import { healthAgentService, ToolAction, HealthTrendsResponse, HealthTrendData } from '../services/healthAgentService';

// 扩展 ChatMessage 类型以支持工具调用
interface ExtendedChatMessage extends ChatMessage {
  toolActions?: ToolAction[];
}

type TimeRange = 'week' | 'month' | 'year';
type TabType = 'activity' | 'sleep' | 'heartRate' | 'calories';

// 自定义 Tooltip 组件
const CustomTooltip = ({ active, payload, label, unit, color }: any) => {
  if (active && payload && payload.length) {
    return (
      <div className="bg-white p-3 rounded-2xl shadow-xl border border-gray-100 flex flex-col gap-0.5 animate-in fade-in zoom-in-95 duration-200">
        <p className="text-[10px] font-black text-gray-400 uppercase tracking-widest">{label}</p>
        <div className="flex items-baseline gap-1">
          <p className="text-base font-black text-[#111814]" style={{ color }}>{payload[0].value}</p>
          <p className="text-[10px] font-bold text-gray-400">{unit}</p>
        </div>
      </div>
    );
  }
  return null;
};

const HealthView: React.FC<{ pet: PetInfo; onNotificationClick: () => void; onGoToRegister?: () => void }> = ({ pet, onNotificationClick, onGoToRegister }) => {
  const [activeTab, setActiveTab] = useState<TabType>('activity');
  const [timeRange, setTimeRange] = useState<TimeRange>('week');

  // 检查宠物是否已注册
  const isPetRegistered = !!pet.id;

  // 如果宠物未注册，显示引导界面
  if (!isPetRegistered && onGoToRegister) {
    return (
      <div className="flex flex-col h-full bg-[#f6f8f8] items-center justify-center px-8 pb-32">
        <div className="bg-white rounded-3xl p-8 shadow-lg max-w-sm w-full text-center">
          <div className="w-20 h-20 bg-gradient-to-br from-[#31d2e8] to-[#28c566] rounded-full flex items-center justify-center mx-auto mb-6">
            <span className="material-symbols-outlined text-white text-3xl">monitor_heart</span>
          </div>
          
          <h2 className="text-2xl font-bold text-[#111814] mb-4">完成宠物档案注册</h2>
          <p className="text-gray-500 text-sm mb-6 leading-relaxed">
            您需要先完成宠物档案注册，才能查看宠物健康数据。
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
              注册后即可享受完整的健康监测功能
            </p>
          </div>
        </div>
      </div>
    );
  }

  const [messages, setMessages] = useState<ExtendedChatMessage[]>([
    { 
      role: 'assistant', 
      text: `你好！我是${pet.name}的健康顾问。有什么可以帮您的吗？`, 
      timestamp: new Date() 
    }
  ]);
  const [inputValue, setInputValue] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [pendingToolActions, setPendingToolActions] = useState<ToolAction[]>([]);
  const [conversationId, setConversationId] = useState<string | null>(null);
  const [suggestions, setSuggestions] = useState<string[]>(['查看最近7天健康数据', '分析睡眠情况', '最近活动怎么样']);
  const [trendData, setTrendData] = useState<HealthTrendsResponse | null>(null);
  const [isLoadingTrends, setIsLoadingTrends] = useState(false);
  const chatEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // 获取健康趋势数据
  useEffect(() => {
    if (!pet.id) return;
    
    const fetchTrends = async () => {
      setIsLoadingTrends(true);
      try {
        const data = await healthAgentService.getHealthTrends(pet.id, timeRange);
        setTrendData(data);
      } catch (error) {
        console.error('获取趋势数据失败:', error);
      } finally {
        setIsLoadingTrends(false);
      }
    };
    
    fetchTrends();
  }, [pet.id, timeRange]);

  const handleSend = async (text: string = inputValue) => {
    if (!text.trim() || isLoading) return;

    const userMsg: ExtendedChatMessage = { role: 'user', text, timestamp: new Date() };
    setMessages(prev => [...prev, userMsg]);
    setInputValue("");
    setIsLoading(true);
    setPendingToolActions([]);

    try {
      // 使用后端 Health Agent API
      const response = await healthAgentService.chat({
        message: text,
        petId: pet.id || '',
        conversationId: conversationId || undefined,
      });
      
      // 保存对话 ID
      if (!conversationId) {
        setConversationId(response.conversationId);
      }
      
      // 更新建议问题
      if (response.suggestions && response.suggestions.length > 0) {
        setSuggestions(response.suggestions);
      }
      
      const assistantMsg: ExtendedChatMessage = { 
        role: 'assistant', 
        text: response.response, 
        timestamp: new Date(),
        toolActions: response.toolActions,
      };
      setMessages(prev => [...prev, assistantMsg]);
    } catch (error) {
      console.error('Health Agent 请求失败:', error);
      const errorMsg: ExtendedChatMessage = { 
        role: 'assistant', 
        text: '抱歉，我暂时无法回答。请稍后再试。', 
        timestamp: new Date() 
      };
      setMessages(prev => [...prev, errorMsg]);
    } finally {
      setIsLoading(false);
      setPendingToolActions([]);
    }
  };

  const config = useMemo(() => {
    // 使用真实数据或空数组
    const getData = (type: TabType): HealthTrendData[] => {
      if (!trendData) return [];
      switch (type) {
        case 'activity': return trendData.activity;
        case 'sleep': return trendData.sleep;
        case 'heartRate': return trendData.heartRate;
        case 'calories': return trendData.calories;
        default: return [];
      }
    };
    
    const data = getData(activeTab);
    const summary = trendData?.summary;
    
    switch(activeTab) {
      case 'sleep':
        return {
          title: '睡眠趋势',
          value: summary ? `${summary.avgSleep.toFixed(1)}h` : '--',
          unit: 'h',
          trend: '+3%',
          isPositive: true,
          color: '#3b82f6',
          data,
        };
      case 'heartRate':
        return {
          title: '心率趋势',
          value: summary ? `${Math.round(summary.avgHeartRate)} bpm` : '--',
          unit: 'bpm',
          trend: '+2%',
          isPositive: true,
          color: '#ef4444',
          data,
        };
      case 'calories':
        return {
          title: '热量消耗',
          value: summary ? `${(summary.totalCalories / 1000).toFixed(1)}k` : '--',
          unit: 'kcal',
          trend: '+15%',
          isPositive: true,
          color: '#f87171',
          data,
        };
      default:
        return {
          title: '活动趋势',
          value: summary ? `${summary.avgActivity.toFixed(0)}min` : '--',
          unit: 'min',
          trend: '+12%',
          isPositive: true,
          color: '#31d2e8',
          data,
        };
    }
  }, [activeTab, trendData]);

  return (
    <div className="flex flex-col min-h-full bg-[#f6f8f8] pb-32">
      <header className="flex items-center bg-white/90 p-4 pb-2 justify-between sticky top-0 z-40 backdrop-blur-md">
        <div className="flex items-center gap-3">
          <div className="bg-center bg-no-repeat aspect-square bg-cover rounded-full size-10 border-2 border-[#31d2e8]/20" style={{backgroundImage: `url(${pet.avatar || 'https://lh3.googleusercontent.com/aida-public/AB6AXuBCtUnGhZGFLRzkKwv7ALb8sz0nauqVY6PWJruCuzdyeEzKpuornSwnuRaq2E50Id8Xc9ugn-VQvoMy7vdFu6QyvL4ZeYZhNOXDdvrWOGVdHmJ2LjQCzLnLZLf8-juseESPt4QAqQ8kqg9qy9x-kRHq8L27R64D3N7aFrTv5KiMx8aGY9hpDrTfcNpNqmA29oMJRdJV-I4rMNS-081A0cmZrrAvFp4NmNFHm74KdvNJ-R1A1Er4nhVkK-choiBni1w6RS7vVT3t7hA'})`}}></div>
          <h2 className="text-[#111814] text-lg font-bold">健康中心</h2>
        </div>
        <button onClick={onNotificationClick} className="p-2 hover:bg-black/5 rounded-full active:scale-90 transition-transform relative">
          <span className="material-symbols-outlined">notifications</span>
          <span className="absolute top-2 right-2 w-2 h-2 bg-red-500 rounded-full border border-white"></span>
        </button>
      </header>

      {/* 顶部主统计展示 */}
      <section className="px-4 py-4">
        <div className="bg-white rounded-[2.5rem] p-6 shadow-sm border border-gray-100 flex flex-col gap-6 relative overflow-hidden">
          <div className="absolute top-0 right-0 w-32 h-32 bg-[#31d2e8]/5 rounded-full blur-3xl -mr-10 -mt-10 pointer-events-none"></div>
          
          <div className="flex justify-between items-start">
            <div className="flex flex-col">
              <span className="text-xs font-bold text-gray-400 uppercase tracking-widest mb-1">{config.title}</span>
              <div className="flex items-baseline gap-1">
                <span className="text-5xl font-black text-[#111814] tracking-tight">{isLoadingTrends ? '...' : config.value}</span>
                <span className="text-sm font-bold text-gray-400">{timeRange === 'week' ? '平均/日' : '总计'}</span>
              </div>
            </div>
            <div className="flex flex-col items-end gap-2 relative z-10">
              <div className="bg-gray-100 p-1 rounded-xl flex items-center">
                {(['week', 'month', 'year'] as TimeRange[]).map((r) => (
                  <button 
                    key={r}
                    onClick={() => setTimeRange(r)}
                    className={`px-3 py-1 rounded-lg text-[10px] font-black uppercase transition-all ${timeRange === r ? 'bg-white shadow-sm text-[#111814]' : 'text-gray-400'}`}
                  >
                    {r === 'week' ? '周' : r === 'month' ? '月' : '年'}
                  </button>
                ))}
              </div>
              <div className={`flex items-center gap-1 px-3 py-1 rounded-full text-[10px] font-bold ${config.isPositive ? 'bg-green-50 text-green-600' : 'bg-red-50 text-red-600'}`}>
                <span className="material-symbols-outlined text-[14px]">{config.isPositive ? 'trending_up' : 'trending_down'}</span>
                {config.trend}
              </div>
            </div>
          </div>

          <div className="h-[200px] w-full mt-2 relative">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={config.data} margin={{ top: 10, right: 10, left: 10, bottom: 0 }}>
                <defs>
                  <linearGradient id="chartGradient" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor={config.color} stopOpacity={0.25}/>
                    <stop offset="100%" stopColor={config.color} stopOpacity={0}/>
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f1f5f9" />
                <XAxis 
                  dataKey="name" 
                  axisLine={false} 
                  tickLine={false} 
                  tick={{fontSize: 10, fill: '#94a3b8', fontWeight: 'bold'}}
                  interval={timeRange === 'year' ? 'preserveStartEnd' : timeRange === 'month' ? 4 : 0}
                  dy={10}
                />
                <Tooltip 
                  cursor={{ stroke: config.color, strokeWidth: 1, strokeDasharray: '3 3' }}
                  content={<CustomTooltip unit={config.unit} color={config.color} />}
                  wrapperStyle={{ pointerEvents: 'none', outline: 'none' }}
                />
                <Area 
                  type="monotone" 
                  dataKey="value" 
                  stroke={config.color} 
                  strokeWidth={3} 
                  fill="url(#chartGradient)"
                  animationDuration={1000}
                  animationEasing="ease-in-out"
                  activeDot={{ r: 6, strokeWidth: 0, fill: config.color, className: 'drop-shadow-sm' }}
                  isAnimationActive={true}
                />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>
      </section>

      {/* 底部功能切换卡片 */}
      <section className="px-4 py-2">
        <div className="flex gap-4 overflow-x-auto no-scrollbar pb-4">
          <QuickStatCard 
            icon="pets" 
            label="活动量" 
            active={activeTab === 'activity'} 
            onClick={() => setActiveTab('activity')}
            color="text-[#31d2e8]"
            bgColor="bg-cyan-50"
          />
          <QuickStatCard 
            icon="bedtime" 
            label="睡眠" 
            active={activeTab === 'sleep'} 
            onClick={() => setActiveTab('sleep')}
            color="text-blue-500"
            bgColor="bg-blue-50"
          />
          <QuickStatCard 
            icon="favorite" 
            label="心率" 
            active={activeTab === 'heartRate'} 
            onClick={() => setActiveTab('heartRate')}
            color="text-red-500"
            bgColor="bg-red-50"
          />
          <QuickStatCard 
            icon="local_fire_department" 
            label="卡路里" 
            active={activeTab === 'calories'} 
            onClick={() => setActiveTab('calories')}
            color="text-orange-500"
            bgColor="bg-orange-50"
          />
        </div>
      </section>

      {/* AI Assistant Section */}
      <section className="flex-1 flex flex-col mt-4 rounded-t-[3rem] bg-white shadow-[0_-10px_40px_rgba(0,0,0,0.03)] border-t border-gray-50 p-8">
        <div className="flex items-center gap-3 mb-8">
          <div className="bg-[#31d2e8]/15 p-3 rounded-2xl">
            <span className="material-symbols-outlined text-[#31d2e8] text-[28px] fill-icon">smart_toy</span>
          </div>
          <div className="flex flex-col">
            <h2 className="text-[#111814] text-xl font-black tracking-tight">AI 医疗助手</h2>
            <div className="flex items-center gap-1.5">
              <div className="size-2 bg-green-500 rounded-full"></div>
              <span className="text-[10px] font-bold text-gray-400 uppercase tracking-widest">实时健康诊断中</span>
            </div>
          </div>
        </div>

        <div className="flex flex-col gap-6 mb-6">
          {messages.map((msg, i) => (
            <div key={i} className={`flex items-start gap-4 ${msg.role === 'user' ? 'flex-row-reverse' : ''}`}>
              <div className={`size-10 shrink-0 rounded-2xl flex items-center justify-center text-white shadow-sm mt-1 transition-transform hover:scale-105 ${msg.role === 'user' ? 'bg-[#31d2e8]' : 'bg-black'}`}>
                <span className="material-symbols-outlined text-[20px]">{msg.role === 'user' ? 'person' : 'medical_services'}</span>
              </div>
              <div className={`flex flex-col gap-2 max-w-[80%] ${msg.role === 'user' ? 'items-end' : ''}`}>
                {/* 工具调用动画 */}
                {msg.role === 'assistant' && msg.toolActions && msg.toolActions.length > 0 && (
                  <div className="flex flex-wrap gap-2 mb-2 animate-in fade-in slide-in-from-left-2 duration-300">
                    {msg.toolActions.map((action, idx) => (
                      <div 
                        key={idx}
                        className="flex items-center gap-2 px-3 py-1.5 bg-gradient-to-r from-[#31d2e8]/10 to-[#28c566]/10 rounded-full border border-[#31d2e8]/20"
                        style={{ animationDelay: `${idx * 100}ms` }}
                      >
                        <span className="material-symbols-outlined text-[16px] text-[#31d2e8]">{action.icon}</span>
                        <span className="text-xs font-medium text-gray-600">{action.name}</span>
                        <span className="material-symbols-outlined text-[14px] text-green-500">check_circle</span>
                      </div>
                    ))}
                  </div>
                )}
                <div className={`p-5 rounded-3xl text-[15px] leading-relaxed shadow-sm transition-all ${msg.role === 'user' ? 'bg-[#31d2e8] text-white rounded-tr-none' : 'bg-gray-50 text-[#111814] rounded-tl-none border border-gray-100'}`}>
                  {msg.text}
                </div>
                <span className="text-[10px] text-gray-400 px-1 font-bold">{msg.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span>
              </div>
            </div>
          ))}
          {isLoading && (
            <div className="flex items-start gap-4">
              <div className="size-10 shrink-0 rounded-2xl flex items-center justify-center text-white shadow-sm mt-1 bg-black">
                <span className="material-symbols-outlined text-[20px]">medical_services</span>
              </div>
              <div className="flex flex-col gap-2">
                {/* 加载中的工具调用动画 */}
                <div className="flex items-center gap-2 px-3 py-1.5 bg-gradient-to-r from-[#31d2e8]/10 to-[#28c566]/10 rounded-full border border-[#31d2e8]/20 animate-pulse">
                  <div className="size-4 rounded-full border-2 border-[#31d2e8] border-t-transparent animate-spin"></div>
                  <span className="text-xs font-medium text-gray-500">正在分析数据...</span>
                </div>
                <div className="flex items-center gap-2 text-xs text-gray-400">
                  <div className="flex gap-1">
                    <div className="size-1 bg-[#31d2e8] rounded-full animate-bounce"></div>
                    <div className="size-1 bg-[#31d2e8] rounded-full animate-bounce [animation-delay:0.2s]"></div>
                    <div className="size-1 bg-[#31d2e8] rounded-full animate-bounce [animation-delay:0.4s]"></div>
                  </div>
                  AI 正在深度分析多维数据...
                </div>
              </div>
            </div>
          )}
          <div ref={chatEndRef} />
        </div>

        <div className="flex gap-3 overflow-x-auto no-scrollbar py-2">
          {suggestions.map(s => (
            <button key={s} onClick={() => handleSend(s)} className="flex-shrink-0 px-5 py-2.5 rounded-full border border-gray-100 bg-white hover:border-[#31d2e8] hover:text-[#31d2e8] text-gray-500 text-xs font-bold transition-all shadow-sm">
              {s}
            </button>
          ))}
        </div>

        <div className="mt-6 relative">
          <input 
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleSend()}
            className="w-full h-16 pl-6 pr-16 rounded-3xl bg-gray-50 border-none focus:ring-2 focus:ring-[#31d2e8]/30 text-[#111814] font-medium placeholder-gray-400 transition-all" 
            placeholder="询问爱宠健康问题..." 
            type="text" 
          />
          <button 
            onClick={() => handleSend()}
            disabled={isLoading}
            className="absolute right-2 top-2 size-12 flex items-center justify-center bg-black hover:bg-gray-800 rounded-2xl text-white transition-all shadow-lg active:scale-95 disabled:opacity-50"
          >
            <span className="material-symbols-outlined text-[24px]">arrow_upward</span>
          </button>
        </div>
      </section>
    </div>
  );
};

const QuickStatCard: React.FC<{ 
  icon: string; 
  label: string; 
  active: boolean; 
  onClick: () => void;
  color: string;
  bgColor: string;
}> = ({ icon, label, active, onClick, color, bgColor }) => (
  <button 
    onClick={onClick}
    className={`flex-shrink-0 flex flex-col items-center gap-2 p-4 rounded-[2rem] border transition-all duration-300 min-w-[90px] ${active ? 'bg-white border-[#31d2e8] shadow-lg shadow-[#31d2e8]/10' : 'bg-white border-transparent shadow-sm grayscale opacity-60'}`}
  >
    <div className={`size-12 rounded-2xl flex items-center justify-center ${active ? bgColor : 'bg-gray-50'}`}>
      <span className={`material-symbols-outlined ${active ? color : 'text-gray-400'} text-[24px] fill-icon leading-none`}>{icon}</span>
    </div>
    <span className={`text-[10px] font-black uppercase tracking-widest ${active ? 'text-[#111814]' : 'text-gray-400'}`}>{label}</span>
  </button>
);

export default HealthView;

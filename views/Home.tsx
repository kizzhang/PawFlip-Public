
import React, { useState, useRef } from 'react';
import { PetInfo } from '../types';
import Model3DViewer from '../components/Model3DViewer';

interface HomeProps {
  pet: PetInfo;
  onOpenCamera: () => void;
  onNotificationClick: () => void;
  onOpenTrends: () => void;
  onMenuClick: () => void;
  onGoToRegister?: () => void;
}

const HomeView: React.FC<HomeProps> = ({ pet, onOpenCamera, onNotificationClick, onOpenTrends, onMenuClick, onGoToRegister }) => {
  // 检查宠物是否已注册
  const isPetRegistered = !!pet.id;

  // 如果宠物未注册，显示引导界面
  if (!isPetRegistered && onGoToRegister) {
    return (
      <div className="flex flex-col h-full bg-[#f6f8f8] items-center justify-center px-8">
        <div className="bg-white rounded-3xl p-8 shadow-lg max-w-sm w-full text-center">
          <div className="w-20 h-20 bg-gradient-to-br from-[#31d2e8] to-[#28c566] rounded-full flex items-center justify-center mx-auto mb-6">
            <span className="material-symbols-outlined text-white text-3xl">pets</span>
          </div>
          
          <h2 className="text-2xl font-bold text-[#111814] mb-4">欢迎使用 PawFlip</h2>
          <p className="text-gray-500 text-sm mb-6 leading-relaxed">
            请先完成宠物档案注册，开始您的智能宠物管家之旅。
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
              注册后即可享受完整的智能管家功能
            </p>
          </div>
        </div>
      </div>
    );
  }

  // 3D 互动状态
  const [rotation, setRotation] = useState({ x: -10, y: 15 });
  const [zoom, setZoom] = useState(1);
  const isDragging = useRef(false);
  const lastPos = useRef({ x: 0, y: 0 });
  const [isOffline, setIsOffline] = useState(false); // Simulated connection state
  const [showAlert, setShowAlert] = useState(true); // Control visibility of the diagnostic block

  // 3D 互动逻辑
  const handleStart = (e: React.MouseEvent | React.TouchEvent) => {
    isDragging.current = true;
    const pos = 'touches' in e ? e.touches[0] : (e as React.MouseEvent);
    lastPos.current = { x: pos.clientX, y: pos.clientY };
  };

  const handleMove = (e: React.MouseEvent | React.TouchEvent) => {
    if (!isDragging.current) return;
    const pos = 'touches' in e ? e.touches[0] : (e as React.MouseEvent);
    const dx = pos.clientX - lastPos.current.x;
    const dy = pos.clientY - lastPos.current.y;
    
    setRotation(prev => ({
      x: Math.max(-30, Math.min(30, prev.x - dy * 0.5)),
      y: prev.y + dx * 0.5
    }));
    
    lastPos.current = { x: pos.clientX, y: pos.clientY };
  };

  const handleEnd = () => {
    isDragging.current = false;
  };

  const handleWheel = (e: React.WheelEvent) => {
    setZoom(prev => Math.max(0.7, Math.min(1.5, prev - e.deltaY * 0.001)));
  };

  return (
    <div className="flex flex-col min-h-full bg-[#f6f8f8] relative select-none pb-32">
      {/* Top Status Bar - Match Screenshot Header */}
      <div className="sticky top-0 z-40 flex items-center justify-between p-4 pt-6 pb-2 bg-[#f6f8f8]/80 backdrop-blur-md">
        <div className="flex items-center gap-3">
          <button 
            onClick={onMenuClick}
            className="flex items-center justify-center p-1 rounded-xl hover:bg-black/5 active:scale-90 transition-all"
          >
            <span className="material-symbols-outlined text-[#111814] text-[32px]">menu</span>
          </button>
          <span className="text-5xl font-black tracking-tighter text-[#111814] opacity-20">12</span>
        </div>

        <div className="flex items-center gap-2 px-4 py-1.5 bg-white rounded-full shadow-sm border border-gray-100">
          <span className="material-symbols-outlined text-[#31d2e8] text-[18px] fill-icon">bolt</span>
          <span className="text-xs font-bold tracking-tight text-[#111814]">{pet.battery}%</span>
        </div>

        <button 
          onClick={onNotificationClick}
          className="flex size-10 items-center justify-center rounded-full hover:bg-black/5 active:scale-90 transition-all relative"
        >
          <span className="material-symbols-outlined text-[#111814] text-[28px]">notifications</span>
          <span className="absolute top-2 right-2 w-2.5 h-2.5 bg-red-500 rounded-full border-2 border-[#f6f8f8]"></span>
        </button>
      </div>

      {/* Pet Tags & Info Section */}
      <section className="px-6 pt-2 pb-4">
        <div className="flex flex-col animate-in fade-in slide-in-from-top-4 duration-700">
          <div className="flex items-center gap-2 mb-4">
            <span className="px-3 py-1 bg-gray-200/60 rounded-lg text-xs font-bold text-[#111814]">{pet.age}</span>
            <span className="px-3 py-1 bg-gray-200/60 rounded-lg text-xs font-bold text-[#111814]">{pet.breed}</span>
          </div>
          
          <div className="flex items-center gap-2 px-3 py-1.5 bg-white/50 w-fit rounded-full border border-gray-100/50 shadow-sm">
            <div className="relative flex size-2">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-[#31d2e8] opacity-75"></span>
              <span className="relative inline-flex rounded-full size-2 bg-[#31d2e8]"></span>
            </div>
            <span className="text-[10px] font-black tracking-widest uppercase text-gray-500">AI 实时数字孪生已同步</span>
          </div>
        </div>
      </section>

      {/* Interactive 3D Model Section */}
      <section className="relative w-full h-[360px] flex items-center justify-center overflow-visible mt-2">
        {pet.model_3d_url ? (
          // 真正的 3D 模型
          <div className="relative w-full h-full max-w-md px-6">
            <Model3DViewer 
              modelUrl={pet.model_3d_url} 
              fallbackImage={pet.model_3d_preview || pet.avatar}
            />
            
            {/* 3D 标识 */}
            <div className="absolute bottom-4 right-8 bg-[#31d2e8] text-white text-[10px] font-bold px-3 py-1.5 rounded-full flex items-center gap-1.5 shadow-lg z-10">
              <span className="material-symbols-outlined text-sm">view_in_ar</span>
              3D 数字孪生
            </div>
            
            {/* 操作提示 */}
            <div className="absolute bottom-4 left-8 bg-black/60 text-white text-[10px] px-3 py-1.5 rounded-full backdrop-blur-sm z-10 flex items-center gap-2">
              <span className="material-symbols-outlined text-sm animate-bounce">gesture</span>
              拖拽旋转 · 滚轮缩放
            </div>
          </div>
        ) : (
          // 备用：CSS 3D 效果
          <div 
            className="relative w-[300px] h-[300px] perspective-1000 touch-none cursor-grab active:cursor-grabbing flex items-center justify-center"
            onMouseDown={handleStart}
            onMouseMove={handleMove}
            onMouseUp={handleEnd}
            onMouseLeave={handleEnd}
            onTouchStart={handleStart}
            onTouchMove={handleMove}
            onTouchEnd={handleEnd}
            onWheel={handleWheel}
          >
            {/* Decorative Background */}
            <div className="absolute inset-0 bg-[radial-gradient(circle,rgba(49,210,232,0.08)_0%,transparent_70%)] pointer-events-none"></div>
            
            <div 
              className="relative size-full transition-transform duration-150 ease-out preserve-3d"
              style={{ transform: `rotateX(${rotation.x}deg) rotateY(${rotation.y}deg) scale(${zoom})` }}
            >
              {/* 3D Model Body */}
              <div className="absolute inset-4 bg-gray-200 rounded-[4rem] shadow-xl overflow-hidden border border-white translate-z-[15px] grayscale-[0.2]">
                <img 
                  src={pet.avatar || "https://lh3.googleusercontent.com/aida-public/AB6AXuAs-GNZCq_t9DksY8z2M15j_y3XUY4bygKLc1NyLHawgnhw6_mEPLegWzMM137J8Y89IC_YkepMAjKINPlmQDwhVkw5s29dM8CgXB7JJJqboaBl6eoxMJwPdocx8fUf6omn6zj50IIMQffIsNv2bF-e8ykiz21GB_PFH8NofUKDuR4nxeyb86oFpSIw454gJkgLuAPDudSRjGAmliVXoWLYmc2BdmI6u42J8J6HSs-pRHAOjJ36dsnGGPQI6bA_IWreCl737ySI9OQ"} 
                  className="w-full h-full object-cover opacity-80" 
                  alt="3D Digital Twin" 
                />
                <div className="absolute inset-0 bg-gradient-to-tr from-black/5 via-transparent to-white/10 pointer-events-none"></div>
              </div>
              
              {/* Tech Effects */}
              <div className="absolute inset-4 rounded-[4rem] border border-[#31d2e8]/20 animate-pulse translate-z-[30px] pointer-events-none"></div>
            </div>
            
            {/* Interaction Label */}
            <div className="absolute -bottom-6 left-1/2 -translate-x-1/2 flex items-center gap-2 px-4 py-2 bg-white/40 backdrop-blur-sm rounded-full text-[10px] font-bold text-[#31d2e8] uppercase tracking-widest pointer-events-none">
              <span className="material-symbols-outlined text-[18px] animate-bounce">gesture</span>
              点击旋转预览
            </div>
          </div>
        )}
      </section>

      {/* AI POV Button */}
      <section className="px-6 pt-12 pb-6">
        <button 
          onClick={onOpenCamera}
          className="group relative flex items-center justify-between gap-4 bg-[#111814] hover:bg-black text-white font-bold text-lg py-5 px-10 rounded-full shadow-2xl transition-all duration-300 w-full active:scale-95 overflow-hidden"
        >
          <div className="flex items-center gap-4">
            <span className="material-symbols-outlined text-[28px] text-[#31d2e8]">videocam</span>
            <span className="tracking-tight text-xl">开启 AI 第一视角</span>
          </div>
          <span className="material-symbols-outlined text-[24px] opacity-40">arrow_forward</span>
        </button>
      </section>

      {/* Health Stats Section */}
      <section className="flex flex-col gap-4 mt-2">
        <div className="px-6 flex items-center justify-between">
          <h2 className="text-2xl font-black text-[#111814] tracking-tight">今日状态</h2>
          <button onClick={onOpenTrends} className="text-xs font-bold text-[#31d2e8] hover:underline">查看趋势报告</button>
        </div>
        <div className="w-full overflow-x-auto no-scrollbar px-6 pb-4">
          <div className="flex gap-4 w-max">
            <StatCard 
              icon="pets" 
              label="步数" 
              value={`${(pet.steps / 1000).toFixed(1)}k`} 
              iconColor="text-orange-500" 
              bgColor="bg-orange-50" 
            />
            <StatCard 
              icon="monitor_heart" 
              label="健康值" 
              value={pet.healthScore.toString()} 
              iconColor="text-[#31d2e8]" 
              bgColor="bg-cyan-50" 
            />
            <StatCard 
              icon="restaurant" 
              label="饮食" 
              value={pet.nextFeeding} 
              iconColor="text-blue-500" 
              bgColor="bg-blue-50" 
            />
          </div>
        </div>
      </section>

      {/* Connectivity / Troubleshooting Section - Click to Dismiss as requested */}
      {showAlert && (
        <section className="px-6 py-4 animate-in fade-in slide-in-from-bottom duration-300">
          <div className={`transition-all duration-500 rounded-[2.5rem] p-6 flex flex-col gap-4 border-2 border-dashed relative overflow-hidden ${isOffline ? 'bg-red-50 border-red-200' : 'bg-white border-gray-100 hover:border-[#31d2e8]/30'}`}>
            <button 
              onClick={() => setShowAlert(false)}
              className="absolute top-4 right-4 text-gray-400 hover:text-gray-600 transition-colors"
            >
              <span className="material-symbols-outlined">close</span>
            </button>
            
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className={`size-10 rounded-xl flex items-center justify-center ${isOffline ? 'bg-red-100 text-red-500' : 'bg-gray-50 text-gray-400'}`}>
                  <span className="material-symbols-outlined">{isOffline ? 'error' : 'wifi_off'}</span>
                </div>
                <div>
                  <h3 className={`text-sm font-black tracking-tight ${isOffline ? 'text-red-900' : 'text-gray-400'}`}>
                    {isOffline ? '无法正常使用' : '连接诊断与支持'}
                  </h3>
                  <p className="text-[10px] text-gray-400 font-medium">
                    {isOffline ? '设备已断开连接，请检查蓝牙设置' : '如果功能无法正常使用，请尝试重置'}
                  </p>
                </div>
              </div>
              <button 
                onClick={(e) => { e.stopPropagation(); setIsOffline(!isOffline); }}
                className={`px-4 py-2 rounded-full text-[10px] font-black uppercase tracking-widest transition-all ${isOffline ? 'bg-red-500 text-white shadow-lg shadow-red-500/30' : 'bg-gray-100 text-gray-400 hover:bg-gray-200'}`}
              >
                {isOffline ? '重试连接' : '检查连接'}
              </button>
            </div>
          </div>
        </section>
      )}

      <style>{`
        .perspective-1000 { perspective: 1000px; }
        .preserve-3d { transform-style: preserve-3d; }
        .rotate-x-90 { transform: rotateX(90deg); }
        .translate-z-[-60px] { transform: translateZ(-60px) rotateX(90deg); }
        .translate-z-[15px] { transform: translateZ(15px); }
        .translate-z-[30px] { transform: translateZ(30px); }
        .translate-z-[40px] { transform: translateZ(40px); }
      `}</style>
    </div>
  );
};

const StatCard: React.FC<{ 
  icon: string; 
  label: string; 
  value: string; 
  iconColor: string; 
  bgColor: string;
}> = ({ icon, label, value, iconColor, bgColor }) => (
  <div className="w-40 bg-white rounded-[2.5rem] p-6 flex flex-col gap-6 shadow-sm border border-gray-100 hover:shadow-md transition-all active:scale-95 text-left">
    <div className={`size-12 ${bgColor} rounded-2xl flex items-center justify-center`}>
      <span className={`material-symbols-outlined ${iconColor} text-[26px] fill-icon leading-none`}>{icon}</span>
    </div>
    <div className="flex flex-col">
      <h3 className="text-3xl font-black text-[#111814] tracking-tight">{value}</h3>
      <p className="text-xs font-bold text-gray-400 uppercase tracking-widest mt-1">{label}</p>
    </div>
  </div>
);

export default HomeView;

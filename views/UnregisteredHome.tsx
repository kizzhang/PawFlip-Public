
import React from 'react';

interface UnregisteredHomeProps {
  onRegister: () => void;
  onLogin: () => void;
  onNotificationClick: () => void;
  onApiTest?: () => void;
}

const UnregisteredHomeView: React.FC<UnregisteredHomeProps> = ({ onRegister, onLogin, onNotificationClick, onApiTest }) => {
  return (
    <div className="relative flex h-full w-full flex-col overflow-hidden bg-[#f6f8f8]">
      {/* Header */}
      <div className="flex items-center justify-between p-4 pt-6 pb-2 z-20">
        {/* Placeholder to keep the badge centered since the menu button is removed */}
        <div className="size-10"></div>
        
        <div className="flex items-center gap-2 px-4 py-1.5 bg-white rounded-full shadow-sm border border-gray-100/50">
          <span className="material-symbols-outlined text-gray-400" style={{ fontSize: '18px' }}>link_off</span>
          <span className="text-xs font-bold tracking-wide text-gray-400 uppercase">未连接设备</span>
        </div>

        <button 
          onClick={onNotificationClick}
          className="flex size-10 shrink-0 items-center justify-center rounded-full hover:bg-black/5 transition-colors"
        >
          <span className="material-symbols-outlined fill-icon text-[#111814]" style={{ fontSize: '24px' }}>notifications</span>
        </button>
      </div>

      {/* Main Content */}
      <div className="flex flex-col items-center justify-center px-4 pt-10 z-20">
        <h1 className="text-4xl font-bold tracking-tight mb-2">欢迎使用</h1>
        <p className="text-[#638872] text-sm font-medium">智能宠物管家，让爱宠生活更精彩</p>
      </div>

      <div className="flex-1 relative w-full flex flex-col justify-end">
        <div className="absolute inset-0 top-0 bottom-40 flex items-center justify-center z-10 pointer-events-none">
          <div className="absolute inset-0 bg-[radial-gradient(circle_at_center,rgba(49,210,232,0.05)_0%,rgba(255,255,255,0)_75%)]"></div>
          <div className="relative flex flex-col items-center justify-center opacity-10 translate-y-[-20px]">
            <span className="material-symbols-outlined fill-icon text-[240px] text-gray-400">pets</span>
          </div>
        </div>
      </div>

      {/* Action Buttons */}
      <div className="absolute top-[60%] left-1/2 transform -translate-x-1/2 -translate-y-1/2 z-30 w-full px-8 flex flex-col items-center gap-4 pointer-events-none">
        {/* Register Button */}
        <button 
          onClick={onRegister}
          className="pointer-events-auto group relative flex items-center justify-center gap-3 bg-[#31d2e8] hover:scale-[1.02] active:scale-95 text-white font-bold text-lg py-5 px-8 rounded-2xl shadow-[0_10px_25px_-5px_rgba(49,210,232,0.4)] transition-all duration-300 w-full max-w-[300px] overflow-hidden border border-white/30"
        >
          <span className="material-symbols-outlined fill-icon relative z-10" style={{ fontSize: '28px' }}>add_reaction</span>
          <span className="relative z-10">注册新账户</span>
          <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/10 to-transparent translate-x-[-100%] group-hover:translate-x-[100%] transition-transform duration-700"></div>
        </button>

        {/* Login Button */}
        <button 
          onClick={onLogin}
          className="pointer-events-auto group relative flex items-center justify-center gap-3 bg-white hover:bg-gray-50 active:scale-95 text-[#31d2e8] font-bold text-lg py-4 px-8 rounded-2xl shadow-lg border-2 border-[#31d2e8]/20 transition-all duration-300 w-full max-w-[300px] overflow-hidden"
        >
          <span className="material-symbols-outlined relative z-10" style={{ fontSize: '24px' }}>login</span>
          <span className="relative z-10">已有账户登录</span>
        </button>

        {/* Quick Access Hint */}
        <p className="pointer-events-auto text-xs text-gray-400 text-center mt-2 max-w-[280px]">
          首次使用？先注册账户，然后添加您的宠物档案
        </p>

        {/* Debug API Test Button (only in development) */}
        {onApiTest && (
          <button 
            onClick={onApiTest}
            className="pointer-events-auto mt-4 px-4 py-2 bg-gray-100 text-gray-600 text-sm font-medium rounded-lg border border-gray-200 hover:bg-gray-200 transition-colors"
          >
            🔧 API 测试
          </button>
        )}
      </div>
      
      <div className="h-32"></div>
    </div>
  );
};

export default UnregisteredHomeView;

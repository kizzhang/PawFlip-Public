import React, { useEffect } from 'react';

interface LogoutSuccessProps {
  onComplete: () => void;
  duration?: number;
}

const LogoutSuccess: React.FC<LogoutSuccessProps> = ({ onComplete, duration = 2000 }) => {
  useEffect(() => {
    const timer = setTimeout(() => {
      onComplete();
    }, duration);

    return () => clearTimeout(timer);
  }, [onComplete, duration]);

  return (
    <div className="fixed inset-0 z-[300] flex items-center justify-center p-4">
      <div className="absolute inset-0 bg-black/30 backdrop-blur-sm animate-in fade-in duration-300"></div>
      <div className="relative bg-white rounded-3xl p-8 w-full max-w-sm shadow-2xl animate-in zoom-in-95 slide-in-from-bottom-4 duration-300">
        <div className="flex flex-col items-center text-center">
          {/* 成功图标 */}
          <div className="w-20 h-20 bg-gradient-to-br from-green-50 to-green-100 rounded-full flex items-center justify-center mb-6 shadow-inner">
            <span className="material-symbols-outlined text-green-500 text-3xl fill-icon">check_circle</span>
          </div>
          
          {/* 成功消息 */}
          <h3 className="text-2xl font-bold text-[#111814] mb-3">退出成功</h3>
          <p className="text-gray-500 text-sm mb-6 leading-relaxed">
            您已安全退出登录，感谢使用 PawFlip 智能宠物管家
          </p>
          
          {/* 加载动画 */}
          <div className="flex items-center gap-2 text-[#31d2e8]">
            <div className="w-4 h-4 border-2 border-[#31d2e8] border-t-transparent rounded-full animate-spin"></div>
            <span className="text-sm font-medium">正在跳转...</span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default LogoutSuccess;
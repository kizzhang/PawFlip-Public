
import React from 'react';

interface LandingProps {
  onStart: () => void;
}

const LandingView: React.FC<LandingProps> = ({ onStart }) => {
  return (
    <div className="relative flex h-full w-full flex-col overflow-hidden">
      {/* Background Image */}
      <div className="absolute inset-0 w-full h-full">
        <img 
          alt="Person cuddling pet" 
          className="w-full h-full object-cover" 
          src="https://lh3.googleusercontent.com/aida-public/AB6AXuChAwCw4HKiCViG-8bco-Dg5A_z1L2OlTRjhFbM9Y1Z0OTDtC-mt9ZFjt3DMNZuZE03PtGEb21PmviCVNrQorOr1ivdVcbXznUhxmPTTw68GxKLMnKk8cnX0cREN-O6JyG9G5i9rV_gqxH3Yp06MrgavcZme4DRFKUQ423RGMdhMAIbdT4vF93qrLHz89aWsOSbUUom6EDNLr3N4sUjpRuwydEc3AdMs8OMKMULsaMs1ODC9dle8UYcv2f15FZGyxSLYWJ9PkhzpXU"
        />
        {/* Gradient Overlay */}
        <div className="absolute inset-0 bg-gradient-to-b from-transparent via-black/40 to-black/80"></div>
      </div>

      {/* Content */}
      <div className="relative flex flex-col h-full justify-between z-10 px-8 pb-32 pt-20">
        <div></div>
        <div className="mb-8">
          <h1 className="text-4xl font-bold text-white mb-4 leading-tight">
            欢迎来到<br/>AI 宠物视界
          </h1>
          <p className="text-white/90 text-lg font-medium opacity-90">
            从它的视角，探索奇妙世界
          </p>
        </div>
        <div className="space-y-6">
          <button 
            onClick={onStart}
            className="w-full bg-[#31d2e8] hover:bg-[#31d2e8]/90 text-white font-bold text-lg py-5 px-8 rounded-2xl shadow-[0_10px_25px_-5px_rgba(49,210,232,0.4)] transition-all duration-300 active:scale-95 flex items-center justify-center gap-2 border border-white/20"
          >
            <span>开始我的宠物之旅</span>
            <span className="material-symbols-outlined">arrow_forward</span>
          </button>
        </div>
      </div>
    </div>
  );
};

export default LandingView;

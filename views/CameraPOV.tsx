
import React, { useEffect, useState } from 'react';
import { PetInfo } from '../types';

interface CameraPOVProps {
  pet: PetInfo;
  onClose: () => void;
}

const CameraPOVView: React.FC<CameraPOVProps> = ({ pet, onClose }) => {
  const [stream, setStream] = useState<MediaStream | null>(null);

  useEffect(() => {
    let currentStream: MediaStream | null = null;
    const startCamera = async () => {
      try {
        // Try requesting the back camera first
        const s = await navigator.mediaDevices.getUserMedia({ 
          video: { facingMode: 'environment' }, 
          audio: true 
        });
        setStream(s);
        currentStream = s;
      } catch (err) {
        console.warn("Back camera not found, falling back to default camera:", err);
        try {
          // Fallback to any available camera
          const s = await navigator.mediaDevices.getUserMedia({ 
            video: true, 
            audio: true 
          });
          setStream(s);
          currentStream = s;
        } catch (fallbackErr) {
          console.error("Error accessing any camera:", fallbackErr);
        }
      }
    };
    startCamera();
    return () => {
      if (currentStream) {
        currentStream.getTracks().forEach(track => track.stop());
      }
    };
  }, []);

  return (
    <div className="fixed inset-0 z-[60] bg-black flex flex-col max-w-md mx-auto h-screen">
      {/* Background Video Simulator / Actual Camera */}
      <div className="absolute inset-0 z-0 bg-black overflow-hidden">
        {stream ? (
          <video 
            autoPlay 
            playsInline 
            muted 
            className="w-full h-full object-cover opacity-90 brightness-90"
            ref={video => { if (video) video.srcObject = stream; }}
          />
        ) : (
          <div className="relative w-full h-full">
            <img 
              alt="Dog POV" 
              className="w-full h-full object-cover opacity-90 brightness-90 grayscale-[10%]" 
              src="https://lh3.googleusercontent.com/aida-public/AB6AXuAYKtqJIGw1zjZfDw9fHRbVeXZvobqg67JUfK-xjYbCSpU9EcFG_A09xi7Dig99SO_Ci6ufoqOXWJkeU4zIemNcW2cFFb5hIYxNhKs1YMvbHtHBmWY0ydwArMJ42aRcBy6Y0kGDfG8pbz0ETOv8aoCvDhkeC9Hr7VLlD9TenN99EeTJZhNVmdPyU_kgmdAMthApuuXcjZ0vtdF1dpQBzTBUuBjhm-1XX60ThH654ev8py2IRzKfqWQCCTkUQV14Q1uzh6touQCU8S8" 
            />
            <div className="absolute inset-0 flex items-center justify-center">
               <div className="bg-black/60 backdrop-blur-md p-4 rounded-xl text-white text-xs text-center border border-white/10">
                 <span className="material-symbols-outlined mb-2 block">videocam_off</span>
                 正在连接摄像头...
               </div>
            </div>
          </div>
        )}
        <div className="absolute inset-0 bg-gradient-to-b from-black/40 via-transparent to-black/40 pointer-events-none"></div>
      </div>

      {/* HUD Header */}
      <div className="relative z-10 p-6 pt-12 flex justify-between items-start w-full">
        <div className="bg-black/30 backdrop-blur-md px-4 py-2 rounded-2xl border border-white/10">
          <div className="flex items-center gap-2">
            <div className="w-2 h-2 bg-red-500 rounded-full animate-pulse"></div>
            <span className="text-sm font-medium tracking-wide text-white">实时第一视角</span>
          </div>
          <div className="mt-1">
            <span className="text-xl font-bold text-white">{pet.name}</span>
          </div>
        </div>
        <div className="flex flex-col items-end gap-2">
          <div className="bg-black/30 backdrop-blur-md px-3 py-1 rounded-full border border-white/10 flex items-center gap-2">
            <span className="material-symbols-outlined text-[14px] text-green-400">signal_cellular_alt</span>
            <span className="text-[10px] font-bold text-white">4G+</span>
          </div>
          <div className="bg-black/30 backdrop-blur-md px-3 py-1 rounded-full border border-white/10 flex items-center gap-2">
            <span className="material-symbols-outlined text-[14px] text-[#31d2e8]">bolt</span>
            <span className="text-[10px] font-bold text-white">{pet.battery}%</span>
          </div>
        </div>
      </div>

      {/* Dynamic Overlays */}
      <div className="relative z-10 flex-1 flex flex-col justify-center px-6 gap-4 pointer-events-none">
        <div className="bg-black/30 backdrop-blur-md w-fit p-3 rounded-2xl border border-white/10 pointer-events-auto">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-red-500/20 rounded-lg">
              <span className="material-symbols-outlined text-red-400 fill-icon">favorite</span>
            </div>
            <div>
              <p className="text-[10px] text-gray-400 leading-none">心率</p>
              <p className="text-lg font-bold leading-tight text-white">88 <span className="text-[10px] font-normal">BPM</span></p>
            </div>
          </div>
        </div>
        <div className="bg-black/30 backdrop-blur-md w-fit p-3 rounded-2xl border border-white/10 pointer-events-auto">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-orange-500/20 rounded-lg">
              <span className="material-symbols-outlined text-orange-400 fill-icon">directions_run</span>
            </div>
            <div>
              <p className="text-[10px] text-gray-400 leading-none">状态</p>
              <p className="text-lg font-bold leading-tight text-white">活跃中</p>
            </div>
          </div>
        </div>
      </div>

      {/* Controls */}
      <div className="relative z-20 px-6 pb-12 flex flex-col items-center gap-8">
        <div className="flex items-center gap-10">
          <button className="flex flex-col items-center gap-2 group">
            <div className="w-12 h-12 bg-white/10 backdrop-blur-xl rounded-full flex items-center justify-center border border-white/20 active:scale-95">
              <span className="material-symbols-outlined text-white">videocam</span>
            </div>
            <span className="text-[10px] font-medium text-white/80">录制</span>
          </button>
          <button className="flex flex-col items-center gap-2 group">
            <div className="w-16 h-16 bg-white/10 backdrop-blur-xl rounded-full flex items-center justify-center border-2 border-white/40 active:scale-95">
              <span className="material-symbols-outlined text-white text-3xl">photo_camera</span>
            </div>
            <span className="text-[10px] font-medium text-white/80">拍照</span>
          </button>
          <button className="flex flex-col items-center gap-2 group">
            <div className="w-12 h-12 bg-white/10 backdrop-blur-xl rounded-full flex items-center justify-center border border-white/20 active:scale-95">
              <span className="material-symbols-outlined text-white">mic</span>
            </div>
            <span className="text-[10px] font-medium text-white/80">对讲</span>
          </button>
        </div>
        <button 
          onClick={onClose}
          className="w-full bg-white/20 backdrop-blur-md hover:bg-white/30 text-white font-bold py-4 rounded-2xl border border-white/20 transition-all active:scale-[0.98]"
        >
          关闭
        </button>
      </div>
    </div>
  );
};

export default CameraPOVView;

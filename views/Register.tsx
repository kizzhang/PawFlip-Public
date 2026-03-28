
import React, { useState, useRef, useEffect } from 'react';
import { PetInfo } from '../types';
import Model3DViewer from '../components/Model3DViewer';

interface RegisterProps {
  onComplete: (info: Partial<PetInfo>) => void;
  onBack: () => void;
}

const RegisterView: React.FC<RegisterProps> = ({ onComplete, onBack }) => {
  const [step, setStep] = useState(1); 
  const [name, setName] = useState('');
  const [breed, setBreed] = useState('金毛寻回犬');
  const [age, setAge] = useState('2');
  const [avatar, setAvatar] = useState<string | undefined>(undefined);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [isPairing, setIsPairing] = useState(false);
  const [isGenerating3D, setIsGenerating3D] = useState(false);

  // 3D 预览互动状态（仅用于备用 CSS 3D 效果）
  const [rotation, setRotation] = useState({ x: -10, y: 15 });
  const [zoom, setZoom] = useState(1);
  const isDragging = useRef(false);
  const lastPos = useRef({ x: 0, y: 0 });

  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleImageClick = () => {
    fileInputRef.current?.click();
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      const reader = new FileReader();
      reader.onloadstart = () => setIsAnalyzing(true);
      reader.onloadend = () => {
        setAvatar(reader.result as string);
        setTimeout(() => setIsAnalyzing(false), 1500);
      };
      reader.readAsDataURL(file);
    }
  };

  const startPairing = () => {
    setIsPairing(true);
    setTimeout(() => {
      setIsPairing(false);
      setStep(2);
    }, 2500);
  };

  // 3D 模型生成结果
  const [model3DResult, setModel3DResult] = useState<{
    model_3d_url?: string;
    model_3d_preview?: string;
    id?: string;
    user_id?: string;
    avatar_url?: string;
  } | null>(null);
  const [model3DError, setModel3DError] = useState<string | null>(null);

  const goToPreview = async () => {
    setStep(3);
    setIsGenerating3D(true);
    setModel3DError(null);
    
    try {
      // 导入 API 服务
      const { default: api } = await import('../services/api');
      
      // 检查用户是否已登录
      if (!api.auth.isLoggedIn()) {
        throw new Error('请先登录账号');
      }
      
      // 调用后端 API 创建宠物并生成 3D 模型
      if (avatar) {
        console.log('开始创建宠物并生成 3D 模型...');
        
        // 将 base64 转换为 File 对象
        const response = await fetch(avatar);
        const blob = await response.blob();
        const photoFile = new File([blob], 'pet-photo.jpg', { type: 'image/jpeg' });
        
        // 调用后端 API（会自动生成 3D 模型）
        const pet = await api.pets.createWith3DModel(name, breed, `${age}岁`, photoFile);
        console.log('宠物创建成功:', pet);
        console.log('3D 模型 URL:', pet.model_3d_url);
        console.log('3D 预览图 URL:', pet.model_3d_preview);
        
        // 保存 3D 模型结果
        setModel3DResult({
          model_3d_url: pet.model_3d_url,
          model_3d_preview: pet.model_3d_preview,
          id: pet.id,
          user_id: pet.user_id,
          avatar_url: pet.avatar_url
        });
        
        console.log('model3DResult 已设置');
      } else {
        throw new Error('请先上传宠物照片');
      }
      
    } catch (error: any) {
      console.error('3D 模型生成失败:', error);
      setModel3DError(error.message || '生成失败');
    } finally {
      setIsGenerating3D(false);
    }
  };

  const handleFinish = async () => {
    // 直接使用已生成的数据完成注册
    onComplete({
      id: model3DResult?.id,
      user_id: model3DResult?.user_id,
      name,
      breed,
      age: `${age}岁`,
      avatar: model3DResult?.avatar_url || avatar,
      model_3d_url: model3DResult?.model_3d_url,
      model_3d_preview: model3DResult?.model_3d_preview
    });
  };

  // 3D 互动逻辑（仅用于备用 CSS 3D 效果）
  const handleStart = (e: React.MouseEvent | React.TouchEvent) => {
    isDragging.current = true;
    const pos = 'touches' in e ? e.touches[0] : e;
    lastPos.current = { x: pos.clientX, y: pos.clientY };
  };

  const handleMove = (e: React.MouseEvent | React.TouchEvent) => {
    if (!isDragging.current) return;
    const pos = 'touches' in e ? e.touches[0] : e;
    const dx = pos.clientX - lastPos.current.x;
    const dy = pos.clientY - lastPos.current.y;
    
    setRotation(prev => ({
      x: Math.max(-45, Math.min(45, prev.x - dy * 0.5)),
      y: prev.y + dx * 0.5
    }));
    
    lastPos.current = { x: pos.clientX, y: pos.clientY };
  };

  const handleEnd = () => {
    isDragging.current = false;
  };

  const handleWheel = (e: React.WheelEvent) => {
    setZoom(prev => Math.max(0.5, Math.min(2, prev - e.deltaY * 0.001)));
  };

  return (
    <div className="flex flex-col h-full bg-[#f6f8f8] relative overflow-hidden select-none">
      {/* 顶部进度条 */}
      <div className="absolute top-0 left-0 w-full h-1 z-50">
        <div 
          className="h-full bg-[#31d2e8] transition-all duration-700 ease-out shadow-[0_0_12px_rgba(49,210,232,0.8)]"
          style={{ width: `${(step / 3) * 100}%` }}
        ></div>
      </div>

      <header className="relative z-10 px-6 pt-12 pb-2 flex items-center">
        {step < 3 && (
          <button 
            onClick={step === 1 ? onBack : () => setStep(step - 1)}
            className="size-10 flex items-center justify-center rounded-2xl bg-white shadow-sm hover:shadow-md transition-all active:scale-90"
          >
            <span className="material-symbols-outlined text-gray-500">arrow_back</span>
          </button>
        )}
        <div className="flex-1 text-center pr-10">
          <p className="text-[10px] font-black uppercase tracking-[0.2em] text-[#31d2e8] mb-1">
            {step === 1 ? 'Step 01: Hardware' : step === 2 ? 'Step 02: Profile' : 'Step 03: Digital Twin'}
          </p>
        </div>
      </header>

      <main className="flex-1 px-8 relative z-10 flex flex-col">
        {step === 1 && (
          <div className="flex-1 flex flex-col items-center justify-center animate-in fade-in slide-in-from-bottom-4 duration-500">
             <div className="text-center mb-12">
              <h1 className="text-3xl font-bold text-[#111814] mb-2 tracking-tight">连接硬件设备</h1>
              <p className="text-gray-400 font-medium text-sm">请长按项圈按钮 3 秒进入配对模式</p>
            </div>

            <div className="relative mb-16">
              <div className={`absolute inset-0 bg-[#31d2e8]/20 rounded-full ${isPairing ? 'animate-ping' : ''}`}></div>
              <div className="size-56 bg-white rounded-full shadow-2xl flex items-center justify-center relative z-10 border-4 border-[#31d2e8]/10 overflow-hidden">
                <span className={`material-symbols-outlined text-[#31d2e8] text-7xl ${isPairing ? 'animate-pulse' : ''} fill-icon`}>
                  {isPairing ? 'settings_input_antenna' : 'bluetooth'}
                </span>
                {isPairing && (
                  <div className="absolute inset-0 border-4 border-transparent border-t-[#31d2e8] rounded-full animate-spin"></div>
                )}
              </div>
            </div>

            <button 
              onClick={startPairing}
              disabled={isPairing}
              className="w-full h-16 bg-[#111814] text-white font-bold rounded-3xl shadow-xl active:scale-95 transition-all flex items-center justify-center gap-3 disabled:opacity-50"
            >
              <span className="material-symbols-outlined">{isPairing ? 'sync' : 'search'}</span>
              <span>{isPairing ? '正在建立加密连接...' : '寻找 PawFlip 智能项圈'}</span>
            </button>
          </div>
        )}

        {step === 2 && (
          <div className="flex flex-col animate-in fade-in slide-in-from-right-4 duration-500">
            <div className="mb-6">
              <h1 className="text-3xl font-bold text-[#111814] mb-2 tracking-tight">爱宠基本资料</h1>
              <p className="text-gray-400 font-medium text-sm">这些信息将用于优化 AI 的识别精度</p>
            </div>

            <div className="flex justify-center mb-8">
              <div className="relative group cursor-pointer" onClick={handleImageClick}>
                <input type="file" ref={fileInputRef} onChange={handleFileChange} accept="image/*" className="hidden" />
                <div className="size-32 rounded-[2.5rem] bg-white shadow-lg flex items-center justify-center border-4 border-white overflow-hidden relative">
                  {avatar ? (
                    <>
                      <img src={avatar} alt="Preview" className="w-full h-full object-cover" />
                      {isAnalyzing && (
                        <div className="absolute inset-0 bg-black/40 backdrop-blur-[2px] flex flex-col items-center justify-center">
                          <div className="w-full h-0.5 bg-[#31d2e8] absolute top-0 animate-[scan_2s_infinite] shadow-[0_0_15px_#31d2e8]"></div>
                          <p className="text-[10px] font-bold text-white drop-shadow-md">AI 扫描中...</p>
                        </div>
                      )}
                    </>
                  ) : (
                    <div className="flex flex-col items-center gap-1 opacity-40">
                      <span className="material-symbols-outlined text-4xl text-[#31d2e8]">add_a_photo</span>
                      <span className="text-[10px] font-bold text-[#31d2e8] uppercase">点击上传</span>
                    </div>
                  )}
                </div>
                <div className="absolute -bottom-1 -right-1 size-10 bg-[#31d2e8] rounded-2xl border-4 border-[#f6f8f8] flex items-center justify-center shadow-lg group-hover:scale-110 transition-transform">
                  <span className="material-symbols-outlined text-white text-xl">{avatar ? 'sync' : 'camera'}</span>
                </div>
              </div>
            </div>

            <div className="space-y-4">
              <div className="bg-white p-5 rounded-3xl shadow-sm border border-gray-100 flex flex-col gap-1 focus-within:ring-2 focus-within:ring-[#31d2e8]/20 transition-all">
                <label className="text-[10px] font-bold text-gray-400 uppercase tracking-widest px-1">昵称</label>
                <input type="text" value={name} onChange={(e) => setName(e.target.value)} placeholder="巴迪" className="w-full border-none p-1 text-lg font-bold text-[#111814] focus:ring-0" />
              </div>
              <div className="flex gap-4">
                <div className="flex-1 bg-white p-5 rounded-3xl shadow-sm border border-gray-100 flex flex-col gap-1">
                  <label className="text-[10px] font-bold text-gray-400 uppercase tracking-widest px-1">品种</label>
                  <select value={breed} onChange={(e) => setBreed(e.target.value)} className="w-full border-none p-1 text-base font-bold text-[#111814] focus:ring-0 bg-transparent">
                    <option>金毛寻回犬</option>
                    <option>拉布拉多</option>
                    <option>柯基</option>
                    <option>暹罗猫</option>
                  </select>
                </div>
                <div className="w-28 bg-white p-5 rounded-3xl shadow-sm border border-gray-100 flex flex-col gap-1">
                  <label className="text-[10px] font-bold text-gray-400 uppercase tracking-widest px-1">年龄</label>
                  <input type="number" value={age} onChange={(e) => setAge(e.target.value)} className="w-full border-none p-1 text-lg font-bold text-[#111814] focus:ring-0 bg-transparent" />
                </div>
              </div>
            </div>

            <button 
              onClick={goToPreview}
              disabled={!name.trim() || !avatar}
              className={`w-full h-16 rounded-3xl font-bold text-lg shadow-xl flex items-center justify-center gap-3 mt-8 transition-all active:scale-95 ${
                !name.trim() || !avatar ? 'bg-gray-200 text-gray-400' : 'bg-[#31d2e8] text-white shadow-[#31d2e8]/30'
              }`}
            >
              <span>生成数字孪生</span>
              <span className="material-symbols-outlined">cognition</span>
            </button>
          </div>
        )}

        {step === 3 && (
          <div className="flex-1 flex flex-col animate-in fade-in zoom-in-95 duration-700">
            <div className="text-center mb-4">
              <h1 className="text-2xl font-bold text-[#111814] mb-1">
                {isGenerating3D ? '点云重构中...' : '3D 数字孪生已完成'}
              </h1>
              <p className="text-gray-400 text-xs font-medium">
                {isGenerating3D ? 'AI 正在进行多维特征映射与骨架绑定' : '拖拽可旋转，滚轮可缩放预览模型'}
              </p>
            </div>

            {/* 3D 预览容器 */}
            <div className="flex-1 flex items-center justify-center relative">
              {/* 背景装饰 */}
              <div className="absolute inset-0 bg-[radial-gradient(circle_at_center,rgba(49,210,232,0.1)_0%,transparent_70%)]"></div>
              
              {isGenerating3D ? (
                // 建模动画
                <div className="relative size-64">
                   {/* 模拟点云 */}
                   <div className="absolute inset-0 flex items-center justify-center opacity-40">
                      <div className="grid grid-cols-6 gap-6">
                        {[...Array(36)].map((_, i) => (
                          <div key={i} className="size-1 bg-[#31d2e8] rounded-full animate-pulse" style={{animationDelay: `${i * 0.1}s`}}></div>
                        ))}
                      </div>
                   </div>
                   {/* 旋转环 */}
                   <div className="absolute inset-0 border-[3px] border-dashed border-[#31d2e8]/30 rounded-full animate-[spin_8s_linear_infinite]"></div>
                   <div className="absolute inset-4 border-[1px] border-[#31d2e8]/20 rounded-full animate-[spin_4s_linear_infinite_reverse]"></div>
                   {/* 中心扫描线 */}
                   <div className="absolute inset-x-0 h-1 bg-[#31d2e8] shadow-[0_0_15px_#31d2e8] animate-[v-scan_2s_ease-in-out_infinite] top-0"></div>
                </div>
              ) : model3DResult?.model_3d_url ? (
                // 真正的 3D 模型查看器
                <div className="relative w-full h-96 max-w-lg">
                  <Model3DViewer 
                    modelUrl={model3DResult.model_3d_url} 
                    fallbackImage={model3DResult.model_3d_preview || avatar}
                  />
                  
                  {/* 3D 模型成功标识 */}
                  <div className="absolute bottom-4 right-4 bg-[#31d2e8] text-white text-xs font-bold px-3 py-1.5 rounded-full flex items-center gap-2 shadow-lg z-10">
                    <span className="material-symbols-outlined text-sm">view_in_ar</span>
                    3D 模型
                  </div>
                  
                  {/* 操作提示 */}
                  <div className="absolute top-4 left-4 bg-black/60 text-white text-[10px] px-3 py-1.5 rounded-full backdrop-blur-sm z-10">
                    拖拽旋转 · 滚轮缩放
                  </div>
                </div>
              ) : (
                // 2D 预览（备用）- 使用 CSS 3D 效果
                <div 
                  className="relative size-64 transition-transform duration-100 ease-out preserve-3d"
                  style={{ transform: `rotateX(${rotation.x}deg) rotateY(${rotation.y}deg) scale(${zoom})` }}
                  onMouseDown={handleStart}
                  onMouseMove={handleMove}
                  onMouseUp={handleEnd}
                  onMouseLeave={handleEnd}
                  onTouchStart={handleStart}
                  onTouchMove={handleMove}
                  onTouchEnd={handleEnd}
                  onWheel={handleWheel}
                >
                  {/* 网格底座 */}
                  <div className="absolute -bottom-8 left-1/2 -translate-x-1/2 w-48 h-48 bg-[radial-gradient(circle,rgba(49,210,232,0.2)_0%,transparent_70%)] rounded-full rotate-x-90 translate-z-[-50px]"></div>
                  
                  {/* 模型预览图 */}
                  <div className="absolute inset-0 bg-white rounded-[3rem] shadow-2xl overflow-hidden border-2 border-white translate-z-[10px]">
                    <img 
                      src={model3DResult?.model_3d_preview || avatar} 
                      className="w-full h-full object-cover" 
                      alt="Model Preview" 
                    />
                    <div className="absolute inset-0 bg-gradient-to-tr from-black/20 via-transparent to-white/20 pointer-events-none"></div>
                  </div>
                  
                  {/* 全息效果层 */}
                  <div className="absolute inset-0 rounded-[3rem] border border-[#31d2e8]/40 animate-pulse translate-z-[25px]"></div>
                  <div className="absolute inset-0 bg-[#31d2e8]/10 backdrop-blur-[1px] rounded-[3rem] translate-z-[15px] mix-blend-overlay"></div>
                  
                  {/* 骨骼节点模拟 */}
                  <div className="absolute top-1/4 left-1/4 size-2 bg-[#31d2e8] rounded-full translate-z-[30px] shadow-[0_0_10px_#31d2e8]"></div>
                  <div className="absolute top-1/2 left-1/2 size-2 bg-[#31d2e8] rounded-full translate-z-[30px] shadow-[0_0_10px_#31d2e8]"></div>
                  <div className="absolute bottom-1/4 right-1/4 size-2 bg-[#31d2e8] rounded-full translate-z-[30px] shadow-[0_0_10px_#31d2e8]"></div>
                  
                  {/* 悬浮 UI */}
                  <div className="absolute -right-16 top-0 bg-white/80 backdrop-blur-md p-2 rounded-xl border border-gray-100 text-[8px] font-bold text-gray-500 translate-z-[40px] shadow-lg">
                    <p className="text-[#31d2e8] mb-1">DATA ANALYTICS</p>
                    <div className="w-12 h-1 bg-gray-100 rounded-full overflow-hidden mb-1">
                      <div className="w-4/5 h-full bg-[#31d2e8]"></div>
                    </div>
                    <p>VERIFIED ✓</p>
                  </div>
                </div>
              )}
            </div>

            <div className="pb-8 space-y-4">
              {/* 显示错误信息 */}
              {model3DError && !isGenerating3D && (
                <div className="bg-red-500/10 text-red-600 p-4 rounded-2xl flex items-center gap-3 animate-in fade-in">
                  <span className="material-symbols-outlined">error</span>
                  <div>
                    <p className="text-xs font-bold">生成失败</p>
                    <p className="text-[10px]">{model3DError}</p>
                  </div>
                </div>
              )}
              
              {/* 显示成功状态 */}
              {!isGenerating3D && !model3DError && (
                <div className="bg-[#111814] text-white p-4 rounded-2xl flex items-center justify-between animate-in fade-in slide-in-from-bottom-2">
                  <div className="flex items-center gap-3">
                    <span className="material-symbols-outlined text-[#31d2e8]">memory</span>
                    <div>
                      <p className="text-[10px] font-bold text-[#31d2e8] uppercase tracking-widest">
                        {model3DResult?.model_3d_url ? '3D 模型已生成' : 'AI 识别状态'}
                      </p>
                      <p className="text-xs font-medium">
                        {model3DResult?.model_3d_url ? '数字孪生创建成功 ✓' : '特征匹配度 99.2%'}
                      </p>
                    </div>
                  </div>
                  <div className="flex gap-1">
                    <div className="size-1.5 bg-[#31d2e8] rounded-full animate-bounce"></div>
                    <div className="size-1.5 bg-[#31d2e8] rounded-full animate-bounce [animation-delay:0.2s]"></div>
                    <div className="size-1.5 bg-[#31d2e8] rounded-full animate-bounce [animation-delay:0.4s]"></div>
                  </div>
                </div>
              )}
              
              <button 
                onClick={handleFinish}
                disabled={isGenerating3D}
                className={`w-full h-16 rounded-3xl font-bold text-lg shadow-xl flex items-center justify-center gap-3 transition-all active:scale-95 ${
                  isGenerating3D ? 'bg-gray-200 text-gray-400 cursor-wait' : 'bg-[#31d2e8] text-white shadow-[#31d2e8]/30'
                }`}
              >
                <span>{isGenerating3D ? '正在生成 3D 模型...' : '开始我的视界'}</span>
                <span className="material-symbols-outlined">{isGenerating3D ? 'cloud_sync' : 'celebration'}</span>
              </button>
            </div>
          </div>
        )}
      </main>

      <style>{`
        .perspective-1000 { perspective: 1000px; }
        .preserve-3d { transform-style: preserve-3d; }
        .rotate-x-90 { transform: rotateX(90deg); }
        .translate-z-[-50px] { transform: translateZ(-50px) rotateX(90deg); }
        .translate-z-[10px] { transform: translateZ(10px); }
        .translate-z-[15px] { transform: translateZ(15px); }
        .translate-z-[25px] { transform: translateZ(25px); }
        .translate-z-[30px] { transform: translateZ(30px); }
        .translate-z-[40px] { transform: translateZ(40px); }

        @keyframes scan {
          0% { top: -5%; }
          50% { top: 100%; }
          100% { top: -5%; }
        }
        @keyframes v-scan {
          0% { top: 0; }
          50% { top: 100%; }
          100% { top: 0; }
        }
      `}</style>
    </div>
  );
};

export default RegisterView;


import React, { useState, useEffect, useRef } from 'react';
import HomeView from './views/Home';
import HealthView from './views/Health';
import TrendsReportView from './views/TrendsReport';
import DiaryView from './views/Diary';
import SocialView from './views/Social';
import SettingsView from './views/Settings';
import CameraPOVView from './views/CameraPOV';
import LandingView from './views/Landing';
import UnregisteredHomeView from './views/UnregisteredHome';
import RegisterView from './views/Register';
import LoginView from './views/Login';
import UserRegisterView from './views/UserRegister';
import ApiTestView from './views/ApiTest';
import LogoutSuccess from './components/LogoutSuccess';
import { ViewState, PetInfo, SocialPost } from './types';

// 视频处理状态类型
export interface VideoProcessingState {
  isProcessing: boolean;
  processingStatus: string;
  processingProgress: number;
}

const NavItem: React.FC<{ active: boolean; icon: string; label: string; onClick: () => void }> = ({ active, icon, label, onClick }) => (
  <button 
    onClick={onClick}
    className="group flex flex-col items-center justify-center gap-1 flex-1 py-1 transition-all"
  >
    <span className={`material-symbols-outlined transition-colors text-[26px] ${active ? 'text-[#31d2e8] fill-icon' : 'text-gray-400'}`}>
      {icon}
    </span>
    <span className={`text-[10px] font-bold transition-colors ${active ? 'text-[#31d2e8]' : 'text-gray-400'}`}>
      {label}
    </span>
  </button>
);

const App: React.FC = () => {
  const [currentView, setCurrentView] = useState<ViewState>('landing');
  const [showNotifications, setShowNotifications] = useState(false);
  const [showMenu, setShowMenu] = useState(false);
  const [showLogoutSuccess, setShowLogoutSuccess] = useState(false);
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const [pet, setPet] = useState<PetInfo>({
    name: "巴迪",
    age: "2岁",
    breed: "金毛寻回犬",
    battery: 84,
    healthScore: 98,
    steps: 8432,
    nextFeeding: "18:00"
  });

  // 视频处理状态 - 提升到 App 层级以支持跨页面保持
  const [videoProcessing, setVideoProcessing] = useState<VideoProcessingState>({
    isProcessing: false,
    processingStatus: '',
    processingProgress: 0
  });
  
  // 后台生成完成的帖子（用于在 Social 组件中添加到列表）
  const [pendingPost, setPendingPost] = useState<SocialPost | null>(null);
  
  // 用于取消请求的 AbortController
  const abortControllerRef = useRef<AbortController | null>(null);
  const progressIntervalRef = useRef<NodeJS.Timeout | null>(null);

  // 视频处理相关函数
  const handleVideoUpload = async (file: File) => {
    // 创建新的 AbortController
    abortControllerRef.current = new AbortController();
    
    try {
      // 开始处理
      setVideoProcessing({
        isProcessing: true,
        processingStatus: '准备上传视频...',
        processingProgress: 0
      });
      
      // 检查宠物 ID
      const petId = pet.id;
      if (!petId) {
        throw new Error('请先完成宠物档案注册才能发布视频');
      }
      
      // 模拟进度更新
      const progressSteps = [
        { progress: 15, status: '📤 上传视频中...' },
        { progress: 35, status: '🎬 AI 正在分析视频内容...' },
        { progress: 55, status: '🔍 识别宠物行为和场景...' },
        { progress: 75, status: '✨ 生成精彩故事文案...' },
        { progress: 90, status: '📝 整理发布内容...' },
      ];
      
      // 启动进度动画
      let stepIndex = 0;
      progressIntervalRef.current = setInterval(() => {
        if (stepIndex < progressSteps.length) {
          const step = progressSteps[stepIndex];
          if (step) {
            setVideoProcessing(prev => ({
              ...prev,
              processingProgress: step.progress,
              processingStatus: step.status
            }));
          }
          stepIndex++;
        } else {
          // 超出范围时清除定时器
          if (progressIntervalRef.current) {
            clearInterval(progressIntervalRef.current);
            progressIntervalRef.current = null;
          }
        }
      }, 1500);
      
      // 导入 API 服务
      const { default: api } = await import('./services/api');
      
      // 调用后端 API 处理视频（传入 AbortSignal 支持取消）
      const result = await api.social.createVideoPost(
        petId, 
        file, 
        'api', 
        abortControllerRef.current?.signal
      );
      
      // 检查是否被取消
      if (abortControllerRef.current?.signal.aborted) {
        return null;
      }
      
      // 清除进度动画
      if (progressIntervalRef.current) {
        clearInterval(progressIntervalRef.current);
        progressIntervalRef.current = null;
      }
      
      setVideoProcessing(prev => ({
        ...prev,
        processingProgress: 100,
        processingStatus: '🎉 发布成功！'
      }));
      
      // 构建新帖子（添加安全检查防止白屏）
      // 注意：后端返回 snake_case，前端 types.ts 使用 camelCase
      const newPost: SocialPost = {
        id: result?.id || Date.now().toString(),
        user_id: result?.user_id || pet.user_id || '',
        pet_id: result?.pet_id || pet.id || '',
        author: result?.pet_name || pet.name,
        breed: result?.pet_breed || pet.breed,
        time: '刚刚',
        avatar: result?.pet_avatar || pet.avatar || 'https://lh3.googleusercontent.com/aida-public/AB6AXuBCtUnGhZGFLRzkKwv7ALb8sz0nauqVY6PWJruCuzdyeEzKpuornSwnuRaq2E50Id8Xc9ugn-VQvoMy7vdFu6QyvL4ZeYZhNOXDdvrWOGVdHmJ2LjQCzLnLZLf8-juseESPt4QAqQ8kqg9qy9x-kRHq8L27R64D3N7aFrTv5KiMx8aGY9hpDrTfcNpNqmA29oMJRdJV-I4rMNS-081A0cmZrrAvFp4NmNFHm74KdvNJ-R1A1Er4nhVkK-choiBni1w6RS7vVT3t7hA',
        content: result?.content || '今天又是充满探索的一天！',
        imageUrl: result?.image_url || 'https://images.unsplash.com/photo-1548199973-03cce0bbc87b?auto=format&fit=crop&q=80&w=800',
        likes: result?.likes || 0,
        comments: result?.comments || 0,
        isAiStory: (result as any)?.is_ai_story ?? true,
        diary_entry_id: result?.diary_entry_id,
        created_at: result?.created_at || new Date().toISOString()
      };
      
      // 保存帖子到 pendingPost（用于后台模式完成后添加到列表）
      setPendingPost(newPost);
      
      // 短暂延迟后重置状态
      setTimeout(() => {
        setVideoProcessing({
          isProcessing: false,
          processingStatus: '',
          processingProgress: 0
        });
      }, 800);
      
      return newPost;
      
    } catch (error: any) {
      // 检查是否是取消导致的错误
      if (error.name === 'AbortError' || abortControllerRef.current?.signal.aborted) {
        console.log('视频上传已取消');
        return null;
      }
      
      console.error('视频上传失败:', error);
      setVideoProcessing(prev => ({
        ...prev,
        processingStatus: '❌ ' + error.message,
        processingProgress: 0
      }));
      
      // 3秒后重置状态
      setTimeout(() => {
        setVideoProcessing({
          isProcessing: false,
          processingStatus: '',
          processingProgress: 0
        });
      }, 3000);
      
      return null;
    } finally {
      // 清理进度定时器
      if (progressIntervalRef.current) {
        clearInterval(progressIntervalRef.current);
        progressIntervalRef.current = null;
      }
    }
  };

  // 取消处理
  const handleCancelProcessing = () => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }
    if (progressIntervalRef.current) {
      clearInterval(progressIntervalRef.current);
      progressIntervalRef.current = null;
    }
    setVideoProcessing({
      isProcessing: false,
      processingStatus: '',
      processingProgress: 0
    });
  };

  // 检查登录状态
  useEffect(() => {
    const checkAuthStatus = async () => {
      try {
        const { default: api } = await import('./services/api');
        const loggedIn = api.auth.isLoggedIn();
        setIsLoggedIn(loggedIn);
        
        if (loggedIn) {
          // 如果已登录，尝试获取用户信息和宠物信息
          try {
            const user = await api.auth.getMe();
            console.log('当前用户:', user);
            
            // 获取宠物列表
            const pets = await api.pets.getAll();
            console.log('初始化时获取到的宠物列表:', pets);
            
            if (pets.length > 0) {
              const firstPet = pets[0];
              setPet({
                id: firstPet.id,
                user_id: firstPet.user_id,
                name: firstPet.name,
                age: firstPet.age,
                breed: firstPet.breed,
                battery: firstPet.battery || 84,
                healthScore: firstPet.health_score || 98,
                steps: firstPet.steps || 8432,
                nextFeeding: firstPet.next_feeding || "18:00",
                avatar: firstPet.avatar_url,
                model_3d_url: firstPet.model_3d_url,
                model_3d_preview: firstPet.model_3d_preview
              });
              console.log('初始化时设置宠物信息:', firstPet);
              setCurrentView('home');
            } else {
              // 已登录但没有宠物，跳转到宠物注册
              console.log('用户已登录但没有宠物，跳转到宠物注册');
              setCurrentView('register');
            }
          } catch (error) {
            console.error('获取用户信息失败:', error);
            // 如果获取失败，可能 token 已过期，清除登录状态
            api.auth.logout();
            setIsLoggedIn(false);
            console.log('Token可能已过期，清除登录状态');
          }
        }
      } catch (error) {
        console.error('检查认证状态失败:', error);
      }
    };
    
    checkAuthStatus();
  }, []);

  const handleLogin = async () => {
    setIsLoggedIn(true);
    
    // 登录成功后，获取用户的宠物信息
    try {
      const { default: api } = await import('./services/api');
      
      // 获取宠物列表
      const pets = await api.pets.getAll();
      console.log('登录后获取到的宠物列表:', pets);
      
      if (pets.length > 0) {
        const firstPet = pets[0];
        setPet({
          id: firstPet.id,
          user_id: firstPet.user_id,
          name: firstPet.name,
          age: firstPet.age,
          breed: firstPet.breed,
          battery: firstPet.battery || 84,
          healthScore: firstPet.health_score || 98,
          steps: firstPet.steps || 8432,
          nextFeeding: firstPet.next_feeding || "18:00",
          avatar: firstPet.avatar_url,
          model_3d_url: firstPet.model_3d_url,
          model_3d_preview: firstPet.model_3d_preview
        });
        console.log('登录后设置宠物信息:', firstPet);
        setCurrentView('home');
      } else {
        // 已登录但没有宠物，跳转到宠物注册
        console.log('用户已登录但没有宠物，跳转到注册页面');
        setCurrentView('register');
      }
    } catch (error) {
      console.error('登录后获取宠物信息失败:', error);
      // 如果获取失败，仍然跳转到首页，但宠物信息可能不完整
      console.log('获取宠物信息失败，但仍跳转到首页');
      setCurrentView('home');
    }
  };

  const handleUserRegisterSuccess = async () => {
    setIsLoggedIn(true);
    
    // 用户注册成功后，检查是否已有宠物信息
    try {
      const { default: api } = await import('./services/api');
      
      // 获取宠物列表
      const pets = await api.pets.getAll();
      if (pets.length > 0) {
        const firstPet = pets[0];
        setPet({
          id: firstPet.id,
          user_id: firstPet.user_id,
          name: firstPet.name,
          age: firstPet.age,
          breed: firstPet.breed,
          battery: firstPet.battery || 84,
          healthScore: firstPet.health_score || 98,
          steps: firstPet.steps || 8432,
          nextFeeding: firstPet.next_feeding || "18:00",
          avatar: firstPet.avatar_url,
          model_3d_url: firstPet.model_3d_url,
          model_3d_preview: firstPet.model_3d_preview
        });
        console.log('用户注册后发现已有宠物信息，直接跳转到首页:', firstPet);
        setCurrentView('home');
      } else {
        // 用户注册成功但没有宠物，跳转到宠物注册
        console.log('用户注册成功但没有宠物，跳转到宠物注册页面');
        setCurrentView('register');
      }
    } catch (error) {
      console.error('用户注册后获取宠物信息失败:', error);
      // 如果获取失败，跳转到宠物注册页面
      setCurrentView('register');
    }
  };

  const handleRegisterComplete = (info: Partial<PetInfo>) => {
    setPet(prev => ({ ...prev, ...info }));
    setCurrentView('home');
  };

  const handleLogout = async () => {
    try {
      const { default: api } = await import('./services/api');
      
      // 调用API退出登录
      api.auth.logout();
      
      // 清除本地状态
      setIsLoggedIn(false);
      setPet({
        name: "巴迪",
        age: "2岁",
        breed: "金毛寻回犬",
        battery: 84,
        healthScore: 98,
        steps: 8432,
        nextFeeding: "18:00"
      });
      
      // 关闭菜单
      setShowMenu(false);
      
      // 显示退出成功提示
      setShowLogoutSuccess(true);
      
      console.log('退出登录成功');
    } catch (error) {
      console.error('退出登录失败:', error);
      throw error; // 重新抛出错误，让调用方处理
    }
  };

  const handleLogoutSuccessComplete = () => {
    setShowLogoutSuccess(false);
    setCurrentView('landing');
  };

  const renderView = () => {
    switch (currentView) {
      case 'landing':
        return <LandingView onStart={() => setCurrentView('unregistered')} />;
      case 'unregistered':
        return (
          <UnregisteredHomeView 
            onRegister={() => setCurrentView('user-register')} 
            onLogin={() => setCurrentView('login')}
            onNotificationClick={() => setShowNotifications(true)}
            onApiTest={() => setCurrentView('api-test')}
          />
        );
      case 'login':
        return (
          <LoginView 
            onLogin={handleLogin}
            onSwitchToRegister={() => setCurrentView('user-register')}
            onBack={() => setCurrentView('unregistered')} 
          />
        );
      case 'user-register':
        return (
          <UserRegisterView 
            onRegisterSuccess={handleUserRegisterSuccess}
            onSwitchToLogin={() => setCurrentView('login')}
            onBack={() => setCurrentView('unregistered')} 
          />
        );
      case 'register':
        return <RegisterView onComplete={handleRegisterComplete} onBack={() => setCurrentView('unregistered')} />;
      case 'api-test':
        return <ApiTestView />;
      case 'home': 
        return <HomeView pet={pet} onOpenCamera={() => setCurrentView('camera')} onNotificationClick={() => setShowNotifications(true)} onOpenTrends={() => setCurrentView('trends')} onMenuClick={() => setShowMenu(true)} onGoToRegister={() => setCurrentView('register')} />;
      case 'health': 
        return <HealthView pet={pet} onNotificationClick={() => setShowNotifications(true)} onGoToRegister={() => setCurrentView('register')} />;
      case 'trends':
        return <TrendsReportView pet={pet} onBack={() => setCurrentView('home')} />;
      case 'diary': 
        return <DiaryView pet={pet} onGoToRegister={() => setCurrentView('register')} />;
      case 'social': 
        return <SocialView 
          pet={pet} 
          onNotificationClick={() => setShowNotifications(true)} 
          onGoToRegister={() => setCurrentView('register')}
          videoProcessing={videoProcessing}
          onVideoUpload={handleVideoUpload}
          onCancelProcessing={handleCancelProcessing}
          pendingPost={pendingPost}
          onClearPendingPost={() => setPendingPost(null)}
        />;
      case 'settings': 
        return <SettingsView pet={pet} onLogout={handleLogout} />;
      case 'camera': 
        return <CameraPOVView pet={pet} onClose={() => setCurrentView('home')} />;
      default: 
        return <HomeView pet={pet} onOpenCamera={() => setCurrentView('camera')} onNotificationClick={() => setShowNotifications(true)} onOpenTrends={() => setCurrentView('trends')} onMenuClick={() => setShowMenu(true)} onGoToRegister={() => setCurrentView('register')} />;
    }
  };

  const hideNavViews: ViewState[] = ['camera', 'landing', 'unregistered', 'login', 'user-register', 'register', 'trends', 'api-test'];
  const showNav = !hideNavViews.includes(currentView);

  const navigateTo = (view: ViewState) => {
    setCurrentView(view);
    setShowMenu(false);
  };

  const handleMenuAction = (label: string) => {
    setShowMenu(false);
    // Logic for individual menu functions
    console.log(`Menu Action Executed: ${label}`);
  };

  return (
    <div className="flex flex-col h-screen w-full max-w-md mx-auto bg-[#f6f8f8] relative overflow-hidden shadow-2xl shadow-black/20">
      <main className="flex-1 overflow-y-auto no-scrollbar h-full relative">
        {renderView()}
      </main>

      {/* Side Menu Drawer */}
      {showMenu && (
        <div className="fixed inset-0 z-[100] flex justify-start">
          <div className="absolute inset-0 bg-black/40 backdrop-blur-sm animate-in fade-in duration-300" onClick={() => setShowMenu(false)}></div>
          <div className="relative w-72 h-full bg-white shadow-2xl animate-in slide-in-from-left duration-300 flex flex-col p-6">
            <div className="flex items-center gap-4 mb-10 pb-6 border-b border-gray-100">
              <div className="size-14 rounded-2xl bg-gradient-to-br from-[#31d2e8] to-[#28c566] flex items-center justify-center text-white shadow-lg shadow-cyan-500/20">
                <span className="material-symbols-outlined text-3xl">pets</span>
              </div>
              <div className="flex flex-col">
                <h3 className="text-xl font-black tracking-tight text-[#111814]">PawFlip Pro</h3>
                <p className="text-[10px] text-gray-400 font-bold uppercase tracking-widest leading-none mt-1">智能管家服务中</p>
              </div>
            </div>

            <div className="flex flex-col gap-1.5 flex-1 overflow-y-auto no-scrollbar">
              <SideMenuItem 
                icon="home" 
                label="首页" 
                onClick={() => navigateTo('home')} 
                active={currentView === 'home'} 
              />
              <SideMenuItem 
                icon="router" 
                label="设备管理" 
                onClick={() => navigateTo('settings')} 
              />
              <SideMenuItem 
                icon="cloud_upload" 
                label="云端备份" 
                onClick={() => handleMenuAction('Cloud Backup')} 
              />
              <SideMenuItem 
                icon="group" 
                label="多宠管理" 
                onClick={() => navigateTo('social')} 
              />
              <SideMenuItem 
                icon="shield" 
                label="隐私安全" 
                onClick={() => handleMenuAction('Security')} 
              />
              <SideMenuItem 
                icon="bug_report" 
                label="API 测试" 
                onClick={() => navigateTo('api-test')} 
              />
              <SideMenuItem 
                icon="info" 
                label="关于我们" 
                onClick={() => handleMenuAction('About')} 
              />
            </div>

            <div className="pt-6 border-t border-gray-50">
              <button 
                onClick={handleLogout}
                className="flex items-center gap-4 px-4 py-4 text-gray-400 font-bold hover:text-red-500 transition-colors w-full text-left active:scale-95 group"
              >
                <span className="material-symbols-outlined transition-colors group-hover:text-red-500">logout</span>
                <span className="text-sm tracking-tight">退出登录</span>
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Global Notification Drawer */}
      {showNotifications && (
        <div className="fixed inset-0 z-[100] flex justify-end">
          <div className="absolute inset-0 bg-black/40 backdrop-blur-sm animate-in fade-in duration-300" onClick={() => setShowNotifications(false)}></div>
          <div className="relative w-80 h-full bg-white shadow-2xl animate-in slide-in-from-right duration-300 flex flex-col">
            <div className="p-6 border-b border-gray-100 flex items-center justify-between">
              <h3 className="text-xl font-bold text-[#111814]">AI 动态洞察</h3>
              <button onClick={() => setShowNotifications(false)} className="size-8 rounded-full bg-gray-50 flex items-center justify-center hover:bg-gray-100 transition-colors">
                <span className="material-symbols-outlined text-gray-400">close</span>
              </button>
            </div>
            <div className="flex-1 overflow-y-auto p-4 space-y-4 no-scrollbar">
              <NotificationItem 
                icon="bolt" 
                color="text-yellow-500" 
                title="电量提醒" 
                desc={`${pet.name} 的项圈电量低于 20%，建议充电以保持 AI 持续监测。`} 
                time="10分钟前"
              />
              <NotificationItem 
                icon="health_and_safety" 
                color="text-green-500" 
                title="健康达标" 
                desc={`今日活动目标已完成 85%！${pet.name} 今天的状态非常棒。`} 
                time="1小时前"
              />
              <NotificationItem 
                icon="smart_toy" 
                color="text-[#31d2e8]" 
                title="AI 自动捕捉" 
                desc="我们刚刚捕捉到了它与另一只狗狗互动的精彩瞬间，快去日记看看吧！" 
                time="3小时前"
              />
            </div>
            <div className="p-6 bg-gray-50">
              <button className="w-full py-3 bg-[#31d2e8] text-white font-bold rounded-xl shadow-md active:scale-95 transition-transform">标记全部已读</button>
            </div>
          </div>
        </div>
      )}

      {showNav && (
        <nav className="fixed bottom-0 left-0 right-0 z-50 w-full max-w-md mx-auto bg-white/95 backdrop-blur-xl border-t border-gray-100 pb-safe shadow-[0_-4px_20px_rgba(0,0,0,0.05)]">
          <div className="flex justify-between items-end px-4 py-2">
            <NavItem active={currentView === 'diary'} icon="book_2" label={`${pet.name}日记`} onClick={() => setCurrentView('diary')} />
            <NavItem active={currentView === 'health'} icon="monitor_heart" label="健康" onClick={() => setCurrentView('health')} />
            <div className="flex flex-col items-center justify-center flex-1 -mt-6">
              <button onClick={() => setCurrentView('home')} className={`flex items-center justify-center size-14 rounded-full shadow-lg ring-4 ring-white mb-1 transition-all active:scale-95 ${currentView === 'home' ? 'bg-[#31d2e8]' : 'bg-gray-200'}`}>
                <span className={`material-symbols-outlined text-[32px] ${currentView === 'home' ? 'text-white fill-icon' : 'text-gray-500'}`}>home</span>
              </button>
              <span className={`text-[10px] font-bold ${currentView === 'home' ? 'text-[#31d2e8]' : 'text-gray-400'}`}>首页</span>
            </div>
            <NavItem active={currentView === 'social'} icon="diversity_3" label="社交" onClick={() => setCurrentView('social')} />
            <NavItem active={currentView === 'settings'} icon="settings" label="设置" onClick={() => setCurrentView('settings')} />
          </div>
        </nav>
      )}

      {/* 退出登录成功提示 */}
      {showLogoutSuccess && (
        <LogoutSuccess onComplete={handleLogoutSuccessComplete} />
      )}
    </div>
  );
};

const SideMenuItem: React.FC<{ icon: string; label: string; onClick: () => void; active?: boolean }> = ({ icon, label, onClick, active }) => (
  <button 
    onClick={onClick}
    className={`flex items-center gap-4 p-4 rounded-2xl transition-all w-full text-left group active:scale-[0.98] ${active ? 'bg-[#f0fdff] text-[#31d2e8]' : 'text-gray-600 hover:bg-gray-50'}`}
  >
    <span className={`material-symbols-outlined transition-colors ${active ? 'fill-icon text-[#31d2e8]' : 'text-gray-400 group-hover:text-gray-700'}`}>{icon}</span>
    <span className="font-bold text-sm tracking-tight">{label}</span>
  </button>
);

const NotificationItem: React.FC<{ icon: string; color: string; title: string; desc: string; time: string }> = ({ icon, color, title, desc, time }) => (
  <div className="p-4 bg-gray-50 rounded-2xl border border-gray-100 flex gap-3 hover:bg-gray-100/50 transition-colors">
    <div className={`shrink-0 size-10 rounded-xl bg-white flex items-center justify-center shadow-sm ${color}`}>
      <span className="material-symbols-outlined">{icon}</span>
    </div>
    <div className="flex-1 min-w-0">
      <div className="flex justify-between items-center mb-1">
        <h4 className="font-bold text-sm text-[#111814] truncate">{title}</h4>
        <span className="text-[10px] text-gray-400 whitespace-nowrap">{time}</span>
      </div>
      <p className="text-xs text-gray-500 leading-relaxed line-clamp-2">{desc}</p>
    </div>
  </div>
);

export default App;

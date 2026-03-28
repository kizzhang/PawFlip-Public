
import React, { useState } from 'react';

interface LoginProps {
  onLogin: () => void;
  onSwitchToRegister: () => void;
  onBack: () => void;
}

const LoginView: React.FC<LoginProps> = ({ onLogin, onSwitchToRegister, onBack }) => {
  const [formData, setFormData] = useState({
    email: '',
    password: ''
  });
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleInputChange = (field: string, value: string) => {
    setFormData(prev => ({ ...prev, [field]: value }));
    setError(null); // 清除错误信息
  };

  const validateForm = () => {
    if (!formData.email.trim()) {
      setError('请输入邮箱地址');
      return false;
    }
    
    if (!formData.password) {
      setError('请输入密码');
      return false;
    }
    
    return true;
  };

  const handleLogin = async () => {
    if (!validateForm()) return;
    
    setIsLoading(true);
    setError(null);
    
    try {
      // 导入 API 服务
      const { default: api } = await import('../services/api');
      
      // 调用登录 API
      const result = await api.auth.login(formData.email, formData.password);
      
      console.log('登录成功:', result);
      
      // 登录成功，调用回调
      onLogin();
      
    } catch (error: any) {
      console.error('登录失败:', error);
      setError(error.message || '登录失败，请检查邮箱和密码');
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      handleLogin();
    }
  };

  return (
    <div className="flex flex-col h-full bg-[#f6f8f8] px-8 pt-12">
      <header className="mb-10">
        <button 
          onClick={onBack}
          className="size-10 flex items-center justify-center rounded-full bg-white shadow-sm border border-gray-100 mb-8"
        >
          <span className="material-symbols-outlined text-gray-600">arrow_back</span>
        </button>
        <h1 className="text-3xl font-bold text-[#111814] mb-2">欢迎回来！</h1>
        <p className="text-gray-500 font-medium">请登录您的 PawFlip 账户</p>
      </header>

      <div className="flex flex-col gap-5">
        <div className="flex flex-col gap-2">
          <label className="text-xs font-bold text-gray-400 uppercase tracking-wider ml-1">电子邮箱</label>
          <div className="relative">
            <input 
              type="email" 
              value={formData.email}
              onChange={(e) => handleInputChange('email', e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="example@gmail.com"
              className="w-full h-14 pl-12 pr-4 bg-white rounded-2xl border-none ring-1 ring-gray-100 focus:ring-2 focus:ring-[#31d2e8] transition-all text-sm font-medium shadow-sm"
            />
            <span className="material-symbols-outlined absolute left-4 top-1/2 -translate-y-1/2 text-gray-400">mail</span>
          </div>
        </div>

        <div className="flex flex-col gap-2">
          <label className="text-xs font-bold text-gray-400 uppercase tracking-wider ml-1">登录密码</label>
          <div className="relative">
            <input 
              type="password" 
              value={formData.password}
              onChange={(e) => handleInputChange('password', e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="••••••••"
              className="w-full h-14 pl-12 pr-4 bg-white rounded-2xl border-none ring-1 ring-gray-100 focus:ring-2 focus:ring-[#31d2e8] transition-all text-sm font-medium shadow-sm"
            />
            <span className="material-symbols-outlined absolute left-4 top-1/2 -translate-y-1/2 text-gray-400">lock</span>
            <button className="absolute right-4 top-1/2 -translate-y-1/2 text-[#31d2e8] text-xs font-bold">忘记密码?</button>
          </div>
        </div>

        {/* 错误消息 */}
        {error && (
          <div className="bg-red-50 border border-red-200 text-red-600 px-4 py-3 rounded-2xl text-sm font-medium animate-in fade-in slide-in-from-top-2">
            <div className="flex items-center gap-2">
              <span className="material-symbols-outlined text-sm">error</span>
              {error}
            </div>
          </div>
        )}

        <button 
          onClick={handleLogin}
          disabled={isLoading}
          className="w-full h-14 bg-[#31d2e8] text-white font-bold rounded-2xl shadow-lg shadow-[#31d2e8]/30 mt-4 active:scale-[0.98] transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
        >
          {isLoading ? (
            <>
              <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
              <span>登录中...</span>
            </>
          ) : (
            <>
              <span className="material-symbols-outlined">login</span>
              <span>登录</span>
            </>
          )}
        </button>
      </div>

      <div className="mt-auto pb-12">
        <div className="flex items-center gap-4 mb-8">
          <div className="h-px flex-1 bg-gray-200"></div>
          <span className="text-xs text-gray-400 font-bold uppercase">或者使用</span>
          <div className="h-px flex-1 bg-gray-200"></div>
        </div>

        <div className="flex justify-center gap-6">
          <SocialBtn icon="wechat" color="text-green-500" />
          <SocialBtn icon="google" color="text-red-400" />
          <SocialBtn icon="apple" color="text-black" />
        </div>

        <p className="text-center mt-10 text-sm text-gray-500">
          还没有账号？ 
          <button 
            onClick={onSwitchToRegister}
            className="text-[#31d2e8] font-bold ml-1"
          >
            立即注册
          </button>
        </p>
      </div>
    </div>
  );
};

const SocialBtn: React.FC<{ icon: string; color: string }> = ({ icon, color }) => (
  <button className="size-14 bg-white rounded-2xl flex items-center justify-center shadow-sm ring-1 ring-gray-100 hover:bg-gray-50 transition-colors">
    <div className={`size-6 flex items-center justify-center font-bold ${color}`}>
      {icon === 'wechat' && <span className="material-symbols-outlined">chat</span>}
      {icon === 'google' && <span className="material-symbols-outlined">api</span>}
      {icon === 'apple' && <span className="material-symbols-outlined">terminal</span>}
    </div>
  </button>
);

export default LoginView;

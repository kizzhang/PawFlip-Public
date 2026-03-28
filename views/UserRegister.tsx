import React, { useState } from 'react';

interface UserRegisterProps {
  onRegisterSuccess: () => void;
  onSwitchToLogin: () => void;
  onBack: () => void;
}

import api from '../services/api';

const UserRegisterView: React.FC<UserRegisterProps> = ({ 
  onRegisterSuccess, 
  onSwitchToLogin, 
  onBack 
}) => {
  const [formData, setFormData] = useState({
    email: '',
    password: '',
    confirmPassword: '',
    username: ''
  });
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  const handleInputChange = (field: string, value: string) => {
    setFormData(prev => ({ ...prev, [field]: value }));
    setError(null); // 清除错误信息
  };

  const validateForm = () => {
    if (!formData.email.trim()) {
      setError('请输入邮箱地址');
      return false;
    }
    
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(formData.email)) {
      setError('请输入有效的邮箱地址');
      return false;
    }
    
    if (!formData.password) {
      setError('请输入密码');
      return false;
    }
    
    if (formData.password.length < 6) {
      setError('密码长度至少 6 位');
      return false;
    }
    
    if (formData.password !== formData.confirmPassword) {
      setError('两次输入的密码不一致');
      return false;
    }
    
    return true;
  };

  const handleRegister = async () => {
    if (!validateForm()) return;
    
    setIsLoading(true);
    setError(null);
    
    try {
      console.log('开始注册流程...');
      console.log('表单数据:', formData);
      console.log('API 服务:', api);
      
      // 调用注册 API
      console.log('调用注册 API...');
      const result = await api.auth.register(
        formData.email,
        formData.password,
        formData.username || undefined
      );
      
      console.log('注册成功:', result);
      setSuccess('注册成功！正在跳转...');
      
      // 延迟跳转，让用户看到成功消息
      setTimeout(() => {
        onRegisterSuccess();
      }, 1500);
      
    } catch (error: any) {
      console.error('注册失败详细信息:', error);
      console.error('错误类型:', typeof error);
      console.error('错误消息:', error.message);
      console.error('错误堆栈:', error.stack);
      
      let errorMessage = '注册失败，请重试';
      
      if (error.message) {
        errorMessage = error.message;
      } else if (typeof error === 'string') {
        errorMessage = error;
      } else if (error.toString && error.toString() !== '[object Object]') {
        errorMessage = error.toString();
      }
      
      setError(errorMessage);
    } finally {
      setIsLoading(false);
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
        <h1 className="text-3xl font-bold text-[#111814] mb-2">创建账户</h1>
        <p className="text-gray-500 font-medium">加入 PawFlip 智能宠物管家</p>
      </header>

      <div className="flex flex-col gap-5">
        {/* 邮箱输入 */}
        <div className="flex flex-col gap-2">
          <label className="text-xs font-bold text-gray-400 uppercase tracking-wider ml-1">
            电子邮箱 *
          </label>
          <div className="relative">
            <input 
              type="email" 
              value={formData.email}
              onChange={(e) => handleInputChange('email', e.target.value)}
              placeholder="example@gmail.com"
              className="w-full h-14 pl-12 pr-4 bg-white rounded-2xl border-none ring-1 ring-gray-100 focus:ring-2 focus:ring-[#31d2e8] transition-all text-sm font-medium shadow-sm"
            />
            <span className="material-symbols-outlined absolute left-4 top-1/2 -translate-y-1/2 text-gray-400">
              mail
            </span>
          </div>
        </div>

        {/* 用户名输入（可选） */}
        <div className="flex flex-col gap-2">
          <label className="text-xs font-bold text-gray-400 uppercase tracking-wider ml-1">
            用户名（可选）
          </label>
          <div className="relative">
            <input 
              type="text" 
              value={formData.username}
              onChange={(e) => handleInputChange('username', e.target.value)}
              placeholder="您的昵称"
              className="w-full h-14 pl-12 pr-4 bg-white rounded-2xl border-none ring-1 ring-gray-100 focus:ring-2 focus:ring-[#31d2e8] transition-all text-sm font-medium shadow-sm"
            />
            <span className="material-symbols-outlined absolute left-4 top-1/2 -translate-y-1/2 text-gray-400">
              person
            </span>
          </div>
        </div>

        {/* 密码输入 */}
        <div className="flex flex-col gap-2">
          <label className="text-xs font-bold text-gray-400 uppercase tracking-wider ml-1">
            登录密码 *
          </label>
          <div className="relative">
            <input 
              type="password" 
              value={formData.password}
              onChange={(e) => handleInputChange('password', e.target.value)}
              placeholder="至少 6 位密码"
              className="w-full h-14 pl-12 pr-4 bg-white rounded-2xl border-none ring-1 ring-gray-100 focus:ring-2 focus:ring-[#31d2e8] transition-all text-sm font-medium shadow-sm"
            />
            <span className="material-symbols-outlined absolute left-4 top-1/2 -translate-y-1/2 text-gray-400">
              lock
            </span>
          </div>
        </div>

        {/* 确认密码输入 */}
        <div className="flex flex-col gap-2">
          <label className="text-xs font-bold text-gray-400 uppercase tracking-wider ml-1">
            确认密码 *
          </label>
          <div className="relative">
            <input 
              type="password" 
              value={formData.confirmPassword}
              onChange={(e) => handleInputChange('confirmPassword', e.target.value)}
              placeholder="再次输入密码"
              className="w-full h-14 pl-12 pr-4 bg-white rounded-2xl border-none ring-1 ring-gray-100 focus:ring-2 focus:ring-[#31d2e8] transition-all text-sm font-medium shadow-sm"
            />
            <span className="material-symbols-outlined absolute left-4 top-1/2 -translate-y-1/2 text-gray-400">
              lock_reset
            </span>
          </div>
        </div>

        {/* 错误/成功消息 */}
        {error && (
          <div className="bg-red-50 border border-red-200 text-red-600 px-4 py-3 rounded-2xl text-sm font-medium animate-in fade-in slide-in-from-top-2">
            <div className="flex items-center gap-2">
              <span className="material-symbols-outlined text-sm">error</span>
              {error}
            </div>
          </div>
        )}

        {success && (
          <div className="bg-green-50 border border-green-200 text-green-600 px-4 py-3 rounded-2xl text-sm font-medium animate-in fade-in slide-in-from-top-2">
            <div className="flex items-center gap-2">
              <span className="material-symbols-outlined text-sm">check_circle</span>
              {success}
            </div>
          </div>
        )}

        {/* 注册按钮 */}
        <button 
          onClick={handleRegister}
          disabled={isLoading}
          className="w-full h-14 bg-[#31d2e8] text-white font-bold rounded-2xl shadow-lg shadow-[#31d2e8]/30 mt-4 active:scale-[0.98] transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
        >
          {isLoading ? (
            <>
              <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
              <span>注册中...</span>
            </>
          ) : (
            <>
              <span className="material-symbols-outlined">person_add</span>
              <span>创建账户</span>
            </>
          )}
        </button>

        {/* 用户协议 */}
        <p className="text-xs text-gray-400 text-center mt-2">
          注册即表示您同意我们的
          <button className="text-[#31d2e8] font-bold mx-1">用户协议</button>
          和
          <button className="text-[#31d2e8] font-bold mx-1">隐私政策</button>
        </p>
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
          已有账号？ 
          <button 
            onClick={onSwitchToLogin}
            className="text-[#31d2e8] font-bold ml-1"
          >
            立即登录
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

export default UserRegisterView;

import React, { useState, useEffect } from 'react';
import { PetInfo } from '../types';

const API_BASE_URL = (import.meta as any).env?.VITE_API_URL || 'http://localhost:8003/api/v1';
const TOKEN_KEY = 'pawflip_token';

interface UserProfile {
  id: string;
  email: string;
  username?: string;
  avatar_url?: string;
  is_pro: boolean;
}

interface SettingsViewProps {
  pet: PetInfo;
  onLogout?: () => void;
}

const SettingsView: React.FC<SettingsViewProps> = ({ pet, onLogout }) => {
  const [showLogoutConfirm, setShowLogoutConfirm] = useState(false);
  const [isLoggingOut, setIsLoggingOut] = useState(false);
  const [showEditProfile, setShowEditProfile] = useState(false);
  const [userProfile, setUserProfile] = useState<UserProfile | null>(null);
  const [editUsername, setEditUsername] = useState('');
  const [isSaving, setIsSaving] = useState(false);
  const [isUploadingAvatar, setIsUploadingAvatar] = useState(false);
  const avatarInputRef = React.useRef<HTMLInputElement>(null);

  // 获取用户信息
  useEffect(() => {
    const fetchProfile = async () => {
      try {
        const token = localStorage.getItem(TOKEN_KEY);
        const res = await fetch(`${API_BASE_URL}/auth/me`, {
          headers: { Authorization: `Bearer ${token}` }
        });
        if (res.ok) {
          const data = await res.json();
          setUserProfile(data);
          setEditUsername(data.username || '');
        }
      } catch (e) {
        console.error('获取用户信息失败:', e);
      }
    };
    fetchProfile();
  }, []);

  const handleSaveProfile = async () => {
    if (!editUsername.trim()) return;
    setIsSaving(true);
    try {
      const token = localStorage.getItem(TOKEN_KEY);
      const res = await fetch(`${API_BASE_URL}/auth/profile`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`
        },
        body: JSON.stringify({ username: editUsername.trim() })
      });
      if (res.ok) {
        const data = await res.json();
        setUserProfile(data);
        setShowEditProfile(false);
      }
    } catch (e) {
      console.error('保存失败:', e);
    } finally {
      setIsSaving(false);
    }
  };

  const handleAvatarClick = () => {
    avatarInputRef.current?.click();
  };

  const handleAvatarChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    // 验证文件类型
    if (!['image/jpeg', 'image/png', 'image/gif', 'image/webp'].includes(file.type)) {
      alert('请上传 jpg/png/gif/webp 格式的图片');
      return;
    }

    // 验证文件大小 (5MB)
    if (file.size > 5 * 1024 * 1024) {
      alert('图片过大，最大允许 5MB');
      return;
    }

    setIsUploadingAvatar(true);
    try {
      const token = localStorage.getItem(TOKEN_KEY);
      const formData = new FormData();
      formData.append('file', file);

      const res = await fetch(`${API_BASE_URL}/auth/avatar`, {
        method: 'POST',
        headers: { Authorization: `Bearer ${token}` },
        body: formData
      });

      if (res.ok) {
        const data = await res.json();
        setUserProfile(data);
      } else {
        const err = await res.json();
        alert(err.detail || '上传失败');
      }
    } catch (e) {
      console.error('上传头像失败:', e);
      alert('上传失败，请重试');
    } finally {
      setIsUploadingAvatar(false);
      // 清空 input 以便重复选择同一文件
      if (avatarInputRef.current) avatarInputRef.current.value = '';
    }
  };

  const handleLogoutClick = () => {
    setShowLogoutConfirm(true);
  };

  const handleConfirmLogout = async () => {
    setIsLoggingOut(true);
    try {
      // 调用退出登录
      if (onLogout) {
        await onLogout();
      }
    } catch (error) {
      console.error('退出登录失败:', error);
    } finally {
      setIsLoggingOut(false);
      setShowLogoutConfirm(false);
    }
  };

  const handleCancelLogout = () => {
    setShowLogoutConfirm(false);
  };
  return (
    <div className="flex flex-col min-h-full bg-[#f6f8f8] pb-32">
      <header className="p-4 pt-8 flex items-center justify-between">
        <h2 className="text-2xl font-bold">设置</h2>
        <button className="size-10 rounded-full bg-white shadow-sm flex items-center justify-center hover:bg-gray-50 active:scale-90 transition-all border border-gray-100">
          <span className="material-symbols-outlined text-[#31d2e8]">help</span>
        </button>
      </header>
      
      <div className="p-4 flex flex-col gap-6">
        {/* 用户资料卡片 */}
        <div className="bg-white rounded-2xl p-4 shadow-sm">
          <div className="flex items-center gap-4">
            <div className="relative">
              <input
                ref={avatarInputRef}
                type="file"
                accept="image/jpeg,image/png,image/gif,image/webp"
                onChange={handleAvatarChange}
                className="hidden"
              />
              <button 
                onClick={handleAvatarClick}
                disabled={isUploadingAvatar}
                className="relative group"
              >
                <div 
                  className="bg-center bg-no-repeat bg-cover rounded-full h-16 w-16 border-2 border-[#31d2e8] group-hover:opacity-80 transition-opacity" 
                  style={{backgroundImage: `url(${userProfile?.avatar_url ? (userProfile.avatar_url.startsWith('/') ? API_BASE_URL + userProfile.avatar_url : userProfile.avatar_url) : 'https://via.placeholder.com/64'})`}}
                ></div>
                <div className="absolute bottom-0 right-0 bg-[#31d2e8] h-5 w-5 rounded-full border-2 border-white flex items-center justify-center">
                  {isUploadingAvatar ? (
                    <div className="w-2.5 h-2.5 border border-white border-t-transparent rounded-full animate-spin"></div>
                  ) : (
                    <span className="material-symbols-outlined text-[10px] text-white font-bold">photo_camera</span>
                  )}
                </div>
              </button>
            </div>
            <div className="flex flex-col justify-center flex-1">
              <p className="text-[#111814] text-lg font-bold">{userProfile?.username || '设置昵称'}</p>
              <p className="text-gray-400 text-sm">{userProfile?.email}</p>
              {userProfile?.is_pro && <p className="text-[#31d2e8] text-xs font-medium">Pro 会员</p>}
            </div>
            <button onClick={() => setShowEditProfile(true)} className="text-gray-400 hover:text-[#31d2e8] transition-colors">
              <span className="material-symbols-outlined">chevron_right</span>
            </button>
          </div>
        </div>

        {/* 设备管理 */}
        <div className="flex flex-col gap-2">
          <h3 className="text-gray-500 text-xs font-bold tracking-wider uppercase px-2">我的设备</h3>
          <div className="bg-white rounded-2xl p-4 shadow-sm flex flex-col gap-4">
            <div className="flex items-start justify-between gap-4">
              <div className="flex flex-col gap-1">
                <div className="flex items-center gap-2">
                  <span className="bg-green-100 text-green-700 text-[10px] font-bold px-2 py-0.5 rounded-full uppercase tracking-wide">已连接</span>
                </div>
                <p className="text-[#111814] text-lg font-bold mt-1">智能项圈 V2</p>
                <div className="flex items-center gap-2 text-gray-500 text-sm">
                  <span className="material-symbols-outlined text-[16px] text-[#31d2e8]">battery_5_bar</span>
                  <span>{pet.battery}% 电量</span>
                </div>
              </div>
              <div className="w-20 h-20 bg-center bg-no-repeat bg-cover rounded-xl shadow-inner bg-gray-50" style={{backgroundImage: 'url("https://lh3.googleusercontent.com/aida-public/AB6AXuBJumJWdhaDoDIQqdZ6Pld2fXht_558KCvjsvK-sTl6ZFBeYlRrmSphvaY5hJ9uBJAcdFegXnpL5HOeLMXXWkQ_H9uhF10u3kcI8JRxaBTRxyA7Ci-MvEhDw8yWRhAW2xS0MLhRyUWMwo1ZxcHtcjW0WsYakeTfn5I_GaaHBKUuRZnjuNqx162HnHIxAS0tLvUm3SiDHlZHmK8KeLm5E8Fv3ICG34Xt3z3y5RGkekW9CBA24or4Dryck9-Y1gi0WuaaLAkVVTpmH-M")'}}></div>
            </div>
            <div className="h-px bg-gray-50 w-full"></div>
            <button className="w-full flex items-center justify-center gap-2 bg-[#31d2e8] text-white font-bold py-3.5 rounded-xl hover:bg-[#28c566] transition-all active:scale-[0.98] shadow-md shadow-[#31d2e8]/20">
              <span className="material-symbols-outlined text-[20px]">settings_photo_camera</span>
              管理相机与设置
            </button>
          </div>
        </div>

        {/* 账户设置列表 */}
        <div className="flex flex-col gap-2">
          <h3 className="text-gray-500 text-xs font-bold tracking-wider uppercase px-2">常规</h3>
          <div className="bg-white rounded-2xl overflow-hidden shadow-sm">
            <SettingsItem icon="person" label="个人信息" />
            <SettingsItem icon="credit_card" label="订阅管理" />
            <SettingsItem icon="pets" label="宠物档案" border={false} />
          </div>
        </div>

        {/* 偏好设置 */}
        <div className="flex flex-col gap-2">
          <h3 className="text-gray-500 text-xs font-bold tracking-wider uppercase px-2">偏好</h3>
          <div className="bg-white rounded-2xl overflow-hidden shadow-sm">
            <div className="w-full flex items-center justify-between p-4">
              <div className="flex items-center gap-3">
                <div className="bg-gray-50 p-2 rounded-xl text-gray-500">
                  <span className="material-symbols-outlined">notifications</span>
                </div>
                <div className="flex flex-col text-left">
                  <span className="text-[#111814] font-bold text-sm">通知</span>
                  <span className="text-[10px] text-gray-400">健康提醒与日记更新</span>
                </div>
              </div>
              <label className="relative inline-flex items-center cursor-pointer">
                <input defaultChecked className="sr-only peer" type="checkbox" />
                <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:start-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-[#31d2e8]"></div>
              </label>
            </div>
            <div className="h-px bg-gray-50 mx-4"></div>
            <SettingsItem icon="shield" label="隐私与数据安全" />
            <div className="h-px bg-gray-50 mx-4"></div>
            <div className="w-full flex items-center justify-between p-4">
              <div className="flex items-center gap-3">
                <div className="bg-gray-50 p-2 rounded-xl text-gray-500">
                  <span className="material-symbols-outlined">videocam</span>
                </div>
                <div className="flex flex-col text-left">
                  <span className="text-[#111814] font-bold text-sm">自动录制 POV</span>
                  <span className="text-[10px] text-gray-400">智能捕捉精彩瞬间</span>
                </div>
              </div>
              <label className="relative inline-flex items-center cursor-pointer">
                <input className="sr-only peer" type="checkbox" />
                <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:start-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-[#31d2e8]"></div>
              </label>
            </div>
          </div>
        </div>

        {/* 底部操作 */}
        <div className="pt-4 pb-12 flex flex-col items-center gap-4">
          <button 
            onClick={handleLogoutClick}
            disabled={isLoggingOut}
            className="w-full p-4 rounded-2xl text-red-500 bg-red-50/50 hover:bg-red-50 font-bold transition-colors flex items-center justify-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isLoggingOut ? (
              <>
                <div className="w-4 h-4 border-2 border-red-500 border-t-transparent rounded-full animate-spin"></div>
                <span>退出中...</span>
              </>
            ) : (
              <>
                <span className="material-symbols-outlined">logout</span>
                <span>退出登录</span>
              </>
            )}
          </button>
          <button className="text-xs text-gray-400 hover:text-gray-600 transition-colors">删除账户</button>
        </div>
      </div>

      {/* 退出登录确认对话框 */}
      {showLogoutConfirm && (
        <div className="fixed inset-0 z-[200] flex items-center justify-center p-4">
          <div className="absolute inset-0 bg-black/50 backdrop-blur-sm animate-in fade-in duration-300" onClick={handleCancelLogout}></div>
          <div className="relative bg-white rounded-3xl p-6 w-full max-w-sm shadow-2xl animate-in zoom-in-95 slide-in-from-bottom-4 duration-300">
            <div className="flex flex-col items-center text-center">
              <div className="w-16 h-16 bg-red-50 rounded-full flex items-center justify-center mb-4">
                <span className="material-symbols-outlined text-red-500 text-2xl">logout</span>
              </div>
              
              <h3 className="text-xl font-bold text-[#111814] mb-2">确认退出登录</h3>
              <p className="text-gray-500 text-sm mb-6 leading-relaxed">
                退出登录后，您需要重新输入账号密码才能访问 {pet.name} 的数据和功能。
              </p>
              
              <div className="flex gap-3 w-full">
                <button 
                  onClick={handleCancelLogout}
                  className="flex-1 py-3 px-4 bg-gray-100 text-gray-700 font-bold rounded-xl hover:bg-gray-200 transition-colors"
                >
                  取消
                </button>
                <button 
                  onClick={handleConfirmLogout}
                  disabled={isLoggingOut}
                  className="flex-1 py-3 px-4 bg-red-500 text-white font-bold rounded-xl hover:bg-red-600 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
                >
                  {isLoggingOut ? (
                    <>
                      <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                      <span>退出中</span>
                    </>
                  ) : (
                    <span>确认退出</span>
                  )}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* 编辑昵称对话框 */}
      {showEditProfile && (
        <div className="fixed inset-0 z-[200] flex items-center justify-center p-4">
          <div className="absolute inset-0 bg-black/50 backdrop-blur-sm animate-in fade-in duration-300" onClick={() => setShowEditProfile(false)}></div>
          <div className="relative bg-white rounded-3xl p-6 w-full max-w-sm shadow-2xl animate-in zoom-in-95 slide-in-from-bottom-4 duration-300">
            <div className="flex flex-col">
              <h3 className="text-xl font-bold text-[#111814] mb-4">编辑昵称</h3>
              <p className="text-gray-500 text-sm mb-4">设置您的昵称，AI 助手会用这个名字称呼您</p>
              
              <input
                type="text"
                value={editUsername}
                onChange={(e) => setEditUsername(e.target.value)}
                placeholder="请输入昵称"
                className="w-full px-4 py-3 rounded-xl bg-gray-50 border-none focus:ring-2 focus:ring-[#31d2e8]/30 text-[#111814] font-medium placeholder-gray-400 mb-4"
              />
              
              <div className="flex gap-3">
                <button 
                  onClick={() => setShowEditProfile(false)}
                  className="flex-1 py-3 px-4 bg-gray-100 text-gray-700 font-bold rounded-xl hover:bg-gray-200 transition-colors"
                >
                  取消
                </button>
                <button 
                  onClick={handleSaveProfile}
                  disabled={isSaving || !editUsername.trim()}
                  className="flex-1 py-3 px-4 bg-[#31d2e8] text-white font-bold rounded-xl hover:bg-[#28c566] transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
                >
                  {isSaving ? (
                    <>
                      <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                      <span>保存中</span>
                    </>
                  ) : (
                    <span>保存</span>
                  )}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

const SettingsItem: React.FC<{ icon: string; label: string; border?: boolean }> = ({ icon, label, border = true }) => (
  <>
    <button className="w-full flex items-center justify-between p-4 hover:bg-gray-50 transition-colors group">
      <div className="flex items-center gap-3">
        <div className="bg-gray-50 p-2 rounded-xl text-gray-500 group-hover:bg-[#31d2e8]/10 group-hover:text-[#31d2e8] transition-colors">
          <span className="material-symbols-outlined">{icon}</span>
        </div>
        <span className="text-[#111814] font-bold text-sm">{label}</span>
      </div>
      <span className="material-symbols-outlined text-gray-300 group-hover:text-[#31d2e8] transition-colors">chevron_right</span>
    </button>
    {border && <div className="h-px bg-gray-50 mx-4"></div>}
  </>
);

export default SettingsView;

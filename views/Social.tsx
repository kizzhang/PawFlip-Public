import React, { useState, useRef, useEffect } from 'react';
import { SocialPost, PetInfo, DiaryEntry } from '../types';
import { VideoProcessingState } from '../App';

interface SocialProps {
  onNotificationClick: () => void;
  pet: PetInfo;
  onGoToRegister?: () => void;
  // 视频处理相关 props
  videoProcessing: VideoProcessingState;
  onVideoUpload: (file: File) => Promise<SocialPost | null>;
  onCancelProcessing: () => void;
  // 后台生成完成的帖子
  pendingPost?: SocialPost | null;
  onClearPendingPost?: () => void;
}

const initialPosts: SocialPost[] = [
  {
    id: '1',
    user_id: 'demo-user-1',
    pet_id: 'demo-pet-1',
    author: '巴斯特 🐶',
    breed: '金毛寻回犬',
    time: '2小时前',
    avatar: 'https://lh3.googleusercontent.com/aida-public/AB6AXuDC7r_pLw_jJHvL00DibmamuPEb15GefRiErKpcgjrstJlIWCoZ4DgvdnMYeWjBWKogKbOchwXH87_mQrny582XO-q_Fbl1IXcrXSS02RgkWk7Av3qz2-EJYrrks8H2Cpuhe0DeYh7dfYmq0lbwAHoBgL_qTHapzv7V6MmDsl6XhZzUSNGahghwlhriLq08wIUYh5Ihr7_q7hlgESQOusJjr_EJwloeisMZ1wlWljdOYr747NSnOg5csIh1NQK9KT2Kq1OIEZlQBfQ',
    content: '日志 上午 09:42。发现敌情。我试图进行垂直拦截，但那个毛茸茸的入侵者使用了作弊般的攀爬战术。我将坚守防线，等待增援。 🐿️🌲',
    imageUrl: 'https://images.unsplash.com/photo-1544198365-f5d60b6d8190?auto=format&fit=crop&q=80&w=800',
    likes: 242,
    comments: 14,
    isAiStory: true,
    created_at: new Date(Date.now() - 2 * 60 * 60 * 1000).toISOString()
  },
  {
    id: '2',
    user_id: 'demo-user-2',
    pet_id: 'demo-pet-2',
    author: '露娜 🐱',
    breed: '暹罗猫',
    time: '4小时前',
    avatar: 'https://lh3.googleusercontent.com/aida-public/AB6AXuDvLDC5fniQINx57Nhggfyx3CmdiB09NVmJsrbC-qKzy4ufVScQKmEjg4rlG4rAv-oH9mnCHJBIExl6FMn2Uv_K0pOFbZDIy97QPLkHMplbHi_fr-XfUbX9EjUKfQ-obRFc3PjuVNemxo-P4ZdsL2tvJHsDQfbJlEpSVHSjtrzHuh1_7tjkzog2dWC7fEEEX1HYekhwYOrak97w9Yuwgo7w2TDvhYdCTZMZcI4g5102vC7V_hL4p8_QKgx0KGonU0GYvuIJL_6Qwt8',
    content: '太阳能充电已启动。人类试图用"咪咪咪"的怪声干扰程序，已被成功忽略。能量值 98%。凌晨3点的疯狂跑酷准备工作正在进行中。 ☀️⚡️',
    imageUrl: 'https://images.unsplash.com/photo-1514888286974-6c03e2ca1dba?auto=format&fit=crop&q=80&w=800',
    likes: 890,
    comments: 52,
    isAiStory: true,
    created_at: new Date(Date.now() - 4 * 60 * 60 * 1000).toISOString()
  }
];

// Mock today's diary entries for the selection feature
const todayDiaryEntries: Partial<DiaryEntry>[] = [
  {
    id: 'd1',
    title: '晨间散步',
    content: '今天的早晨非常清爽，我在草地上发现了一只色彩斑斓的蝴蝶！',
    imageUrl: 'https://lh3.googleusercontent.com/aida-public/AB6AXuD8aCJEZBl-xr6GYUIxiRY37BGvvKo1RqtbS_0cMl14Qn-sudYG2dOm9YCRVhvsgWSKfFmI1KufQnYwh1ivxs8kREy80MBYHCheAN0oHTZDIX-8WhyElEeICmBoQlyWWh1Os8vG2oFsqjr6DWXfpvnhM-OSp2fBgzsOCOd0DXF1-okVcWgXysd8B_FdwqdTIO7CWXOGGzlNfW3Kmw95_gfPApghBA6_kUh9L8zjChcuEdByFfXCUOD8mZ-1ZEEKTQlo8TdBTimcqtA',
    time: '08:30'
  },
  {
    id: 'd2',
    title: '午后小憩',
    content: '阳光晒在肚皮上暖洋洋的，这是狗生最惬意的时刻。',
    imageUrl: 'https://lh3.googleusercontent.com/aida-public/AB6AXuD9y4_BzhL5e2NAm4fMR1ixhiN09nbe0qIyKEyVdzzPDQ_8pxC2zWEIeYY1Ri61zuKRXpU3FW8rjEk6ist0YUN81Zu7AAv0-KuUSQugw5bB_zxEnVc3xuy8hQAlXsg0a1nyPBUFDD0qzG0KBSdS0GFuqHktvLo7R6ECWZHGOXTPUp2zd6tdDFVYr5JfO-4tMhGVLORGCqU_GWP74VV9thvq_jYicKgQHU-liP0fKyzeGNv8mLDLCgqjojoNrOMeXTJZsdNbjDaVHH8',
    time: '14:20'
  }
];

const SocialView: React.FC<SocialProps> = ({ 
  onNotificationClick, 
  pet, 
  onGoToRegister,
  videoProcessing,
  onVideoUpload,
  onCancelProcessing,
  pendingPost,
  onClearPendingPost
}) => {
  const [tab, setTab] = useState<'following' | 'discovery'>('following');
  const [feed, setFeed] = useState<SocialPost[]>(initialPosts);
  const [showPostModal, setShowPostModal] = useState(false);
  const [showDiarySelector, setShowDiarySelector] = useState(false);
  const [newPostContent, setNewPostContent] = useState('');
  const [selectedImageUrl, setSelectedImageUrl] = useState<string | null>(null);
  const [hasNotification, setHasNotification] = useState(true);
  const [openMenuId, setOpenMenuId] = useState<string | null>(null);

  const photoInputRef = useRef<HTMLInputElement>(null);
  const videoInputRef = useRef<HTMLInputElement>(null);

  // 当有后台生成完成的帖子时，添加到列表
  useEffect(() => {
    if (pendingPost) {
      // 检查是否已存在（避免重复添加）
      const exists = feed.some(post => post.id === pendingPost.id);
      if (!exists) {
        setFeed(prev => [pendingPost, ...prev]);
      }
      // 清除 pendingPost
      onClearPendingPost?.();
    }
  }, [pendingPost, onClearPendingPost]);

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
          
          <h2 className="text-2xl font-bold text-[#111814] mb-4">完成宠物档案注册</h2>
          <p className="text-gray-500 text-sm mb-6 leading-relaxed">
            您需要先完成宠物档案注册，才能在社交圈发布视频和与其他宠物主人互动。
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
              注册后即可享受完整的社交功能
            </p>
          </div>
        </div>
      </div>
    );
  }

  const handleCreatePost = () => {
    if (!newPostContent.trim()) return;

    const newPost: SocialPost = {
      id: Date.now().toString(),
      user_id: pet.user_id || '',
      pet_id: pet.id || '',
      author: pet.name,
      breed: pet.breed,
      time: '刚刚',
      avatar: pet.avatar || 'https://lh3.googleusercontent.com/aida-public/AB6AXuBCtUnGhZGFLRzkKwv7ALb8sz0nauqVY6PWJruCuzdyeEzKpuornSwnuRaq2E50Id8Xc9ugn-VQvoMy7vdFu6QyvL4ZeYZhNOXDdvrWOGVdHmJ2LjQCzLnLZLf8-juseESPt4QAqQ8kqg9qy9x-kRHq8L27R64D3N7aFrTv5KiMx8aGY9hpDrTfcNpNqmA29oMJRdJV-I4rMNS-081A0cmZrrAvFp4NmNFHm74KdvNJ-R1A1Er4nhVkK-choiBni1w6RS7vVT3t7hA',
      content: newPostContent,
      imageUrl: selectedImageUrl || 'https://images.unsplash.com/photo-1583511655857-d19b40a7a54e?auto=format&fit=crop&q=80&w=800',
      likes: 0,
      comments: 0,
      isAiStory: false,
      created_at: new Date().toISOString()
    };

    setFeed([newPost, ...feed]);
    setNewPostContent('');
    setSelectedImageUrl(null);
    setShowPostModal(false);
  };

  const handlePhotoUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      const reader = new FileReader();
      reader.onloadend = () => {
        setSelectedImageUrl(reader.result as string);
      };
      reader.readAsDataURL(file);
    }
  };

  const handleVideoUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      try {
        // 调用 App 层的视频上传处理
        const newPost = await onVideoUpload(file);
        
        if (newPost) {
          // 添加到动态列表
          setFeed(prev => [newPost, ...prev]);
          setNewPostContent('');
          setSelectedImageUrl(null);
          setShowPostModal(false);
        }
      } catch (error) {
        console.error('视频上传处理错误:', error);
        // 不抛出错误，防止白屏
      }
    }
    // 重置 input 以便可以再次选择同一文件
    if (videoInputRef.current) {
      videoInputRef.current.value = '';
    }
  };

  const selectDiaryEntry = (entry: Partial<DiaryEntry>) => {
    setNewPostContent(entry.content || '');
    setSelectedImageUrl(entry.imageUrl || null);
    setShowDiarySelector(false);
  };

  const handleNotificationClick = () => {
    setHasNotification(false);
    onNotificationClick();
  };

  const handleDeletePost = (id: string) => {
    setFeed(prev => prev.filter(post => post.id !== id));
    setOpenMenuId(null);
  };

  const toggleMenu = (id: string) => {
    setOpenMenuId(openMenuId === id ? null : id);
  };

  return (
    <div className="flex flex-col min-h-full bg-[#f6f8f8] pb-32">
      {/* Header */}
      <div className="sticky top-0 z-30 bg-white/95 backdrop-blur-md border-b border-gray-100">
        <div className="flex items-center p-4 pb-2 justify-between">
          <div className="flex items-center gap-2">
            <div 
              className="bg-center bg-no-repeat bg-cover rounded-xl size-8 border-2 border-[#31d2e8]/20 shadow-sm" 
              style={{backgroundImage: `url(${pet.avatar || 'https://lh3.googleusercontent.com/aida-public/AB6AXuBCtUnGhZGFLRzkKwv7ALb8sz0nauqVY6PWJruCuzdyeEzKpuornSwnuRaq2E50Id8Xc9ugn-VQvoMy7vdFu6QyvL4ZeYZhNOXDdvrWOGVdHmJ2LjQCzLnLZLf8-juseESPt4QAqQ8kqg9qy9x-kRHq8L27R64D3N7aFrTv5KiMx8aGY9hpDrTfcNpNqmA29oMJRdJV-I4rMNS-081A0cmZrrAvFp4NmNFHm74KdvNJ-R1A1Er4nhVkK-choiBni1w6RS7vVT3t7hA'})`}}
            ></div>
            <h2 className="text-[#111814] text-lg font-black tracking-tight">宠物社交圈</h2>
          </div>
          <button 
            onClick={handleNotificationClick} 
            className="flex items-center justify-center rounded-full size-10 hover:bg-black/5 active:scale-90 transition-transform relative"
          >
            <span className="material-symbols-outlined text-[28px]">notifications</span>
            {hasNotification && (
              <span className="absolute top-2.5 right-2.5 w-2 h-2 bg-red-500 rounded-full border border-white"></span>
            )}
          </button>
        </div>
        
        {/* Tabs */}
        <div className="px-4">
          <div className="flex justify-center gap-12">
            <button 
              onClick={() => setTab('following')} 
              className={`flex flex-col items-center justify-center border-b-[3px] pb-3 pt-2 px-4 transition-all ${tab === 'following' ? 'border-b-[#31d2e8] text-[#111814]' : 'border-b-transparent text-gray-400'}`}
            >
              <p className="text-sm font-black">关注</p>
            </button>
            <button 
              onClick={() => setTab('discovery')} 
              className={`flex flex-col items-center justify-center border-b-[3px] pb-3 pt-2 px-4 transition-all ${tab === 'discovery' ? 'border-b-[#31d2e8] text-[#111814]' : 'border-b-transparent text-gray-400'}`}
            >
              <p className="text-sm font-black">发现</p>
            </button>
          </div>
        </div>
      </div>

      <div className="flex flex-col gap-6 p-4 max-w-md mx-auto w-full">
        {/* Post Diary Button - 处理中时显示进度 */}
        <div className="px-2">
          {videoProcessing.isProcessing ? (
            <button 
              onClick={() => {
                // 点击后打开生成界面查看进度
                setShowPostModal(true);
              }}
              className="flex w-full items-center justify-center gap-3 rounded-2xl h-14 bg-gradient-to-r from-[#31d2e8] to-[#28c566] text-white shadow-lg shadow-cyan-500/20 transition-all active:scale-[0.98] animate-pulse"
            >
              {/* 小型进度环 */}
              <div className="relative size-6">
                <svg className="size-6 -rotate-90" viewBox="0 0 100 100">
                  <circle cx="50" cy="50" r="40" fill="none" stroke="rgba(255,255,255,0.3)" strokeWidth="12" />
                  <circle 
                    cx="50" cy="50" r="40" fill="none" stroke="white" strokeWidth="12" strokeLinecap="round"
                    strokeDasharray={`${videoProcessing.processingProgress * 2.51} 251`}
                  />
                </svg>
              </div>
              <span className="text-sm font-black tracking-wide">生成日记中... {videoProcessing.processingProgress}%</span>
            </button>
          ) : (
            <button 
              onClick={() => {
                setShowPostModal(true);
                setShowDiarySelector(false);
              }}
              className="flex w-full items-center justify-center gap-2 rounded-2xl h-14 bg-[#31d2e8] hover:bg-[#2bc4d8] text-white shadow-lg shadow-cyan-500/20 transition-all active:scale-[0.98]"
            >
              <span className="material-symbols-outlined text-[22px]">edit_square</span>
              <span className="text-sm font-black tracking-wide">+ 发布日记</span>
            </button>
          )}
        </div>

        {/* Feed */}
        <div className="flex flex-col gap-6">
          {feed.map(post => (
            <div key={post.id} className="flex flex-col rounded-3xl bg-white shadow-sm border border-gray-100 overflow-hidden animate-in fade-in slide-in-from-bottom-4 duration-500">
              <div className="flex items-center justify-between p-4 pb-3">
                <div className="flex items-center gap-3">
                  <div className="bg-center bg-no-repeat bg-cover rounded-2xl size-10 shadow-sm" style={{backgroundImage: `url(${post.avatar || 'https://via.placeholder.com/40'})`}}></div>
                  <div className="flex flex-col">
                    <p className="text-[#111814] text-sm font-black leading-tight flex items-center gap-1">
                      {post.author || '未知'}
                      {post.isAiStory && <span className="text-xs">🤖</span>}
                    </p>
                    <p className="text-gray-400 text-[10px] font-bold uppercase tracking-widest">{post.breed || '未知'} • {post.time || '刚刚'}</p>
                  </div>
                </div>
                <div className="relative">
                  <button 
                    onClick={() => toggleMenu(post.id)}
                    className="text-gray-400 hover:text-gray-600 transition-colors p-1 rounded-full hover:bg-gray-100"
                  >
                    <span className="material-symbols-outlined">more_horiz</span>
                  </button>
                  {openMenuId === post.id && (
                    <div className="absolute right-0 top-8 bg-white shadow-xl rounded-2xl border border-gray-100 py-2 w-32 z-20 animate-in zoom-in-95 duration-200">
                      {post.author === pet.name ? (
                        <button 
                          onClick={() => handleDeletePost(post.id)}
                          className="flex items-center gap-2 px-4 py-2 text-red-500 hover:bg-red-50 w-full text-left transition-colors"
                        >
                          <span className="material-symbols-outlined text-sm">delete</span>
                          <span className="text-sm font-bold">删除动态</span>
                        </button>
                      ) : (
                        <>
                          <button className="flex items-center gap-2 px-4 py-2 text-gray-700 hover:bg-gray-50 w-full text-left transition-colors">
                            <span className="material-symbols-outlined text-sm">flag</span>
                            <span className="text-sm font-bold">举报</span>
                          </button>
                          <button className="flex items-center gap-2 px-4 py-2 text-gray-700 hover:bg-gray-50 w-full text-left transition-colors">
                            <span className="material-symbols-outlined text-sm">not_interested</span>
                            <span className="text-sm font-bold">不感兴趣</span>
                          </button>
                        </>
                      )}
                    </div>
                  )}
                </div>
              </div>
              
              <div className="relative w-full aspect-square bg-gray-50">
                <img src={post.imageUrl} alt="Post content" className="absolute inset-0 w-full h-full object-cover" />
                <div className="absolute top-4 right-4 bg-black/40 backdrop-blur-md px-3 py-1.5 rounded-xl flex items-center gap-1.5 border border-white/20">
                  <span className="material-symbols-outlined text-[#31d2e8] text-[16px] fill-icon">videocam</span>
                  <span className="text-white text-[10px] font-black tracking-widest uppercase">实时视角</span>
                </div>
              </div>

              <div className="p-5 flex flex-col gap-4">
                {post.isAiStory && (
                  <div className="px-3 py-1 rounded-full bg-[#f0fdff] border border-[#31d2e8]/20 flex items-center gap-1.5 w-fit">
                    <span className="material-symbols-outlined text-[#31d2e8] text-[14px] fill-icon">auto_awesome</span>
                    <p className="text-[#31d2e8] text-[10px] font-black uppercase tracking-widest">AI 故事生成的洞察</p>
                  </div>
                )}
                <p className="text-[#111814] text-[15px] leading-relaxed font-medium">{post.content}</p>
                
                <div className="flex items-center justify-between pt-3 border-t border-gray-50">
                  <div className="flex items-center gap-6">
                    <button className="flex items-center gap-1.5 group">
                      <span className="material-symbols-outlined text-gray-400 group-hover:text-red-500 transition-colors">favorite</span>
                      <span className="text-[#111814] text-xs font-bold">{post.likes}</span>
                    </button>
                    <button className="flex items-center gap-1.5 group">
                      <span className="material-symbols-outlined text-gray-400 group-hover:text-[#31d2e8] transition-colors">chat_bubble</span>
                      <span className="text-[#111814] text-xs font-bold">{post.comments}</span>
                    </button>
                  </div>
                  <button className="text-gray-400 hover:text-[#31d2e8] transition-colors">
                    <span className="material-symbols-outlined text-[20px]">share</span>
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Post Creation Modal */}
      {showPostModal && (
        <div className="fixed inset-0 z-[100] flex items-end sm:items-center justify-center p-0 sm:p-4">
          <div 
            className="absolute inset-0 bg-black/60 backdrop-blur-sm animate-in fade-in duration-300" 
            onClick={() => {
              // 直接关闭弹窗（处理中也可以关闭，会在后台继续）
              setShowPostModal(false);
            }}
          ></div>
          <div className="relative w-full max-w-md bg-white rounded-t-[2.5rem] sm:rounded-[2.5rem] shadow-2xl animate-in slide-in-from-bottom duration-300 flex flex-col overflow-hidden">
            <div className="p-6 border-b border-gray-100 flex items-center justify-between">
              <button 
                onClick={() => {
                  if (showDiarySelector) {
                    setShowDiarySelector(false);
                  } else {
                    // 直接关闭弹窗
                    setShowPostModal(false);
                  }
                }} 
                className="size-10 rounded-full bg-gray-50 flex items-center justify-center text-gray-400 hover:bg-gray-100 transition-colors"
              >
                <span className="material-symbols-outlined">
                  {showDiarySelector ? 'arrow_back' : 'close'}
                </span>
              </button>
              <h3 className="text-lg font-black tracking-tight">
                {videoProcessing.isProcessing ? '生成日记中' : showDiarySelector ? '选择今日日记' : '发布新动态'}
              </h3>
              <button 
                onClick={handleCreatePost}
                disabled={!newPostContent.trim() || showDiarySelector || videoProcessing.isProcessing}
                className="px-6 py-2 bg-[#31d2e8] text-white font-black rounded-full text-sm disabled:opacity-50 disabled:grayscale transition-all active:scale-95"
              >
                {videoProcessing.isProcessing ? '处理中...' : '发布'}
              </button>
            </div>
            
            {showDiarySelector ? (
              <div className="p-6 max-h-[60vh] overflow-y-auto no-scrollbar flex flex-col gap-4 animate-in slide-in-from-right duration-300">
                {todayDiaryEntries.map(entry => (
                  <button 
                    key={entry.id}
                    onClick={() => selectDiaryEntry(entry)}
                    className="flex gap-4 p-4 rounded-3xl bg-gray-50 hover:bg-cyan-50 border border-transparent hover:border-cyan-100 transition-all text-left group"
                  >
                    <div className="size-20 rounded-2xl overflow-hidden bg-gray-200 shrink-0">
                      <img src={entry.imageUrl} alt={entry.title} className="w-full h-full object-cover" />
                    </div>
                    <div className="flex flex-col justify-center min-w-0">
                      <p className="text-[10px] font-bold text-gray-400 mb-1">{entry.time} 生成</p>
                      <h4 className="font-black text-[#111814] truncate">{entry.title}</h4>
                      <p className="text-xs text-gray-500 line-clamp-2 mt-1">{entry.content}</p>
                    </div>
                  </button>
                ))}
              </div>
            ) : (
              <div className="p-6 flex flex-col gap-6 animate-in slide-in-from-left duration-300">
                {/* 处理中状态显示 */}
                {videoProcessing.isProcessing ? (
                  <div className="flex flex-col items-center justify-center py-8 gap-6">
                    {/* 动画圆环 */}
                    <div className="relative size-24">
                      <svg className="size-24 -rotate-90" viewBox="0 0 100 100">
                        <circle
                          cx="50"
                          cy="50"
                          r="45"
                          fill="none"
                          stroke="#e5e7eb"
                          strokeWidth="8"
                        />
                        <circle
                          cx="50"
                          cy="50"
                          r="45"
                          fill="none"
                          stroke="#31d2e8"
                          strokeWidth="8"
                          strokeLinecap="round"
                          strokeDasharray={`${videoProcessing.processingProgress * 2.83} 283`}
                          className="transition-all duration-500 ease-out"
                        />
                      </svg>
                      <div className="absolute inset-0 flex items-center justify-center">
                        <span className="text-2xl font-black text-[#31d2e8]">{videoProcessing.processingProgress}%</span>
                      </div>
                    </div>
                    
                    {/* 状态文字 */}
                    <div className="text-center">
                      <p className="text-lg font-bold text-[#111814] mb-2">{videoProcessing.processingStatus}</p>
                      <p className="text-sm text-gray-400">请稍候，AI 正在为您创作精彩内容</p>
                    </div>
                    
                    {/* 动态点点 */}
                    <div className="flex gap-1.5">
                      <div className="size-2 bg-[#31d2e8] rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></div>
                      <div className="size-2 bg-[#31d2e8] rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></div>
                      <div className="size-2 bg-[#31d2e8] rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></div>
                    </div>
                    
                    {/* 操作按钮 */}
                    <div className="flex gap-3 w-full mt-2">
                      <button
                        onClick={onCancelProcessing}
                        className="flex-1 py-3 px-4 bg-red-50 hover:bg-red-100 text-red-500 font-bold rounded-2xl text-sm transition-all flex items-center justify-center gap-2"
                      >
                        <span className="material-symbols-outlined text-lg">close</span>
                        取消生成
                      </button>
                    </div>
                  </div>
                ) : (
                  <>
                    <textarea 
                      autoFocus
                      value={newPostContent}
                      onChange={(e) => setNewPostContent(e.target.value)}
                      placeholder="分享你的宠物瞬间..." 
                      className="w-full h-40 border-none focus:ring-0 text-lg resize-none placeholder-gray-300"
                    />
                    
                    {selectedImageUrl && (
                      <div className="relative size-24 rounded-2xl overflow-hidden border border-gray-100 shadow-sm">
                        <img src={selectedImageUrl} alt="Selected" className="w-full h-full object-cover" />
                        <button 
                          onClick={() => setSelectedImageUrl(null)}
                          className="absolute top-1 right-1 size-6 bg-black/50 rounded-full flex items-center justify-center text-white"
                        >
                          <span className="material-symbols-outlined text-sm">close</span>
                        </button>
                      </div>
                    )}

                    <div className="flex gap-3">
                      <input type="file" ref={photoInputRef} onChange={handlePhotoUpload} accept="image/*" className="hidden" />
                      <input type="file" ref={videoInputRef} onChange={handleVideoUpload} accept="video/*" className="hidden" />
                      
                      <button 
                        onClick={() => photoInputRef.current?.click()}
                        className="flex flex-col items-center justify-center flex-1 aspect-square rounded-3xl bg-gray-50 border-2 border-dashed border-gray-200 text-gray-400 hover:border-[#31d2e8] hover:text-[#31d2e8] transition-all group"
                      >
                        <span className="material-symbols-outlined text-3xl group-hover:scale-110 transition-transform">add_a_photo</span>
                        <span className="text-[10px] font-bold mt-1 uppercase">照片</span>
                      </button>
                      <button 
                        onClick={() => videoInputRef.current?.click()}
                        className="flex flex-col items-center justify-center flex-1 aspect-square rounded-3xl bg-gray-50 border-2 border-dashed border-gray-200 text-gray-400 hover:border-[#31d2e8] hover:text-[#31d2e8] transition-all group"
                      >
                        <span className="material-symbols-outlined text-3xl group-hover:scale-110 transition-transform">videocam</span>
                        <span className="text-[10px] font-bold mt-1 uppercase">视频</span>
                      </button>
                      <button 
                        onClick={() => setShowDiarySelector(true)}
                        className="flex flex-col items-center justify-center flex-1 aspect-square rounded-3xl bg-[#f0fdff] border-2 border-dashed border-cyan-100 text-[#31d2e8] hover:bg-cyan-50 transition-all group"
                      >
                        <span className="material-symbols-outlined text-3xl group-hover:scale-110 transition-transform">auto_stories</span>
                        <span className="text-[10px] font-bold mt-1 uppercase text-center leading-tight">选择今日<br/>日记</span>
                      </button>
                    </div>
                    
                    <div className="flex items-center gap-2 p-4 bg-cyan-50 rounded-2xl border border-cyan-100">
                      <span className="material-symbols-outlined text-[#31d2e8]">auto_awesome</span>
                      <p className="text-xs font-bold text-cyan-700">AI 将自动为您生成精彩故事文案</p>
                    </div>
                  </>
                )}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default SocialView;
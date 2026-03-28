/**
 * PawFlip 前端 API 服务
 * 封装所有与后端的通信
 */

// ===========================================
// 配置
// ===========================================

// 后端 API 基础 URL
const API_BASE_URL = (import.meta as any).env?.VITE_API_URL || 'http://localhost:8003/api/v1';

// 存储令牌的 key
const TOKEN_KEY = 'pawflip_token';

/**
 * 将外部 3D 资源 URL 转换为代理 URL（解决 CORS 问题）
 * 支持 Meshy AI、腾讯云 COS（混元3D）等来源
 */
function proxyMeshyUrl(url: string | undefined, type: '3d-model' | '3d-preview' = '3d-model'): string | undefined {
  if (!url) return undefined;
  
  // 需要代理的域名模式
  const needsProxy =
    url.includes('assets.meshy.ai') ||
    url.includes('.cos.') ||           // 腾讯云 COS
    url.includes('hunyuan') ||         // 混元相关域名
    url.includes('tencentcos.cn') ||   // 腾讯云 COS 域名
    url.includes('myqcloud.com');      // 腾讯云通用域名
  
  if (!needsProxy) return url;
  
  // 转换为代理 URL
  const endpoint = type === '3d-model' ? '/proxy/3d-model' : '/proxy/3d-preview';
  return `${API_BASE_URL}${endpoint}?url=${encodeURIComponent(url)}`;
}

// ===========================================
// 类型定义
// ===========================================

export interface User {
  id: string;
  email: string;
  username?: string;
  avatar_url?: string;
  created_at: string;
  is_pro: boolean;
}

export interface Pet {
  id: string;
  user_id: string;
  name: string;
  breed: string;
  age: string;
  avatar_url?: string;
  created_at: string;
  battery: number;
  health_score: number;
  steps: number;
  next_feeding?: string;
  model_3d_url?: string;
  model_3d_preview?: string;
}

export interface DiaryEntry {
  id: string;
  pet_id: string;
  user_id: string;
  title: string;
  content: string;
  type: 'activity' | 'feeding' | 'health' | 'social';
  image_url?: string;
  video_url?: string;
  is_video: boolean;
  duration?: string;
  created_at: string;
  status: string;
  activity_trend?: { v: number }[];
  ai_analysis?: Record<string, any>;
}

export interface HealthTrend {
  period: string;
  data: { name: string; value: number }[];
  summary: {
    average: number;
    trend: string;
    change: string;
  };
}

export interface SocialPost {
  id: string;
  pet_id: string;
  user_id: string;
  content: string;
  image_url?: string;
  is_ai_story: boolean;
  created_at: string;
  likes: number;
  comments: number;
  pet_name?: string;
  pet_breed?: string;
  pet_avatar?: string;
  diary_entry_id?: string;
}

export interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
}

export interface VideoJobStatus {
  job_id: string;
  status: 'pending' | 'processing' | 'completed' | 'failed';
  progress?: string;
  result?: any;
  error?: string;
  created_at: string;
  completed_at?: string;
}

// ===========================================
// 基础请求函数
// ===========================================

/**
 * 获取存储的令牌
 */
function getToken(): string | null {
  return localStorage.getItem(TOKEN_KEY);
}

/**
 * 保存令牌
 */
function setToken(token: string): void {
  localStorage.setItem(TOKEN_KEY, token);
}

/**
 * 清除令牌
 */
function clearToken(): void {
  localStorage.removeItem(TOKEN_KEY);
}

/**
 * 发送 API 请求
 */
async function request<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const token = getToken();
  
  const headers: HeadersInit = {
    'Content-Type': 'application/json',
    ...options.headers,
  };
  
  if (token) {
    (headers as Record<string, string>)['Authorization'] = `Bearer ${token}`;
  }
  
  const response = await fetch(`${API_BASE_URL}${endpoint}`, {
    ...options,
    headers,
  });
  
  if (!response.ok) {
    const error = await response.json().catch(() => ({ error: '请求失败' }));
    throw new Error(error.detail || error.error || '请求失败');
  }
  
  return response.json();
}

/**
 * 发送带文件的请求（支持取消）
 */
async function uploadRequest<T>(
  endpoint: string,
  formData: FormData,
  signal?: AbortSignal
): Promise<T> {
  const token = getToken();
  
  const headers: HeadersInit = {};
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }
  
  const response = await fetch(`${API_BASE_URL}${endpoint}`, {
    method: 'POST',
    headers,
    body: formData,
    signal, // 支持取消
  });
  
  if (!response.ok) {
    const error = await response.json().catch(() => ({ error: '上传失败' }));
    throw new Error(error.detail || error.error || '上传失败');
  }
  
  return response.json();
}

// ===========================================
// 认证 API
// ===========================================

export const authApi = {
  /**
   * 用户注册
   */
  async register(email: string, password: string, username?: string) {
    const result = await request<{ access_token: string; user: User }>('/auth/register', {
      method: 'POST',
      body: JSON.stringify({ email, password, username }),
    });
    setToken(result.access_token);
    return result;
  },
  
  /**
   * 用户登录
   */
  async login(email: string, password: string) {
    const result = await request<{ access_token: string; user: User }>('/auth/login', {
      method: 'POST',
      body: JSON.stringify({ email, password }),
    });
    setToken(result.access_token);
    return result;
  },
  
  /**
   * 获取当前用户信息
   */
  async getMe(): Promise<User> {
    return request<User>('/auth/me');
  },
  
  /**
   * 验证令牌
   */
  async verifyToken(): Promise<boolean> {
    try {
      await request('/auth/verify');
      return true;
    } catch {
      return false;
    }
  },
  
  /**
   * 登出
   */
  logout() {
    try {
      // 清除存储的令牌
      clearToken();
      
      // 清除其他可能的用户数据缓存
      localStorage.removeItem('pawflip_user');
      localStorage.removeItem('pawflip_pets');
      
      // 清除会话存储
      sessionStorage.clear();
      
      console.log('用户已成功退出登录');
    } catch (error) {
      console.error('退出登录时清理数据失败:', error);
    }
  },
  
  /**
   * 检查是否已登录
   */
  isLoggedIn(): boolean {
    return !!getToken();
  },
};

// ===========================================
// 宠物 API
// ===========================================

export const petsApi = {
  /**
   * 创建宠物
   */
  async create(data: { name: string; breed: string; age: string; avatar_url?: string }): Promise<Pet> {
    return request<Pet>('/pets', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  },
  
  /**
   * 创建宠物并生成 3D 模型
   */
  async createWith3DModel(
    name: string,
    breed: string,
    age: string,
    photo: File
  ): Promise<Pet> {
    const formData = new FormData();
    formData.append('name', name);
    formData.append('breed', breed);
    formData.append('age', age);
    formData.append('photo', photo);
    
    const pet = await uploadRequest<Pet>('/pets/with-3d-model', formData);
    
    // 转换 3D 模型 URL 为代理 URL（解决 CORS 问题）
    if (pet.model_3d_url) {
      pet.model_3d_url = proxyMeshyUrl(pet.model_3d_url, '3d-model') || pet.model_3d_url;
    }
    if (pet.model_3d_preview) {
      pet.model_3d_preview = proxyMeshyUrl(pet.model_3d_preview, '3d-preview') || pet.model_3d_preview;
    }
    
    return pet;
  },
  
  /**
   * 获取所有宠物
   */
  async getAll(): Promise<Pet[]> {
    const pets = await request<Pet[]>('/pets');
    
    // 转换所有宠物的 3D 模型 URL
    return pets.map(pet => ({
      ...pet,
      model_3d_url: proxyMeshyUrl(pet.model_3d_url, '3d-model') || pet.model_3d_url,
      model_3d_preview: proxyMeshyUrl(pet.model_3d_preview, '3d-preview') || pet.model_3d_preview
    }));
  },
  
  /**
   * 获取单个宠物
   */
  async get(petId: string): Promise<Pet> {
    const pet = await request<Pet>(`/pets/${petId}`);
    
    // 转换 3D 模型 URL
    if (pet.model_3d_url) {
      pet.model_3d_url = proxyMeshyUrl(pet.model_3d_url, '3d-model') || pet.model_3d_url;
    }
    if (pet.model_3d_preview) {
      pet.model_3d_preview = proxyMeshyUrl(pet.model_3d_preview, '3d-preview') || pet.model_3d_preview;
    }
    
    return pet;
  },
  
  /**
   * 更新宠物
   */
  async update(petId: string, data: Partial<Pet>): Promise<Pet> {
    return request<Pet>(`/pets/${petId}`, {
      method: 'PATCH',
      body: JSON.stringify(data),
    });
  },
  
  /**
   * 删除宠物
   */
  async delete(petId: string): Promise<void> {
    await request(`/pets/${petId}`, { method: 'DELETE' });
  },
};

// ===========================================
// 日记 API
// ===========================================

export const diaryApi = {
  /**
   * 创建日记
   */
  async create(data: {
    pet_id: string;
    title: string;
    content: string;
    type?: string;
    image_url?: string;
    video_url?: string;
  }): Promise<DiaryEntry> {
    return request<DiaryEntry>('/diary', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  },
  
  /**
   * 获取宠物的日记列表
   */
  async getByPet(petId: string, type?: string, limit = 20): Promise<DiaryEntry[]> {
    let url = `/diary/pet/${petId}?limit=${limit}`;
    if (type) url += `&entry_type=${type}`;
    return request<DiaryEntry[]>(url);
  },
  
  /**
   * 获取单条日记
   */
  async get(entryId: string): Promise<DiaryEntry> {
    return request<DiaryEntry>(`/diary/${entryId}`);
  },
  
  /**
   * 删除日记
   */
  async delete(entryId: string): Promise<void> {
    await request(`/diary/${entryId}`, { method: 'DELETE' });
  },
  
  /**
   * AI 生成日记
   */
  async generate(petId: string, prompt?: string): Promise<DiaryEntry> {
    let url = `/diary/generate/${petId}`;
    if (prompt) url += `?prompt=${encodeURIComponent(prompt)}`;
    return request<DiaryEntry>(url, { method: 'POST' });
  },
  
  /**
   * 获取周总结
   */
  async getWeeklySummary(petId: string): Promise<{ summary: string }> {
    return request<{ summary: string }>(`/diary/summary/${petId}`);
  },
};

// ===========================================
// 健康 API
// ===========================================

export const healthApi = {
  /**
   * 记录健康数据
   */
  async record(petId: string, data: {
    heart_rate?: number;
    steps?: number;
    sleep_hours?: number;
    calories?: number;
    activity_minutes?: number;
  }): Promise<any> {
    return request(`/health/record/${petId}`, {
      method: 'POST',
      body: JSON.stringify({ pet_id: petId, ...data }),
    });
  },
  
  /**
   * 获取健康趋势
   */
  async getTrend(
    petId: string,
    period: 'week' | 'month' | 'year' = 'week',
    metric: 'activity' | 'sleep' | 'heartRate' | 'calories' = 'activity'
  ): Promise<HealthTrend> {
    return request<HealthTrend>(`/health/trend/${petId}?period=${period}&metric=${metric}`);
  },
  
  /**
   * 获取 AI 健康建议
   */
  async getAdvice(petId: string): Promise<{ pet_id: string; advice: string; health_score: number }> {
    return request(`/health/advice/${petId}`);
  },
  
  /**
   * 获取实时状态
   */
  async getStatus(petId: string): Promise<{
    pet_id: string;
    name: string;
    battery: number;
    health_score: number;
    steps: number;
    next_feeding?: string;
    status: string;
  }> {
    return request(`/health/status/${petId}`);
  },
};

// ===========================================
// 视频 API
// ===========================================

export const videoApi = {
  /**
   * 同步处理视频
   */
  async process(file: File, petId?: string, mode = 'api'): Promise<any> {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('mode', mode);
    if (petId) formData.append('pet_id', petId);
    
    return uploadRequest('/video/process', formData);
  },
  
  /**
   * 异步处理视频
   */
  async processAsync(file: File, petId?: string, mode = 'api'): Promise<{ job_id: string }> {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('mode', mode);
    if (petId) formData.append('pet_id', petId);
    
    return uploadRequest('/video/process/async', formData);
  },
  
  /**
   * 查询任务状态
   */
  async getJobStatus(jobId: string): Promise<VideoJobStatus> {
    return request<VideoJobStatus>(`/video/jobs/${jobId}`);
  },
  
  /**
   * 列出所有任务
   */
  async listJobs(): Promise<{ total: number; jobs: VideoJobStatus[] }> {
    return request('/video/jobs');
  },
  
  /**
   * 视频转日记
   */
  async toDiary(file: File, petId: string, mode = 'api'): Promise<DiaryEntry> {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('pet_id', petId);
    formData.append('mode', mode);
    
    return uploadRequest<DiaryEntry>('/video/to-diary', formData);
  },
};

// ===========================================
// AI 聊天 API
// ===========================================

export const aiApi = {
  /**
   * AI 聊天
   */
  async chat(
    message: string,
    history: ChatMessage[] = [],
    petId?: string,
    contextType?: 'health' | 'diary' | 'general'
  ): Promise<{ message: string; suggestions?: string[] }> {
    return request('/ai/chat', {
      method: 'POST',
      body: JSON.stringify({
        message,
        history,
        pet_id: petId,
        context_type: contextType,
      }),
    });
  },
  
  /**
   * 健康问诊
   */
  async healthConsult(
    message: string,
    history: ChatMessage[] = [],
    petId?: string
  ): Promise<{ message: string; suggestions?: string[] }> {
    return request('/ai/health-consult', {
      method: 'POST',
      body: JSON.stringify({
        message,
        history,
        pet_id: petId,
      }),
    });
  },
  
  /**
   * 生成故事
   */
  async generateStory(analysis: Record<string, any>): Promise<{ story: string }> {
    return request('/ai/generate-story', {
      method: 'POST',
      body: JSON.stringify(analysis),
    });
  },
  
  /**
   * 获取 AI 配置
   */
  async getConfig(): Promise<{
    provider: string;
    model: string;
    features: Record<string, boolean>;
  }> {
    return request('/ai/config');
  },
};

// ===========================================
// 社交 API
// ===========================================

export const socialApi = {
  /**
   * 发布帖子
   */
  async createPost(data: {
    pet_id: string;
    content: string;
    image_url?: string;
    is_ai_story?: boolean;
    diary_entry_id?: string;
  }): Promise<SocialPost> {
    return request<SocialPost>('/social/posts', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  },
  
  /**
   * 发布视频日记（调用 pet-vision-narrator）
   * @param signal - 可选的 AbortSignal，用于取消请求
   */
  async createVideoPost(
    petId: string,
    videoFile: File,
    mode: string = 'api',
    signal?: AbortSignal
  ): Promise<SocialPost> {
    const formData = new FormData();
    formData.append('pet_id', petId);
    formData.append('video', videoFile);
    formData.append('mode', mode);
    
    return uploadRequest<SocialPost>('/social/posts/video', formData, signal);
  },
  
  /**
   * 获取关注动态
   */
  async getFollowingPosts(limit = 20): Promise<SocialPost[]> {
    return request<SocialPost[]>(`/social/posts/following?limit=${limit}`);
  },
  
  /**
   * 获取发现页动态
   */
  async getDiscoveryPosts(limit = 20): Promise<SocialPost[]> {
    return request<SocialPost[]>(`/social/posts/discovery?limit=${limit}`);
  },
  
  /**
   * 点赞帖子
   */
  async likePost(postId: string): Promise<void> {
    await request(`/social/posts/${postId}/like`, { method: 'POST' });
  },
  
  /**
   * 取消点赞
   */
  async unlikePost(postId: string): Promise<void> {
    await request(`/social/posts/${postId}/like`, { method: 'DELETE' });
  },
  
  /**
   * 删除帖子
   */
  async deletePost(postId: string): Promise<void> {
    await request(`/social/posts/${postId}`, { method: 'DELETE' });
  },
};

// ===========================================
// 导出所有 API 和工具函数
// ===========================================

export { proxyMeshyUrl };

export default {
  auth: authApi,
  pets: petsApi,
  diary: diaryApi,
  health: healthApi,
  video: videoApi,
  ai: aiApi,
  social: socialApi,
};

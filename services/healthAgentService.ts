/**
 * Health Agent 前端服务
 * 封装与后端 Health Agent API 的通信
 */

// ===========================================
// 配置
// ===========================================

const API_BASE_URL = (import.meta as any).env?.VITE_API_URL || 'http://localhost:8003/api/v1';
const TOKEN_KEY = 'pawflip_token';

// ===========================================
// 类型定义
// ===========================================

export interface ChatRequest {
  message: string;
  petId: string;
  conversationId?: string;
}

export interface ToolAction {
  name: string;
  icon: string;
  status: 'pending' | 'running' | 'completed';
}

export interface ChatResponse {
  conversationId: string;
  messageId: string;
  response: string;
  suggestions: string[];
  toolActions: ToolAction[];
}

export interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  createdAt: string;
  metadata?: Record<string, any>;
}

export interface KeyInfo {
  id: string;
  type: 'symptom' | 'diagnosis' | 'advice';
  content: string;
  createdAt: string;
}

export interface ConversationSummary {
  id: string;
  title?: string;
  summary?: string;
  petId: string;
  petName: string;
  updatedAt: string;
  messageCount: number;
}

export interface ConversationDetail {
  id: string;
  title?: string;
  summary?: string;
  petId: string;
  status: 'active' | 'archived';
  messages: Message[];
  keyInfo: KeyInfo[];
  createdAt: string;
  updatedAt: string;
}

export interface HealthTrendData {
  name: string;
  value: number;
}

export interface HealthTrendSummary {
  avgActivity: number;
  avgSleep: number;
  avgHeartRate: number;
  totalCalories: number;
  totalSteps: number;
}

export interface HealthTrendsResponse {
  activity: HealthTrendData[];
  sleep: HealthTrendData[];
  heartRate: HealthTrendData[];
  calories: HealthTrendData[];
  summary: HealthTrendSummary | null;
}

// ===========================================
// 工具函数
// ===========================================

function getToken(): string | null {
  return localStorage.getItem(TOKEN_KEY);
}

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

// ===========================================
// 数据转换
// ===========================================

function transformMessage(msg: any): Message {
  return {
    id: msg.id,
    role: msg.role,
    content: msg.content,
    createdAt: msg.created_at,
    metadata: msg.metadata,
  };
}

function transformKeyInfo(ki: any): KeyInfo {
  return {
    id: ki.id,
    type: ki.type,
    content: ki.content,
    createdAt: ki.created_at,
  };
}

function transformConversationSummary(conv: any): ConversationSummary {
  return {
    id: conv.id,
    title: conv.title,
    summary: conv.summary,
    petId: conv.pet_id,
    petName: conv.pet_name,
    updatedAt: conv.updated_at,
    messageCount: conv.message_count,
  };
}

function transformConversationDetail(conv: any): ConversationDetail {
  return {
    id: conv.id,
    title: conv.title,
    summary: conv.summary,
    petId: conv.pet_id,
    status: conv.status,
    messages: (conv.messages || []).map(transformMessage),
    keyInfo: (conv.key_info || []).map(transformKeyInfo),
    createdAt: conv.created_at,
    updatedAt: conv.updated_at,
  };
}

// ===========================================
// Health Agent API
// ===========================================

export const healthAgentService = {
  /**
   * 发送消息到 AI 健康助手
   */
  async chat(req: ChatRequest): Promise<ChatResponse> {
    const response = await request<any>('/health-agent/chat', {
      method: 'POST',
      body: JSON.stringify({
        message: req.message,
        pet_id: req.petId,
        conversation_id: req.conversationId,
      }),
    });
    
    return {
      conversationId: response.conversation_id,
      messageId: response.message_id,
      response: response.response,
      suggestions: response.suggestions || [],
      toolActions: (response.tool_actions || []).map((ta: any) => ({
        name: ta.name,
        icon: ta.icon,
        status: ta.status,
      })),
    };
  },
  
  /**
   * 获取对话列表
   */
  async getConversations(limit = 20): Promise<ConversationSummary[]> {
    const response = await request<any>(`/health-agent/conversations?limit=${limit}`);
    return (response.conversations || []).map(transformConversationSummary);
  },
  
  /**
   * 获取对话详情
   */
  async getConversation(conversationId: string): Promise<ConversationDetail> {
    const response = await request<any>(`/health-agent/conversations/${conversationId}`);
    return transformConversationDetail(response);
  },
  
  /**
   * 创建新对话
   */
  async createConversation(petId: string, initialMessage?: string): Promise<string> {
    const response = await request<any>('/health-agent/conversations', {
      method: 'POST',
      body: JSON.stringify({
        pet_id: petId,
        initial_message: initialMessage,
      }),
    });
    return response.conversation_id;
  },
  
  /**
   * 获取健康趋势数据
   */
  async getHealthTrends(petId: string, range: 'week' | 'month' | 'year' = 'week'): Promise<HealthTrendsResponse> {
    return request<HealthTrendsResponse>(`/health-agent/trends/${petId}?range=${range}`);
  },
};

export default healthAgentService;

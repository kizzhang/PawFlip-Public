
export type ViewState = 'landing' | 'unregistered' | 'login' | 'user-register' | 'register' | 'home' | 'health' | 'trends' | 'diary' | 'social' | 'settings' | 'camera' | 'api-test';

export interface User {
  id: string;
  email: string;
  username?: string;
  avatar_url?: string;
  is_pro: boolean;
  created_at: string;
}

export interface PetInfo {
  id?: string;
  user_id?: string;
  name: string;
  age: string;
  breed: string;
  battery: number;
  healthScore: number;
  steps: number;
  nextFeeding: string;
  avatar?: string;
  model_3d_url?: string;
  model_3d_preview?: string;
  created_at?: string;
}

export interface ChatMessage {
  role: 'user' | 'assistant';
  text: string;
  timestamp: Date;
}

export interface DiaryEntry {
  id: string;
  user_id: string;
  pet_id: string;
  time: string;
  status: string;
  title: string;
  content: string;
  imageUrl: string;
  isVideo?: boolean;
  duration?: string;
  type: 'activity' | 'feeding' | 'health' | 'social';
  ai_analysis?: Record<string, any>;
  created_at: string;
}

export interface SocialPost {
  id: string;
  user_id: string;
  pet_id: string;
  author: string;
  avatar: string;
  breed: string;
  time: string;
  content: string;
  imageUrl: string;
  likes: number;
  comments: number;
  isAiStory: boolean;
  diary_entry_id?: string;
  created_at: string;
}

export interface HealthRecord {
  id: string;
  pet_id: string;
  heart_rate?: number;
  steps?: number;
  sleep_hours?: number;
  calories?: number;
  activity_minutes?: number;
  created_at: string;
}

export interface Notification {
  id: string;
  user_id: string;
  title: string;
  description?: string;
  icon: string;
  color: string;
  is_read: boolean;
  created_at: string;
}

export interface Device {
  id: string;
  user_id: string;
  pet_id: string;
  name: string;
  device_type: string;
  firmware_version?: string;
  is_connected: boolean;
  battery_level: number;
  last_sync?: string;
  created_at: string;
}

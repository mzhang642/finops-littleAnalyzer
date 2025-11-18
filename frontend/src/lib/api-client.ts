import axios from 'axios';
import { useAuthStore } from '@/stores/auth';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export const apiClient = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add auth token to requests
apiClient.interceptors.request.use((config) => {
  const token = useAuthStore.getState().token;
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Handle auth errors
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      useAuthStore.getState().logout();
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

// API Types
export interface CloudAccount {
  id: string;
  provider: string;
  account_id: string;
  account_name: string;
  is_active: boolean;
  last_sync: string | null;
  last_sync_status: string | null;
}

export interface Recommendation {
  id: string;
  type: string;
  title: string;
  description: string;
  monthly_savings: number;
  risk_level: string;
  confidence: number;
  actions: string[];
  created_at: string;
}

export interface DashboardData {
  current_month_spend: number;
  potential_monthly_savings: number;
  savings_percentage: number;
  active_recommendations: number;
  top_recommendations: Array<{
    title: string;
    savings: number;
    risk: string;
  }>;
  service_breakdown: Record<string, number>;
  last_analysis: string | null;
}

// Form Data Types
export interface SignupData {
  email: string;
  password: string;
  full_name: string;
  organization_name: string;
}

export interface CloudAccountConnectData {
  provider: string;
  account_name: string;
  access_key: string;
  secret_key: string;
  region: string;
}

// API Functions
export const api = {
  auth: {
    login: (email: string, password: string) =>
      apiClient.post('/api/v1/auth/login', 
        new URLSearchParams({ username: email, password }),
        { headers: { 'Content-Type': 'application/x-www-form-urlencoded' } }
      ),
    signup: (data: SignupData) => 
      apiClient.post('/api/v1/auth/signup', data),
    me: () => 
      apiClient.get('/api/v1/auth/me'),
  },
  
  cloudAccounts: {
    list: () => 
      apiClient.get<CloudAccount[]>('/api/v1/cloud-accounts'),
    connect: (data: CloudAccountConnectData) => 
      apiClient.post<CloudAccount>('/api/v1/cloud-accounts/connect', data),
    disconnect: (id: string) => 
      apiClient.delete(`/api/v1/cloud-accounts/${id}`),
  },
  
  analysis: {
    run: (accountId: string, types: string[] = ['cost', 'ec2', 'storage']) =>
      apiClient.post('/api/v1/analysis/analyze', {
        cloud_account_id: accountId,
        analysis_types: types,
      }),
    recommendations: () => 
      apiClient.get<{ recommendations: Recommendation[] }>('/api/v1/analysis/recommendations'),
    dashboard: () => 
      apiClient.get<DashboardData>('/api/v1/analysis/dashboard'),
  },
};
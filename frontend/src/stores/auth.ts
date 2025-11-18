import { create } from 'zustand';
import { persist } from 'zustand/middleware';

export interface User {
  id: string;
  email: string;
  full_name: string;
  organization_id: string;
  role: string;
}

interface AuthState {
  token: string | null;
  user: User | null;
  isAuthenticated: boolean;
  login: (token: string, user: User) => void;
  logout: () => void;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      token: null,
      user: null,
      isAuthenticated: false,
      
      login: (token: string, user: User) => {
        set({ token, user, isAuthenticated: true });
        localStorage.setItem('auth_token', token);
      },
      
      logout: () => {
        set({ token: null, user: null, isAuthenticated: false });
        localStorage.removeItem('auth_token');
      },
    }),
    {
      name: 'auth-storage',
    }
  )
);
import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import { FilterOptions, UserProfile } from '@/types';

interface AppState {
  // Search filters
  filters: FilterOptions;
  setFilters: (filters: Partial<FilterOptions>) => void;
  resetFilters: () => void;
  
  // User session
  userId: string | null;
  sessionId: string;
  setUserId: (userId: string | null) => void;
  
  // User profile
  userProfile: UserProfile | null;
  setUserProfile: (profile: UserProfile | null) => void;
  
  // UI state
  isLoading: boolean;
  setIsLoading: (loading: boolean) => void;
  error: string | null;
  setError: (error: string | null) => void;
  
  // Search results
  lastSearchResults: number;
  setLastSearchResults: (count: number) => void;
  
  // Recent searches
  recentSearches: string[];
  addRecentSearch: (search: string) => void;
  clearRecentSearches: () => void;
  
  // Saved restaurants
  savedRestaurants: string[];
  toggleSavedRestaurant: (restaurantName: string) => void;
  isRestaurantSaved: (restaurantName: string) => boolean;
}

const defaultFilters: FilterOptions = {
  location: '',
  budget: 'medium',
  preferred_cuisine: '',
  min_rating: 3.5,
  top_n: 5,
};

export const useAppStore = create<AppState>()(
  persist(
    (set, get) => ({
      // Filters
      filters: { ...defaultFilters },
      setFilters: (newFilters) =>
        set((state) => ({
          filters: { ...state.filters, ...newFilters },
        })),
      resetFilters: () => set({ filters: { ...defaultFilters } }),
      
      // User
      userId: null,
      sessionId: '',
      setUserId: (userId) => set({ userId }),
      
      // Profile
      userProfile: null,
      setUserProfile: (profile) => set({ userProfile: profile }),
      
      // UI
      isLoading: false,
      setIsLoading: (loading) => set({ isLoading: loading }),
      error: null,
      setError: (error) => set({ error }),
      
      // Results
      lastSearchResults: 0,
      setLastSearchResults: (count) => set({ lastSearchResults: count }),
      
      // Recent searches
      recentSearches: [],
      addRecentSearch: (search) =>
        set((state) => ({
          recentSearches: [
            search,
            ...state.recentSearches.filter((s) => s !== search).slice(0, 4),
          ],
        })),
      clearRecentSearches: () => set({ recentSearches: [] }),
      
      // Saved restaurants
      savedRestaurants: [],
      toggleSavedRestaurant: (restaurantName) =>
        set((state) => {
          const isSaved = state.savedRestaurants.includes(restaurantName);
          return {
            savedRestaurants: isSaved
              ? state.savedRestaurants.filter((name) => name !== restaurantName)
              : [...state.savedRestaurants, restaurantName],
          };
        }),
      isRestaurantSaved: (restaurantName) =>
        get().savedRestaurants.includes(restaurantName),
    }),
    {
      name: 'dinesmart-storage',
      partialize: (state) => ({
        filters: state.filters,
        userId: state.userId,
        recentSearches: state.recentSearches,
        savedRestaurants: state.savedRestaurants,
      }),
    }
  )
);

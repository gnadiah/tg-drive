import { writable } from 'svelte/store';
import { checkAuth } from '../lib/api';

function createAuthStore() {
    const { subscribe, set, update } = writable({
        isAuthenticated: false,
        user: null,
        loading: true,
        error: null
    });

    return {
        subscribe,
        login: (user) => update(state => ({ ...state, isAuthenticated: true, user, loading: false, error: null })),
        logout: () => set({ isAuthenticated: false, user: null, loading: false, error: null }),
        check: async () => {
            try {
                const res = await checkAuth();
                if (res.authenticated) {
                    set({ isAuthenticated: true, user: res.user, loading: false, error: null });
                } else {
                    set({ isAuthenticated: false, user: null, loading: false, error: null });
                }
            } catch (err) {
                console.error("Auth check failed:", err);
                set({ isAuthenticated: false, user: null, loading: false, error: err.message || "Failed to connect" });
            }
        }
    };
}

export const auth = createAuthStore();

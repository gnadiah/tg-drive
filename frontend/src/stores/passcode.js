import { writable } from 'svelte/store';
import { hasPasscode, verifyPasscode, setPasscode, resetEncryption } from '../lib/api';

function createPasscodeStore() {
    const { subscribe, set, update } = writable({
        hasPasscode: false,
        isVerified: false,
        isLoading: false,
        error: null,
        attemptsRemaining: 5,
        lockedUntil: null
    });

    return {
        subscribe,

        async check() {
            update(state => ({ ...state, isLoading: true, error: null }));
            try {
                const result = await hasPasscode();
                update(state => ({
                    ...state,
                    hasPasscode: result.has_passcode,
                    isLoading: false
                }));
            } catch (error) {
                update(state => ({
                    ...state,
                    error: error.message,
                    isLoading: false
                }));
            }
        },

        async setup(passcode) {
            update(state => ({ ...state, isLoading: true, error: null }));
            try {
                const result = await setPasscode(passcode);
                if (result.success) {
                    update(state => ({
                        ...state,
                        hasPasscode: true,
                        isVerified: true,
                        isLoading: false
                    }));
                    return { success: true };
                } else {
                    update(state => ({
                        ...state,
                        error: result.error,
                        isLoading: false
                    }));
                    return { success: false, error: result.error };
                }
            } catch (error) {
                update(state => ({
                    ...state,
                    error: error.message,
                    isLoading: false
                }));
                return { success: false, error: error.message };
            }
        },

        async verify(passcode) {
            update(state => ({ ...state, isLoading: true, error: null }));
            try {
                const result = await verifyPasscode(passcode);

                if (result.valid) {
                    update(state => ({
                        ...state,
                        isVerified: true,
                        isLoading: false,
                        attemptsRemaining: 5,
                        lockedUntil: null,
                        error: null
                    }));
                    return { success: true };
                } else if (result.error === 'locked_out') {
                    const lockedUntil = Date.now() + (result.retry_after * 1000);
                    update(state => ({
                        ...state,
                        isLoading: false,
                        lockedUntil,
                        error: result.message
                    }));
                    return { success: false, locked: true, retryAfter: result.retry_after };
                } else if (result.error === 'too_many_attempts') {
                    const lockedUntil = Date.now() + (result.locked_for * 1000);
                    update(state => ({
                        ...state,
                        isLoading: false,
                        lockedUntil,
                        attemptsRemaining: 0,
                        error: result.message
                    }));
                    return { success: false, locked: true, lockedFor: result.locked_for };
                } else {
                    update(state => ({
                        ...state,
                        isLoading: false,
                        attemptsRemaining: result.attempts_remaining || 0,
                        error: result.message
                    }));
                    return {
                        success: false,
                        attemptsRemaining: result.attempts_remaining
                    };
                }
            } catch (error) {
                update(state => ({
                    ...state,
                    error: error.message,
                    isLoading: false
                }));
                return { success: false, error: error.message };
            }
        },

        async reset() {
            update(state => ({ ...state, isLoading: true, error: null }));
            try {
                const result = await resetEncryption();
                if (result.success) {
                    update(state => ({
                        hasPasscode: false,
                        isVerified: false,
                        isLoading: false,
                        error: null,
                        attemptsRemaining: 5,
                        lockedUntil: null
                    }));
                    return {
                        success: true,
                        passcodeDeleted: result.passcode_deleted,
                        filesDeleted: result.encrypted_files_deleted
                    };
                }
            } catch (error) {
                update(state => ({
                    ...state,
                    error: error.message,
                    isLoading: false
                }));
                return { success: false, error: error.message };
            }
        },

        async change(oldPasscode, newPasscode) {
            update(state => ({ ...state, isLoading: true, error: null }));
            try {
                // API call
                const { changePasscode } = await import('../lib/api');
                const result = await changePasscode(oldPasscode, newPasscode);

                if (result.success) {
                    update(state => ({
                        ...state,
                        isLoading: false,
                        error: null
                    }));
                    return { success: true };
                } else {
                    update(state => ({
                        ...state,
                        isLoading: false,
                        error: result.error
                    }));
                    return { success: false, error: result.error };
                }
            } catch (error) {
                update(state => ({
                    ...state,
                    isLoading: false,
                    error: error.message
                }));
                return { success: false, error: error.message };
            }
        },

        clearError() {
            update(state => ({ ...state, error: null }));
        },

        skip() {
            // User skips passcode setup, continues with plaintext
            update(state => ({
                ...state,
                hasPasscode: false,
                isVerified: true  // Allow access to app
            }));
        },

        resetState() {
            set({
                hasPasscode: false,
                isVerified: false,
                isLoading: false,
                error: null,
                attemptsRemaining: 5,
                lockedUntil: null
            });
        }
    };
}

export const passcode = createPasscodeStore();

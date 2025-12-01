import { writable, derived } from 'svelte/store';
import { listFiles, uploadFile, downloadFile, renameFile, deleteFile } from '../lib/api';

function createFileStore() {
    const { subscribe, set, update } = writable({
        files: [],
        loading: false,
        error: null,
        uploads: {},   // id -> { id, file, progress, status, error }
        downloads: {}  // id -> { id, file, progress, status, error }
    });

    // Setup global listeners for Bridge events
    if (typeof window !== 'undefined') {
        window.onUploadProgress = (fileId, progress, speed, statusMsg) => {
            update(s => {
                const upload = s.uploads[fileId] || { id: fileId, file: { name: 'Uploading...' }, progress: 0, status: 'uploading', speed: '0 B/s' };
                return {
                    ...s,
                    uploads: {
                        ...s.uploads,
                        [fileId]: { ...upload, progress, speed, status: 'uploading' }
                    }
                };
            });
        };

        window.onUploadComplete = (fileId) => {
            update(s => ({
                ...s,
                uploads: {
                    ...s.uploads,
                    [fileId]: { ...s.uploads[fileId], progress: 100, status: 'completed', speed: 'Done' }
                }
            }));
            // Refresh list
            fileStore.loadFiles();
            // Cleanup
            setTimeout(() => {
                update(s => {
                    const { [fileId]: _, ...rest } = s.uploads;
                    return { ...s, uploads: rest };
                });
            }, 3000);
        };

        window.onUploadError = (fileId, error) => {
            update(s => ({
                ...s,
                uploads: {
                    ...s.uploads,
                    [fileId]: { ...s.uploads[fileId], status: 'error', error, speed: '-' }
                }
            }));
        };

        window.onDownloadProgress = (fileId, progress, speed, statusMsg) => {
            update(s => {
                const download = s.downloads[fileId] || { id: fileId, file: { name: 'Downloading...' }, progress: 0, status: 'downloading', speed: '0 B/s' };
                return {
                    ...s,
                    downloads: {
                        ...s.downloads,
                        [fileId]: { ...download, progress, speed, status: 'downloading' }
                    }
                };
            });
        };

        window.onDownloadComplete = (fileId) => {
            update(s => ({
                ...s,
                downloads: {
                    ...s.downloads,
                    [fileId]: { ...s.downloads[fileId], progress: 100, status: 'completed' }
                }
            }));
            setTimeout(() => {
                update(s => {
                    const { [fileId]: _, ...rest } = s.downloads;
                    return { ...s, downloads: rest };
                });
            }, 3000);
        };

        window.onDownloadError = (fileId, error) => {
            update(s => ({
                ...s,
                downloads: {
                    ...s.downloads,
                    [fileId]: { ...s.downloads[fileId], status: 'error', error }
                }
            }));
        };
    }

    return {
        subscribe,

        // Load files from backend
        loadFiles: async () => {
            update(s => ({ ...s, loading: true, error: null }));
            try {
                const res = await listFiles();
                update(s => ({ ...s, files: res, loading: false }));
            } catch (err) {
                console.error("Failed to load files:", err);
                update(s => ({ ...s, loading: false, error: err.message }));
            }
        },

        // Upload file - Triggers native picker
        uploadFile: async () => {
            try {
                const res = await uploadFile();
                if (res.status === 'started') {
                    // Wait for progress events
                }
            } catch (err) {
                console.error("Upload trigger failed:", err);
            }
        },

        // Download file
        downloadFile: async (file) => {
            const downloadId = file.id;
            // Init state
            update(s => ({
                ...s,
                downloads: {
                    ...s.downloads,
                    [downloadId]: {
                        id: downloadId,
                        file: file,
                        progress: 0,
                        status: 'downloading',
                        error: null
                    }
                }
            }));

            try {
                await downloadFile(file.id);
            } catch (err) {
                console.error("Download trigger failed:", err);
                update(s => ({
                    ...s,
                    downloads: {
                        ...s.downloads,
                        [downloadId]: { ...s.downloads[downloadId], status: 'error', error: err.message }
                    }
                }));
            }
        },

        // Rename file
        renameFile: async (file, newName) => {
            try {
                await renameFile(file.id, newName, file.metadata_message_id);
                const res = await listFiles();
                update(s => ({ ...s, files: res }));
                return true;
            } catch (err) {
                console.error("Rename failed:", err);
                throw err;
            }
        },

        // Delete file
        deleteFile: async (file) => {
            try {
                await deleteFile(file.id, file.metadata_message_id);
                const res = await listFiles();
                update(s => ({ ...s, files: res }));
                return true;
            } catch (err) {
                console.error("Delete failed:", err);
                throw err;
            }
        },

        // Clear completed transfers
        clearCompleted: () => {
            update(s => {
                const newUploads = {};
                const newDownloads = {};

                Object.values(s.uploads).forEach(u => {
                    if (u.status !== 'completed') newUploads[u.id] = u;
                });

                Object.values(s.downloads).forEach(d => {
                    if (d.status !== 'completed') newDownloads[d.id] = d;
                });

                return { ...s, uploads: newUploads, downloads: newDownloads };
            });
        }
    };
}

export const fileStore = createFileStore();

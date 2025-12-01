// PyWebView Bridge Wrapper

const call = async (method, ...args) => {
    if (window.pywebview) {
        try {
            return await window.pywebview.api[method](...args);
        } catch (e) {
            console.error(`Bridge error [${method}]:`, e);
            throw e;
        }
    } else {
        console.warn(`PyWebView not ready. Calling [${method}] mocked.`);
        // Mock for browser testing without python
        if (method === 'check_auth') {
            console.warn("Mocking check_auth: { authenticated: false }");
            return { authenticated: false };
        }
        throw new Error("PyWebView not ready");
    }
};

// Auth
export const checkAuth = () => call('check_auth');
export const requestOtp = (phone) => call('request_code', phone);
export const signIn = (phone, code, password) => call('sign_in', phone, code, password);
export const logout = () => call('logout');

// QR Auth
export const requestQR = () => call('request_qr');
export const checkQRStatus = (tokenId) => call('check_qr_status', tokenId);
// cancelQR not strictly needed if we just stop polling, or implement in bridge

// Files
export const listFiles = () => call('list_files');

// Upload - Triggers native picker
export const uploadFile = () => call('pick_and_upload_file');

// Download - Triggers native save dialog
export const downloadFile = (fileId) => call('download_file', fileId);

export const renameFile = (fileId, newName, metadataMessageId) => call('rename_file', fileId, newName, metadataMessageId);
export const deleteFile = (fileId, metadataMessageId) => call('delete_file', fileId, metadataMessageId);

// Listeners for progress (exposed to window by Bridge)
// window.onUploadProgress = (fileId, progress, status) => ...
// window.onDownloadProgress = (fileId, progress) => ...

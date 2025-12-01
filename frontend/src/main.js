import { mount } from 'svelte'
import './app.css'
import App from './App.svelte'

// Redirect logs to Python
const setupLogBridge = () => {
  if (window.pywebview) {
    const sendLog = (level, args) => {
      try {
        const msg = args.map(a => {
          if (a instanceof Error) return a.toString();
          if (typeof a === 'object') return JSON.stringify(a);
          return String(a);
        }).join(' ');
        window.pywebview.api.log(`[${level}] ${msg}`).catch(() => { });
      } catch (e) {
        // Ignore logging errors
      }
    };

    const originalLog = console.log;
    console.log = (...args) => { originalLog(...args); sendLog('INFO', args); };

    const originalError = console.error;
    console.error = (...args) => { originalError(...args); sendLog('ERROR', args); };

    const originalWarn = console.warn;
    console.warn = (...args) => { originalWarn(...args); sendLog('WARN', args); };

    console.log("Log bridge setup complete");
  }
};

if (window.pywebview) {
  setupLogBridge();
} else {
  window.addEventListener('pywebviewready', setupLogBridge);
}

const app = mount(App, {
  target: document.getElementById('app'),
})

export default app

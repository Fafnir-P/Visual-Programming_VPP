const { contextBridge, ipcRenderer } = require('electron');

// Only these calls reach the main process. Passwords go in; the hash never comes out.
contextBridge.exposeInMainWorld('vpAuth', {
  status: () => ipcRenderer.invoke('auth:status'),
  register: (username, password) => ipcRenderer.invoke('auth:register', String(username), String(password)),
  login: (username, password) => ipcRenderer.invoke('auth:login', String(username), String(password)),
  logout: () => ipcRenderer.invoke('auth:logout'),
  saveKey: (key) => ipcRenderer.invoke('key:save', String(key)),
  loadKey: () => ipcRenderer.invoke('key:load'),
  clearKey: () => ipcRenderer.invoke('key:clear')
});

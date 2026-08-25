const { app, BrowserWindow, Tray, Menu, globalShortcut, Notification, nativeImage } = require('electron')
const path = require('path')
const http = require('http')

let mainWindow = null
let tray = null
let isQuitting = false

function checkBackendHealth(callback) {
  const req = http.get('http://127.0.0.1:8000/api/health', (res) => {
    callback(res.statusCode === 200)
  })
  req.on('error', () => callback(false))
  req.setTimeout(1500, () => {
    req.destroy()
    callback(false)
  })
}

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1280,
    height: 820,
    minWidth: 1024,
    minHeight: 700,
    title: 'Jarvis AI OS',
    backgroundColor: '#0a0d14',
    show: true,
    center: true,
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
      webSecurity: false,
      allowRunningInsecureContent: true,
    },
  })

  const devUrl = 'http://localhost:3000'
  const prodFile = path.join(__dirname, '../dist/index.html')

  mainWindow.webContents.on('did-fail-load', (event, errorCode, errorDescription, validatedURL) => {
    if (errorCode !== -3 && validatedURL && validatedURL.startsWith('http://localhost:3000')) {
      mainWindow.loadFile(prodFile).catch((err) => console.error('loadFile error:', err))
    }
  })

  mainWindow.loadURL(devUrl).catch(() => {
    mainWindow.loadFile(prodFile)
  })

  mainWindow.once('ready-to-show', () => {
    if (mainWindow) {
      mainWindow.show()
      mainWindow.setAlwaysOnTop(true)
      mainWindow.focus()
      mainWindow.setAlwaysOnTop(false)
    }
  })

  mainWindow.show()
  mainWindow.setAlwaysOnTop(true)
  mainWindow.focus()
  mainWindow.setAlwaysOnTop(false)

  // Close-to-tray: keep running in background 24/7
  mainWindow.on('close', (event) => {
    if (!isQuitting) {
      event.preventDefault()
      mainWindow.hide()
      if (Notification.isSupported()) {
        new Notification({
          title: 'Jarvis AI OS',
          body: 'Jarvis is running silently in your System Tray and working 24/7.',
          silent: true,
        }).show()
      }
    }
  })
}

function createTray() {
  try {
    const iconPath = path.join(__dirname, '../public/iconedge-logo.png')
    let trayIcon = nativeImage.createFromPath(iconPath)
    if (!trayIcon.isEmpty()) {
      trayIcon = trayIcon.resize({ width: 16, height: 16 })
      tray = new Tray(trayIcon)
      tray.setToolTip('Jarvis AI OS - Active 24/7')

      const contextMenu = Menu.buildFromTemplate([
        { label: '🟢 Jarvis AI OS (Online)', enabled: false },
        { type: 'separator' },
        {
          label: '🎙️ Summon Voice Orb (Alt + J)',
          click: () => toggleMainWindow(),
        },
        {
          label: '📋 Open Board Room',
          click: () => {
            showAndNavigate('/meetings')
          },
        },
        {
          label: '⚡ Open Autonomous Scheduler',
          click: () => {
            showAndNavigate('/scheduler')
          },
        },
        {
          label: '🎯 Open Growth Hub',
          click: () => {
            showAndNavigate('/growth-hub')
          },
        },
        { type: 'separator' },
        {
          label: '👁️ Show / Hide Window',
          click: () => toggleMainWindow(),
        },
        {
          label: '🛑 Quit Jarvis',
          click: () => {
            isQuitting = true
            app.quit()
          },
        },
      ])

      tray.setContextMenu(contextMenu)
      tray.on('click', () => toggleMainWindow())
      tray.on('double-click', () => toggleMainWindow())
    }
  } catch (err) {
    console.error('Tray initialization skipped:', err)
  }
}

function toggleMainWindow() {
  if (!mainWindow) {
    createWindow()
    return
  }
  if (mainWindow.isVisible()) {
    mainWindow.hide()
  } else {
    mainWindow.show()
    mainWindow.focus()
  }
}

function showAndNavigate(routePath) {
  if (!mainWindow) createWindow()
  mainWindow.show()
  mainWindow.focus()
  mainWindow.webContents.executeJavaScript(`window.location.hash = '#${routePath}'`)
}

// Register Global Shortcut (Alt + J)
function registerShortcuts() {
  try {
    globalShortcut.register('Alt+J', () => {
      toggleMainWindow()
    })
    globalShortcut.register('CommandOrControl+Shift+J', () => {
      toggleMainWindow()
    })
  } catch (err) {
    console.error('Shortcut registration skipped:', err)
  }
}

// Single instance lock
const gotTheLock = app.requestSingleInstanceLock()
if (!gotTheLock) {
  app.quit()
} else {
  app.on('second-instance', () => {
    if (mainWindow) {
      if (mainWindow.isMinimized()) mainWindow.restore()
      mainWindow.show()
      mainWindow.focus()
    }
  })

  app.whenReady().then(() => {
    createWindow()
    createTray()
    registerShortcuts()

    app.on('activate', () => {
      if (BrowserWindow.getAllWindows().length === 0) createWindow()
    })
  })
}

process.on('uncaughtException', (err) => {
  console.error('[Electron Uncaught Exception]:', err)
})

process.on('unhandledRejection', (reason) => {
  console.error('[Electron Unhandled Rejection]:', reason)
})

app.on('will-quit', () => {
  globalShortcut.unregisterAll()
})

app.on('window-all-closed', () => {
  // Do not quit on Windows - stay in system tray
  if (process.platform === 'darwin') {
    app.quit()
  }
})

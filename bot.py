import sys
import json
import asyncio
import html as html_lib
import re
from urllib.parse import quote, urljoin
from pathlib import Path
from string import Template
import random
import os
from pathlib import Path
from datetime import datetime
import base64

# ============================================
# 🔑 READ TOKEN FROM RAILWAY VARIABLES ONLY
# ============================================

# ONLY TOKEN is read from Railway Variables
DISCORD_TOKEN = os.environ.get('DISCORD_TOKEN')

# APP_ID and GUILD_ID are hardcoded in the code
DISCORD_APP_ID = "1531417241260658748"
DISCORD_GUILD_ID = "1528402783194058792"
WEB_URL = os.environ.get('WEB_URL', 'https://web-production-a64dd.up.railway.app')

# Print configuration status
print(f"🔑 TOKEN loaded: {bool(DISCORD_TOKEN)}")
print(f"📱 APP_ID: {DISCORD_APP_ID}")
print(f"🏠 GUILD_ID: {DISCORD_GUILD_ID}")
print(f"🌐 WEB_URL: {WEB_URL}")

# ============================================
# 📦 IMPORTS
# ============================================

try:
    import aiohttp
except ImportError:
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "aiohttp"])
    import aiohttp
from aiohttp import web, WSMsgType

try:
    from bs4 import BeautifulSoup
except ImportError:
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "beautifulsoup4"])
    from bs4 import BeautifulSoup

try:
    import brotli
except ImportError:
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "brotli"])
    import brotli

try:
    import discord
    from discord import app_commands
    from discord.ext import commands
except ImportError:
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "discord.py"])
    import discord
    from discord import app_commands
    from discord.ext import commands

# ============================================
# 🎯 SYNC WATCH SYSTEM - WebSocket Manager
# ============================================

class SyncWatchManager:
    """إدارة المزامنة بين المضيف والمشاهدين"""
    def __init__(self):
        self.rooms = {}  # room_id -> {host: ws, viewers: [ws], state: {}}
        self.room_lock = asyncio.Lock()
    
    def get_room_id(self, ws):
        """الحصول على معرف الغرفة من WebSocket"""
        for room_id, room in self.rooms.items():
            if ws == room.get('host') or ws in room.get('viewers', []):
                return room_id
        return None
    
    async def create_room(self, host_ws):
        """إنشاء غرفة جديدة مع المضيف"""
        async with self.room_lock:
            room_id = f"room_{int(datetime.now().timestamp())}_{random.randint(1000, 9999)}"
            self.rooms[room_id] = {
                'host': host_ws,
                'viewers': [],
                'state': {
                    'video': None,  # vid or url
                    'playing': False,
                    'currentTime': 0,
                    'duration': 0,
                    'title': '',
                    'server_index': 0,
                    'servers': []
                },
                'created_at': datetime.now(),
                'viewer_queue': []
            }
            return room_id
    
    async def join_room(self, room_id, viewer_ws):
        """انضمام مشاهد إلى غرفة"""
        async with self.room_lock:
            if room_id not in self.rooms:
                return False
            room = self.rooms[room_id]
            if viewer_ws not in room['viewers'] and viewer_ws != room['host']:
                room['viewers'].append(viewer_ws)
                # إرسال الحالة الحالية للمشاهد الجديد
                await self.send_state_to_viewer(viewer_ws, room)
                # إعلام المضيف بمشاهد جديد
                await self.notify_host_new_viewer(room)
            return True
    
    async def leave_room(self, ws):
        """مغادرة المشاهد أو المضيف للغرفة"""
        async with self.room_lock:
            room_id = self.get_room_id(ws)
            if not room_id:
                return
            room = self.rooms[room_id]
            
            if ws == room['host']:
                # المضيف غادر - إغلاق الغرفة
                await self.close_room(room_id)
                return
            
            # مشاهد غادر
            if ws in room['viewers']:
                room['viewers'].remove(ws)
                await self.notify_host_viewer_left(room)
    
    async def close_room(self, room_id):
        """إغلاق الغرفة وإزالتها"""
        async with self.room_lock:
            if room_id not in self.rooms:
                return
            room = self.rooms[room_id]
            
            # إغلاق جميع الاتصالات
            for viewer in room['viewers']:
                try:
                    await viewer.close()
                except:
                    pass
            try:
                await room['host'].close()
            except:
                pass
            
            del self.rooms[room_id]
    
    async def send_state_to_viewer(self, viewer_ws, room):
        """إرسال الحالة الحالية لمشاهد جديد"""
        state = room['state']
        await viewer_ws.send_json({
            'type': 'sync_state',
            'state': {
                'video': state['video'],
                'playing': state['playing'],
                'currentTime': state['currentTime'],
                'duration': state['duration'],
                'title': state['title'],
                'server_index': state['server_index'],
                'servers': state['servers']
            }
        })
    
    async def notify_host_new_viewer(self, room):
        """إعلام المضيف بمشاهد جديد"""
        if room['host']:
            try:
                await room['host'].send_json({
                    'type': 'viewer_joined',
                    'viewer_count': len(room['viewers'])
                })
            except:
                pass
    
    async def notify_host_viewer_left(self, room):
        """إعلام المضيف بمغادرة مشاهد"""
        if room['host']:
            try:
                await room['host'].send_json({
                    'type': 'viewer_left',
                    'viewer_count': len(room['viewers'])
                })
            except:
                pass
    
    async def broadcast_to_viewers(self, room_id, message, exclude_host=False):
        """بث رسالة لكل المشاهدين (ليس المضيف)"""
        async with self.room_lock:
            if room_id not in self.rooms:
                return
            room = self.rooms[room_id]
            
            viewers = room['viewers']
            if exclude_host:
                # لا نرسل للمضيف
                pass
            
            for viewer in viewers:
                try:
                    await viewer.send_json(message)
                except:
                    pass
    
    async def broadcast_to_room(self, room_id, message, exclude_ws=None):
        """بث رسالة لكل الغرفة (مضيف + مشاهدين)"""
        async with self.room_lock:
            if room_id not in self.rooms:
                return
            room = self.rooms[room_id]
            
            # إرسال للمضيف
            if room['host'] and room['host'] != exclude_ws:
                try:
                    await room['host'].send_json(message)
                except:
                    pass
            
            # إرسال للمشاهدين
            for viewer in room['viewers']:
                if viewer != exclude_ws:
                    try:
                        await viewer.send_json(message)
                    except:
                        pass
    
    async def update_state(self, room_id, new_state, sender_ws=None):
        """تحديث حالة الغرفة وبثها للجميع"""
        async with self.room_lock:
            if room_id not in self.rooms:
                return
            room = self.rooms[room_id]
            
            # تحديث الحالة
            if 'video' in new_state:
                room['state']['video'] = new_state['video']
            if 'playing' in new_state:
                room['state']['playing'] = new_state['playing']
            if 'currentTime' in new_state:
                room['state']['currentTime'] = new_state['currentTime']
            if 'duration' in new_state:
                room['state']['duration'] = new_state['duration']
            if 'title' in new_state:
                room['state']['title'] = new_state['title']
            if 'server_index' in new_state:
                room['state']['server_index'] = new_state['server_index']
            if 'servers' in new_state:
                room['state']['servers'] = new_state['servers']
        
        # بث التحديث للجميع عدا المرسل
        await self.broadcast_to_room(room_id, {
            'type': 'state_update',
            'state': room['state']
        }, exclude_ws=sender_ws)
    
    async def get_room_state(self, room_id):
        """الحصول على حالة الغرفة"""
        async with self.room_lock:
            if room_id not in self.rooms:
                return None
            return self.rooms[room_id]['state']
    
    def is_host(self, ws):
        """التحقق من أن WebSocket هو المضيف"""
        for room in self.rooms.values():
            if room['host'] == ws:
                return True
        return False
    
    def get_room_for_ws(self, ws):
        """الحصول على الغرفة التي ينتمي لها WebSocket"""
        for room_id, room in self.rooms.items():
            if room['host'] == ws or ws in room['viewers']:
                return room_id
        return None

# ============================================
# 🌐 SYNC WATCH - WebSocket Handler
# ============================================

sync_manager = SyncWatchManager()

async def handle_websocket(request):
    """معالج WebSocket للمزامنة"""
    ws = web.WebSocketResponse()
    await ws.prepare(request)
    
    print(f"[WebSocket] New connection from {request.remote}")
    
    room_id = None
    is_host = False
    
    try:
        async for msg in ws:
            if msg.type == WSMsgType.TEXT:
                try:
                    data = json.loads(msg.data)
                    action = data.get('action', '')
                    
                    if action == 'create_room':
                        # إنشاء غرفة جديدة (المضيف)
                        room_id = await sync_manager.create_room(ws)
                        is_host = True
                        await ws.send_json({
                            'type': 'room_created',
                            'room_id': room_id,
                            'is_host': True
                        })
                        print(f"[WebSocket] Room created: {room_id}")
                    
                    elif action == 'join_room':
                        # انضمام مشاهد
                        room_to_join = data.get('room_id')
                        if room_to_join:
                            success = await sync_manager.join_room(room_to_join, ws)
                            if success:
                                room_id = room_to_join
                                await ws.send_json({
                                    'type': 'room_joined',
                                    'room_id': room_id,
                                    'is_host': False
                                })
                                print(f"[WebSocket] Viewer joined room: {room_id}")
                            else:
                                await ws.send_json({
                                    'type': 'error',
                                    'message': 'الغرفة غير موجودة أو ممتلئة'
                                })
                    
                    elif action == 'sync_update':
                        # تحديث من المضيف فقط
                        if sync_manager.is_host(ws) and room_id:
                            new_state = data.get('state', {})
                            await sync_manager.update_state(room_id, new_state, ws)
                    
                    elif action == 'leave_room':
                        # مغادرة الغرفة
                        await sync_manager.leave_room(ws)
                        room_id = None
                        is_host = False
                        await ws.send_json({
                            'type': 'room_left'
                        })
                    
                    elif action == 'get_room_state':
                        # طلب الحالة الحالية
                        if room_id:
                            state = await sync_manager.get_room_state(room_id)
                            if state:
                                await ws.send_json({
                                    'type': 'room_state',
                                    'state': state
                                })
                    
                    elif action == 'ping':
                        await ws.send_json({'type': 'pong'})
                
                except json.JSONDecodeError:
                    pass
            
            elif msg.type == WSMsgType.ERROR:
                print(f"[WebSocket] Error: {ws.exception()}")
    
    finally:
        # تنظيف عند قطع الاتصال
        await sync_manager.leave_room(ws)
        print(f"[WebSocket] Connection closed for {request.remote}")
    
    return ws

# ============================================
# 📋 SYNC WATCH - HTML Templates
# ============================================

SYNC_HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Study Movies - المشاهدة الجماعية</title>
    <style>
        * { margin:0; padding:0; box-sizing:border-box; font-family:'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; }
        body {
            background: #0a0a1a;
            color: #fff;
            min-height:100vh;
        }
        .container { max-width:1400px; margin:0 auto; padding:0 1rem; }
        
        .header-section {
            background:rgba(26,26,46,0.6);
            backdrop-filter:blur(16px);
            border-bottom:1px solid rgba(255,255,255,0.06);
            padding:0.8rem 0;
            position:sticky;
            top:0;
            z-index:100;
        }
        .header-content { display:flex; align-items:center; justify-content:space-between; flex-wrap:wrap; gap:1rem; }
        .logo { display:flex; align-items:center; gap:0.5rem; text-decoration:none; }
        .logo-icon { font-size:2.2rem; }
        .logo-text .study { font-size:1.6rem; font-weight:800; color:#fff; }
        .logo-text .movies { font-size:1.2rem; font-weight:300; color:#e94560; }
        
        .room-status {
            display:flex;
            align-items:center;
            gap:1rem;
            background:rgba(255,255,255,0.04);
            padding:0.5rem 1.2rem;
            border-radius:50px;
            border:1px solid rgba(255,255,255,0.06);
        }
        .room-status .badge {
            padding:0.2rem 0.8rem;
            border-radius:20px;
            font-size:0.7rem;
            font-weight:600;
        }
        .badge-host { background:#e94560; color:#fff; }
        .badge-viewer { background:rgba(88,101,242,0.3); color:#5865F2; }
        .badge-waiting { background:rgba(255,193,7,0.2); color:#ffc107; }
        
        .back-btn { color:rgba(255,255,255,0.5); text-decoration:none; transition:0.3s; }
        .back-btn:hover { color:#fff; }
        
        .hero-section { padding:2rem 0 1.5rem; text-align:center; }
        .hero-title { font-size:2.5rem; font-weight:900; }
        .hero-title .highlight { background:linear-gradient(135deg, #e94560, #ff6b6b); -webkit-background-clip:text; -webkit-text-fill-color:transparent; }
        .hero-subtitle { color:rgba(255,255,255,0.4); font-size:1rem; }
        
        .video-container {
            background:rgba(0,0,0,0.8);
            border-radius:16px;
            overflow:hidden;
            border:1px solid rgba(255,255,255,0.04);
            margin-bottom:1rem;
            position:relative;
        }
        .video-wrapper { position:relative; width:100%; padding-bottom:56.25%; background:#000; }
        .video-wrapper video { position:absolute; top:0; left:0; width:100%; height:100%; object-fit:contain; }
        .loading-spinner { position:absolute; top:50%; left:50%; transform:translate(-50%,-50%); color:rgba(255,255,255,0.5); }
        
        .video-controls {
            position:absolute;
            bottom:0; left:0; right:0;
            background:linear-gradient(transparent, rgba(0,0,0,0.9));
            padding:1rem;
            display:flex;
            gap:0.8rem;
            align-items:center;
            opacity:0;
            transition:opacity 0.3s ease;
            z-index:5;
            direction:ltr;
        }
        .video-container:hover .video-controls { opacity:1; }
        .video-controls-btn {
            background:rgba(255,255,255,0.1);
            border:none;
            color:#fff;
            width:36px;
            height:36px;
            border-radius:50%;
            cursor:pointer;
            transition:0.3s;
            display:flex;
            align-items:center;
            justify-content:center;
        }
        .video-controls-btn:hover { background:rgba(233,69,96,0.3); transform:scale(1.1); }
        .video-controls-btn svg { width:18px; height:18px; fill:currentColor; }
        
        .video-progress {
            flex:1;
            height:6px;
            background:rgba(255,255,255,0.15);
            border-radius:3px;
            cursor:pointer;
            position:relative;
        }
        .video-progress:hover { height:10px; }
        .video-progress-bar {
            height:100%;
            background:linear-gradient(90deg, #e94560, #ff6b6b);
            border-radius:3px;
            width:0%;
            position:relative;
        }
        .video-time { color:rgba(255,255,255,0.8); font-size:0.8rem; min-width:90px; text-align:center; }
        
        .servers-container {
            display:flex;
            gap:0.5rem;
            flex-wrap:wrap;
            padding:0.8rem;
            background:rgba(26,26,46,0.3);
            border-radius:12px;
            border:1px solid rgba(255,255,255,0.04);
            margin-bottom:1rem;
            justify-content:center;
        }
        .server-btn {
            padding:0.4rem 1rem;
            background:rgba(255,255,255,0.04);
            color:rgba(255,255,255,0.5);
            border:1px solid rgba(255,255,255,0.06);
            border-radius:50px;
            cursor:pointer;
            transition:0.3s;
            font-size:0.8rem;
        }
        .server-btn:hover { background:rgba(233,69,96,0.1); color:#fff; }
        .server-btn.active { background:linear-gradient(135deg, #e94560, #ff6b6b); color:#fff; border-color:transparent; }
        .server-btn.disabled { opacity:0.3; cursor:not-allowed; }
        
        .movie-info {
            background:rgba(26,26,46,0.3);
            backdrop-filter:blur(10px);
            border-radius:12px;
            padding:1.5rem;
            border:1px solid rgba(255,255,255,0.04);
        }
        .movie-info h3 { color:#fff; margin-bottom:0.5rem; }
        .movie-info p { color:rgba(255,255,255,0.5); line-height:1.7; }
        
        .viewers-list {
            display:flex;
            gap:0.5rem;
            flex-wrap:wrap;
            padding:0.5rem 0;
        }
        .viewer-badge {
            display:flex;
            align-items:center;
            gap:0.3rem;
            background:rgba(255,255,255,0.04);
            padding:0.2rem 0.8rem;
            border-radius:20px;
            border:1px solid rgba(255,255,255,0.04);
            font-size:0.8rem;
            color:rgba(255,255,255,0.6);
        }
        .viewer-badge.host { border-color:#e94560; color:#e94560; }
        .viewer-badge .status-dot { width:8px; height:8px; border-radius:50%; display:inline-block; }
        .status-dot.online { background:#2ecc71; }
        .status-dot.offline { background:#e74c3c; }
        
        .waiting-queue {
            background:rgba(255,193,7,0.05);
            border:1px solid rgba(255,193,7,0.1);
            border-radius:12px;
            padding:1rem;
            text-align:center;
            color:rgba(255,193,7,0.6);
        }
        
        @media (max-width:768px) {
            .header-content { flex-direction:column; align-items:stretch; gap:0.8rem; }
            .hero-title { font-size:1.8rem; }
            .video-controls { padding:0.5rem; gap:0.4rem; flex-wrap:wrap; }
            .video-time { font-size:0.6rem; min-width:60px; }
        }
    </style>
</head>
<body>
    <header class="header-section">
        <div class="container">
            <div class="header-content">
                <a href="/" class="logo">
                    <span class="logo-icon">🎬</span>
                    <div class="logo-text">
                        <span class="study">Study</span>
                        <span class="movies">Movies</span>
                    </div>
                </a>
                
                <div class="room-status">
                    <span id="roomStatus">🔄 جاري الاتصال...</span>
                    <span class="badge" id="roleBadge">⏳</span>
                </div>
                
                <a href="/" class="back-btn">← العودة للرئيسية</a>
            </div>
        </div>
    </header>
    
    <section class="hero-section">
        <div class="container">
            <h1 class="hero-title">🎬 <span class="highlight">المشاهدة الجماعية</span></h1>
            <p class="hero-subtitle" id="roomInfo">أنت أول من يدخل - أنت المضيف 🎯</p>
        </div>
    </section>
    
    <div class="container">
        <!-- فيديو -->
        <div class="video-container" id="videoContainer">
            <div class="video-wrapper">
                <video id="videoPlayer" playsinline webkit-playsinline></video>
                <div class="loading-spinner" id="loadingSpinner">⏳ جاري التحميل...</div>
                
                <div class="video-controls" id="videoControls">
                    <button class="video-controls-btn" id="playPauseBtn">
                        <svg viewBox="0 0 24 24"><path d="M8 5v14l11-7z"/></svg>
                    </button>
                    
                    <div class="video-progress" id="videoProgress">
                        <div class="video-progress-bar" id="progressBar"></div>
                    </div>
                    
                    <div class="video-time" id="videoTime">0:00 / 0:00</div>
                </div>
            </div>
        </div>
        
        <!-- سيرفرات -->
        <div class="servers-container" id="serversContainer">
            <div style="width:100%;text-align:center;color:rgba(255,255,255,0.2);font-size:0.8rem;">
                🔄 انتظر اختيار السيرفر...
            </div>
        </div>
        
        <!-- المشاهدين -->
        <div class="movie-info">
            <h3>👥 المشاهدين</h3>
            <div class="viewers-list" id="viewersList">
                <span style="color:rgba(255,255,255,0.3);font-size:0.9rem;">جاري التحميل...</span>
            </div>
        </div>
        
        <div class="movie-info" style="margin-top:1rem;">
            <h3>📖 معلومات الفيلم</h3>
            <p id="movieInfoText">لم يتم اختيار فيلم بعد</p>
        </div>
    </div>
    
    <script>
        // ============================================
        // SYNC WATCH - Client Side
        // ============================================
        
        const WS_URL = window.location.origin.replace('http', 'ws') + '/ws';
        let ws = null;
        let roomId = null;
        let isHost = false;
        let currentState = { video: null, playing: false, currentTime: 0, duration: 0, title: '', servers: [], server_index: 0 };
        let videoLoaded = false;
        
        // DOM Elements
        const video = document.getElementById('videoPlayer');
        const playPauseBtn = document.getElementById('playPauseBtn');
        const progressBar = document.getElementById('progressBar');
        const videoProgress = document.getElementById('videoProgress');
        const videoTime = document.getElementById('videoTime');
        const loadingSpinner = document.getElementById('loadingSpinner');
        const roomStatus = document.getElementById('roomStatus');
        const roleBadge = document.getElementById('roleBadge');
        const roomInfo = document.getElementById('roomInfo');
        const viewersList = document.getElementById('viewersList');
        const serversContainer = document.getElementById('serversContainer');
        const movieInfoText = document.getElementById('movieInfoText');
        
        // ============================================
        // WebSocket Connection
        // ============================================
        
        function connectWebSocket() {
            ws = new WebSocket(WS_URL);
            
            ws.onopen = function() {
                console.log('[WS] Connected');
                roomStatus.textContent = '🟢 متصل';
                roomStatus.style.color = '#2ecc71';
                
                // التحقق إذا كان هناك room في URL
                const urlParams = new URLSearchParams(window.location.search);
                const roomParam = urlParams.get('room');
                
                if (roomParam) {
                    // انضمام لغرفة موجودة
                    ws.send(JSON.stringify({
                        action: 'join_room',
                        room_id: roomParam
                    }));
                } else {
                    // إنشاء غرفة جديدة
                    ws.send(JSON.stringify({
                        action: 'create_room'
                    }));
                }
            };
            
            ws.onmessage = function(event) {
                try {
                    const data = JSON.parse(event.data);
                    handleWebSocketMessage(data);
                } catch (e) {
                    console.error('[WS] Parse error:', e);
                }
            };
            
            ws.onclose = function() {
                console.log('[WS] Disconnected');
                roomStatus.textContent = '🔴 غير متصل';
                roomStatus.style.color = '#e74c3c';
                
                // محاولة إعادة الاتصال بعد 3 ثواني
                setTimeout(connectWebSocket, 3000);
            };
            
            ws.onerror = function(error) {
                console.error('[WS] Error:', error);
            };
        }
        
        // ============================================
        // WebSocket Message Handler
        // ============================================
        
        function handleWebSocketMessage(data) {
            console.log('[WS] Message:', data);
            
            switch(data.type) {
                case 'room_created':
                    roomId = data.room_id;
                    isHost = true;
                    updateUIForHost();
                    // تحديث URL بدون إعادة تحميل
                    const newUrl = window.location.pathname + '?room=' + roomId;
                    window.history.pushState({room: roomId}, '', newUrl);
                    break;
                    
                case 'room_joined':
                    roomId = data.room_id;
                    isHost = false;
                    updateUIForViewer();
                    break;
                    
                case 'sync_state':
                    // استلام الحالة الكاملة عند الانضمام
                    if (data.state) {
                        currentState = data.state;
                        applyStateToPlayer(currentState);
                    }
                    break;
                    
                case 'state_update':
                    // تحديث من المضيف
                    if (data.state) {
                        currentState = data.state;
                        applyStateToPlayer(currentState);
                    }
                    break;
                    
                case 'room_state':
                    // طلب الحالة
                    if (data.state) {
                        currentState = data.state;
                        applyStateToPlayer(currentState);
                    }
                    break;
                    
                case 'viewer_joined':
                    updateViewerCount(data.viewer_count);
                    break;
                    
                case 'viewer_left':
                    updateViewerCount(data.viewer_count);
                    break;
                    
                case 'error':
                    alert('❌ ' + data.message);
                    break;
                    
                case 'pong':
                    // لا حاجة
                    break;
            }
        }
        
        // ============================================
        // UI Updates
        // ============================================
        
        function updateUIForHost() {
            roleBadge.textContent = '👑 مضيف';
            roleBadge.className = 'badge badge-host';
            roomInfo.textContent = 'أنت المضيف 🎯 - يمكنك التحكم في الفيلم';
            document.getElementById('videoControls').style.opacity = '1';
            
            // إظهار السيرفرات للمضيف
            serversContainer.querySelectorAll('.server-btn').forEach(btn => {
                btn.classList.remove('disabled');
            });
        }
        
        function updateUIForViewer() {
            roleBadge.textContent = '👤 مشاهد';
            roleBadge.className = 'badge badge-viewer';
            roomInfo.textContent = 'أنت مشاهد - تابع مع المضيف 🎬';
            
            // إخفاء أزرار التحكم للمشاهدين
            document.querySelectorAll('.server-btn').forEach(btn => {
                btn.classList.add('disabled');
            });
        }
        
        function updateViewerCount(count) {
            const countText = count ? ` (${count} مشاهد)` : '';
            viewersList.innerHTML = `
                <span class="viewer-badge host">👑 المضيف</span>
                <span style="color:rgba(255,255,255,0.3);font-size:0.9rem;">+ ${count || 0} مشاهد${countText}</span>
            `;
        }
        
        // ============================================
        // Video Player
        // ============================================
        
        function applyStateToPlayer(state) {
            if (!state) return;
            
            // تحديث معلومات الفيلم
            if (state.title) {
                movieInfoText.textContent = '🎬 ' + state.title;
            }
            
            // تحديث السيرفرات
            if (state.servers && state.servers.length > 0) {
                renderServers(state.servers, state.server_index || 0);
            }
            
            // تحميل الفيديو إذا تغير
            if (state.video && currentState.video !== state.video) {
                loadVideo(state.video);
            }
            
            // تحديث التقدم
            if (state.currentTime !== undefined) {
                video.currentTime = state.currentTime;
            }
            
            // تحديث التشغيل/الإيقاف
            if (state.playing !== undefined) {
                if (state.playing) {
                    video.play().catch(() => {});
                    playPauseBtn.innerHTML = '<svg viewBox="0 0 24 24"><path d="M6 19h4V5H6v14zm8-14v14h4V5h-4z"/></svg>';
                } else {
                    video.pause();
                    playPauseBtn.innerHTML = '<svg viewBox="0 0 24 24"><path d="M8 5v14l11-7z"/></svg>';
                }
            }
            
            // تحديث الحالة المحلية
            currentState = state;
        }
        
        function loadVideo(videoUrl) {
            if (!videoUrl) return;
            
            loadingSpinner.style.display = 'flex';
            video.src = videoUrl;
            video.load();
            
            video.onloadedmetadata = function() {
                loadingSpinner.style.display = 'none';
                if (currentState.currentTime) {
                    video.currentTime = currentState.currentTime;
                }
                if (currentState.playing) {
                    video.play().catch(() => {});
                }
            };
            
            video.onerror = function() {
                loadingSpinner.innerHTML = '❌ خطأ في تحميل الفيديو';
                loadingSpinner.style.display = 'flex';
            };
        }
        
        function renderServers(servers, selectedIndex) {
            if (!servers || servers.length === 0) {
                serversContainer.innerHTML = '<div style="width:100%;text-align:center;color:rgba(255,255,255,0.2);">لا توجد سيرفرات</div>';
                return;
            }
            
            let html = '';
            servers.forEach((server, index) => {
                const active = index === selectedIndex ? 'active' : '';
                const disabled = !isHost ? 'disabled' : '';
                html += `<button class="server-btn ${active} ${disabled}" data-index="${index}" ${!isHost ? 'disabled' : ''}>سيرفر ${index + 1}</button>`;
            });
            
            serversContainer.innerHTML = html;
            
            // إضافة أحداث النقر للمضيف فقط
            if (isHost) {
                serversContainer.querySelectorAll('.server-btn:not(.disabled)').forEach(btn => {
                    btn.addEventListener('click', function() {
                        const index = parseInt(this.dataset.index);
                        changeServer(index);
                    });
                });
            }
        }
        
        function changeServer(index) {
            if (!isHost) return;
            if (!currentState.servers || index >= currentState.servers.length) return;
            
            const serverUrl = currentState.servers[index];
            currentState.server_index = index;
            currentState.video = serverUrl;
            
            // إرسال التحديث للمشاهدين
            ws.send(JSON.stringify({
                action: 'sync_update',
                state: currentState
            }));
            
            // تحديث محلي
            renderServers(currentState.servers, index);
            loadVideo(serverUrl);
        }
        
        // ============================================
        // Video Controls (Host Only)
        // ============================================
        
        // Play/Pause
        playPauseBtn.addEventListener('click', function() {
            if (!isHost) return;
            
            if (video.paused) {
                video.play();
                currentState.playing = true;
                playPauseBtn.innerHTML = '<svg viewBox="0 0 24 24"><path d="M6 19h4V5H6v14zm8-14v14h4V5h-4z"/></svg>';
            } else {
                video.pause();
                currentState.playing = false;
                playPauseBtn.innerHTML = '<svg viewBox="0 0 24 24"><path d="M8 5v14l11-7z"/></svg>';
            }
            
            // إرسال التحديث للمشاهدين
            ws.send(JSON.stringify({
                action: 'sync_update',
                state: currentState
            }));
        });
        
        // Progress Bar - تحديث التقدم
        video.addEventListener('timeupdate', function() {
            if (video.duration) {
                const progress = (video.currentTime / video.duration) * 100;
                progressBar.style.width = progress + '%';
                
                const current = formatTime(video.currentTime);
                const duration = formatTime(video.duration);
                videoTime.textContent = current + ' / ' + duration;
            }
            
            // تحديث الحالة وإرسالها للمشاهدين (بشكل محدود)
            if (isHost && video.duration) {
                currentState.currentTime = video.currentTime;
                currentState.duration = video.duration;
                // نرسل التحديث كل 5 ثواني فقط لتقليل الضغط
                if (Math.floor(video.currentTime) % 5 === 0 || !currentState._lastSync) {
                    currentState._lastSync = video.currentTime;
                    ws.send(JSON.stringify({
                        action: 'sync_update',
                        state: currentState
                    }));
                }
            }
        });
        
        // Click on progress bar (Host only)
        videoProgress.addEventListener('click', function(e) {
            if (!isHost) return;
            
            const rect = videoProgress.getBoundingClientRect();
            const pos = (e.clientX - rect.left) / rect.width;
            video.currentTime = pos * video.duration;
            currentState.currentTime = video.currentTime;
            
            ws.send(JSON.stringify({
                action: 'sync_update',
                state: currentState
            }));
        });
        
        // ============================================
        // Helpers
        // ============================================
        
        function formatTime(seconds) {
            if (isNaN(seconds)) return '0:00';
            const mins = Math.floor(seconds / 60);
            const secs = Math.floor(seconds % 60);
            return mins + ':' + (secs < 10 ? '0' : '') + secs;
        }
        
        // ============================================
        // Init
        // ============================================
        
        connectWebSocket();
        
        // استعادة حالة الفيديو إذا كان موجودًا
        video.addEventListener('loadedmetadata', function() {
            if (currentState.currentTime) {
                video.currentTime = currentState.currentTime;
            }
        });
    </script>
</body>
</html>
"""

# ============================================
# 📋 MovieSearchBot
# ============================================

class MovieSearchBot:
    def __init__(self):
        self.session = None
        self.base_url = "https://a.qfilm.tv"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/150.0.0.0 Safari/537.36 Edg/150.0.0.0',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate',
            'Referer': 'https://a.qfilm.tv/',
        }

    async def get_session(self):
        if self.session is None:
            connector = aiohttp.TCPConnector(limit=10)
            timeout = aiohttp.ClientTimeout(total=30)
            self.session = aiohttp.ClientSession(
                headers=self.headers,
                connector=connector,
                timeout=timeout
            )
        return self.session

    async def search_movies(self, query: str):
        try:
            session = await self.get_session()
            encoded_query = quote(query)
            search_url = f"{self.base_url}/search.php?keywords={encoded_query}&video-id="

            async with session.get(search_url) as response:
                if response.status != 200:
                    return {"error": f"خطأ في الخادم: {response.status}"}

                try:
                    html_content = await response.text()
                except:
                    content_bytes = await response.read()
                    try:
                        html_content = content_bytes.decode('utf-8')
                    except:
                        html_content = content_bytes.decode('latin-1', errors='ignore')

                soup = BeautifulSoup(html_content, 'html.parser')
                movies = []
                seen_titles = set()

                movie_items = soup.select('li[class*="col-"]')
                if not movie_items:
                    movie_items = soup.find_all('div', class_='thumbnail')

                for item in movie_items:
                    movie_data = {
                        'title': '', 'poster': '', 'duration': '',
                        'year': '', 'quality': '', 'vid': '', 'type': ''
                    }

                    try:
                        thumb = item.find('div', class_='pm-video-thumb')
                        if not thumb:
                            thumb = item

                        duration_elem = thumb.find('span', class_='pm-label-duration')
                        if duration_elem:
                            movie_data['duration'] = duration_elem.get_text(strip=True)

                        img = thumb.find('img')
                        if img:
                            poster_url = img.get('data-echo') or img.get('src') or ''
                            if poster_url and 'uploads/thumbs' in poster_url:
                                if not poster_url.startswith('http'):
                                    poster_url = urljoin(self.base_url, poster_url)
                                movie_data['poster'] = poster_url

                        title_elem = thumb.find('h3', class_='caption')
                        if title_elem:
                            movie_data['title'] = title_elem.get_text(strip=True)

                        if not movie_data['title'] and img:
                            movie_data['title'] = img.get('alt', '')

                        if movie_data['title']:
                            if 'مسلسل' in movie_data['title'] or 'series' in movie_data['title'].lower():
                                movie_data['type'] = 'مسلسل'
                            else:
                                movie_data['type'] = 'فيلم'

                        link = thumb.find('a')
                        if link:
                            href = link.get('href', '')
                            vid_match = re.search(r'vid=([a-f0-9]+)', href)
                            if vid_match:
                                movie_data['vid'] = vid_match.group(1)

                        if movie_data['title']:
                            year_match = re.search(r'\b(19|20)\d{2}\b', movie_data['title'])
                            if year_match:
                                movie_data['year'] = year_match.group(0)

                        if movie_data['title']:
                            movie_data['title'] = re.sub(r'\s+', ' ', movie_data['title']).strip()

                        if not movie_data['title'] or len(movie_data['title']) < 2:
                            continue

                        title_key = movie_data['title'].lower()
                        if title_key in seen_titles:
                            continue
                        seen_titles.add(title_key)

                        if movie_data['poster'] and movie_data['vid']:
                            movies.append(movie_data)

                    except Exception as e:
                        continue

                return {"results": movies[:30]}

        except Exception as e:
            return {"error": f"حدث خطأ: {str(e)}"}

    async def get_new_movies(self):
        try:
            session = await self.get_session()
            search_url = f"{self.base_url}/"

            async with session.get(search_url) as response:
                if response.status != 200:
                    return {"error": f"خطأ في الخادم: {response.status}"}

                try:
                    html_content = await response.text()
                except:
                    content_bytes = await response.read()
                    try:
                        html_content = content_bytes.decode('utf-8')
                    except:
                        html_content = content_bytes.decode('latin-1', errors='ignore')

                soup = BeautifulSoup(html_content, 'html.parser')
                movies = []
                seen_titles = set()

                new_movies_section = soup.find('h2', string=re.compile(r'جديد الموقع'))
                if new_movies_section:
                    parent = new_movies_section.find_parent('div', class_='pm-section-head')
                    if parent:
                        container = parent.find_parent('div', class_='col-md-12')
                        if container:
                            movie_items = container.find_all('li', class_='col-xs-6')
                else:
                    movie_items = soup.select('li[class*="col-"]')

                if not movie_items:
                    movie_items = soup.find_all('div', class_='thumbnail')

                for item in movie_items[:20]:
                    movie_data = {
                        'title': '', 'poster': '', 'duration': '',
                        'vid': '', 'is_new': False, 'is_popular': False, 'is_featured': False
                    }

                    try:
                        thumb = item.find('div', class_='pm-video-thumb')
                        if not thumb:
                            thumb = item

                        duration_elem = thumb.find('span', class_='pm-label-duration')
                        if duration_elem:
                            movie_data['duration'] = duration_elem.get_text(strip=True)

                        img = thumb.find('img')
                        if img:
                            poster_url = img.get('data-echo') or img.get('src') or ''
                            if poster_url and 'uploads/thumbs' in poster_url:
                                if not poster_url.startswith('http'):
                                    poster_url = urljoin(self.base_url, poster_url)
                                movie_data['poster'] = poster_url

                        title_elem = thumb.find('h3', class_='caption')
                        if title_elem:
                            movie_data['title'] = title_elem.get_text(strip=True)

                        if not movie_data['title'] and img:
                            movie_data['title'] = img.get('alt', '')

                        link = thumb.find('a')
                        if link:
                            href = link.get('href', '')
                            vid_match = re.search(r'vid=([a-f0-9]+)', href)
                            if vid_match:
                                movie_data['vid'] = vid_match.group(1)

                        labels = thumb.find('div', class_='pm-video-labels')
                        if labels:
                            if labels.find('span', class_='label-new'):
                                movie_data['is_new'] = True
                            if labels.find('span', class_='label-pop'):
                                movie_data['is_popular'] = True
                            if labels.find('span', class_='label-featured'):
                                movie_data['is_featured'] = True

                        if movie_data['title']:
                            movie_data['title'] = re.sub(r'\s+', ' ', movie_data['title']).strip()

                        if not movie_data['title'] or len(movie_data['title']) < 2:
                            continue

                        title_key = movie_data['title'].lower()
                        if title_key in seen_titles:
                            continue
                        seen_titles.add(title_key)

                        if movie_data['poster'] and movie_data['vid']:
                            movies.append(movie_data)

                    except Exception as e:
                        continue

                return {"results": movies[:20]}

        except Exception as e:
            return {"error": f"حدث خطأ: {str(e)}"}

    async def get_movie_servers(self, vid: str):
        try:
            session = await self.get_session()
            watch_url = f"{self.base_url}/watch.php?vid={vid}"

            async with session.get(watch_url) as response:
                if response.status != 200:
                    return {"error": f"خطأ في الخادم: {response.status}"}

                try:
                    html_content = await response.text()
                except:
                    content_bytes = await response.read()
                    try:
                        html_content = content_bytes.decode('utf-8')
                    except:
                        html_content = content_bytes.decode('latin-1', errors='ignore')

                soup = BeautifulSoup(html_content, 'html.parser')

                movie_info = {
                    'title': '', 'year': '', 'duration': '',
                    'quality': '', 'category': '', 'description': '',
                    'servers': [], 'episodes': [], 'is_series': False,
                    'story': ''
                }

                title_tag = soup.find('title')
                if title_tag:
                    movie_info['title'] = title_tag.get_text(strip=True).replace(' - كيو فيلم', '')

                if 'مسلسل' in movie_info['title'] or 'series' in movie_info['title'].lower():
                    movie_info['is_series'] = True

                story_box = soup.find('div', class_='StoryBox')
                if story_box:
                    story_text = story_box.find('div', class_='StoryBoxText')
                    if story_text:
                        movie_info['story'] = story_text.get_text(strip=True)

                meta_desc = soup.find('meta', {'name': 'description'})
                if meta_desc:
                    movie_info['description'] = meta_desc.get('content', '')

                breadcrumb = soup.find('ul', class_='breadcrumbNav')
                if breadcrumb:
                    links = breadcrumb.find_all('a')
                    if links:
                        movie_info['category'] = links[0].get_text(strip=True)

                duration_elem = soup.find('span', class_='pm-label-duration')
                if duration_elem:
                    movie_info['duration'] = duration_elem.get_text(strip=True)

                year_match = re.search(r'\b(19|20)\d{2}\b', movie_info['title'])
                if year_match:
                    movie_info['year'] = year_match.group(0)

                quality_match = re.search(r'(HD|4K|Full HD|720p|1080p|2160p|WEB-DL|BluRay)', movie_info['description'], re.I)
                if quality_match:
                    movie_info['quality'] = quality_match.group(1)

                script_tags = soup.find_all('script')
                servers = []

                for script in script_tags:
                    script_text = script.get_text()
                    if 'servers = [' in script_text:
                        server_match = re.search(r'servers\s*=\s*\[(.*?)\];', script_text, re.DOTALL)
                        if server_match:
                            server_content = server_match.group(1)
                            iframe_matches = re.findall(r'src="([^"]+)"', server_content)
                            for url in iframe_matches:
                                if url and not url.startswith('data:') and url not in servers:
                                    servers.append(url)

                if not servers:
                    iframes = soup.find_all('iframe')
                    for iframe in iframes:
                        src = iframe.get('src', '')
                        if src and 'embed' in src and src not in servers:
                            servers.append(src)

                if not servers or len(servers) < 9:
                    play_url = f"{self.base_url}/play.php?vid={vid}"
                    async with session.get(play_url) as play_response:
                        if play_response.status == 200:
                            try:
                                play_content = await play_response.text()
                            except:
                                play_content = ''

                            iframe_matches = re.findall(r'<iframe[^>]*src="([^"]+)"', play_content)
                            for url in iframe_matches:
                                if url and not url.startswith('data:') and 'embed' in url and url not in servers:
                                    servers.append(url)

                if not servers:
                    embed_matches = re.findall(r'(?:https?://[^"\']*embed[^"\']*\.html?)', html_content)
                    for url in embed_matches:
                        if url not in servers:
                            servers.append(url)

                movie_info['servers'] = servers[:9] if len(servers) > 9 else servers

                if movie_info['is_series']:
                    episode_links = soup.find_all('a', href=re.compile(r'watch\.php\?vid=[a-f0-9]+'))
                    for link in episode_links:
                        href = link.get('href', '')
                        vid_match = re.search(r'vid=([a-f0-9]+)', href)
                        if vid_match:
                            episode_vid = vid_match.group(1)
                            episode_title = link.get_text(strip=True)
                            if episode_vid != vid and episode_vid not in [e['vid'] for e in movie_info['episodes']]:
                                movie_info['episodes'].append({
                                    'vid': episode_vid,
                                    'title': episode_title[:50] if episode_title else f'حلقة {len(movie_info["episodes"]) + 1}'
                                })

                return movie_info

        except Exception as e:
            return {"error": f"حدث خطأ: {str(e)}"}

    async def close(self):
        if self.session:
            await self.session.close()
            self.session = None

# ============================================
# 🤖 Discord Bot
# ============================================

class DiscordBot(commands.Bot):
    def __init__(self, web_url='http://localhost:8080'):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.guilds = True
        intents.members = True
        intents.voice_states = True
        super().__init__(command_prefix='!', intents=intents)
        self.movie_bot = MovieSearchBot()
        self.web_url = web_url
        self.discord_app_id = DISCORD_APP_ID

    async def setup_hook(self):
        print('⚠️ Skipping automatic command sync to avoid Entry Point conflicts')

    async def on_ready(self):
        print(f'✅ Discord Bot logged in as {self.user.name}')
        print(f'🌐 Web URL: {self.web_url}')
        if self.discord_app_id:
            print(f'🎮 Discord Activity URL: https://discord.com/application-directory/{self.discord_app_id}')

    @app_commands.command(name='search', description='ابحث عن فيلم أو مسلسل')
    async def search(self, interaction: discord.Interaction, query: str):
        await interaction.response.defer()

        result = await self.movie_bot.search_movies(query)

        if 'error' in result:
            await interaction.followup.send(f'❌ {result["error"]}')
            return

        movies = result.get('results', [])
        if not movies:
            await interaction.followup.send('😕 لم يتم العثور على نتائج')
            return

        embed = discord.Embed(
            title=f'🎬 نتائج البحث عن: {query}',
            color=0xe94560
        )

        for movie in movies[:5]:
            movie_title = movie.get('title', 'غير معروف')
            movie_type = movie.get('type', '')
            movie_year = movie.get('year', '')
            movie_vid = movie.get('vid', '')

            if movie_vid:
                watch_url = f'{self.web_url}/sync?vid={movie_vid}'
                embed.add_field(
                    name=f'{movie_title}',
                    value=f'📅 {movie_year} | 🎭 {movie_type}\n[🎥 شاهد جماعي]({watch_url})',
                    inline=False
                )

        embed.set_footer(text='Study Movies - المشاهدة الجماعية')
        await interaction.followup.send(embed=embed)

    @app_commands.command(name='movie', description='افتح فيلم في المشاهدة الجماعية')
    async def movie(self, interaction: discord.Interaction, vid: str):
        await interaction.response.defer()

        movie_info = await self.movie_bot.get_movie_servers(vid)

        if 'error' in movie_info:
            await interaction.followup.send(f'❌ {movie_info["error"]}')
            return

        title = movie_info.get('title', 'فيلم')
        watch_url = f'{self.web_url}/sync?vid={vid}'

        embed = discord.Embed(
            title=f'🎬 {title}',
            description='افتح النشاط للمشاهدة الجماعية',
            color=0xe94560
        )

        view = discord.ui.View()
        button = discord.ui.Button(
            label='🎥 افتح المشاهدة الجماعية',
            style=discord.ButtonStyle.url,
            url=watch_url
        )
        view.add_item(button)
        await interaction.followup.send(embed=embed, view=view)

    @app_commands.command(name='launch', description='افتح المشاهدة الجماعية')
    async def launch(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title='🎬 Study Movies',
            description='المشاهدة الجماعية مع الأصدقاء',
            color=0xe94560
        )
        embed.add_field(name='رابط النشاط', value=f'[🎥 افتح المشاهدة الجماعية]({self.web_url}/sync)', inline=False)

        view = discord.ui.View()
        button = discord.ui.Button(
            label='🎬 افتح النشاط',
            style=discord.ButtonStyle.url,
            url=f'{self.web_url}/sync'
        )
        view.add_item(button)

        await interaction.response.send_message(embed=embed, view=view)

# ============================================
# 🌐 Web Handlers
# ============================================

bot = MovieSearchBot()
discord_bot = None

async def handle_search(request):
    query = request.query.get('q', '').strip()
    if not query:
        return web.json_response({"error": "الرجاء كتابة اسم الفيلم أو المسلسل"})

    result = await bot.search_movies(query)
    return web.json_response(result)

async def handle_new_movies(request):
    result = await bot.get_new_movies()
    return web.json_response(result)

async def handle_sync(request):
    """صفحة المشاهدة الجماعية"""
    vid = request.query.get('vid', '').strip()
    
    if vid:
        movie_info = await bot.get_movie_servers(vid)
        servers = movie_info.get('servers', [])
        title = movie_info.get('title', 'فيلم')
        servers_json = json.dumps(servers)
        
        # نعدل الـ HTML ونضيف معلومات الفيلم
        html = SYNC_HTML_TEMPLATE
        # نضيف JavaScript لتحميل الفيلم تلقائياً
        html = html.replace(
            '</body>',
            f'''
            <script>
                // تحميل الفيلم تلقائياً للمضيف
                document.addEventListener('DOMContentLoaded', function() {{
                    // انتظار اتصال WebSocket
                    const checkWS = setInterval(function() {{
                        if (ws && ws.readyState === WebSocket.OPEN && isHost) {{
                            clearInterval(checkWS);
                            // تعيين حالة الفيلم
                            currentState.video = '{servers[0] if servers else ''}';
                            currentState.title = '{title}';
                            currentState.servers = {servers_json};
                            currentState.server_index = 0;
                            
                            // إرسال التحديث
                            ws.send(JSON.stringify({{
                                action: 'sync_update',
                                state: currentState
                            }}));
                            
                            // تحميل الفيديو
                            loadVideo(currentState.video);
                            renderServers(currentState.servers, 0);
                            movieInfoText.textContent = '🎬 {title}';
                        }}
                    }}, 500);
                }});
            </script>
            </body>
            '''
        )
        return web.Response(text=html, content_type='text/html')
    
    return web.Response(text=SYNC_HTML_TEMPLATE, content_type='text/html')

async def handle_index(request):
    return web.Response(text=HTML_TEMPLATE, content_type='text/html')

# ============================================
# 🚀 Main
# ============================================

async def on_shutdown(app):
    await bot.close()

async def run_discord_bot():
    discord_token = DISCORD_TOKEN
    if not discord_token:
        print('⚠️ DISCORD_TOKEN not found')
        return

    try:
        await discord_bot.start(discord_token)
    except asyncio.CancelledError:
        print('🛑 Discord bot cancelled')
    except Exception as e:
        print(f'❌ Discord bot error: {e}')

async def run_web_server():
    app = web.Application()
    app.router.add_get('/', handle_index)
    app.router.add_get('/api/search', handle_search)
    app.router.add_get('/api/new-movies', handle_new_movies)
    app.router.add_get('/sync', handle_sync)
    app.router.add_get('/ws', handle_websocket)
    
    app.on_shutdown.append(on_shutdown)

    @web.middleware
    async def cors_middleware(request, handler):
        response = await handler(request)
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS, PUT, DELETE'
        response.headers['Access-Control-Allow-Headers'] = '*'
        return response

    app.middlewares.append(cors_middleware)

    print("\n🌐 Web Server: http://localhost:8080")
    print("🔗 Sync Watch: http://localhost:8080/sync")
    print("🔗 WebSocket: ws://localhost:8080/ws")

    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, 'localhost', 8080)
    await site.start()

    return runner

async def main():
    discord_token = DISCORD_TOKEN
    web_url = WEB_URL

    if discord_token:
        global discord_bot
        discord_bot = DiscordBot(web_url=web_url)
        print('🤖 Starting Discord bot and web server...')
        web_runner = await run_web_server()

        discord_task = asyncio.create_task(run_discord_bot())

        try:
            await discord_task
        except asyncio.CancelledError:
            print('\n🛑 Tasks cancelled, shutting down...')
        except KeyboardInterrupt:
            print('\n🛑 Shutting down...')
        finally:
            await web_runner.cleanup()
            if discord_bot:
                await discord_bot.close()
            await bot.close()
    else:
        print('⚠️ DISCORD_TOKEN not found, running web server only...')
        web_runner = await run_web_server()

        try:
            while True:
                await asyncio.sleep(3600)
        except asyncio.CancelledError:
            print('\n🛑 Tasks cancelled, shutting down...')
        except KeyboardInterrupt:
            print('\n🛑 Shutting down...')
        finally:
            await web_runner.cleanup()
            await bot.close()

def main_sync():
    asyncio.run(main())

if __name__ == "__main__":
    main_sync()

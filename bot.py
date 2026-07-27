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

try:
    from dotenv import load_dotenv
    env_path = Path(__file__).parent / '.env'
    if env_path.exists():
        load_dotenv(env_path)
except ImportError:
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "python-dotenv"])
    from dotenv import load_dotenv
    env_path = Path(__file__).parent / '.env'
    if env_path.exists():
        load_dotenv(env_path)

try:
    import aiohttp
except ImportError:
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "aiohttp"])
    import aiohttp
from aiohttp import web

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

def check_cloudflared():
    """Check if cloudflared is installed"""
    try:
        import subprocess
        result = subprocess.run(['cloudflared', '--version'], capture_output=True, text=True)
        if result.returncode == 0:
            print(f'✅ cloudflared found: {result.stdout.strip()}')
            return True
    except FileNotFoundError:
        pass
    return False

async def start_cloudflare_tunnel(port=8080):
    """Start Cloudflare tunnel and return the HTTPS URL"""
    if not check_cloudflared():
        print('❌ cloudflared not found. Please install it from: https://developers.cloudflare.com/cloudflare-one/connections/connect-apps/install-and-setup/installation/')
        print('💡 On Windows: winget install --id Cloudflare.cloudflared')
        return None

    try:
        import subprocess
        import time
        import threading
        print('🚀 Starting Cloudflare tunnel...')

        process = subprocess.Popen(
            ['cloudflared', 'tunnel', '--url', f'http://localhost:{port}'],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            universal_newlines=True
        )

        tunnel_url = None

        def read_output():
            nonlocal tunnel_url
            for line in process.stdout:
                line = line.strip()
                print(f'[cloudflared] {line}')
                if 'https://' in line and '.trycloudflare.com' in line:
                    import re
                    url_match = re.search(r'https://[a-zA-Z0-9\-]+\.trycloudflare\.com', line)
                    if url_match:
                        tunnel_url = url_match.group(0)
                        print(f'🔗 Found Tunnel URL: {tunnel_url}')
                        break

        reader_thread = threading.Thread(target=read_output, daemon=True)
        reader_thread.start()

        for _ in range(15):
            time.sleep(1)
            if tunnel_url:
                break

        if tunnel_url:
            print(f'✅ Cloudflare tunnel started: {tunnel_url}')
            print('⚠️ Use this URL in Discord Developer Portal for Activities')
            return tunnel_url
        else:
            print('⚠️ Could not extract tunnel URL from output')
            print('⚠️ Check cloudflared output above for the URL')
            return 'https://your-tunnel.trycloudflare.com'

    except Exception as e:
        print(f'❌ Error starting tunnel: {e}')
        return None


HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Study Movies</title>
    <link rel="icon" type="image/svg+xml" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'%3E%3Crect fill='%23e94560' width='100' height='100' rx='20'/%3E%3Ctext x='50' y='65' text-anchor='middle' fill='white' font-size='50' font-family='Arial'%3E🎬%3C/text%3E%3C/svg%3E">
    <meta name="description" content="Study Movies - أفضل منصة لمشاهدة الأفلام والمسلسلات العربية والعالمية">
    <style>
        * { margin:0; padding:0; box-sizing:border-box; font-family:'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; }
        body {
            background:
            min-height:100vh;
            background-image:radial-gradient(ellipse at 20% 50%, rgba(72,0,255,0.15) 0%, transparent 60%),
                radial-gradient(ellipse at 80% 50%, rgba(255,0,128,0.10) 0%, transparent 60%),
                radial-gradient(ellipse at 50% 100%, rgba(0,200,255,0.08) 0%, transparent 50%),
                linear-gradient(180deg,
            background-attachment:fixed;
            overflow-x:hidden;
        }
        body::before {
            content:'';
            position:fixed;
            top:0; left:0;
            width:100%; height:100%;
            background-image:radial-gradient(2px 2px at 20px 30px,
                radial-gradient(2px 2px at 40px 70px, rgba(255,255,255,0.8), transparent),
                radial-gradient(2px 2px at 50px 160px,
                radial-gradient(2px 2px at 90px 40px, rgba(255,255,255,0.6), transparent),
                radial-gradient(2px 2px at 130px 80px,
                radial-gradient(2px 2px at 160px 30px, rgba(255,255,255,0.7), transparent);
            background-size:200px 200px;
            background-repeat:repeat;
            opacity:0.3;
            pointer-events:none;
            z-index:0;
        }
        .container { max-width:1400px; margin:0 auto; padding:0 1rem; position:relative; z-index:1; }
        .header-section {
            background:rgba(26,26,46,0.6);
            backdrop-filter:blur(16px);
            -webkit-backdrop-filter:blur(16px);
            border-bottom:1px solid rgba(255,255,255,0.06);
            padding:0.8rem 0;
            position:sticky;
            top:0;
            z-index:100;
            animation:slideDown 0.6s ease-out;
        }
        @keyframes slideDown { from { transform:translateY(-100%); opacity:0; } to { transform:translateY(0); opacity:1; } }
        .header-content { display:flex; align-items:center; justify-content:space-between; flex-wrap:wrap; gap:1rem; }
        .logo { display:flex; align-items:center; gap:0.5rem; text-decoration:none; transition:transform 0.3s ease; }
        .logo:hover { transform:scale(1.05); }
        .logo-icon { font-size:2.2rem; color:
        @keyframes pulse { 0%,100% { transform:scale(1); } 50% { transform:scale(1.1); } }
        .logo-text { display:flex; flex-direction:column; line-height:1.1; }
        .logo-text .study { font-size:1.6rem; font-weight:800; color:
        .logo-text .movies { font-size:1.2rem; font-weight:300; color:
        .logo-text .movies span { color:

        .header-search {
            display:flex;
            flex:1;
            max-width:450px;
            background:rgba(255,255,255,0.04);
            border-radius:50px;
            padding:0.3rem;
            border:1px solid rgba(255,255,255,0.06);
            transition:all 0.3s ease;
        }
        .header-search:focus-within {border-color:rgba(233,69,96,0.3);box-shadow:0 0 20px rgba(233,69,96,0.05);}
        .header-search input {
            flex:1;
            padding:0.5rem 1.2rem;
            background:transparent;
            border:none;
            color:
            font-size:0.85rem;
            outline:none;
        }
        .header-search input::placeholder {color:rgba(255,255,255,0.3);}
        .header-search button {
            padding:0.4rem 1.2rem;
            background:linear-gradient(135deg,
            color:white;
            border:none;
            border-radius:50px;
            font-size:0.8rem;
            font-weight:600;
            cursor:pointer;
            transition:all 0.3s ease;
        }
        .header-search button:hover {transform:scale(1.02);}

        .discord-btn {
            display:flex;
            align-items:center;
            gap:0.6rem;
            padding:0.6rem 1.4rem;
            background:linear-gradient(135deg,
            color:white;
            border:none;
            border-radius:50px;
            font-size:0.9rem;
            font-weight:600;
            cursor:pointer;
            transition:all 0.3s ease;
            text-decoration:none;
            box-shadow:0 4px 20px rgba(88,101,242,0.3);
        }
        .discord-btn:hover { transform:translateY(-3px) scale(1.02); box-shadow:0 8px 35px rgba(88,101,242,0.5); }
        .discord-btn i { font-size:1.2rem; }

        .hero-section {
            padding:3rem 0 2rem;
            text-align:center;
        }
        .hero-title {
            font-size:3.2rem;
            font-weight:900;
            color:
            margin-bottom:0.5rem;
            text-shadow:0 0 60px rgba(233,69,96,0.15);
            animation:fadeInUp 0.8s ease-out;
        }
        @keyframes fadeInUp { from { opacity:0; transform:translateY(30px); } to { opacity:1; transform:translateY(0); } }
        .hero-title .highlight { background:linear-gradient(135deg,
        .hero-subtitle { font-size:1.2rem; color:rgba(255,255,255,0.5); font-weight:300; animation:fadeInUp 0.8s ease-out 0.2s both; }

        .results-grid { display:grid; grid-template-columns:repeat(auto-fill, minmax(220px,1fr)); gap:1.8rem; padding:1.5rem 0 3rem; }
        .movie-card {
            background:rgba(26,26,46,0.4);
            backdrop-filter:blur(12px);
            -webkit-backdrop-filter:blur(12px);
            border-radius:16px;
            overflow:hidden;
            transition:all 0.4s cubic-bezier(0.175,0.885,0.32,1.275);
            border:1px solid rgba(255,255,255,0.05);
            cursor:pointer;
            text-decoration:none;
            display:block;
            position:relative;
        }
        .movie-card:hover { transform:translateY(-10px) scale(1.02); box-shadow:0 20px 60px rgba(233,69,96,0.15); border-color:rgba(233,69,96,0.2); }
        .movie-poster-container { width:100%; aspect-ratio:240/170; background:rgba(26,26,46,0.6); position:relative; overflow:hidden; display:flex; align-items:center; justify-content:center; }
        .movie-poster { width:100%; height:100%; object-fit:cover; display:block; transition:transform 0.5s ease; }
        .movie-card:hover .movie-poster { transform:scale(1.05); }
        .play-overlay {
            position:absolute;
            top:50%; left:50%;
            transform:translate(-50%, -50%) scale(0);
            width:60px; height:60px;
            background:rgba(233,69,96,0.9);
            border-radius:50%;
            display:flex;
            align-items:center;
            justify-content:center;
            color:white;
            font-size:1.5rem;
            transition:all 0.4s cubic-bezier(0.175,0.885,0.32,1.275);
            z-index:2;
            box-shadow:0 0 40px rgba(233,69,96,0.3);
        }
        .movie-card:hover .play-overlay { transform:translate(-50%, -50%) scale(1); }
        .movie-info { padding:0.9rem 1rem 1rem; }
        .movie-title { color:
        .movie-details { display:flex; gap:0.4rem; flex-wrap:wrap; margin-top:0.3rem; }
        .movie-detail { background:rgba(233,69,96,0.08); color:
        .loading { display:none; text-align:center; color:
        .loading.active { display:block; }
        .loading i { font-size:2rem; margin-bottom:0.5rem; }
        .no-results { text-align:center; color:rgba(255,255,255,0.3); font-size:1.3rem; padding:4rem 0; grid-column:1 / -1; }
        .error-message { background:rgba(233,69,96,0.08); border:1px solid rgba(233,69,96,0.2); color:
        .error-message.active { display:block; animation:shake 0.5s ease; }
        @keyframes shake { 0%,100% { transform:translateX(0); } 25% { transform:translateX(-10px); } 75% { transform:translateX(10px); } }

        .pm-section-head {
            display:flex;
            align-items:center;
            justify-content:space-between;
            margin-bottom:1.5rem;
            padding-bottom:0.5rem;
            border-bottom:2px solid rgba(255,255,255,0.04);
        }
        .pm-section-head h2 {
            color:
            font-size:1.4rem;
            font-weight:700;
            display:flex;
            align-items:center;
            gap:0.5rem;
        }
        .pm-section-head h2 i { color:
        .pm-section-head h2 a { color:
        .pm-section-head h2 a:hover { color:

        .pm-ul-browse-videos {
            display:grid;
            grid-template-columns:repeat(auto-fill, minmax(220px,1fr));
            gap:1.5rem;
            padding:0;
            list-style:none;
        }
        .pm-ul-browse-videos .thumbnail {
            background:rgba(26,26,46,0.3);
            backdrop-filter:blur(10px);
            border-radius:14px;
            overflow:hidden;
            border:1px solid rgba(255,255,255,0.04);
            padding:0;
            transition:all 0.4s cubic-bezier(0.175,0.885,0.32,1.275);
        }
        .pm-ul-browse-videos .thumbnail:hover {
            transform:translateY(-6px);
            box-shadow:0 15px 40px rgba(0,0,0,0.4);
            border-color:rgba(233,69,96,0.15);
        }
        .pm-video-thumb {
            position:relative;
            overflow:hidden;
        }
        .pm-video-thumb img {
            width:100%;
            height:170px;
            object-fit:cover;
            transition:transform 0.5s ease;
        }
        .pm-ul-browse-videos .thumbnail:hover .pm-video-thumb img {
            transform:scale(1.05);
        }
        .pm-label-duration {
            position:absolute;
            bottom:8px;
            left:8px;
            background:rgba(0,0,0,0.7);
            color:
            padding:0.15rem 0.6rem;
            border-radius:6px;
            font-size:0.7rem;
            backdrop-filter:blur(4px);
        }
        .pm-video-labels {
            position:absolute;
            top:8px;
            right:8px;
            display:flex;
            gap:0.3rem;
            flex-wrap:wrap;
        }
        .pm-video-labels .label {
            padding:0.1rem 0.5rem;
            border-radius:4px;
            font-size:0.6rem;
            font-weight:700;
        }
        .label-new { background:
        .label-pop { background:
        .label-featured { background:

        .pm-video-thumb .caption {
            padding:0.7rem 0.9rem;
            color:
            font-size:0.85rem;
            font-weight:500;
            display:-webkit-box;
            -webkit-line-clamp:2;
            -webkit-box-orient:vertical;
            overflow:hidden;
            line-height:1.3;
            margin:0;
            text-decoration:none;
        }
        .pm-video-thumb .caption a {
            color:
            text-decoration:none;
        }
        .pm-video-thumb .caption a:hover { color:

        .pm-video-thumb .overlay {
            position:absolute;
            top:50%;
            left:50%;
            transform:translate(-50%, -50%);
            width:50px;
            height:50px;
            background:rgba(233,69,96,0.9);
            border-radius:50%;
            display:flex;
            align-items:center;
            justify-content:center;
            color:white;
            font-size:1.2rem;
            opacity:0;
            transition:all 0.4s cubic-bezier(0.175,0.885,0.32,1.275);
            box-shadow:0 0 40px rgba(233,69,96,0.3);
        }
        .pm-video-thumb:hover .overlay {
            opacity:1;
            transform:translate(-50%, -50%) scale(1);
        }

        .clearfix { clear:both; }

        .footer { text-align:center; padding:2.5rem 0 1.5rem; border-top:1px solid rgba(255,255,255,0.04); color:rgba(255,255,255,0.2); font-size:0.85rem; }
        .footer .heart { color:
        .footer-content { display:flex; flex-direction:column; align-items:center; gap:1rem; }
        .social-links { display:flex; gap:1rem; }
        .social-link {
            display:flex;
            align-items:center;
            justify-content:center;
            width:40px;
            height:40px;
            border-radius:50%;
            background:rgba(255,255,255,0.05);
            color:rgba(255,255,255,0.5);
            text-decoration:none;
            transition:all 0.3s ease;
            border:1px solid rgba(255,255,255,0.06);
        }
        .social-link:hover {
            background:rgba(233,69,96,0.15);
            color:
            border-color:rgba(233,69,96,0.3);
            transform:translateY(-3px);
        }
        .social-link i { font-size:1.2rem; }

        ::-webkit-scrollbar { width:6px; height:6px; }
        ::-webkit-scrollbar-track { background:rgba(255,255,255,0.02); }
        ::-webkit-scrollbar-thumb { background:rgba(233,69,96,0.3); border-radius:10px; }
        ::-webkit-scrollbar-thumb:hover { background:rgba(233,69,96,0.5); }

        @media (max-width:768px) {
            .header-content { flex-direction:column; align-items:stretch; gap:0.8rem; }
            .logo { justify-content:center; }
            .header-search { max-width:100%; }
            .discord-btn { justify-content:center; padding:0.5rem 1rem; font-size:0.8rem; }
            .hero-title { font-size:2rem; }
            .hero-subtitle { font-size:1rem; }
            .pm-ul-browse-videos { grid-template-columns:repeat(auto-fill, minmax(160px,1fr)); gap:1rem; }
            .results-grid { grid-template-columns:repeat(auto-fill, minmax(160px,1fr)); gap:1rem; }
            .logo-text .study { font-size:1.3rem; }
            .logo-text .movies { font-size:1rem; }
        }
        @media (max-width:480px) {
            .pm-ul-browse-videos { grid-template-columns:repeat(auto-fill, minmax(140px,1fr)); gap:0.8rem; }
            .results-grid { grid-template-columns:repeat(auto-fill, minmax(140px,1fr)); gap:0.8rem; }
            .pm-video-thumb img { height:140px; }
        }
    </style>
</head>
<body>
    <header class="header-section">
        <div class="container">
            <div class="header-content">
                <a href="/" class="logo">
                    <i class="fas fa-film logo-icon"></i>
                    <div class="logo-text">
                        <span class="study">Study</span>
                        <span class="movies">Movies <span>✦</span></span>
                    </div>
                </a>

                <div class="header-search">
                    <input type="text" id="headerSearchInput" placeholder="ابحث عن فيلمك من هنا ...">
                    <button id="headerSearchBtn"><i class="fas fa-search"></i></button>
                </div>

                <a href="https://discord.gg/BCnBNN2xY" target="_blank" class="discord-btn">
                    <i class="fab fa-discord"></i>
                    <span>Join Us Community</span>
                </a>
            </div>
        </div>
    </header>

    <section class="hero-section">
        <div class="container">
            <h1 class="hero-title">🎬 <span class="highlight">Study Movies</span></h1>
            <p class="hero-subtitle">تقدر تشوف افلامك المفضلة مع صحابك في روم واحدة ومن غير اعلانات</p>
            <p class="hero-subtitle">منصتنا بتجمع أفضل الأفلام العربية والعالمية</p>
            <p class="hero-subtitle">جاهز تعمل اجمد Movie Night .؟</p>
        </div>
    </section>

    <section class="container">
        <div class="results-grid" id="resultsGrid"></div>
        <div class="loading" id="loading"><i class="fas fa-spinner fa-spin"></i><br>جاري البحث...</div>
        <div class="error-message" id="errorMessage"></div>
    </section>

    <section class="container" style="padding-top:1rem;">
        <div class="pm-section-head">
            <h2><i class="fas fa-star"></i> <a href="#" id="newMoviesLink">جديد الموقع</a></h2>
        </div>
        <ul class="pm-ul-browse-videos" id="newMoviesGrid"></ul>
        <div class="clearfix"></div>
    </section>

    <footer class="footer">
        <div class="container">
            <div class="footer-content">
                <p><i class="fas fa-heart heart"></i> Study Movies — أفضل تجربة مشاهدة</p>
                <div class="social-links">
                    <a href="https://discord.gg/BCnBNN2xY" target="_blank" class="social-link" title="Discord">
                        <i class="fab fa-discord"></i>
                    </a>
                    <a href="https://twitter.com" target="_blank" class="social-link" title="Twitter">
                        <i class="fab fa-twitter"></i>
                    </a>
                    <a href="https://facebook.com" target="_blank" class="social-link" title="Facebook">
                        <i class="fab fa-facebook"></i>
                    </a>
                    <a href="https://instagram.com" target="_blank" class="social-link" title="Instagram">
                        <i class="fab fa-instagram"></i>
                    </a>
                </div>
                <p style="font-size:0.75rem;opacity:0.5;margin-top:0.5rem;">جميع الحقوق محفوظة &copy; 2026</p>
            </div>
        </div>
    </footer>

    <script>
        const headerSearchInput = document.getElementById('headerSearchInput');
        const resultsGrid = document.getElementById('resultsGrid');
        const loading = document.getElementById('loading');
        const errorMessage = document.getElementById('errorMessage');
        const newMoviesGrid = document.getElementById('newMoviesGrid');

        function performHeaderSearch() {
            const query = headerSearchInput.value.trim();
            if (query) {
                window.location.href = '/?q=' + encodeURIComponent(query);
            }
        }

        function showError(msg) {
            errorMessage.textContent = msg;
            errorMessage.classList.add('active');
            setTimeout(() => errorMessage.classList.remove('active'), 5000);
        }

        function displayResults(movies) {
            if (!movies || movies.length === 0) {
                resultsGrid.innerHTML = '<div class="no-results">😕 لا توجد نتائج</div>';
                return;
            }
            resultsGrid.innerHTML = movies.map(movie => `
                <a href="/watch?vid=` + (movie.vid || '') + `" class="movie-card">
                    <div class="movie-poster-container">
                        <img src="` + (movie.poster ? '/img-proxy?url=' + encodeURIComponent(movie.poster) : 'data:image/svg+xml,%3Csvg xmlns=%22http://www.w3.org/2000/svg%22 width=%22240%22 height=%22170%22%3E%3Crect fill=%22%231a1a2e%22 width=%22240%22 height=%22170%22/%3E%3Ctext x=%2250%25%22 y=%2250%25%22 text-anchor=%22middle%22 dy=%22.3em%22 fill=%22%23666%22 font-size=%2220%22%3E🎬%3C/text%3E%3C/svg%3E') + `" alt="` + movie.title + `" class="movie-poster" loading="lazy">
                        <div class="play-overlay">▶</div>
                    </div>
                    <div class="movie-info">
                        <div class="movie-title">` + movie.title + `</div>
                        <div class="movie-details">
                            ` + (movie.duration ? '<span class="movie-detail">⏱ ' + movie.duration + '</span>' : '') + `
                            ` + (movie.year ? '<span class="movie-detail">📅 ' + movie.year + '</span>' : '') + `
                            ` + (movie.quality ? '<span class="movie-detail">' + movie.quality + '</span>' : '') + `
                            ` + (movie.type ? '<span class="movie-detail">' + movie.type + '</span>' : '') + `
                        </div>
                    </div>
                </a>
            `).join('');
        }

        async function performSearch(query) {
            if (!query.trim()) { showError('الرجاء كتابة اسم الفيلم أو المسلسل'); return; }
            loading.classList.add('active');
            resultsGrid.innerHTML = '';
            try {
                const response = await fetch('/api/search?q=' + encodeURIComponent(query));
                const data = await response.json();
                if (data.error) { showError(data.error); } else { displayResults(data.results || []); }
            } catch (err) { showError('حدث خطأ في الاتصال بالخادم'); console.error('Search error:', err); }
            finally { loading.classList.remove('active'); }
        }

        async function loadNewMovies() {
            try {
                const response = await fetch('/api/new-movies');
                const data = await response.json();
                if (data.error) {
                    newMoviesGrid.innerHTML = '<div style="color:rgba(255,255,255,0.3);text-align:center;padding:2rem;">' + data.error + '</div>';
                    return;
                }
                const movies = data.results || [];
                if (movies.length === 0) {
                    newMoviesGrid.innerHTML = '<div style="color:rgba(255,255,255,0.3);text-align:center;padding:2rem;">لا توجد أفلام جديدة</div>';
                    return;
                }
                newMoviesGrid.innerHTML = movies.map(movie => `
                    <li class="col-xs-6 col-sm-6 col-md-3">
                        <div class="thumbnail">
                            <div class="pm-video-thumb">
                                <span class="pm-label-duration">` + (movie.duration || '--:--') + `</span>
                                <a href="/watch?vid=` + (movie.vid || '') + `" title="` + movie.title + `">
                                    <div class="pm-video-labels hidden-xs">
                                        ` + (movie.is_new ? '<span class="label label-new">جديد</span>' : '') + `
                                        ` + (movie.is_popular ? '<span class="label label-pop">شائع</span>' : '') + `
                                        ` + (movie.is_featured ? '<span class="label label-featured">مميز</span>' : '') + `
                                    </div>
                                    <img src="` + (movie.poster ? '/img-proxy?url=' + encodeURIComponent(movie.poster) : 'data:image/svg+xml,%3Csvg xmlns=%22http://www.w3.org/2000/svg%22 width=%22240%22 height=%22170%22%3E%3Crect fill=%22%231a1a2e%22 width=%22240%22 height=%22170%22/%3E%3Ctext x=%2250%25%22 y=%2250%25%22 text-anchor=%22middle%22 dy=%22.3em%22 fill=%22%23666%22 font-size=%2220%22%3E🎬%3C/text%3E%3C/svg%3E') + `" alt="` + movie.title + `" class="img-responsive" loading="lazy">
                                    <span class="overlay">▶</span>
                                </a>
                                <a style="overflow-wrap:break-word;white-space:normal;" href="/watch?vid=` + (movie.vid || '') + `">
                                    <h3 class="caption">` + movie.title + `</h3>
                                </a>
                            </div>
                        </div>
                    </li>
                `).join('');
            } catch (err) {
                newMoviesGrid.innerHTML = '<div style="color:rgba(255,255,255,0.3);text-align:center;padding:2rem;">حدث خطأ في تحميل الأفلام</div>';
                console.error('Error loading new movies:', err);
            }
        }

        (function() {
            const params = new URLSearchParams(window.location.search);
            const q = params.get('q');
            if (q) {
                headerSearchInput.value = q;
                performSearch(q);
                setTimeout(() => {
                    document.querySelector('.results-grid').scrollIntoView({ behavior: 'smooth', block: 'start' });
                }, 500);
            }
        })();

        document.addEventListener('DOMContentLoaded', function() {
            // Add event listeners for search
            const searchBtn = document.getElementById('headerSearchBtn');
            if (searchBtn) {
                searchBtn.addEventListener('click', performHeaderSearch);
            }

            const searchInput = document.getElementById('headerSearchInput');
            if (searchInput) {
                searchInput.addEventListener('keypress', function(e) {
                    if (e.key === 'Enter') {
                        performHeaderSearch();
                    }
                });
            }

            // Load new movies
            loadNewMovies();
        });
    </script>
</body>
</html>"""

WATCH_TEMPLATE = Template("""<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>مشاهدة فيلم - Study Movies</title>
    <script src="/static/js/hls.min.js"></script>
    <style>
        * {margin:0;padding:0;box-sizing:border-box;font-family:'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;}
        body {
            background:
            min-height:100vh;
            background-image:radial-gradient(ellipse at 20% 50%, rgba(72,0,255,0.12) 0%, transparent 60%),
                radial-gradient(ellipse at 80% 50%, rgba(255,0,128,0.08) 0%, transparent 60%),
                linear-gradient(180deg,
            background-attachment:fixed;
            padding:1rem;
        }
        .container {max-width:1200px;margin:0 auto;}

        .header-section {
            background:rgba(26,26,46,0.5);
            backdrop-filter:blur(16px);
            -webkit-backdrop-filter:blur(16px);
            border-radius:16px;
            padding:0.8rem 1.5rem;
            margin-bottom:1.5rem;
            border:1px solid rgba(255,255,255,0.04);
            display:flex;
            align-items:center;
            justify-content:space-between;
            flex-wrap:wrap;
            gap:0.8rem;
        }
        .logo {display:flex;align-items:center;gap:0.5rem;text-decoration:none;transition:transform 0.3s ease;}
        .logo:hover {transform:scale(1.03);}
        .logo-icon {font-size:1.6rem;color:
        .logo-text .study {font-size:1.2rem;font-weight:800;color:
        .logo-text .movies {font-size:1rem;font-weight:300;color:
        .logo-text .movies span {color:

        .header-search {
            display:flex;
            flex:1;
            max-width:350px;
            background:rgba(255,255,255,0.04);
            border-radius:50px;
            padding:0.3rem;
            border:1px solid rgba(255,255,255,0.06);
            transition:all 0.3s ease;
        }
        .header-search:focus-within {border-color:rgba(233,69,96,0.3);box-shadow:0 0 20px rgba(233,69,96,0.05);}
        .header-search input {
            flex:1;
            padding:0.5rem 1.2rem;
            background:transparent;
            border:none;
            color:
            font-size:0.85rem;
            outline:none;
        }
        .header-search input::placeholder {color:rgba(255,255,255,0.3);}
        .header-search button {
            padding:0.4rem 1.2rem;
            background:linear-gradient(135deg,
            color:white;
            border:none;
            border-radius:50px;
            font-size:0.8rem;
            font-weight:600;
            cursor:pointer;
            transition:all 0.3s ease;
        }
        .header-search button:hover {transform:scale(1.02);}

        .back-btn {display:inline-flex;align-items:center;gap:0.5rem;color:
        .back-btn:hover {background:rgba(233,69,96,0.12);transform:translateX(-4px);border-color:rgba(233,69,96,0.3);}

        .movie-title {color:
        .video-container {background:rgba(0,0,0,0.6);backdrop-filter:blur(10px);border-radius:16px;overflow:hidden;border:1px solid rgba(255,255,255,0.04);margin-bottom:1.5rem;position:relative;}
        .video-wrapper {position:relative;width:100%;padding-bottom:56.25%;background:
        .video-wrapper video {position:absolute;top:0;left:0;width:100%;height:100%;object-fit:contain;playsinline:true;webkit-playsinline:true;}
        .loading-spinner {position:absolute;top:50%;left:50%;transform:translate(-50%, -50%);color:
        .loading-spinner::before {content:'';width:20px;height:20px;border:3px solid rgba(255,255,255,0.3);border-top-color:
        @keyframes spin {to {transform:rotate(360deg);}}

        /* Video Controls */
        .video-controls {position:absolute;bottom:0;left:0;right:0;background:linear-gradient(transparent, rgba(0,0,0,0.9));padding:1rem;display:flex;gap:0.8rem;align-items:center;opacity:0;transition:opacity 0.3s ease;z-index:5;direction:ltr;}
        .video-container:hover .video-controls {opacity:1;}
        .video-controls-btn {background:rgba(255,255,255,0.1);border:none;color:
        .video-controls-btn:hover {background:rgba(233,69,96,0.3);transform:scale(1.1);}
        .video-controls-btn svg {width:18px;height:18px;fill:currentColor;}
        .video-progress {flex:1;height:6px;background:rgba(255,255,255,0.15);border-radius:3px;cursor:pointer;position:relative;transition:height 0.2s ease;}
        .video-progress:hover {height:10px;}
        .video-progress-buffer {position:absolute;top:0;left:0;height:100%;background:rgba(255,255,255,0.3);border-radius:3px;transition:width 0.3s ease;}
        .video-progress-bar {height:100%;background:linear-gradient(90deg,
        .video-progress-bar::before {content:'';position:absolute;right:0;top:50%;transform:translate(50%, -50%);width:14px;height:14px;background:
        .video-progress:hover .video-progress-bar::before {opacity:1;transform:translate(50%, -50%) scale(1.2);}
        .video-time {color:rgba(255,255,255,0.8);font-size:0.8rem;min-width:90px;text-align:center;font-weight:500;}
        .volume-control {display:flex;align-items:center;gap:0.5rem;}
        .volume-slider {width:70px;height:6px;background:rgba(255,255,255,0.15);border-radius:3px;cursor:pointer;}
        .volume-slider::-webkit-slider-thumb {-webkit-appearance:none;width:14px;height:14px;background:

        /* Quality Selector */
        .quality-selector {position:relative;}
        .quality-btn {background:rgba(255,255,255,0.1);border:1px solid rgba(255,255,255,0.2);color:
        .quality-btn:hover {background:rgba(233,69,96,0.2);border-color:rgba(233,69,96,0.4);}
        .quality-menu {position:absolute;bottom:100%;left:0;background:rgba(26,26,46,0.95);backdrop-filter:blur(16px);border:1px solid rgba(255,255,255,0.1);border-radius:8px;padding:0.4rem;min-width:120px;display:none;flex-direction:column;gap:0.2rem;margin-bottom:0.5rem;z-index:20;}
        .quality-menu.active {display:flex;}
        .quality-option {padding:0.5rem 0.8rem;color:rgba(255,255,255,0.7);border-radius:4px;cursor:pointer;font-size:0.75rem;transition:all 0.2s ease;}
        .quality-option:hover {background:rgba(233,69,96,0.2);color:
        .quality-option.active {background:rgba(233,69,96,0.3);color:

        /* Fullscreen */
        .video-container.fullscreen {position:fixed;top:0;left:0;right:0;bottom:0;border-radius:0;z-index:9999;margin:0;background:
        .video-container.fullscreen .video-wrapper {width:100%;height:100%;padding-bottom:0;}
        .video-container.fullscreen video {width:100%;height:100%;object-fit:contain;}
        .video-container.fullscreen .video-controls {padding:2rem;opacity:0;}
        .video-container.fullscreen:hover .video-controls {opacity:1;}
        .video-container.fullscreen .video-controls:hover {opacity:1;}

        .servers-container {display:flex;gap:0.5rem;flex-wrap:wrap;padding:1rem;background:rgba(26,26,46,0.3);backdrop-filter:blur(10px);border-radius:12px;border:1px solid rgba(255,255,255,0.04);margin-bottom:1.5rem;justify-content:center;max-height:300px;overflow-y:auto;}
        .server-btn {padding:0.5rem 1.2rem;background:rgba(255,255,255,0.04);color:rgba(255,255,255,0.5);border:1px solid rgba(255,255,255,0.06);border-radius:50px;cursor:pointer;transition:all 0.3s ease;font-size:0.85rem;font-weight:500;white-space:nowrap;}
        .server-btn:hover {background:rgba(233,69,96,0.1);color:
        .server-btn.active {background:linear-gradient(135deg,
        .server-btn.loading {opacity:0.5;pointer-events:none;}
        .server-btn.working {background:rgba(46,204,113,0.15);border-color:rgba(46,204,113,0.3);color:
        .server-btn.broken {background:rgba(231,76,60,0.1);border-color:rgba(231,76,60,0.2);color:
        .server-btn.auto-selected {border-color:
        .server-status {font-size:0.65rem;margin-right:0.3rem;}
        .server-info-text {width:100%;text-align:center;color:rgba(255,255,255,0.2);font-size:0.8rem;margin-bottom:0.3rem;}

        .no-servers {background:rgba(255,193,7,0.05);border:1px solid rgba(255,193,7,0.1);color:

        .episodes-container {display:flex;gap:0.5rem;flex-wrap:wrap;padding:0.8rem;background:rgba(255,255,255,0.02);border-radius:12px;margin-bottom:1rem;justify-content:center;max-height:200px;overflow-y:auto;}
        .episode-btn {padding:0.4rem 1rem;background:rgba(255,255,255,0.03);color:rgba(255,255,255,0.4);border:1px solid rgba(255,255,255,0.04);border-radius:50px;cursor:pointer;transition:all 0.3s ease;font-size:0.8rem;}
        .episode-btn:hover {background:rgba(233,69,96,0.08);color:
        .episode-btn.active {background:linear-gradient(135deg,
        .episode-btn.current {border-color:

        .movie-info {background:rgba(26,26,46,0.3);backdrop-filter:blur(10px);border-radius:12px;padding:1.5rem;border:1px solid rgba(255,255,255,0.04);color:
        .movie-info h3 {color:
        .movie-info p {color:rgba(255,255,255,0.5);line-height:1.7;}
        .movie-details-grid {display:grid;grid-template-columns:repeat(auto-fill,minmax(180px,1fr));gap:0.6rem;margin:0.8rem 0;}
        .movie-detail-item {background:rgba(255,255,255,0.02);padding:0.4rem 0.8rem;border-radius:8px;border:1px solid rgba(255,255,255,0.03);}
        .movie-detail-item .label {color:rgba(255,255,255,0.3);font-size:0.7rem;}
        .movie-detail-item .value {color:

        .StoryBox {background:rgba(255,255,255,0.02);border-radius:12px;padding:1.2rem 1.5rem;margin-top:1rem;border:1px solid rgba(255,255,255,0.03);}
        .StoryBox h3 {color:
        .StoryBoxText {color:rgba(255,255,255,0.5);line-height:1.8;font-size:0.95rem;}

        .label-tag {display:inline-block;padding:0.15rem 0.8rem;border-radius:20px;font-size:0.7rem;margin:0 0.2rem;vertical-align:middle;}
        .label-movie {background:rgba(52,152,219,0.15);color:
        .label-series {background:rgba(46,204,113,0.15);color:

        .controls-row {display:flex;gap:0.5rem;flex-wrap:wrap;align-items:center;justify-content:center;margin-bottom:0.8rem;}
        .ep-label {color:rgba(255,255,255,0.3);font-size:0.85rem;margin-left:0.5rem;}

        @media (max-width:768px) {
            .header-section {padding:0.6rem 1rem;flex-direction:column;align-items:stretch;}
            .header-search {max-width:100%;}
            .movie-title {font-size:1.1rem;}
            .server-btn {padding:0.4rem 0.8rem;font-size:0.75rem;}
            .servers-container {gap:0.3rem;padding:0.6rem;}
            .movie-details-grid {grid-template-columns:1fr 1fr;}
            .back-btn {align-self:center;}
        }
        @media (max-width:480px) {
            .movie-details-grid {grid-template-columns:1fr;}
            .logo-text .study {font-size:1rem;}
            .logo-text .movies {font-size:0.8rem;}
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header-section">
            <a href="/" class="logo">
                <i class="fas fa-film logo-icon"></i>
                <div class="logo-text">
                    <span class="study">Study</span>
                    <span class="movies">Movies <span>✦</span></span>
                </div>
            </a>
            <div class="header-search">
                <input type="text" id="headerSearchInput" placeholder="ابحث عن فيلم أو مسلسل...">
                <button id="headerSearchBtn"><i class="fas fa-search"></i></button>
            </div>
            <a href="/" class="back-btn"><i class="fas fa-arrow-right"></i> العودة</a>
        </div>

        <h1 class="movie-title">$title <span class="label-tag $type_class">$type_label</span></h1>

        <div class="video-container" id="videoContainer">
            <div class="video-wrapper" id="videoWrapper">
                <video id="videoPlayer" playsinline webkit-playsinline></video>
                <div class="loading-spinner" id="loadingSpinner">جاري التحميل...</div>

                <!-- Video Controls -->
                <div class="video-controls" id="videoControls">
                    <button class="video-controls-btn" id="playPauseBtn" title="تشغيل/إيقاف">
                        <svg viewBox="0 0 24 24"><path d="M8 5v14l11-7z"/></svg>
                    </button>

                    <div class="video-progress" id="videoProgress">
                        <div class="video-progress-buffer" id="progressBuffer"></div>
                        <div class="video-progress-bar" id="progressBar"></div>
                    </div>

                    <div class="video-time" id="videoTime">0:00 / 0:00</div>

                    <div class="volume-control">
                        <button class="video-controls-btn" id="muteBtn" title="كتم/تشغيل الصوت">
                            <svg viewBox="0 0 24 24"><path d="M3 9v6h4l5 5V4L7 9H3zm13.5 3c0-1.77-1.02-3.29-2.5-4.03v8.05c1.48-.73 2.5-2.25 2.5-4.02zM14 3.23v2.06c2.89.86 5 3.54 5 6.71s-2.11 5.85-5 6.71v2.06c4.01-.91 7-4.49 7-8.77s-2.99-7.86-7-8.77z"/></svg>
                        </button>
                        <input type="range" class="volume-slider" id="volumeSlider" min="0" max="1" step="0.1" value="1">
                    </div>

                    <div class="quality-selector">
                        <button class="quality-btn" id="qualityBtn">
                            <span>HD</span>
                            <svg viewBox="0 0 24 24" width="12" height="12" fill="currentColor"><path d="M7 10l5 5.5L17 10H7z"/></svg>
                        </button>
                        <div class="quality-menu" id="qualityMenu">
                            <div class="quality-option active" data-level="-1">Auto</div>
                        </div>
                    </div>

                    <button class="video-controls-btn" id="fullscreenBtn" title="ملء الشاشة">
                        <svg viewBox="0 0 24 24"><path d="M7 14H5v5h5v-2H7v-3zm-2-4h2V7h3V5H5v5zm12 7h-3v2h5v-5h-2v3zM14 5v2h3v3h2V5h-5z"/></svg>
                    </button>
                </div>
            </div>
        </div>

        $servers_html

        $episodes_html

        <div class="movie-info">
            <h3>↩︎ معلومات $type_label</h3>
            <div class="movie-details-grid">
                $details_html
            </div>
            $story_html
        </div>
    </div>

    <script>
        function performHeaderSearch() {
            const query = document.getElementById('headerSearchInput').value.trim();
            if (query) {
                window.location.href = '/?q=' + encodeURIComponent(query);
            }
        }

        // Add event listeners instead of inline onclick
        document.addEventListener('DOMContentLoaded', function() {
            const searchBtn = document.getElementById('headerSearchBtn');
            if (searchBtn) {
                searchBtn.addEventListener('click', performHeaderSearch);
            }

            const searchInput = document.getElementById('headerSearchInput');
            if (searchInput) {
                searchInput.addEventListener('keypress', function(e) {
                    if (e.key === 'Enter') {
                        performHeaderSearch();
                    }
                });
            }
        });

        const servers = $servers_json;
        let currentServer = 0;
        let workingServer = -1;

        async function testServer(url) {
            try {
                // Skip server testing in Discord Activity due to CSP restrictions
                // Just return true to allow server selection
                return true;
            } catch (e) {
                return false;
            }
        }

        async function findWorkingServer() {
            const buttons = document.querySelectorAll('.server-btn');
            let workingIndex = -1;

            const indices = Array.from({length: servers.length}, (_, i) => i);
            for (let i = indices.length - 1; i > 0; i--) {
                const j = Math.floor(Math.random() * (i + 1));
                [indices[i], indices[j]] = [indices[j], indices[i]];
            }

            for (const i of indices) {
                if (i >= buttons.length) continue;
                buttons[i].classList.add('loading');
                buttons[i].innerHTML = '⏳ جاري الاختبار...';

                const isWorking = await testServer(servers[i]);

                if (isWorking) {
                    buttons[i].classList.remove('loading');
                    buttons[i].classList.add('working');
                    buttons[i].innerHTML = '✅ سيرفر ' + (i + 1) + ' <span class="server-status">(يعمل)</span>';
                    workingIndex = i;
                    break;
                } else {
                    buttons[i].classList.remove('loading');
                    buttons[i].classList.add('broken');
                    buttons[i].innerHTML = '❌ سيرفر ' + (i + 1) + ' <span class="server-status">(لا يعمل)</span>';
                }
            }

            if (workingIndex === -1 && servers.length > 0) {
                workingIndex = 0;
                if (buttons[0]) {
                    buttons[0].classList.add('auto-selected');
                    buttons[0].innerHTML = '⚠️ سيرفر 1 <span class="server-status">(تجريبي)</span>';
                }
            }

            return workingIndex;
        }

        function changeServer(index) {
            currentServer = index;
            loadVideo(servers[index]);
            document.querySelectorAll('.server-btn').forEach((btn, i) => {
                btn.classList.remove('active');
                if (i === index) {
                    btn.classList.add('active');
                }
            });
        }

        async function loadVideo(embedUrl) {
            const video = document.getElementById('videoPlayer');
            const spinner = document.getElementById('loadingSpinner');

            if (!video) return;

            spinner.style.display = 'flex';
            video.pause();
            video.src = '';

            try {
                // Extract media URL from embed page
                const response = await fetch('/extract-media?url=' + encodeURIComponent(embedUrl));
                const data = await response.json();

                if (data.error) {
                    spinner.innerHTML = '❌ ' + data.error;
                    return;
                }

                if (!data.media_url) {
                    // If extraction failed, show error (no window.open in Discord Activity)
                    spinner.innerHTML = '❌ لا يمكن استخراج رابط الفيديو';
                    return;
                }

                // Load video based on type
                if (data.type === 'hls') {
                    console.log('[HLS] Loading HLS URL:', data.media_url);
                    console.log('[HLS] HLS.js supported:', Hls.isSupported());

                    if (Hls.isSupported()) {
                        // Use HLS.js for Chromium-based browsers (Discord Activity)
                        const hls = new Hls({
                            debug: false,
                            enableWorker: true,
                            lowLatencyMode: false,
                            // Adaptive Bitrate Settings
                            abrEwmaFastLive: 3.0,
                            abrEwmaSlowLive: 9.0,
                            abrEwmaFastVoD: 3.0,
                            abrEwmaSlowVoD: 9.0,
                            abrEwmaDefaultEstimate: 500000,
                            abrBandwidthFactor: 0.95,
                            abrBandwidthUpFactor: 0.7,
                            abrMaxWithRealBitrate: false,
                            // Buffer Settings for smooth playback
                            maxBufferLength: 30,
                            maxMaxBufferLength: 60,
                            maxBufferSize: 60 * 1000 * 1000,
                            maxBufferHole: 0.5,
                            // Fragment loading
                            maxFragLookUpTolerance: 0.25,
                            // Network recovery
                            manifestLoadingTimeOut: 10000,
                            manifestLoadingMaxRetry: 4,
                            levelLoadingTimeOut: 10000,
                            levelLoadingMaxRetry: 4,
                            fragLoadingTimeOut: 20000,
                            fragLoadingMaxRetry: 6,
                            // Start with auto quality
                            startLevel: -1,
                        });

                        hls.loadSource(data.media_url);
                        hls.attachMedia(video);

                        // Store hls instance globally for quality switching
                        window.currentHls = hls;

                        hls.on(Hls.Events.MANIFEST_PARSED, function(event, data) {
                            console.log('[HLS] Manifest parsed successfully');
                            spinner.style.display = 'none';

                            // Populate quality levels
                            const qualityMenu = document.getElementById('qualityMenu');
                            qualityMenu.innerHTML = '<div class="quality-option active" data-level="-1">Auto</div>';

                            if (hls.levels.length > 0) {
                                hls.levels.forEach((level, index) => {
                                    const levelHeight = level.height || 'Unknown';
                                    const bitrate = Math.round(level.bitrate / 1000);
                                    const option = document.createElement('div');
                                    option.className = 'quality-option';
                                    option.dataset.level = index;
                                    option.textContent = levelHeight + 'p (' + bitrate + 'k)';
                                    option.addEventListener('click', () => {
                                        hls.currentLevel = index;
                                        document.querySelectorAll('.quality-option').forEach(opt => opt.classList.remove('active'));
                                        option.classList.add('active');
                                        document.querySelector('#qualityBtn span').textContent = levelHeight + 'p';
                                    });
                                    qualityMenu.appendChild(option);
                                });
                            }

                            video.play().catch(e => {
                                console.log('[HLS] Autoplay prevented:', e);
                                // Try to play with user interaction
                                document.addEventListener('click', function playHandler() {
                                    video.play().catch(err => console.log('[HLS] Play failed:', err));
                                    document.removeEventListener('click', playHandler);
                                }, { once: true });
                            });
                        });

                        hls.on(Hls.Events.ERROR, function(event, data) {
                            console.error('[HLS] Error:', event, data);
                            if (data.fatal) {
                                switch (data.type) {
                                    case Hls.ErrorTypes.NETWORK_ERROR:
                                        console.error('[HLS] Network error:', data);
                                        spinner.innerHTML = '❌ خطأ في الشبكة';
                                        hls.startLoad();
                                        break;
                                    case Hls.ErrorTypes.MEDIA_ERROR:
                                        console.error('[HLS] Media error:', data);
                                        spinner.innerHTML = '❌ خطأ في الوسائط';
                                        hls.recoverMediaError();
                                        break;
                                    default:
                                        console.error('[HLS] Fatal error:', data);
                                        spinner.innerHTML = '❌ خطأ في تحميل الفيديو HLS';
                                        hls.destroy();
                                        break;
                                }
                            }
                        });
                    } else if (video.canPlayType('application/vnd.apple.mpegurl')) {
                        // Native HLS support (Safari)
                        video.src = data.media_url;
                        video.addEventListener('loadedmetadata', function() {
                            spinner.style.display = 'none';
                            video.play().catch(e => console.log('Autoplay prevented:', e));
                        });
                        video.addEventListener('error', function() {
                            spinner.innerHTML = '❌ خطأ في تحميل الفيديو HLS';
                        });
                    } else {
                        // HLS not supported
                        spinner.innerHTML = '❌ متصفحك لا يدعم HLS';
                    }
                } else {
                    // MP4 direct playback
                    video.src = data.media_url;
                    video.addEventListener('loadedmetadata', function() {
                        spinner.style.display = 'none';
                        video.play().catch(e => console.log('Autoplay prevented:', e));
                    });
                    video.addEventListener('error', function() {
                        spinner.innerHTML = '❌ خطأ في تحميل الفيديو';
                    });
                }
            } catch (error) {
                spinner.innerHTML = '❌ خطأ في الاتصال';
                console.error('Error loading video:', error);
            }
        }

        document.addEventListener('DOMContentLoaded', async function() {
            // Video Controls
            const video = document.getElementById('videoPlayer');
            const playPauseBtn = document.getElementById('playPauseBtn');
            const progressBar = document.getElementById('progressBar');
            const videoProgress = document.getElementById('videoProgress');
            const videoTime = document.getElementById('videoTime');
            const volumeSlider = document.getElementById('volumeSlider');
            const muteBtn = document.getElementById('muteBtn');
            const fullscreenBtn = document.getElementById('fullscreenBtn');
            const qualityBtn = document.getElementById('qualityBtn');
            const qualityMenu = document.getElementById('qualityMenu');
            const videoContainer = document.getElementById('videoContainer');

            // Play/Pause
            playPauseBtn.addEventListener('click', () => {
                if (video.paused) {
                    video.play();
                    playPauseBtn.innerHTML = '<svg viewBox="0 0 24 24"><path d="M6 19h4V5H6v14zm8-14v14h4V5h-4z"/></svg>';
                } else {
                    video.pause();
                    playPauseBtn.innerHTML = '<svg viewBox="0 0 24 24"><path d="M8 5v14l11-7z"/></svg>';
                }
            });

            video.addEventListener('play', () => {
                playPauseBtn.innerHTML = '<svg viewBox="0 0 24 24"><path d="M6 19h4V5H6v14zm8-14v14h4V5h-4z"/></svg>';
            });

            video.addEventListener('pause', () => {
                playPauseBtn.innerHTML = '<svg viewBox="0 0 24 24"><path d="M8 5v14l11-7z"/></svg>';
            });

            // Progress Bar
            video.addEventListener('timeupdate', () => {
                const progress = (video.currentTime / video.duration) * 100;
                progressBar.style.width = progress + '%';

                // Update buffer progress
                if (video.buffered.length > 0) {
                    const bufferedEnd = video.buffered.end(video.buffered.length - 1);
                    const bufferProgress = (bufferedEnd / video.duration) * 100;
                    progressBuffer.style.width = bufferProgress + '%';
                }

                const current = formatTime(video.currentTime);
                const duration = formatTime(video.duration);
                videoTime.textContent = current + ' / ' + duration;
            });

            videoProgress.addEventListener('click', (e) => {
                const rect = videoProgress.getBoundingClientRect();
                const pos = (e.clientX - rect.left) / rect.width;
                video.currentTime = pos * video.duration;
            });

            // Add drag support for progress bar
            let isDragging = false;

            videoProgress.addEventListener('mousedown', (e) => {
                isDragging = true;
                updateProgress(e);
            });

            document.addEventListener('mousemove', (e) => {
                if (isDragging) {
                    updateProgress(e);
                }
            });

            document.addEventListener('mouseup', () => {
                if (isDragging) {
                    isDragging = false;
                }
            });

            function updateProgress(e) {
                const rect = videoProgress.getBoundingClientRect();
                let pos = (e.clientX - rect.left) / rect.width;
                pos = Math.max(0, Math.min(1, pos));
                video.currentTime = pos * video.duration;
            }

            // Volume
            volumeSlider.addEventListener('input', (e) => {
                video.volume = e.target.value;
                if (video.volume === 0) {
                    muteBtn.innerHTML = '<svg viewBox="0 0 24 24"><path d="M16.5 12c0-1.77-1.02-3.29-2.5-4.03v2.21l2.45 2.45c.03-.2.05-.41.05-.63zm2.5 0c0 .94-.2 1.82-.54 2.64l1.51 1.51C20.63 14.91 21 13.5 21 12c0-4.28-2.99-7.86-7-8.77v2.06c2.89.86 5 3.54 5 6.71zM4.27 3L3 4.27 7.73 9H3v6h4l5 5v-6.73l4.25 4.25c-.67.52-1.42.93-2.25 1.18v2.06c1.38-.31 2.63-.95 3.69-1.81L19.73 21 21 19.73l-9-9L4.27 3zM12 4L9.91 6.09 12 8.18V4z"/></svg>';
                } else {
                    muteBtn.innerHTML = '<svg viewBox="0 0 24 24"><path d="M3 9v6h4l5 5V4L7 9H3zm13.5 3c0-1.77-1.02-3.29-2.5-4.03v8.05c1.48-.73 2.5-2.25 2.5-4.02zM14 3.23v2.06c2.89.86 5 3.54 5 6.71s-2.11 5.85-5 6.71v2.06c4.01-.91 7-4.49 7-8.77s-2.99-7.86-7-8.77z"/></svg>';
                }
            });

            muteBtn.addEventListener('click', () => {
                if (video.volume > 0) {
                    video.dataset.volume = video.volume;
                    video.volume = 0;
                    volumeSlider.value = 0;
                    muteBtn.innerHTML = '<svg viewBox="0 0 24 24"><path d="M16.5 12c0-1.77-1.02-3.29-2.5-4.03v2.21l2.45 2.45c.03-.2.05-.41.05-.63zm2.5 0c0 .94-.2 1.82-.54 2.64l1.51 1.51C20.63 14.91 21 13.5 21 12c0-4.28-2.99-7.86-7-8.77v2.06c2.89.86 5 3.54 5 6.71zM4.27 3L3 4.27 7.73 9H3v6h4l5 5v-6.73l4.25 4.25c-.67.52-1.42.93-2.25 1.18v2.06c1.38-.31 2.63-.95 3.69-1.81L19.73 21 21 19.73l-9-9L4.27 3zM12 4L9.91 6.09 12 8.18V4z"/></svg>';
                } else {
                    video.volume = video.dataset.volume || 1;
                    volumeSlider.value = video.volume;
                    muteBtn.innerHTML = '<svg viewBox="0 0 24 24"><path d="M3 9v6h4l5 5V4L7 9H3zm13.5 3c0-1.77-1.02-3.29-2.5-4.03v8.05c1.48-.73 2.5-2.25 2.5-4.02zM14 3.23v2.06c2.89.86 5 3.54 5 6.71s-2.11 5.85-5 6.71v2.06c4.01-.91 7-4.49 7-8.77s-2.99-7.86-7-8.77z"/></svg>';
                }
            });

            // Quality Menu Toggle
            qualityBtn.addEventListener('click', (e) => {
                e.stopPropagation();
                qualityMenu.classList.toggle('active');
            });

            document.addEventListener('click', () => {
                qualityMenu.classList.remove('active');
            });

            // Fullscreen
            fullscreenBtn.addEventListener('click', () => {
                if (!document.fullscreenElement) {
                    videoContainer.classList.add('fullscreen');
                    if (videoContainer.requestFullscreen) {
                        videoContainer.requestFullscreen();
                    } else if (videoContainer.webkitRequestFullscreen) {
                        videoContainer.webkitRequestFullscreen();
                    }
                    // Show controls in fullscreen
                    videoControls.style.opacity = '1';
                } else {
                    videoContainer.classList.remove('fullscreen');
                    if (document.exitFullscreen) {
                        document.exitFullscreen();
                    } else if (document.webkitExitFullscreen) {
                        video.webkitExitFullscreen();
                    }
                }
            });

            document.addEventListener('fullscreenchange', () => {
                if (!document.fullscreenElement) {
                    videoContainer.classList.remove('fullscreen');
                    videoControls.style.opacity = '';
                } else {
                    videoControls.style.opacity = '1';
                }
            });

            // Show controls on video mouse move in fullscreen
            let controlsTimeout;
            video.addEventListener('mousemove', () => {
                if (document.fullscreenElement) {
                    videoControls.style.opacity = '1';
                    clearTimeout(controlsTimeout);
                    controlsTimeout = setTimeout(() => {
                        if (!video.paused) {
                            videoControls.style.opacity = '0';
                        }
                    }, 3000);
                }
            });

            // Show controls when video is paused
            video.addEventListener('pause', () => {
                if (document.fullscreenElement) {
                    videoControls.style.opacity = '1';
                }
            });

            video.addEventListener('play', () => {
                if (document.fullscreenElement) {
                    clearTimeout(controlsTimeout);
                    controlsTimeout = setTimeout(() => {
                        videoControls.style.opacity = '0';
                    }, 3000);
                }
            });

            // Format time helper
            function formatTime(seconds) {
                if (isNaN(seconds)) return '0:00';
                const mins = Math.floor(seconds / 60);
                const secs = Math.floor(seconds % 60);
                return mins + ':' + (secs < 10 ? '0' : '') + secs;
            }

            // Add event listeners to server buttons
            document.querySelectorAll('.server-btn').forEach((btn, index) => {
                btn.addEventListener('click', function() {
                    changeServer(index);
                });
            });

            // Add event listeners to episode buttons
            document.querySelectorAll('.episode-btn').forEach(btn => {
                btn.addEventListener('click', function() {
                    const vid = this.getAttribute('data-vid');
                    window.location.href = '/watch?vid=' + vid;
                });
            });

            // Add error handlers for images
            document.querySelectorAll('img').forEach(img => {
                img.addEventListener('error', function() {
                    this.src = 'data:image/svg+xml,%3Csvg xmlns=%22http://www.w3.org/2000/svg%22 width=%22240%22 height=%22170%22%3E%3Crect fill=%22%231a1a2e%22 width=%22240%22 height=%22170%22/%3E%3Ctext x=%2250%25%22 y=%2250%25%22 text-anchor=%22middle%22 dy=%22.3em%22 fill=%22%23666%22 font-size=%2220%22%3E🎬%3C/text%3E%3C/svg%3E';
                });
            });

            // Load first video
            if (servers.length > 0) {
                loadVideo(servers[0]);
            }
        });
    </script>
</body>
</html>""")

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
        self.discord_app_id = os.getenv('DISCORD_APP_ID', '')

    async def setup_hook(self):
        print('⚠️ Skipping automatic command sync to avoid Entry Point conflicts')
        print('⚠️ If commands don\'t appear, sync them manually in Discord Developer Portal')

    async def on_ready(self):
        print(f'✅ Discord Bot logged in as {self.user.name}')
        print(f'🌐 Web URL: {self.web_url}')
        if self.discord_app_id:
            activity_url = f'https://discord.com/application-directory/{self.discord_app_id}'
            print(f'🎮 Discord Activity URL: {activity_url}')

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
                watch_url = f'{self.web_url}/watch?vid={movie_vid}'
                embed.add_field(
                    name=f'{movie_title}',
                    value=f'📅 {movie_year} | 🎭 {movie_type}\n[🎥 شاهد الآن]({watch_url})',
                    inline=False
                )

        embed.set_footer(text='Study Movies - أفضل تجربة مشاهدة')
        await interaction.followup.send(embed=embed)

    @app_commands.command(name='movie', description='افتح فيلم مباشرة في Discord Activity')
    async def movie(self, interaction: discord.Interaction, vid: str):
        await interaction.response.defer()

        movie_info = await self.movie_bot.get_movie_servers(vid)

        if 'error' in movie_info:
            await interaction.followup.send(f'❌ {movie_info["error"]}')
            return

        title = movie_info.get('title', 'فيلم')
        watch_url = f'{self.web_url}/watch?vid={vid}'

        embed = discord.Embed(
            title=f'🎬 {title}',
            description='اضغط على الزر لفتح الفيلم في Discord Activity',
            color=0xe94560
        )

        if self.discord_app_id:
            activity_url = f'https://discord.com/application-directory/{self.discord_app_id}/store'
            view = discord.ui.View()
            button = discord.ui.Button(
                label='🎮 افتح في Discord Activity',
                style=discord.ButtonStyle.url,
                url=watch_url
            )
            view.add_item(button)
            await interaction.followup.send(embed=embed, view=view)
        else:
            await interaction.followup.send(f'🎥 شاهد الآن: {watch_url}')

    @app_commands.command(name='new', description='عرض جديد الأفلام')
    async def new(self, interaction: discord.Interaction):
        await interaction.response.defer()

        result = await self.movie_bot.get_new_movies()

        if 'error' in result:
            await interaction.followup.send(f'❌ {result["error"]}')
            return

        movies = result.get('results', [])
        if not movies:
            await interaction.followup.send('😕 لا توجد أفلام جديدة')
            return

        embed = discord.Embed(
            title='🌟 جديد الأفلام',
            color=0xe94560
        )

        for movie in movies[:5]:
            movie_title = movie.get('title', 'غير معروف')
            movie_vid = movie.get('vid', '')

            if movie_vid:
                watch_url = f'{self.web_url}/watch?vid={movie_vid}'
                embed.add_field(
                    name=movie_title,
                    value=f'[🎥 شاهد الآن]({watch_url})',
                    inline=False
                )

        embed.set_footer(text='Study Movies - أفضل تجربة مشاهدة')
        await interaction.followup.send(embed=embed)

    @app_commands.command(name='activity', description='احصل على رابط Discord Activity')
    async def activity(self, interaction: discord.Interaction):
        if self.discord_app_id:
            activity_url = f'https://discord.com/application-directory/{self.discord_app_id}/store'
            embed = discord.Embed(
                title='🎮 Discord Activity',
                description='افتح الموقع في Discord Activity لمشاهدة الأفلام مع أصدقائك',
                color=0x5865F2
            )
            embed.add_field(name='رابط النشاط', value=f'[اضغط هنا لفتح Activity]({activity_url})', inline=False)
            embed.add_field(name='رابط الموقع المباشر', value=f'[افتح الموقع]({self.web_url})', inline=False)
            await interaction.response.send_message(embed=embed)
        else:
            await interaction.response.send_message(f'🎥 رابط الموقع: {self.web_url}')

    @app_commands.command(name='launch', description='افتح موقع الأفلام')
    async def launch(self, interaction: discord.Interaction):
        """Entry point command for Discord Activity"""
        embed = discord.Embed(
            title='🎬 Study Movies',
            description='افتح الموقع لمشاهدة الأفلام',
            color=0xe94560
        )
        embed.add_field(name='رابط الموقع', value=f'[🎥 افتح الموقع]({self.web_url})', inline=False)

        view = discord.ui.View()
        button = discord.ui.Button(
            label='🎬 افتح الموقع',
            style=discord.ButtonStyle.url,
            url=self.web_url
        )
        view.add_item(button)

        await interaction.response.send_message(embed=embed, view=view)

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

class PlaywrightHLSSessionManager:
    def __init__(self):
        self.sessions = {}
        self.session_lock = asyncio.Lock()
        self.playwright = None

    async def get_playwright(self):
        """Get or create Playwright instance"""
        if self.playwright is None:
            from playwright.async_api import async_playwright
            self.playwright = await async_playwright().start()
        return self.playwright

    async def get_or_create_session(self, embed_url):
        """Get or create a persistent browser session for the given embed URL"""
        async with self.session_lock:
            if embed_url not in self.sessions:
                print(f"[Playwright HLS Manager] Creating persistent browser session for: {embed_url}")
                start_time = asyncio.get_event_loop().time()

                try:
                    playwright = await self.get_playwright()

                    browser = await playwright.chromium.launch(
                        headless=True,
                        args=[
                            '--no-sandbox',
                            '--disable-setuid-sandbox',
                            '--disable-dev-shm-usage',
                            '--disable-blink-features=AutomationControlled',
                            '--disable-features=IsolateOrigins,site-per-process',
                        ]
                    )

                    context = await browser.new_context(
                        viewport={'width': 1920, 'height': 1080},
                        user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                        locale='en-US',
                        timezone_id='America/New_York',
                        java_script_enabled=True,
                        ignore_https_errors=True,
                    )

                    page = await context.new_page()

                    request_log = []
                    response_log = []

                    async def log_request(request):
                        request_data = {
                            'url': request.url,
                            'method': request.method,
                            'headers': dict(request.headers),
                            'resource_type': request.resource_type,
                            'timestamp': asyncio.get_event_loop().time(),
                        }
                        request_log.append(request_data)
                        if '.m3u8' in request.url or '.ts' in request.url:
                            print(f"[Playwright] Request: {request.method} {request.url}")
                            print(f"[Playwright] Headers: {dict(request.headers)}")

                    async def log_response(response):
                        response_data = {
                            'url': response.url,
                            'status': response.status,
                            'headers': dict(response.headers),
                            'timestamp': asyncio.get_event_loop().time(),
                        }
                        response_log.append(response_data)
                        if '.m3u8' in response.url or '.ts' in response.url:
                            print(f"[Playwright] Response: {response.status} {response.url}")
                            print(f"[Playwright] Headers: {dict(response.headers)}")

                    page.on('request', log_request)
                    page.on('response', log_response)

                    print(f"[Playwright] Navigating to embed page: {embed_url}")
                    nav_start = asyncio.get_event_loop().time()
                    await page.goto(embed_url, wait_until='networkidle', timeout=30000)
                    nav_time = asyncio.get_event_loop().time() - nav_start
                    print(f"[Playwright] Page loaded in {nav_time:.2f}s")

                    await asyncio.sleep(3)

                    cookies = await context.cookies()
                    cookie_header = '; '.join([f"{c['name']}={c['value']}" for c in cookies])
                    print(f"[Playwright] Cookies captured: {len(cookies)}")
                    print(f"[Playwright] Cookie header: {cookie_header[:200]}...")

                    local_storage = await page.evaluate('() => JSON.stringify(localStorage)')

                    session_time = asyncio.get_event_loop().time() - start_time
                    print(f"[Playwright] Session created in {session_time:.2f}s")

                    self.sessions[embed_url] = {
                        'browser': browser,
                        'context': context,
                        'page': page,
                        'cookies': cookie_header,
                        'local_storage': local_storage,
                        'referer': embed_url,
                        'request_log': request_log,
                        'response_log': response_log,
                        'created_at': asyncio.get_event_loop().time(),
                    }

                    print(f"[Playwright HLS Manager] Persistent browser session created successfully")

                except Exception as e:
                    print(f"[Playwright HLS Manager] Error creating session: {e}")
                    import traceback
                    traceback.print_exc()
                    if embed_url in self.sessions:
                        await self.close_session(embed_url)
                    raise

            return self.sessions[embed_url]

    async def close_session(self, embed_url):
        """Close a browser session for the given embed URL"""
        async with self.session_lock:
            if embed_url in self.sessions:
                session_data = self.sessions[embed_url]
                try:
                    await session_data['page'].close()
                    await session_data['context'].close()
                    await session_data['browser'].close()
                except Exception as e:
                    print(f"[Playwright HLS Manager] Error closing session: {e}")
                del self.sessions[embed_url]
                print(f"[Playwright HLS Manager] Closed session for: {embed_url}")

    async def close_all(self):
        """Close all browser sessions"""
        async with self.session_lock:
            for embed_url, session_data in list(self.sessions.items()):
                try:
                    await session_data['page'].close()
                    await session_data['context'].close()
                    await session_data['browser'].close()
                except Exception as e:
                    print(f"[Playwright HLS Manager] Error closing session: {e}")
            self.sessions.clear()

            if self.playwright:
                await self.playwright.stop()
                self.playwright = None

            print("[Playwright HLS Manager] Closed all sessions")

    async def fetch_hls_with_browser(self, embed_url, hls_url):
        """
        Fetch HLS content using Playwright's browser context.
        This preserves exact browser fingerprint (TLS, HTTP/2, TCP stack).
        """
        session_data = await self.get_or_create_session(embed_url)
        context = session_data['context']
        page = session_data['page']

        print(f"[Playwright HLS] Fetching: {hls_url}")
        print(f"[Playwright HLS] Full URL preserved: {hls_url}")
        print(f"[Playwright HLS] Query params: {hls_url.split('?')[1] if '?' in hls_url else 'None'}")

        start_time = asyncio.get_event_loop().time()

        try:
            api_request = context.request

            response = await api_request.get(
                hls_url,
                headers={
                    'Accept': '*/*',
                    'Referer': session_data['referer'],
                }
            )

            fetch_time = asyncio.get_event_loop().time() - start_time

            status = response.status
            headers = dict(response.headers)
            body = await response.body()

            print(f"[Playwright HLS] Response status: {status}")
            print(f"[Playwright HLS] Response headers: {headers}")
            print(f"[Playwright HLS] Content length: {len(body)}")
            print(f"[Playwright HLS] Fetch time: {fetch_time:.2f}s")

            if status != 200:
                print(f"[Playwright HLS] ERROR: Non-200 status")
                print(f"[Playwright HLS] Response body: {body[:500]}")

            return {
                'status': status,
                'headers': headers,
                'body': body,
                'content_type': headers.get('content-type', 'application/vnd.apple.mpegurl'),
                'fetch_time': fetch_time,
            }
        except Exception as e:
            print(f"[Playwright HLS] Error fetching: {e}")
            import traceback
            traceback.print_exc()
            raise

playwright_session_manager = PlaywrightHLSSessionManager()

async def extract_media_url(embed_url):
    """Extract actual media URL from embed page using persistent Playwright browser session"""
    try:
        print(f"[Extract Media] Using persistent Playwright browser session for: {embed_url}")

        session_data = await playwright_session_manager.get_or_create_session(embed_url)
        page = session_data['page']

        content = await page.content()
        print(f"[Extract Media] Page content length: {len(content)}")

        import html
        content_decoded = html.unescape(content)
        print(f"[Extract Media] HTML entities decoded")

        import re

        mp4_patterns = [
            r'(https?://[^\s"\'<>]+\.mp4[^\s"\'<>]*)',
            r'file:\s*["\']([^"\']+\.mp4[^"\']*)["\']',
            r'source:\s*["\']([^"\']+\.mp4[^"\']*)["\']',
        ]

        for pattern in mp4_patterns:
            matches = re.findall(pattern, content_decoded, re.IGNORECASE)
            if matches:
                print(f"[Extract Media] Found MP4 URL: {matches[0]}")
                print(f"[Extract Media] URL query params: {matches[0].split('?')[1] if '?' in matches[0] else 'None'}")
                return {
                    'type': 'mp4',
                    'url': matches[0],
                    'referer': embed_url,
                }

        m3u8_patterns = [
            r'(https?://[^\s"\'<>]+\.m3u8[^\s"\'<>]*)',
            r'file:\s*["\']([^"\']+\.m3u8[^"\']*)["\']',
            r'source:\s*["\']([^"\']+\.m3u8[^"\']*)["\']',
        ]

        for pattern in m3u8_patterns:
            matches = re.findall(pattern, content_decoded, re.IGNORECASE)
            if matches:
                print(f"[Extract Media] Found HLS URL: {matches[0]}")
                print(f"[Extract Media] URL query params: {matches[0].split('?')[1] if '?' in matches[0] else 'None'}")
                return {
                    'type': 'hls',
                    'url': matches[0],
                    'referer': embed_url,
                }

        json_patterns = [
            r'"url":\s*"([^"]+)"',
            r'"file":\s*"([^"]+)"',
            r'"source":\s*"([^"]+)"',
        ]

        for pattern in json_patterns:
            matches = re.findall(pattern, content_decoded)
            for match in matches:
                if '.mp4' in match or '.m3u8' in match:
                    media_type = 'hls' if '.m3u8' in match else 'mp4'
                    print(f"[Extract Media] Found {media_type.upper()} URL in JSON: {match}")
                    print(f"[Extract Media] URL query params: {match.split('?')[1] if '?' in match else 'None'}")
                    return {
                        'type': media_type,
                        'url': match,
                        'referer': embed_url,
                    }

        print(f"[Extract Media] No media URL found in page content")
        return None

    except Exception as e:
        print(f"Error extracting media URL: {e}")
        import traceback
        traceback.print_exc()
        return None

async def handle_extract_media(request):
    """API endpoint to extract media URL from embed page"""
    embed_url = request.query.get('url', '').strip()
    if not embed_url:
        return web.json_response({"error": "لم يتم تحديد الرابط"}, status=400)

    try:
        print(f"[Extract Media] Processing URL: {embed_url}")
        media_info = await extract_media_url(embed_url)
        print(f"[Extract Media] Result: {media_info}")

        if media_info:
            if media_info['type'] == 'hls':
                from urllib.parse import quote
                hls_url = media_info["url"]
                print(f"[Extract Media] Original HLS URL: {hls_url}")
                print(f"[Extract Media] HLS URL query params: {hls_url.split('?')[1] if '?' in hls_url else 'None'}")

                encoded_hls_url = quote(hls_url, safe='')
                print(f"[Extract Media] Encoded HLS URL: {encoded_hls_url}")

                proxy_url = f'/hls-proxy?url={encoded_hls_url}&embed={embed_url}'
                print(f"[Extract Media] HLS detected, returning proxy: {proxy_url}")
                return web.json_response({
                    "media_url": proxy_url,
                    "type": media_info['type'],
                    "is_proxied": True,
                    "embed_url": embed_url
                })
            print(f"[Extract Media] MP4 detected, returning direct: {media_info['url']}")
            return web.json_response({
                "media_url": media_info['url'],
                "type": media_info['type'],
                "is_proxied": False
            })
        else:
            print(f"[Extract Media] No media URL found")
            return web.json_response({
                "media_url": None,
                "type": None,
                "message": "Could not extract media URL"
            })
    except Exception as e:
        print(f"[Extract Media] Error: {e}")
        import traceback
        traceback.print_exc()
        return web.json_response({"error": str(e)}, status=500)

async def handle_hls_proxy(request):
    """HLS manifest proxy using Playwright browser context (production-grade)"""
    from urllib.parse import unquote, urlparse, urljoin, quote

    manifest_url_encoded = request.query.get('url', '').strip()
    embed_url = request.query.get('embed', '').strip()

    if not manifest_url_encoded:
        return web.Response(text="لم يتم تحديد الرابط", status=400)

    if not embed_url:
        return web.Response(text="Embed URL required for session management", status=400)

    try:
        manifest_url = unquote(manifest_url_encoded)

        print(f"[HLS Proxy] Encoded URL received: {manifest_url_encoded}")
        print(f"[HLS Proxy] Decoded URL: {manifest_url}")
        print(f"[HLS Proxy] Original embed URL: {embed_url}")
        print(f"[HLS Proxy] Query params preserved: {manifest_url.split('?')[1] if '?' in manifest_url else 'None'}")

        result = await playwright_session_manager.fetch_hls_with_browser(embed_url, manifest_url)

        if result['status'] != 200:
            print(f"[HLS Proxy] ERROR: HTTP {result['status']}")
            print(f"[HLS Proxy] Response body: {result['body'][:500]}")
            print(f"[HLS Proxy] Response headers: {result['headers']}")
            return web.Response(text=f"خطأ في تحميل HLS manifest: HTTP {result['status']}", status=result['status'])

        content = result['body'].decode('utf-8') if isinstance(result['body'], bytes) else result['body']
        content_type = result.get('content_type', 'application/vnd.apple.mpegurl')

        print(f"[HLS Proxy] Response status: {result['status']}")
        print(f"[HLS Proxy] Response content-type: {content_type}")
        print(f"[HLS Proxy] Content length: {len(content)}")
        print(f"[HLS Proxy] Fetch time: {result.get('fetch_time', 0):.2f}s")

        parsed_url = urlparse(manifest_url)
        base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
        base_path = manifest_url.rsplit('/', 1)[0] if '/' in manifest_url else base_url
        print(f"[HLS Proxy] Base URL: {base_url}, Base Path: {base_path}")

        lines = content.split('\n')
        rewritten_lines = []

        for line in lines:
            line = line.strip()
            if not line or line.startswith('#'):
                rewritten_lines.append(line)
                continue

            if line.startswith('http'):
                encoded_line = quote(line, safe='')
                proxied_url = f'/segment-proxy?url={encoded_line}&embed={embed_url}'
                rewritten_lines.append(proxied_url)
                print(f"[HLS Proxy] Rewrote absolute: {line} -> {proxied_url}")
            elif not line.startswith('#') and '.' in line:
                absolute_url = urljoin(base_url + '/', line)
                encoded_absolute = quote(absolute_url, safe='')
                proxied_url = f'/segment-proxy?url={encoded_absolute}&embed={embed_url}'
                rewritten_lines.append(proxied_url)
                print(f"[HLS Proxy] Rewrote relative: {line} -> {absolute_url} -> {proxied_url}")
            else:
                rewritten_lines.append(line)

        rewritten_content = '\n'.join(rewritten_lines)
        print(f"[HLS Proxy] Rewritten content length: {len(rewritten_content)}")

        response_headers = {
            'Content-Type': content_type,
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'GET, OPTIONS',
            'Access-Control-Allow-Headers': '*',
            'Cache-Control': 'no-cache',
        }

        return web.Response(
            text=rewritten_content,
            headers=response_headers
        )
    except Exception as e:
        print(f"[HLS Proxy] Error: {e}")
        import traceback
        traceback.print_exc()
        return web.Response(text=f"خطأ في تحميل HLS manifest: {str(e)}", status=500)

async def handle_segment_proxy(request):
    """Proxy for HLS segments and sub-playlists using Playwright browser context (production-grade)"""
    from urllib.parse import unquote, urlparse, quote, urljoin

    segment_url_encoded = request.query.get('url', '').strip()
    embed_url = request.query.get('embed', '').strip()

    if not segment_url_encoded:
        return web.Response(text="لم يتم تحديد الرابط", status=400)

    if not embed_url:
        return web.Response(text="Embed URL required for session management", status=400)

    try:
        segment_url = unquote(segment_url_encoded)

        print(f"[Segment Proxy] Encoded URL received: {segment_url_encoded}")
        print(f"[Segment Proxy] Decoded URL: {segment_url}")
        print(f"[Segment Proxy] Embed URL: {embed_url}")
        print(f"[Segment Proxy] Query params preserved: {segment_url.split('?')[1] if '?' in segment_url else 'None'}")

        is_playlist = '.m3u8' in segment_url.lower()

        result = await playwright_session_manager.fetch_hls_with_browser(embed_url, segment_url)

        if result['status'] != 200:
            print(f"[Segment Proxy] ERROR: HTTP {result['status']}")
            print(f"[Segment Proxy] Response body: {result['body'][:500]}")
            print(f"[Segment Proxy] Response headers: {result['headers']}")
            return web.Response(text=f"خطأ في تحميل segment: HTTP {result['status']}", status=result['status'])

        content = result['body']
        content_type = result.get('content_type', 'video/mp2t')

        print(f"[Segment Proxy] Response status: {result['status']}")
        print(f"[Segment Proxy] Response content-type: {content_type}")
        print(f"[Segment Proxy] Content size: {len(content)}")
        print(f"[Segment Proxy] Fetch time: {result.get('fetch_time', 0):.2f}s")
        print(f"[Segment Proxy] Is playlist: {is_playlist}")

        if is_playlist:
            content_text = content.decode('utf-8') if isinstance(content, bytes) else content

            parsed_url = urlparse(segment_url)
            base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
            base_path = segment_url.rsplit('/', 1)[0] if '/' in segment_url else base_url

            print(f"[Segment Proxy] Rewriting sub-playlist TS segments")
            print(f"[Segment Proxy] Base URL: {base_url}, Base Path: {base_path}")

            lines = content_text.split('\n')
            rewritten_lines = []

            for line in lines:
                line = line.strip()
                if not line or line.startswith('#'):
                    rewritten_lines.append(line)
                    continue

                if any(ext in line.lower() for ext in ['.ts', '.m4s', '.aac', '.mp4']):
                    if line.startswith('http'):
                        encoded_line = quote(line, safe='')
                        proxied_url = f'/segment-proxy?url={encoded_line}&embed={embed_url}'
                        rewritten_lines.append(proxied_url)
                        print(f"[Segment Proxy] Rewrote TS: {line} -> {proxied_url}")
                    else:
                        absolute_url = urljoin(base_url + '/', line)
                        encoded_absolute = quote(absolute_url, safe='')
                        proxied_url = f'/segment-proxy?url={encoded_absolute}&embed={embed_url}'
                        rewritten_lines.append(proxied_url)
                        print(f"[Segment Proxy] Rewrote relative TS: {line} -> {absolute_url} -> {proxied_url}")
                else:
                    rewritten_lines.append(line)

            content = '\n'.join(rewritten_lines).encode('utf-8')
            content_type = 'application/vnd.apple.mpegurl'
            print(f"[Segment Proxy] Rewritten sub-playlist length: {len(content)}")

        response_headers = {
            'Content-Type': content_type,
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'GET, OPTIONS',
            'Access-Control-Allow-Headers': '*',
            'Cache-Control': 'public, max-age=3600',
        }

        if result['headers'] and 'content-range' in result['headers']:
            response_headers['Content-Range'] = result['headers']['content-range']

        return web.Response(
            body=content,
            headers=response_headers
        )
    except Exception as e:
        print(f"[Segment Proxy] Error: {e}")
        import traceback
        traceback.print_exc()
        return web.Response(text=f"خطأ في تحميل segment: {str(e)}", status=500)

async def handle_proxy(request):
    """Proxy endpoint to bypass X-Frame-Options and CSP restrictions for video players"""
    server_url = request.query.get('server', '').strip()
    if not server_url:
        return web.Response(text="لم يتم تحديد السيرفر", status=400)

    try:
        from urllib.parse import urlparse
        parsed_url = urlparse(server_url)
        referer = f"{parsed_url.scheme}://{parsed_url.netloc}/"

        async with aiohttp.ClientSession() as session:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Referer': referer,
                'Accept': '*/*',
                'Accept-Language': 'en-US,en;q=0.9',
                'Origin': referer,
            }

            async with session.get(server_url, headers=headers, timeout=aiohttp.ClientTimeout(total=30)) as response:
                content = await response.read()
                content_type = response.headers.get('Content-Type', 'text/html')

                content_text = content.decode('utf-8', errors='ignore')
                if 'upgrade' in content_text.lower() or 'subscription' in content_text.lower() or 'premium' in content_text.lower():
                    return web.Response(text=f'<script>window.location.href="{server_url}";</script>', content_type='text/html')

                response_headers = {
                    'Content-Type': content_type,
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
                    'Access-Control-Allow-Headers': '*',
                    'X-Content-Type-Options': 'nosniff',
                }

                return web.Response(
                    body=content,
                    headers=response_headers
                )
    except Exception as e:
        return web.Response(text=f"خطأ في الاتصال بالسيرفر: {str(e)}", status=500)

async def handle_image_proxy(request):
    """Image proxy endpoint to bypass hotlink protection"""
    image_url = request.query.get('url', '').strip()
    if not image_url:
        return web.Response(text="لم يتم تحديد الصورة", status=400)

    try:
        async with aiohttp.ClientSession() as session:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Referer': 'https://www.google.com/',
                'Accept': 'image/webp,image/apng,image/*,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.9',
            }

            async with session.get(image_url, headers=headers, timeout=aiohttp.ClientTimeout(total=15)) as response:
                content = await response.read()
                content_type = response.headers.get('Content-Type', 'image/jpeg')

                response_headers = {
                    'Content-Type': content_type,
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Methods': 'GET, OPTIONS',
                    'Access-Control-Allow-Headers': '*',
                    'Cache-Control': 'public, max-age=86400',
                }

                return web.Response(
                    body=content,
                    headers=response_headers
                )
    except Exception as e:
        fallback_svg = """<svg xmlns="http://www.w3.org/2000/svg" width="240" height="170">
            <rect fill="#1a1a2e" width="240" height="170"/>
            <text x="50%" y="50%" text-anchor="middle" dy=".3em" fill="#666" font-size="20">🎬</text>
        </svg>"""
        return web.Response(
            body=fallback_svg.encode(),
            content_type='image/svg+xml',
            headers={'Cache-Control': 'public, max-age=3600'}
        )

async def handle_watch(request):
    vid = request.query.get('vid', '').strip()
    if not vid:
        return web.Response(text="لم يتم تحديد الفيلم", status=400)

    movie_info = await bot.get_movie_servers(vid)

    if 'error' in movie_info:
        return web.Response(text=f"خطأ: {movie_info['error']}", status=500)

    servers = movie_info.get('servers', [])
    episodes = movie_info.get('episodes', [])
    is_series = movie_info.get('is_series', False)
    story = movie_info.get('story', '')

    title = html_lib.escape(movie_info.get('title', 'فيلم'))
    year = html_lib.escape(movie_info.get('year', ''))
    duration = html_lib.escape(movie_info.get('duration', ''))
    quality = html_lib.escape(movie_info.get('quality', ''))
    category = html_lib.escape(movie_info.get('category', ''))
    story_html = html_lib.escape(story) if story else ''

    type_label = 'مسلسل' if is_series else 'فيلم'
    type_class = 'label-series' if is_series else 'label-movie'

    if servers:
        servers_json = json.dumps(servers)
        iframe_html = ''

        server_buttons = []
        for i in range(len(servers)):
            active_class = 'active' if i == 0 else ''
            server_buttons.append(f'<button class="server-btn {active_class}" data-server-index="{i}">سيرفر {i + 1}</button>')

        servers_html = f'''
        <div class="servers-container" id="serversContainer">
            <div class="server-info-text">🔄 لو السيرفر مشتغلش بشكل كويس اختار سيرفر تاني</div>
            {''.join(server_buttons)}
        </div>
        '''
    else:
        servers_json = '[]'
        iframe_html = '<div class="no-servers">⚠️ لا توجد سيرفرات متاحة لهذا المحتوى حالياً</div>'
        servers_html = ''

    episodes_html = ''
    if is_series and episodes:
        episode_buttons = []
        for e in episodes[:20]:
            active_class = 'active' if e['vid'] == vid else ''
            episode_buttons.append(f'<button class="episode-btn {active_class}" data-vid="{e["vid"]}">{html_lib.escape(e["title"])}</button>')

        episodes_html = f'''
        <div class="controls-row">
            <span class="ep-label">📺 الحلقات:</span>
            <div class="episodes-container">
                {''.join(episode_buttons)}
            </div>
        </div>
        '''

    details_items = []
    if year:
        details_items.append(f'<div class="movie-detail-item"><div class="label">📅 السنة</div><div class="value">{year}</div></div>')
    if duration:
        details_items.append(f'<div class="movie-detail-item"><div class="label">⏱ المدة</div><div class="value">{duration}</div></div>')
    if quality:
        details_items.append(f'<div class="movie-detail-item"><div class="label">🎬 الجودة</div><div class="value">{quality}</div></div>')
    if category:
        details_items.append(f'<div class="movie-detail-item"><div class="label">📂 التصنيف</div><div class="value">{category}</div></div>')
    if is_series:
        details_items.append(f'<div class="movie-detail-item"><div class="label">📺 النوع</div><div class="value">مسلسل</div></div>')

    details_html = ''.join(details_items)

    story_html_formatted = ''
    if story_html:
        story_html_formatted = f'''
        <div class="StoryBox">
            <h3>📖 قصة العمل</h3>
            <div class="StoryBoxText">{story_html}</div>
        </div>
        '''

    html = WATCH_TEMPLATE.substitute(
        title=title,
        type_label=type_label,
        type_class=type_class,
        iframe_html=iframe_html,
        servers_html=servers_html,
        servers_json=servers_json,
        episodes_html=episodes_html,
        details_html=details_html,
        story_html=story_html_formatted,
        guild_id=os.getenv('DISCORD_GUILD_ID', '')
    )

    return web.Response(text=html, content_type='text/html')

async def handle_index(request):
    return web.Response(text=HTML_TEMPLATE, content_type='text/html')

async def on_shutdown(app):
    await bot.close()
    await playwright_session_manager.close_all()

async def run_discord_bot():
    discord_token = os.getenv('DISCORD_TOKEN')
    if not discord_token:
        print('⚠️ DISCORD_TOKEN not found in environment variables')
        print('⚠️ Discord bot will not run')
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
    app.router.add_get('/watch', handle_watch)
    app.router.add_get('/proxy', handle_proxy)
    app.router.add_get('/img-proxy', handle_image_proxy)
    app.router.add_get('/extract-media', handle_extract_media)
    app.router.add_get('/hls-proxy', handle_hls_proxy)
    app.router.add_get('/segment-proxy', handle_segment_proxy)

    import os
    static_path = os.path.join(os.path.dirname(__file__), 'static')
    if os.path.exists(static_path):
        app.router.add_static('/static', static_path)

    app.on_shutdown.append(on_shutdown)

    @web.middleware
    async def discord_activity_middleware(request, handler):
        response = await handler(request)
        response.headers.pop('X-Frame-Options', None)
        response.headers.pop('Content-Security-Policy', None)

        content_type = response.headers.get('Content-Type', '')
        if 'text/html' in content_type:
            csp = (
                "default-src 'self' *; "
                "script-src 'self' 'unsafe-inline' 'unsafe-eval' *; "
                "style-src 'self' 'unsafe-inline' *; "
                "img-src 'self' data: blob: *; "
                "font-src 'self' data: *; "
                "connect-src 'self' *; "
                "media-src 'self' blob: *; "
                "frame-src 'self' *; "
                "frame-ancestors 'self' https://discord.com https://discord.gg *.trycloudflare.com *; "
                "worker-src 'self' blob: *; "
                "child-src 'self' blob: *; "
                "form-action 'self' *; "
                "base-uri 'self' *;"
            )
            response.headers['Content-Security-Policy'] = csp

        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS, PUT, DELETE'
        response.headers['Access-Control-Allow-Headers'] = '*'
        response.headers['Access-Control-Expose-Headers'] = '*'

        return response

    app.middlewares.append(discord_activity_middleware)

    print("\n🌐 Web Server: http://localhost:8080\n")

    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, 'localhost', 8080)
    await site.start()

    return runner

async def main():
    discord_token = os.getenv('DISCORD_TOKEN')

    tunnel_url = await start_cloudflare_tunnel(8080)

    if tunnel_url:
        print(f'🔗 Tunnel URL: {tunnel_url}')
        print('⚠️ Use this URL in Discord Developer Portal for Activities')
        web_url = tunnel_url
    else:
        print('⚠️ Could not start Cloudflare tunnel')
        print('⚠️ Discord Activities require HTTPS. Using localhost instead.')
        web_url = os.getenv('WEB_URL', 'http://localhost:8080')

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
        print('⚠️ To enable Discord bot, set DISCORD_TOKEN environment variable')
        print('⚠️ Optional: Set WEB_URL and DISCORD_APP_ID for full functionality')
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
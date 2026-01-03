(function() {
    // 注入 iframe 样式
    const style = document.createElement('style');
    style.textContent = `
        body.in-iframe #global-navbar { display: none !important; }
        body.in-iframe { padding-top: 0 !important; }
        body.in-iframe .h-16 { display: none !important; }
    `;
    document.head.appendChild(style);

    // 标记 iframe 环境
    if (window.self !== window.top) {
        if (document.body) {
            document.body.classList.add('in-iframe');
        } else {
            document.addEventListener('DOMContentLoaded', function() {
                document.body.classList.add('in-iframe');
            });
        }
    }

    // 导航菜单配置
    const navItems = [
        { name: '首页', path: '/static/dashboard.html' },
        { name: '标签管理', path: '/static/tag-management.html' },
        { name: '定时任务', path: '/static/timed-task.html' },
        { name: '任务日志', path: '/static/timed-task.html' },
        { name: '数据浏览', path: '/static/stock-data-viewer.html' },
        { name: '问财数据', path: '/static/wencai-data-viewer.html' },
        { name: '标签云图', path: '/static/concept-cloud.html' },
        { name: '日线数据', path: '/static/stock-daily-data.html' },
        { name: '测试工具', path: '/static/test-tool.html' }
    ];

    // 判断当前链接是否激活
    function isActive(path) {
        const current = window.location.pathname;
        const filename = path.split('/').pop();
        if (filename === 'dashboard.html' && (current === '/' || current.endsWith('/'))) {
            return true;
        }
        return current.includes(filename);
    }

    // 导航条HTML结构
    const navHTML = `
    <nav class="bg-gray-800 text-white shadow-lg fixed w-full z-50 top-0 left-0 print:hidden" id="global-navbar">
        <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div class="flex items-center justify-between h-16">
                <!-- Logo / Brand -->
                <div class="flex items-center">
                    <div class="flex-shrink-0 cursor-pointer nav-link" href="/static/dashboard.html">
                        <span class="font-bold text-xl flex items-center gap-2 hover:text-blue-400 transition">
                            📈 股票监控
                        </span>
                    </div>
                    <!-- Desktop Menu -->
                    <div class="hidden md:block">
                        <div class="ml-10 flex items-baseline space-x-4">
                            ${navItems.map(item => `
                                <a href="${item.path}" 
                                   class="nav-link ${isActive(item.path) ? 'bg-gray-900 text-white' : 'text-gray-300 hover:bg-gray-700 hover:text-white'} px-3 py-2 rounded-md text-sm font-medium transition duration-150 ease-in-out">
                                    ${item.name}
                                </a>
                            `).join('')}
                        </div>
                    </div>
                </div>
                <!-- Mobile Menu Button -->
                <div class="-mr-2 flex md:hidden">
                    <button type="button" id="mobile-menu-btn" class="inline-flex items-center justify-center p-2 rounded-md text-gray-400 hover:text-white hover:bg-gray-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-offset-gray-800 focus:ring-white">
                        <span class="sr-only">Open main menu</span>
                        <svg class="block h-6 w-6" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden="true">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16M4 18h16" />
                        </svg>
                    </button>
                </div>
            </div>
        </div>

        <!-- Mobile Menu Panel -->
        <div class="hidden md:hidden" id="mobile-menu">
            <div class="px-2 pt-2 pb-3 space-y-1 sm:px-3 bg-gray-800 shadow-xl">
                ${navItems.map(item => `
                    <a href="${item.path}" 
                       class="nav-link ${isActive(item.path) ? 'bg-gray-900 text-white' : 'text-gray-300 hover:bg-gray-700 hover:text-white'} block px-3 py-2 rounded-md text-base font-medium">
                        ${item.name}
                    </a>
                `).join('')}
            </div>
        </div>
    </nav>
    <!-- Spacer to prevent content overlap -->
    <div class="h-16 print:hidden"></div>
    `;

    // 注入 Tailwind CSS (如果页面未引入)
    function loadTailwind() {
        if (!document.querySelector('script[src*="tailwindcss"]')) {
            console.log('Injecting Tailwind CSS...');
            const script = document.createElement('script');
            script.src = "https://cdn.tailwindcss.com";
            document.head.appendChild(script);
        }
    }

    // 全局 WebSocket 和 Toast 逻辑
    function initGlobalWebSocket() {
        window.GlobalWS = {
            listeners: {},
            ws: null,
            
            on(event, callback) {
                if (!this.listeners[event]) {
                    this.listeners[event] = [];
                }
                this.listeners[event].push(callback);
            },
            
            off(event, callback) {
                if (!this.listeners[event]) return;
                this.listeners[event] = this.listeners[event].filter(cb => cb !== callback);
            },
            
            emit(event, data) {
                if (this.listeners[event]) {
                    this.listeners[event].forEach(cb => cb(data));
                }
            },
            
            showToast(message, type = 'info') {
                let container = document.getElementById('global-toast-container');
                if (!container) {
                     container = document.createElement('div');
                     container.id = 'global-toast-container';
                     container.className = 'fixed bottom-4 right-4 z-50 flex flex-col gap-2 pointer-events-none';
                     document.body.appendChild(container);
                }
                
                const toast = document.createElement('div');
                const bgClass = type === 'success' ? 'bg-green-500' : (type === 'error' ? 'bg-red-500' : 'bg-blue-500');
                toast.className = `${bgClass} text-white px-6 py-3 rounded shadow-lg transition-all duration-300 opacity-0 transform translate-y-2 pointer-events-auto min-w-[300px]`;
                toast.innerText = message;
                
                container.appendChild(toast);
                
                requestAnimationFrame(() => {
                    toast.classList.remove('opacity-0', 'translate-y-2');
                });
                
                setTimeout(() => {
                    toast.classList.add('opacity-0', 'translate-y-2');
                    setTimeout(() => toast.remove(), 300);
                }, 3000);
            },
            
            connect() {
                const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
                const wsUrl = `${protocol}//${window.location.host}/api/tasks/ws`;
                console.log('Global WS Connecting:', wsUrl);
                
                this.ws = new WebSocket(wsUrl);
                
                this.ws.onmessage = (event) => {
                    try {
                        const msg = JSON.parse(event.data);
                        if (msg.type === 'task_result') {
                            this.showToast(msg.data.message, msg.data.status === 'success' ? 'success' : 'error');
                        }
                        this.emit(msg.type, msg.data);
                    } catch (e) {
                        console.error('Global WS parse error:', e);
                    }
                };
                
                this.ws.onclose = () => {
                    console.log('Global WS disconnected, retrying in 5s...');
                    setTimeout(() => this.connect(), 5000);
                };
                
                this.ws.onerror = (err) => {
                    console.error('Global WS error:', err);
                    this.ws.close();
                };
            }
        };
        window.GlobalWS.connect();
    }
    
    // 立即初始化 WebSocket
    initGlobalWebSocket();

    // 初始化导航条
    function initNavBar() {
        loadTailwind();
        
        const div = document.createElement('div');
        div.innerHTML = navHTML;
        document.body.insertBefore(div, document.body.firstChild);

        setTimeout(() => {
            const btn = document.getElementById('mobile-menu-btn');
            const menu = document.getElementById('mobile-menu');
            if (btn && menu) {
                btn.addEventListener('click', () => {
                    menu.classList.toggle('hidden');
                });
            }
        }, 0);
    }

    // 全局点击事件代理
    document.addEventListener('click', function(e) {
        const target = e.target.closest('a, .nav-link');
        if (!target) return;

        const href = target.getAttribute('href');
        if (!href) return;

        if (href.startsWith('/static/') || href.startsWith('http')) {
             const urlObj = new URL(href, window.location.origin);
             if (urlObj.origin === window.location.origin && urlObj.pathname.startsWith('/static/')) {
                 const title = target.innerText.trim() || '新标签页';
                 
                 if (window.self !== window.top) {
                     e.preventDefault();
                     window.parent.postMessage({
                         type: 'OPEN_TAB',
                         url: urlObj.pathname + urlObj.search,
                         title: title
                     }, '*');
                     return;
                 }
                 
                 if (window.OPEN_TAB_Function) {
                     e.preventDefault();
                     window.OPEN_TAB_Function(urlObj.pathname + urlObj.search, title);
                     return;
                 }
             }
        }
    });

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initNavBar);
    } else {
        initNavBar();
    }
})();

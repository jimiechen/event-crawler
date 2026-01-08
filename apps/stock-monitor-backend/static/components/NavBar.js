const NavBar = {
    template: `
    <nav class="bg-gray-800 text-white shadow-lg fixed w-full z-50 top-0 left-0">
        <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div class="flex items-center justify-between h-16">
                <div class="flex items-center">
                    <div class="flex-shrink-0 cursor-pointer" @click="goHome">
                        <span class="font-bold text-xl flex items-center gap-2">
                            📈 股票监控
                        </span>
                    </div>
                    <div class="hidden md:block">
                        <div class="ml-10 flex items-baseline space-x-4">
                            <a v-for="item in navItems" 
                               :key="item.path" 
                               :href="item.path"
                               :class="[
                                   isActive(item.path) 
                                   ? 'bg-gray-900 text-white' 
                                   : 'text-gray-300 hover:bg-gray-700 hover:text-white',
                                   'px-3 py-2 rounded-md text-sm font-medium transition duration-150 ease-in-out'
                               ]"
                            >
                                {{ item.name }}
                            </a>
                        </div>
                    </div>
                </div>
                <div class="-mr-2 flex md:hidden">
                    <!-- Mobile menu button -->
                    <button @click="isOpen = !isOpen" class="inline-flex items-center justify-center p-2 rounded-md text-gray-400 hover:text-white hover:bg-gray-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-offset-gray-800 focus:ring-white">
                        <span class="sr-only">Open main menu</span>
                        <svg :class="{'hidden': isOpen, 'block': !isOpen }" class="h-6 w-6" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden="true">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16M4 18h16" />
                        </svg>
                        <svg :class="{'hidden': !isOpen, 'block': isOpen }" class="h-6 w-6" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden="true">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
                        </svg>
                    </button>
                </div>
            </div>
        </div>

        <!-- Mobile menu -->
        <div :class="{'block': isOpen, 'hidden': !isOpen}" class="md:hidden">
            <div class="px-2 pt-2 pb-3 space-y-1 sm:px-3 bg-gray-800 shadow-xl">
                <a v-for="item in navItems" 
                   :key="item.path" 
                   :href="item.path"
                   :class="[
                       isActive(item.path) 
                       ? 'bg-gray-900 text-white' 
                       : 'text-gray-300 hover:bg-gray-700 hover:text-white',
                       'block px-3 py-2 rounded-md text-base font-medium'
                   ]"
                >
                    {{ item.name }}
                </a>
            </div>
        </div>
    </nav>
    <div class="h-16"></div> <!-- Spacer to prevent content overlap -->
    `,
    data() {
        return {
            isOpen: false,
            navItems: [
                { name: '首页', path: '/static/index.html' },
                { name: '缠论分析', path: '/static/pattern-analysis.html' },
                { name: '标签管理', path: '/static/tag-management.html' },
                { name: '定时任务', path: '/static/timed-task.html' },
                { name: '数据浏览', path: '/static/stock-data-viewer.html' },
                { name: '问财数据', path: '/static/wencai-data-viewer.html' },
                { name: '爬虫维护', path: '/static/crawler.html' },
                { name: '测试工具', path: '/static/test-tool.html' }
            ]
        }
    },
    methods: {
        isActive(path) {
            const current = window.location.pathname;
            const filename = path.split('/').pop();
            
            // Exact match for root
            if (filename === 'index.html' && (current === '/' || current.endsWith('/'))) {
                return true;
            }
            
            return current.includes(filename);
        },
        goHome() {
            const url = '/static/index.html';
            const title = '首页';
            if (window.self !== window.top) {
                window.parent.postMessage({
                    type: 'OPEN_TAB',
                    url: url,
                    title: title
                }, '*');
            } else if (window.OPEN_TAB_Function) {
                window.OPEN_TAB_Function(url, title);
            } else {
                window.location.href = url;
            }
        }
    }
};

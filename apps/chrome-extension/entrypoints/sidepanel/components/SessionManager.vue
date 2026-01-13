<template>
  <div class="session-manager">
    <h3>平台会话管理</h3>
    <div class="platform-grid">
      <div v-for="platform in platforms" :key="platform.platform_id" class="platform-card">
        <div class="platform-header">
          <span class="platform-icon">{{ platform.icon }}</span>
          <span class="platform-name">{{ platform.name }}</span>
        </div>
        <div class="platform-status">
          <span v-if="platform.currentAccount" class="account-name">
            {{ platform.currentAccount }}
          </span>
          <span v-else class="account-name">未登录</span>
        </div>
        <div class="platform-actions">
          <button 
            class="action-btn login-btn" 
            @click="openPlatform(platform)"
            :disabled="loading"
          >
            🔗 快捷登录
          </button>
          <button 
            class="action-btn sync-btn" 
            @click="syncSession(platform)" 
            :disabled="syncing === platform.platform_id || loading"
          >
            {{ syncing === platform.platform_id ? '同步中...' : '🔄 同步会话' }}
          </button>
        </div>
      </div>
    </div>
    <div v-if="error" class="error-message">
      {{ error }}
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';

interface Platform {
  platform_id: string;
  name: string;
  icon: string;
  home_url: string;
  login_url: string;
  currentAccount?: string;
}

const platforms = ref<Platform[]>([]);
const loading = ref(false);
const syncing = ref<string | null>(null);
const error = ref<string | null>(null);

const fetchPlatforms = async () => {
  try {
    loading.value = true;
    error.value = null;
    
    const res = await fetch('http://localhost:8000/api/v1/platforms');
    if (!res.ok) {
      throw new Error('Failed to fetch platforms');
    }
    
    const data = await res.json();
    if (data.success && data.data) {
      platforms.value = data.data.map((p: any) => ({
        platform_id: p.platform_id,
        name: p.name,
        icon: p.icon,
        home_url: p.home_url,
        login_url: p.login_url,
        currentAccount: undefined
      }));
      
      console.log('Fetched platforms:', platforms.value);
      
      // 检查每个平台的登录状态
      await checkAllPlatforms();
    } else {
      throw new Error(data.message || 'Failed to fetch platforms');
    }
  } catch (e) {
    console.error('Failed to fetch platforms:', e);
    error.value = '获取平台列表失败';
  } finally {
    loading.value = false;
  }
};

const checkAllPlatforms = async () => {
  for (const platform of platforms.value) {
    await checkPlatformLogin(platform);
  }
};

const checkPlatformLogin = async (platform: Platform) => {
  try {
    if (!chrome.cookies) return;
    
    const cookies = await chrome.cookies.getAll({});
    
    // 根据平台配置的域名检测Cookie
    // 支持多种域名格式：.domain.com, domain.com, sub.domain.com
    const platformDomains = [
      platform.domain,
      platform.domain?.replace(/^\./, ''),
      platform.home_url?.replace(/^https?:\/\/(www\.)?/, ''),
      platform.login_url?.replace(/^https?:\/\/(www\.)?/, '')
    ].filter(Boolean);
    
    // 检查是否有该平台的Cookie
    const hasCookies = cookies.some(c => {
      const cookieDomain = c.domain?.replace(/^\./, '');
      return platformDomains.some(pd => {
        const pdClean = pd?.replace(/^https?:\/\/(www\.)?/, '');
        return cookieDomain.includes(pdClean) || pdClean.includes(cookieDomain);
      });
    });
    
    if (hasCookies) {
      // 尝试从Cookie中提取账号信息
      const userIdCookie = cookies.find(c => 
        c.name === 'user_id' || 
        c.name === 'sessionid' || 
        c.name === 'token' ||
        c.name === 'auth_token'
      );
      
      if (userIdCookie) {
        platform.currentAccount = userIdCookie.value?.substring(0, 20) || '已登录';
      } else {
        platform.currentAccount = '已登录';
      }
    } else {
      platform.currentAccount = undefined;
    }
  } catch (e) {
    console.error(`Failed to check login status for ${platform.name}:`, e);
  }
};

const openPlatform = async (platform: Platform) => {
  try {
    await chrome.tabs.create({ url: platform.home_url || platform.login_url });
  } catch (e) {
    console.error(`Failed to open ${platform.name}:`, e);
    error.value = `打开${platform.name}失败`;
  }
};

const syncSession = async (platform: Platform) => {
  try {
    syncing.value = platform.platform_id;
    error.value = null;
    
    // 获取Cookie
    const cookies = await chrome.cookies.getAll({});
    
    // 过滤出该平台的Cookie
    const platformCookies = cookies.filter(c => {
      const cookieDomain = c.domain?.replace(/^\./, '');
      const platformDomain = platform.domain?.replace(/^\./, '');
      return cookieDomain.includes(platformDomain) || 
             platform.home_url?.includes(cookieDomain) ||
             platform.login_url?.includes(cookieDomain);
    });
    
    if (platformCookies.length === 0) {
      error.value = `未找到${platform.name}的Cookie，请先登录`;
      syncing.value = null;
      return;
    }
    
    // 生成用户ID（使用Cookie中的特定字段）
    const userIdCookie = platformCookies.find(c => 
      c.name === 'user_id' || 
      c.name === 'sessionid' || 
      c.name === 'token' ||
      c.name === 'auth_token'
    );
    
    const userId = userIdCookie?.value || 
                   platformCookies.find(c => c.name === 'sessionid')?.value || 
                   'unknown_' + Date.now();
    
    // 格式化Cookie为API需要的格式
    const formattedCookies = platformCookies.map(c => ({
      name: c.name,
      value: c.value,
      domain: c.domain,
      path: c.path || '/',
      secure: c.secure || false,
      httpOnly: c.httpOnly || false
    }));
    
    console.log(`Syncing ${platform.name} session:`, {
      platform_id: platform.platform_id,
      user_id: userId,
      cookie_count: formattedCookies.length
    });
    
    // 调用会话API
    const res = await fetch('http://localhost:8000/api/v1/sessions', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        platform_id: platform.platform_id,
        user_id: userId,
        account_name: platform.currentAccount || userId,
        cookies: formattedCookies,
        user_agent: navigator.userAgent
      })
    });
    
    if (res.ok) {
      const data = await res.json();
      if (data.success) {
        console.log(`Session synced for ${platform.name}:`, data.data);
        platform.currentAccount = data.data?.account_name || platform.currentAccount;
        error.value = null;
      } else {
        throw new Error(data.message || 'Failed to sync session');
      }
    } else {
      throw new Error(`HTTP ${res.status}: Failed to sync session`);
    }
  } catch (e) {
    console.error(`Error syncing session for ${platform.name}:`, e);
    error.value = `同步${platform.name}会话失败: ${e.message || e}`;
  } finally {
    syncing.value = null;
  }
};

onMounted(() => {
  fetchPlatforms();
});
</script>

<style scoped>
.session-manager {
  padding: 16px;
  background-color: #f5f7fa;
  min-height: 100%;
}

.session-manager h3 {
  margin: 0 0 16px 0;
  font-size: 16px;
  font-weight: 600;
  color: #333;
}

.platform-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 16px;
}

.platform-card {
  background: white;
  border-radius: 8px;
  padding: 16px;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05);
  transition: all 0.2s;
}

.platform-card:hover {
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  transform: translateY(-2px);
}

.platform-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 12px;
  padding-bottom: 12px;
  border-bottom: 1px solid #f0f0f0;
}

.platform-icon {
  font-size: 24px;
}

.platform-name {
  font-size: 14px;
  font-weight: 500;
  color: #333;
}

.platform-status {
  margin-bottom: 12px;
  min-height: 20px;
}

.account-name {
  font-size: 13px;
  color: #666;
}

.account-name:not(:empty)::before {
  content: '• ';
  color: #52c41a;
}

.platform-actions {
  display: flex;
  gap: 8px;
}

.action-btn {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  padding: 10px 16px;
  border-radius: 6px;
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
  border: none;
}

.action-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.login-btn {
  background: #1890ff;
  color: white;
}

.login-btn:hover:not(:disabled) {
  background: #40a9ff;
}

.sync-btn {
  background: #52c41a;
  color: white;
}

.sync-btn:hover:not(:disabled) {
  background: #73d13d;
}

.error-message {
  margin-top: 16px;
  padding: 12px;
  background: #fff1f0;
  border: 1px solid #f5222d;
  border-radius: 6px;
  color: #f5222d;
  font-size: 13px;
  text-align: center;
}
</style>

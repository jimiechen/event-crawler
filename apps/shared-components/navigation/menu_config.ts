export interface MenuItem {
  path: string
  label: string
  icon: string
}

export const menuConfig: MenuItem[] = [
  {
    path: '/dashboard',
    label: 'Dashboard',
    icon: '📊',
    description: 'Overview of stock performance and market data'
  },
  {
    path: '/klines',
    label: 'K Lines',
    icon: '📈',
    description: 'Candlestick charts and technical indicators'
  },
  {
    path: '/patterns',
    label: 'Patterns',
    icon: '📋',
    description: 'Pattern recognition and analysis'
  },
  {
    path: '/ai',
    label: 'AI Decision',
    icon: '🤖',
    description: 'AI-powered trading decisions and strategies'
  },
  {
    path: '/signals',
    label: 'Signals',
    icon: '⚡',
    description: 'Signal detection and monitoring'
  },
  {
    path: '/ranking',
    label: 'Ranking',
    icon: '🏆',
    description: 'Stock ranking and performance metrics'
  },
  {
    path: '/portfolio',
    label: 'Portfolio',
    icon: '💼',
    description: 'Portfolio management and tracking'
  },
]

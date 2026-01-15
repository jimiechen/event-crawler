import React from 'react';
import { Link, Outlet, useLocation } from 'react-router-dom';
import { LayoutDashboard, MessageSquare, Activity, Settings, Brain } from 'lucide-react';
import { cn } from '@/lib/utils';

interface SidebarItemProps {
  icon: React.ElementType;
  label: string;
  to: string;
  active?: boolean;
}

const SidebarItem: React.FC<SidebarItemProps> = ({ icon: Icon, label, to, active }) => {
  return (
    <Link
      to={to}
      className={cn(
        "flex items-center gap-3 px-3 py-2 rounded-md text-sm font-medium transition-colors",
        active
          ? "bg-primary/10 text-primary"
          : "text-muted-foreground hover:bg-muted hover:text-foreground"
      )}
    >
      <Icon className="h-4 w-4" />
      {label}
    </Link>
  );
};

export const MainLayout: React.FC = () => {
  const location = useLocation();

  return (
    <div className="flex h-screen w-full bg-background">
      {/* Sidebar */}
      <aside className="w-64 border-r bg-card hidden md:flex flex-col">
        <div className="p-6 border-b">
          <h1 className="text-xl font-bold tracking-tight">A股 AI 决策系统</h1>
          <p className="text-xs text-muted-foreground mt-1">v1.0.0 (Arena Core)</p>
        </div>
        <nav className="flex-1 p-4 space-y-1">
          <SidebarItem 
            icon={LayoutDashboard} 
            label="概览 (Dashboard)" 
            to="/" 
            active={location.pathname === "/"} 
          />
          <SidebarItem 
            icon={Brain} 
            label="每日 AI 复盘 (AI Review)" 
            to="/ai-review" 
            active={location.pathname.startsWith("/ai-review")} 
          />
          <SidebarItem 
            icon={MessageSquare} 
            label="提示词管理 (Prompts)" 
            to="/prompts" 
            active={location.pathname.startsWith("/prompts")} 
          />
          <SidebarItem 
            icon={Activity} 
            label="信号管理 (Signals)" 
            to="/signals" 
            active={location.pathname.startsWith("/signals")} 
          />
          <SidebarItem 
            icon={Settings} 
            label="系统设置" 
            to="/settings" 
            active={location.pathname.startsWith("/settings")} 
          />
        </nav>
      </aside>

      {/* Main Content */}
      <main className="flex-1 overflow-y-auto">
        <div className="container mx-auto p-6 max-w-7xl">
          <Outlet />
        </div>
      </main>
    </div>
  );
};

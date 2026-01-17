import { useEffect, useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { schedulerApi } from '@/lib/api';
import type { ScheduledTask } from '@/types/arena';
import { Link } from 'react-router-dom';

export default function Dashboard() {
    const [tasks, setTasks] = useState<ScheduledTask[]>([]);

    useEffect(() => {
        loadData();
    }, []);

    const loadData = async () => {
        try {
            // Load Tasks
            const taskRes = await schedulerApi.getTasks();
            // Check if response has success field or just data
            // Based on api.ts: api.get<{success: boolean, data: ScheduledTask[]}>
            if (taskRes.data.success && Array.isArray(taskRes.data.data)) {
                setTasks(taskRes.data.data);
            } else if (Array.isArray(taskRes.data)) {
                 // Fallback if API structure is different
                 setTasks(taskRes.data);
            }
        } catch (e) {
            console.error(e);
        }
    };

    const aiReviewTask = tasks.find(t => t.task_type === 'daily_ai_review');

    return (
        <div className="container mx-auto p-6 space-y-6">
            <h1 className="text-3xl font-bold">A股智能监控看板</h1>
            
            {/* Status Cards */}
            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
                <Card>
                    <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                        <CardTitle className="text-sm font-medium">系统状态</CardTitle>
                    </CardHeader>
                    <CardContent>
                        <div className="text-2xl font-bold text-green-600">运行中</div>
                        <p className="text-xs text-muted-foreground">Scheduler Active</p>
                    </CardContent>
                </Card>

                <Card>
                    <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                        <CardTitle className="text-sm font-medium">AI 复盘任务</CardTitle>
                    </CardHeader>
                    <CardContent>
                         {aiReviewTask ? (
                            <>
                                <div className={`text-2xl font-bold ${
                                    aiReviewTask.last_run_status === 'success' ? 'text-green-600' : 
                                    aiReviewTask.last_run_status === 'failed' ? 'text-red-600' : 
                                    aiReviewTask.last_run_status === 'running' ? 'text-blue-600' : 'text-yellow-600'
                                }`}>
                                    {aiReviewTask.last_run_status?.toUpperCase() || 'PENDING'}
                                </div>
                                <p className="text-xs text-muted-foreground">
                                    Last: {aiReviewTask.last_run_at ? new Date(aiReviewTask.last_run_at).toLocaleString() : 'Never'}
                                </p>
                            </>
                         ) : (
                             <div className="text-sm text-gray-500">未初始化</div>
                         )}
                    </CardContent>
                </Card>
                
                 <Card>
                    <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                        <CardTitle className="text-sm font-medium">快速入口</CardTitle>
                    </CardHeader>
                    <CardContent className="flex gap-2">
                        <Link to="/prompts"><Button size="sm" variant="outline">Prompt 管理</Button></Link>
                        <Link to="/signals"><Button size="sm" variant="outline">信号配置</Button></Link>
                    </CardContent>
                </Card>
            </div>
            
            {/* Task List */}
            <Card>
                <CardHeader>
                    <CardTitle>定时任务监控</CardTitle>
                </CardHeader>
                <CardContent>
                    <div className="space-y-4">
                        {tasks.map(task => (
                            <div key={task.id} className="flex items-center justify-between border-b pb-2 last:border-0">
                                <div>
                                    <p className="font-medium">{task.name}</p>
                                    <p className="text-sm text-gray-500">{task.cron_expression} ({task.task_type})</p>
                                </div>
                                <div className="text-right">
                                    <div className={`text-sm font-bold ${
                                        task.last_run_status === 'success' ? 'text-green-600' : 
                                        task.last_run_status === 'failed' ? 'text-red-600' : 
                                        task.last_run_status === 'running' ? 'text-blue-600' : 'text-gray-600'
                                    }`}>
                                        {task.last_run_status || 'PENDING'}
                                    </div>
                                    <p className="text-xs text-gray-400">
                                        {task.last_run_at ? new Date(task.last_run_at).toLocaleString() : 'Never'}
                                    </p>
                                </div>
                            </div>
                        ))}
                        {tasks.length === 0 && <p className="text-center text-gray-500">暂无任务数据</p>}
                    </div>
                </CardContent>
            </Card>
        </div>
    );
}

// Access Globals
const { useState, useCallback, useEffect } = React;
const { createRoot } = ReactDOM;

// Handle React Flow UMD Exports
// window.ReactFlow is the namespace containing named exports
// window.ReactFlow.default is the main component (if present)
const rfNamespace = window.ReactFlow;
const ReactFlow = rfNamespace.default || rfNamespace;
const { 
    Controls, 
    Background, 
    applyEdgeChanges, 
    applyNodeChanges, 
    addEdge,
    Handle, 
    Position
} = rfNamespace;

// Polyfill hooks if missing (React Flow UMD might not export them directly in some versions)
const useNodesState = rfNamespace.useNodesState || ((initialNodes) => {
    const [nodes, setNodes] = useState(initialNodes);
    const onNodesChange = useCallback((changes) => setNodes((nds) => applyNodeChanges(changes, nds)), []);
    return [nodes, setNodes, onNodesChange];
});

const useEdgesState = rfNamespace.useEdgesState || ((initialEdges) => {
    const [edges, setEdges] = useState(initialEdges);
    const onEdgesChange = useCallback((changes) => setEdges((eds) => applyEdgeChanges(changes, eds)), []);
    return [edges, setEdges, onEdgesChange];
});

// Lucide React Icons
const { Play, Save, Undo, Redo, MousePointer2, Box, Globe, Code2, FileText, Settings, Activity, List, Zap, Radio, Heart, Terminal } = window.LucideReact;

// --- Components ---

// 1. Custom Node Component (n8n Style)
const N8nNode = ({ data, selected }) => {
    const Icon = data.icon || Box;
    return (
        <div className={`
            min-w-[180px] bg-n8n-card rounded-lg border-2 shadow-lg transition-all
            ${selected ? 'border-n8n-primary ring-2 ring-n8n-primary/20' : 'border-transparent hover:border-n8n-border'}
        `}>
            <Handle type="target" position={Position.Left} className="!bg-n8n-text !w-3 !h-3" />
            
            <div className="flex items-center p-3 gap-3">
                <div className={`p-2 rounded-md ${data.color || 'bg-gray-700'}`}>
                    <Icon size={20} className="text-white" />
                </div>
                <div>
                    <div className="font-bold text-sm text-white">{data.label}</div>
                    <div className="text-xs text-gray-400">{data.subLabel || 'Node'}</div>
                </div>
            </div>
            
            {/* Status Indicator */}
            {data.status && (
                <div className="absolute -top-1 -right-1">
                    <span className="relative flex h-3 w-3">
                      <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-green-400 opacity-75"></span>
                      <span className="relative inline-flex rounded-full h-3 w-3 bg-green-500"></span>
                    </span>
                </div>
            )}

            <Handle type="source" position={Position.Right} className="!bg-n8n-text !w-3 !h-3" />
        </div>
    );
};

const nodeTypes = {
    custom: N8nNode,
};

// 2. Initial Data
const initialNodes = [
    { 
        id: 'start-node', 
        type: 'custom', 
        position: { x: 100, y: 200 }, 
        data: { label: 'Start', subLabel: 'Manual Trigger', icon: Play, color: 'bg-n8n-primary' } 
    },
    { 
        id: 'http-request', 
        type: 'custom', 
        position: { x: 400, y: 200 }, 
        data: { label: 'Baidu Search', subLabel: 'HTTP Request', icon: Globe, color: 'bg-green-600', url: 'https://www.baidu.com/s?wd=小米汽车' } 
    },
    { 
        id: 'html-extract', 
        type: 'custom', 
        position: { x: 700, y: 200 }, 
        data: { label: 'Extract Titles', subLabel: 'HTML Parser', icon: Code2, color: 'bg-blue-600' } 
    },
    { 
        id: 'save-file', 
        type: 'custom', 
        position: { x: 1000, y: 200 }, 
        data: { label: 'Save Results', subLabel: 'Write File', icon: FileText, color: 'bg-purple-600' } 
    },
];

const initialEdges = [
    { id: 'e1-2', source: 'start-node', target: 'http-request', animated: true },
    { id: 'e2-3', source: 'http-request', target: 'html-extract', animated: true },
    { id: 'e3-4', source: 'html-extract', target: 'save-file', animated: true },
];

// 3. Main Application
function App() {
    const [nodes, setNodes, onNodesChange] = useNodesState(initialNodes);
    const [edges, setEdges, onEdgesChange] = useEdgesState(initialEdges);
    const [selectedNode, setSelectedNode] = useState(null);
    const [isRunning, setIsRunning] = useState(false);
    const [executionResult, setExecutionResult] = useState(null);

    // Sync selection
    useEffect(() => {
        const selected = nodes.find(n => n.selected);
        setSelectedNode(selected || null);
    }, [nodes]);

    const onConnect = useCallback((params) => setEdges((eds) => addEdge(params, eds)), [setEdges]);

    // Update Node Data
    const updateNodeData = (id, newData) => {
        setNodes((nds) => nds.map((node) => {
            if (node.id === id) {
                return { ...node, data: { ...node.data, ...newData } };
            }
            return node;
        }));
    };

    // Execute Workflow
    const executeWorkflow = async () => {
        setIsRunning(true);
        setExecutionResult(null);
        
        try {
            // Find the search node to get the keyword (simulated logic)
            const searchNode = nodes.find(n => n.id === 'http-request');
            let keyword = '小米汽车';
            if (searchNode && searchNode.data.url) {
                const match = searchNode.data.url.match(/wd=([^&]*)/);
                if (match) keyword = decodeURIComponent(match[1]);
            }

            // Call Backend
            const res = await fetch('/api/run', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ keyword })
            });
            const data = await res.json();
            
            setExecutionResult(data);
            
            // Animate Success
            const newNodes = nodes.map(n => ({
                ...n,
                data: { ...n.data, status: 'success' }
            }));
            setNodes(newNodes);

        } catch (err) {
            console.error(err);
            setExecutionResult({ error: err.message });
        } finally {
            setIsRunning(false);
        }
    };

    // Drag and Drop (Simplified)
    const onDragStart = (event, nodeType, label, iconName, color, subLabel) => {
        event.dataTransfer.setData('application/reactflow', JSON.stringify({ type: nodeType, label, iconName, color, subLabel }));
        event.dataTransfer.effectAllowed = 'move';
    };

    const onDrop = useCallback(
        (event) => {
            event.preventDefault();
            
            const reactFlowBounds = document.querySelector('.react-flow').getBoundingClientRect();
            const rawData = event.dataTransfer.getData('application/reactflow');
            
            if (!rawData) return;
            const { type, label, iconName, color } = JSON.parse(rawData);

            // Map string icon name to component
            const iconMap = { Globe, Code2, FileText, Box, Activity, List, Zap, Radio, Heart, Terminal };
            const IconComponent = iconMap[iconName] || Box;

            const position = {
                x: event.clientX - reactFlowBounds.left,
                y: event.clientY - reactFlowBounds.top,
            };

            const newNode = {
                id: `node-${nodes.length + 1}`,
                type: 'custom',
                position,
                data: { label, icon: IconComponent, color, subLabel: JSON.parse(rawData).subLabel },
            };

            setNodes((nds) => nds.concat(newNode));
        },
        [nodes, setNodes]
    );

    const onDragOver = useCallback((event) => {
        event.preventDefault();
        event.dataTransfer.dropEffect = 'move';
    }, []);

    return (
        <div className="flex h-full flex-col">
            {/* Header */}
            <header className="h-14 bg-n8n-card border-b border-n8n-border flex items-center px-4 justify-between z-10">
                <div className="flex items-center gap-3">
                    <div className="text-n8n-primary font-bold text-xl">n8n</div>
                    <div className="h-6 w-[1px] bg-gray-600 mx-2"></div>
                    <div className="text-sm font-medium">My Workflow</div>
                </div>
                
                <div className="flex items-center gap-2">
                    <button className="p-2 hover:bg-white/10 rounded text-gray-400 hover:text-white"><Undo size={18} /></button>
                    <button className="p-2 hover:bg-white/10 rounded text-gray-400 hover:text-white"><Redo size={18} /></button>
                    <div className="h-6 w-[1px] bg-gray-600 mx-2"></div>
                    <button 
                        onClick={executeWorkflow}
                        disabled={isRunning}
                        className={`
                            flex items-center gap-2 px-4 py-1.5 rounded-full font-bold text-sm transition-all
                            ${isRunning ? 'bg-gray-600 cursor-not-allowed' : 'bg-n8n-accent hover:bg-green-500 text-white shadow-lg shadow-green-900/20'}
                        `}
                    >
                        <Play size={16} className={isRunning ? "animate-spin" : "fill-current"} />
                        {isRunning ? 'Executing...' : 'Execute Workflow'}
                    </button>
                </div>
            </header>

            <div className="flex flex-1 overflow-hidden">
                {/* Sidebar (Nodes) */}
                <aside className="w-64 bg-n8n-card border-r border-n8n-border flex flex-col">
                    <div className="p-4 font-bold text-xs uppercase text-gray-500 tracking-wider">Nodes</div>
                    <div className="flex flex-col gap-2 px-2">
                        {[
                            { label: 'HTTP Request', icon: 'Globe', color: 'bg-green-600', iconComp: Globe },
                            { label: 'Code', icon: 'Code2', color: 'bg-blue-600', iconComp: Code2 },
                            { label: 'Edit File', icon: 'FileText', color: 'bg-purple-600', iconComp: FileText },
                            { label: 'Wait', icon: 'Box', color: 'bg-gray-600', iconComp: Box },
                            { label: 'Device Health', icon: 'Activity', color: 'bg-green-500', iconComp: Activity, subLabel: 'POST /health' },
                            { label: 'App List', icon: 'List', color: 'bg-blue-500', iconComp: List, subLabel: 'POST /app_list' },
                            { label: 'Events', icon: 'Zap', color: 'bg-yellow-500', iconComp: Zap, subLabel: 'POST /events' },
                            { label: 'SSE Listen', icon: 'Radio', color: 'bg-purple-500', iconComp: Radio, subLabel: 'GET /events' },
                            { label: 'Heartbeat', icon: 'Heart', color: 'bg-red-500', iconComp: Heart, subLabel: 'POST /heartbeat' },
                            { label: 'Send Command', icon: 'Terminal', color: 'bg-gray-800', iconComp: Terminal, subLabel: 'POST /command/send' },
                        ].map((item) => (
                            <div 
                                key={item.label}
                                draggable 
                                onDragStart={(e) => onDragStart(e, 'custom', item.label, item.icon, item.color, item.subLabel)}
                                className="flex items-center gap-3 p-3 rounded hover:bg-white/5 cursor-grab active:cursor-grabbing group transition-colors"
                            >
                                <div className={`p-1.5 rounded ${item.color}`}>
                                    <item.iconComp size={16} className="text-white" />
                                </div>
                                <span className="text-sm font-medium group-hover:text-white text-gray-300">{item.label}</span>
                            </div>
                        ))}
                    </div>
                </aside>

                {/* Canvas */}
                <main className="flex-1 relative" onDrop={onDrop} onDragOver={onDragOver}>
                    <ReactFlow
                        nodes={nodes}
                        edges={edges}
                        onNodesChange={onNodesChange}
                        onEdgesChange={onEdgesChange}
                        onConnect={onConnect}
                        nodeTypes={nodeTypes}
                        fitView
                        className="bg-n8n-dark"
                    >
                        <Background color="#333" gap={20} />
                        <Controls className="bg-n8n-card border-n8n-border fill-white text-white" />
                    </ReactFlow>

                    {/* Execution Result Panel (Overlay) */}
                    {executionResult && (
                        <div className="absolute bottom-4 left-4 right-4 bg-n8n-card border border-n8n-border rounded-lg shadow-2xl max-h-60 overflow-hidden flex flex-col animate-in slide-in-from-bottom-10 fade-in duration-300">
                            <div className="flex items-center justify-between p-3 bg-black/20 border-b border-n8n-border">
                                <span className="font-bold text-sm flex items-center gap-2">
                                    {executionResult.success ? <span className="w-2 h-2 rounded-full bg-green-500"/> : <span className="w-2 h-2 rounded-full bg-red-500"/>}
                                    Execution Output
                                </span>
                                <button onClick={() => setExecutionResult(null)} className="text-gray-400 hover:text-white">×</button>
                            </div>
                            <pre className="p-4 overflow-auto text-xs font-mono text-green-400">
                                {JSON.stringify(executionResult, null, 2)}
                            </pre>
                        </div>
                    )}
                </main>

                {/* Properties Panel (Right) */}
                {selectedNode && (
                    <aside className="w-80 bg-n8n-card border-l border-n8n-border flex flex-col animate-in slide-in-from-right duration-200">
                        <div className="p-4 border-b border-n8n-border flex items-center gap-3">
                            <div className={`p-2 rounded ${selectedNode.data.color}`}>
                                {selectedNode.data.icon ? <selectedNode.data.icon size={20} className="text-white"/> : <Box size={20}/>}
                            </div>
                            <div>
                                <div className="font-bold">{selectedNode.data.label}</div>
                                <div className="text-xs text-gray-400">ID: {selectedNode.id}</div>
                            </div>
                        </div>
                        
                        <div className="p-4 flex flex-col gap-4">
                            <div className="flex flex-col gap-1">
                                <label className="text-xs font-bold text-gray-500 uppercase">Label</label>
                                <input 
                                    type="text" 
                                    value={selectedNode.data.label}
                                    onChange={(e) => updateNodeData(selectedNode.id, { label: e.target.value })}
                                    className="bg-n8n-dark border border-n8n-border rounded p-2 text-sm focus:border-n8n-primary outline-none"
                                />
                            </div>

                            {selectedNode.data.url !== undefined && (
                                <div className="flex flex-col gap-1">
                                    <label className="text-xs font-bold text-gray-500 uppercase">URL</label>
                                    <input 
                                        type="text" 
                                        value={selectedNode.data.url}
                                        onChange={(e) => updateNodeData(selectedNode.id, { url: e.target.value })}
                                        className="bg-n8n-dark border border-n8n-border rounded p-2 text-sm focus:border-n8n-primary outline-none font-mono"
                                    />
                                    <div className="text-[10px] text-gray-500">Edit the URL query to change search keyword</div>
                                </div>
                            )}

                            {selectedNode.data.label === 'Send Command' && (
                                <div className="flex flex-col gap-1">
                                    <label className="text-xs font-bold text-gray-500 uppercase">Command</label>
                                    <input 
                                        type="text" 
                                        value={selectedNode.data.command || ''}
                                        onChange={(e) => updateNodeData(selectedNode.id, { command: e.target.value })}
                                        placeholder="e.g. adb shell ls"
                                        className="bg-n8n-dark border border-n8n-border rounded p-2 text-sm focus:border-n8n-primary outline-none font-mono"
                                    />
                                </div>
                            )}

                             <div className="flex flex-col gap-1">
                                <label className="text-xs font-bold text-gray-500 uppercase">Notes</label>
                                <textarea 
                                    className="bg-n8n-dark border border-n8n-border rounded p-2 text-sm focus:border-n8n-primary outline-none h-24 resize-none"
                                    placeholder="Add notes here..."
                                ></textarea>
                            </div>
                        </div>
                    </aside>
                )}
            </div>
        </div>
    );
}

const root = createRoot(document.getElementById('root'));
root.render(<App />);

import { useEffect, useState } from 'react'
import {
  fetchSignals,
  createSignal,
  updateSignal,
  deleteSignal,
  createPool,
  updatePool,
  deletePool,
  SignalDefinition,
  SignalPool
} from '@/lib/api'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import {
  Dialog,
  DialogContent,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Plus, Trash2, Edit, Sparkles } from 'lucide-react'

// Mock translation
const useTranslation = () => ({ t: (key: string, defaultVal: string) => defaultVal })
const toast = {
  success: (msg: string) => alert(msg),
  error: (msg: string) => alert(msg),
}

interface TriggerCondition {
  metric?: string
  operator?: string
  threshold?: number
  time_window?: string
  logic?: string
  conditions?: TriggerCondition[]
}

const METRICS = [
  { value: 'price_change', label: 'Price Change', desc: 'Price change % over time window. Positive=up, Negative=down' },
  { value: 'volatility', label: 'Volatility', desc: 'Price volatility % over time window.' },
  { value: 'volume_spike', label: 'Volume Spike', desc: 'Volume increase relative to MA.' },
  { value: 'rsi', label: 'RSI', desc: 'Relative Strength Index' },
  { value: 'macd', label: 'MACD', desc: 'MACD Crossover' },
]

const OPERATORS = [
  { value: 'greater_than', label: '> (Greater)', desc: 'Triggers when value is greater than threshold' },
  { value: 'less_than', label: '< (Less)', desc: 'Triggers when value is less than threshold' },
  { value: 'equals', label: '= (Equals)', desc: 'Triggers when value equals threshold' },
]

const TIME_WINDOWS = [
  { value: '1m', label: '1 min', desc: 'Very short-term' },
  { value: '5m', label: '5 min', desc: 'Short-term' },
  { value: '15m', label: '15 min', desc: 'Medium-term' },
  { value: '30m', label: '30 min', desc: 'Longer-term' },
  { value: '1h', label: '1 hour', desc: 'Major trend' },
  { value: '1d', label: '1 day', desc: 'Daily' },
]

export default function SignalManager() {
  const { t } = useTranslation()
  const [signals, setSignals] = useState<SignalDefinition[]>([])
  const [pools, setPools] = useState<SignalPool[]>([])
  const [loading, setLoading] = useState(true)
  const [activeTab, setActiveTab] = useState('signals')

  // Signal dialog state
  const [signalDialogOpen, setSignalDialogOpen] = useState(false)
  const [editingSignal, setEditingSignal] = useState<SignalDefinition | null>(null)
  const [signalForm, setSignalForm] = useState({
    signal_name: '',
    description: '',
    metric: 'price_change',
    operator: 'greater_than',
    threshold: 5,
    time_window: '5m',
    enabled: true,
  })

  // Pool dialog state
  const [poolDialogOpen, setPoolDialogOpen] = useState(false)
  const [editingPool, setEditingPool] = useState<SignalPool | null>(null)
  const [poolForm, setPoolForm] = useState({
    pool_name: '',
    signal_ids: [] as number[],
    symbols: [] as string[],
    enabled: true,
    logic: 'OR' as 'OR' | 'AND',
  })

  const [savingSignal, setSavingSignal] = useState(false)
  const [savingPool, setSavingPool] = useState(false)

  const loadData = async () => {
    try {
      setLoading(true)
      const data = await fetchSignals()
      setSignals(data.signals)
      setPools(data.pools)
    } catch (err) {
      console.error(err)
      toast.error('Failed to load signal data')
    } finally {
      setLoading(false)
    }
  }

  const refreshDataSilently = async () => {
    try {
      const data = await fetchSignals()
      setSignals(data.signals)
      setPools(data.pools)
    } catch (err) {
      console.error(err)
    }
  }

  useEffect(() => {
    loadData()
  }, [])

  const openSignalDialog = (signal?: SignalDefinition) => {
    if (signal) {
      setEditingSignal(signal)
      const cond = signal.trigger_condition as TriggerCondition
      setSignalForm({
        signal_name: signal.signal_name,
        description: signal.description || '',
        metric: cond.metric || 'price_change',
        operator: cond.operator || 'greater_than',
        threshold: cond.threshold ?? 5,
        time_window: cond.time_window || '5m',
        enabled: signal.enabled,
      })
    } else {
      setEditingSignal(null)
      setSignalForm({
        signal_name: '',
        description: '',
        metric: 'price_change',
        operator: 'greater_than',
        threshold: 5,
        time_window: '5m',
        enabled: true,
      })
    }
    setSignalDialogOpen(true)
  }

  const handleSaveSignal = async () => {
    setSavingSignal(true)
    try {
      const trigger_condition = {
        metric: signalForm.metric,
        operator: signalForm.operator,
        threshold: signalForm.threshold,
        time_window: signalForm.time_window,
      }
      const data = {
        signal_name: signalForm.signal_name,
        description: signalForm.description,
        trigger_condition,
        enabled: signalForm.enabled,
      }
      if (editingSignal) {
        await updateSignal(editingSignal.id, data)
        toast.success('Signal updated')
      } else {
        await createSignal(data)
        toast.success('Signal created')
      }
      setSignalDialogOpen(false)
      refreshDataSilently()
    } catch (err) {
      console.error(err)
      toast.error('Failed to save signal')
    } finally {
      setSavingSignal(false)
    }
  }

  const handleDeleteSignal = async (id: number) => {
    if (!confirm('Delete this signal?')) return
    try {
      await deleteSignal(id)
      toast.success('Signal deleted')
      refreshDataSilently()
    } catch (err) {
      console.error(err)
      toast.error('Failed to delete signal')
    }
  }

  const openPoolDialog = (pool?: SignalPool) => {
    if (pool) {
      setEditingPool(pool)
      setPoolForm({
        pool_name: pool.pool_name,
        signal_ids: pool.signal_ids,
        symbols: pool.symbols,
        enabled: pool.enabled,
        logic: (pool.logic as 'OR' | 'AND') || 'OR',
      })
    } else {
      setEditingPool(null)
      setPoolForm({ pool_name: '', signal_ids: [], symbols: [], enabled: true, logic: 'OR' })
    }
    setPoolDialogOpen(true)
  }

  const handleSavePool = async () => {
    setSavingPool(true)
    try {
      if (editingPool) {
        await updatePool(editingPool.id, poolForm)
        toast.success('Pool updated')
      } else {
        await createPool(poolForm)
        toast.success('Pool created')
      }
      setPoolDialogOpen(false)
      refreshDataSilently()
    } catch (err) {
      console.error(err)
      toast.error('Failed to save pool')
    } finally {
      setSavingPool(false)
    }
  }

  const handleDeletePool = async (id: number) => {
    if (!confirm('Delete this pool?')) return
    try {
      await deletePool(id)
      toast.success('Pool deleted')
      refreshDataSilently()
    } catch (err) {
      console.error(err)
      toast.error('Failed to delete pool')
    }
  }

  const toggleSignalInPool = (signalId: number) => {
    setPoolForm(prev => ({
      ...prev,
      signal_ids: prev.signal_ids.includes(signalId)
        ? prev.signal_ids.filter(id => id !== signalId)
        : [...prev.signal_ids, signalId]
    }))
  }

  const formatCondition = (cond: TriggerCondition) => {
    const metric = METRICS.find(m => m.value === cond.metric)?.label || cond.metric
    const op = OPERATORS.find(o => o.value === cond.operator)?.label || cond.operator
    return `${metric} ${op} ${cond.threshold} (${cond.time_window})`
  }

  if (loading) {
    return <div className="flex items-center justify-center h-64">{t('signals.loading', 'Loading...')}</div>
  }

  return (
    <div className="p-4 space-y-4">
      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <div className="flex items-center justify-between gap-4 mb-4">
          <TabsList className="justify-start">
            <TabsTrigger value="signals" className="min-w-[100px]">{t('signals.tabs.signals', 'Signals')}</TabsTrigger>
            <TabsTrigger value="pools" className="min-w-[120px]">{t('signals.tabs.pools', 'Signal Pools')}</TabsTrigger>
          </TabsList>
          <div className="flex gap-2">
            <Button onClick={() => openSignalDialog()} size="sm">
              <Plus className="w-4 h-4 mr-2" />{t('signals.newSignal', 'New Signal')}
            </Button>
            <Button onClick={() => openPoolDialog()} size="sm">
              <Plus className="w-4 h-4 mr-2" />{t('signals.newPool', 'New Pool')}
            </Button>
          </div>
        </div>

        <TabsContent value="signals" className="space-y-4">
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            {signals.map(signal => (
              <Card key={signal.id}>
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <CardTitle className="text-sm font-medium">
                    {signal.signal_name}
                  </CardTitle>
                  <div className="flex gap-2">
                    <Button variant="ghost" size="icon" className="h-8 w-8" onClick={() => openSignalDialog(signal)}>
                        <Edit className="h-4 w-4" />
                    </Button>
                    <Button variant="ghost" size="icon" className="h-8 w-8 text-red-500" onClick={() => handleDeleteSignal(signal.id)}>
                        <Trash2 className="h-4 w-4" />
                    </Button>
                  </div>
                </CardHeader>
                <CardContent>
                  <div className="text-xs text-gray-500 mb-2">{signal.description}</div>
                  <div className="text-sm font-bold">
                    {formatCondition(signal.trigger_condition as TriggerCondition)}
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </TabsContent>

        <TabsContent value="pools" className="space-y-4">
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            {pools.map(pool => (
              <Card key={pool.id}>
                 <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <CardTitle className="text-sm font-medium">
                    {pool.pool_name}
                  </CardTitle>
                  <div className="flex gap-2">
                    <Button variant="ghost" size="icon" className="h-8 w-8" onClick={() => openPoolDialog(pool)}>
                        <Edit className="h-4 w-4" />
                    </Button>
                    <Button variant="ghost" size="icon" className="h-8 w-8 text-red-500" onClick={() => handleDeletePool(pool.id)}>
                        <Trash2 className="h-4 w-4" />
                    </Button>
                  </div>
                </CardHeader>
                <CardContent>
                  <div className="text-xs text-gray-500 mb-2">Logic: {pool.logic}</div>
                  <div className="text-sm">
                    Signals: {pool.signal_ids.length} | Stocks: {pool.symbols.length}
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </TabsContent>
      </Tabs>

      {/* Signal Dialog */}
      <Dialog open={signalDialogOpen} onOpenChange={setSignalDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>{editingSignal ? 'Edit Signal' : 'New Signal'}</DialogTitle>
          </DialogHeader>
          <div className="grid gap-4 py-4">
            <div className="grid gap-2">
                <label className="text-sm">Name</label>
                <Input value={signalForm.signal_name} onChange={e => setSignalForm({...signalForm, signal_name: e.target.value})} />
            </div>
            <div className="grid gap-2">
                <label className="text-sm">Description</label>
                <Input value={signalForm.description} onChange={e => setSignalForm({...signalForm, description: e.target.value})} />
            </div>
            <div className="grid grid-cols-2 gap-4">
                <div className="grid gap-2">
                    <label className="text-sm">Metric</label>
                    <Select value={signalForm.metric} onValueChange={v => setSignalForm({...signalForm, metric: v})}>
                        <SelectTrigger><SelectValue /></SelectTrigger>
                        <SelectContent>
                            {METRICS.map(m => <SelectItem key={m.value} value={m.value}>{m.label}</SelectItem>)}
                        </SelectContent>
                    </Select>
                </div>
                <div className="grid gap-2">
                    <label className="text-sm">Time Window</label>
                    <Select value={signalForm.time_window} onValueChange={v => setSignalForm({...signalForm, time_window: v})}>
                        <SelectTrigger><SelectValue /></SelectTrigger>
                        <SelectContent>
                            {TIME_WINDOWS.map(t => <SelectItem key={t.value} value={t.value}>{t.label}</SelectItem>)}
                        </SelectContent>
                    </Select>
                </div>
            </div>
            <div className="grid grid-cols-2 gap-4">
                <div className="grid gap-2">
                    <label className="text-sm">Operator</label>
                    <Select value={signalForm.operator} onValueChange={v => setSignalForm({...signalForm, operator: v})}>
                        <SelectTrigger><SelectValue /></SelectTrigger>
                        <SelectContent>
                            {OPERATORS.map(o => <SelectItem key={o.value} value={o.value}>{o.label}</SelectItem>)}
                        </SelectContent>
                    </Select>
                </div>
                <div className="grid gap-2">
                    <label className="text-sm">Threshold</label>
                    <Input type="number" value={signalForm.threshold} onChange={e => setSignalForm({...signalForm, threshold: parseFloat(e.target.value)})} />
                </div>
            </div>
          </div>
          <DialogFooter>
            <Button onClick={handleSaveSignal} disabled={savingSignal}>Save</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Pool Dialog */}
      <Dialog open={poolDialogOpen} onOpenChange={setPoolDialogOpen}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>{editingPool ? 'Edit Pool' : 'New Pool'}</DialogTitle>
          </DialogHeader>
          <div className="grid gap-4 py-4">
             <div className="grid gap-2">
                <label className="text-sm">Pool Name</label>
                <Input value={poolForm.pool_name} onChange={e => setPoolForm({...poolForm, pool_name: e.target.value})} />
            </div>
            <div className="grid gap-2">
                <label className="text-sm">Logic</label>
                <Select value={poolForm.logic} onValueChange={v => setPoolForm({...poolForm, logic: v as 'OR' | 'AND'})}>
                    <SelectTrigger><SelectValue /></SelectTrigger>
                    <SelectContent>
                        <SelectItem value="OR">OR (Any signal triggers)</SelectItem>
                        <SelectItem value="AND">AND (All signals match)</SelectItem>
                    </SelectContent>
                </Select>
            </div>
            <div className="grid gap-2">
                <label className="text-sm">Select Signals</label>
                <div className="grid grid-cols-2 gap-2 border p-2 rounded max-h-40 overflow-y-auto">
                    {signals.map(s => (
                        <div key={s.id} className="flex items-center gap-2">
                            <input 
                                type="checkbox" 
                                checked={poolForm.signal_ids.includes(s.id)}
                                onChange={() => toggleSignalInPool(s.id)}
                            />
                            <span className="text-sm">{s.signal_name}</span>
                        </div>
                    ))}
                </div>
            </div>
          </div>
          <DialogFooter>
            <Button onClick={handleSavePool} disabled={savingPool}>Save</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}

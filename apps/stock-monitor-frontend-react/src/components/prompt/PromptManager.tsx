import { useEffect, useMemo, useState } from 'react'
import {
  getPromptTemplates,
  updatePromptTemplateById,
  upsertPromptBinding,
  deletePromptBinding,
  getAccounts,
  createPromptTemplate,
  copyPromptTemplate,
  deletePromptTemplate,
  updatePromptTemplateName,
  PromptTemplate,
  PromptBinding,
  TradingAccount,
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
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { Textarea } from '@/components/ui/textarea'

// Mock translation
const useTranslation = () => ({ t: (key: string, defaultVal: string) => defaultVal, i18n: { language: 'zh' } })

// Mock Toast
const toast = {
  success: (msg: string) => alert(msg),
  error: (msg: string) => alert(msg),
}

interface BindingFormState {
  id?: number
  accountId?: number
  promptTemplateId?: number
}

const DEFAULT_BINDING_FORM: BindingFormState = {
  accountId: undefined,
  promptTemplateId: undefined,
}

export default function PromptManager() {
  const { t } = useTranslation()
  const [templates, setTemplates] = useState<PromptTemplate[]>([])
  const [bindings, setBindings] = useState<PromptBinding[]>([])
  const [accounts, setAccounts] = useState<TradingAccount[]>([])
  const [accountsLoading, setAccountsLoading] = useState(false)
  const [selectedId, setSelectedId] = useState<number | null>(null)
  const [templateDraft, setTemplateDraft] = useState<string>('')
  const [nameDraft, setNameDraft] = useState<string>('')
  const [descriptionDraft, setDescriptionDraft] = useState<string>('')
  const [loading, setLoading] = useState(false)
  const [saving, setSaving] = useState(false)
  const [bindingSaving, setBindingSaving] = useState(false)
  const [bindingForm, setBindingForm] = useState<BindingFormState>(DEFAULT_BINDING_FORM)
  
  // New template dialog
  const [newTemplateDialogOpen, setNewTemplateDialogOpen] = useState(false)
  const [newTemplateName, setNewTemplateName] = useState('')
  const [newTemplateDescription, setNewTemplateDescription] = useState('')
  const [creating, setCreating] = useState(false)

  // Copy template dialog
  const [copyDialogOpen, setCopyDialogOpen] = useState(false)
  const [copyName, setCopyName] = useState('')
  const [copying, setCopying] = useState(false)

  // Auth context mock
  const user = { id: 1, name: 'Admin' }

  const selectedTemplate = useMemo(
    () => templates.find((tpl) => tpl.id === selectedId) || null,
    [templates, selectedId],
  )

  const loadTemplates = async () => {
    setLoading(true)
    try {
      const data = await getPromptTemplates()
      setTemplates(data.templates)
      setBindings(data.bindings)

      if (!selectedId && data.templates.length > 0) {
        const first = data.templates[0]
        setSelectedId(first.id)
        setTemplateDraft(first.template_text)
        setNameDraft(first.name)
        setDescriptionDraft(first.description ?? '')
      } else if (selectedId) {
        const tpl = data.templates.find((item) => item.id === selectedId)
        if (tpl) {
          setTemplateDraft(tpl.template_text)
          setNameDraft(tpl.name)
          setDescriptionDraft(tpl.description ?? '')
        }
      }
    } catch (err) {
      console.error(err)
      toast.error(err instanceof Error ? err.message : 'Failed to load prompt templates')
    } finally {
      setLoading(false)
    }
  }

  const loadAccounts = async () => {
    setAccountsLoading(true)
    try {
      const list = await getAccounts()
      setAccounts(list)
    } catch (err) {
      console.error(err)
      toast.error(err instanceof Error ? err.message : 'Failed to load AI traders')
    } finally {
      setAccountsLoading(false)
    }
  }

  useEffect(() => {
    loadTemplates()
    loadAccounts()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  const handleSelectTemplate = (id: string) => {
    const numId = Number(id)
    setSelectedId(numId)
    const tpl = templates.find((item) => item.id === numId)
    setTemplateDraft(tpl?.template_text ?? '')
    setNameDraft(tpl?.name ?? '')
    setDescriptionDraft(tpl?.description ?? '')
  }

  const handleSaveTemplate = async () => {
    if (!selectedTemplate) return
    setSaving(true)
    try {
      const updated = await updatePromptTemplateById(selectedTemplate.id, {
        template_text: templateDraft,
        description: descriptionDraft,
        updated_by: 'ui',
      })

      // Also update name if changed
      if (nameDraft !== selectedTemplate.name) {
        await updatePromptTemplateName(selectedTemplate.id, {
          name: nameDraft,
          description: descriptionDraft,
          updated_by: 'ui',
        })
      }

      setTemplates((prev) =>
        prev.map((tpl) =>
          tpl.id === selectedTemplate.id
            ? { ...tpl, ...updated, name: nameDraft, description: descriptionDraft, template_text: templateDraft }
            : tpl,
        ),
      )
      toast.success('Prompt template saved')
    } catch (err) {
      console.error(err)
      toast.error(err instanceof Error ? err.message : 'Failed to save prompt template')
    } finally {
      setSaving(false)
    }
  }

  const handleCreateTemplate = async () => {
    if (!newTemplateName.trim()) {
      toast.error('Please enter a template name')
      return
    }

    setCreating(true)
    try {
      const created = await createPromptTemplate({
        name: newTemplateName,
        description: newTemplateDescription,
        template_text: 'You are a helpful AI assistant.', // Default content
        created_by: 'ui',
      })

      setTemplates((prev) => [created, ...prev])
      setSelectedId(created.id)
      setTemplateDraft(created.template_text)
      setNameDraft(created.name)
      setDescriptionDraft(created.description ?? '')

      setNewTemplateDialogOpen(false)
      setNewTemplateName('')
      setNewTemplateDescription('')
      toast.success('Template created')
    } catch (err) {
      console.error(err)
      toast.error(err instanceof Error ? err.message : 'Failed to create template')
    } finally {
      setCreating(false)
    }
  }

  const handleCopyTemplate = async () => {
    if (!selectedTemplate) return

    setCopying(true)
    try {
      const copied = await copyPromptTemplate(selectedTemplate.id, {
        newName: copyName || undefined,
        createdBy: 'ui',
      })

      setTemplates((prev) => [copied, ...prev])
      setSelectedId(copied.id)
      setTemplateDraft(copied.template_text)
      setNameDraft(copied.name)
      setDescriptionDraft(copied.description ?? '')

      setCopyDialogOpen(false)
      setCopyName('')
      toast.success('Template copied')
    } catch (err) {
      console.error(err)
      toast.error(err instanceof Error ? err.message : 'Failed to copy template')
    } finally {
      setCopying(false)
    }
  }

  const handleDeleteTemplate = async () => {
    if (!selectedTemplate) return

    if (selectedTemplate.is_system) {
      toast.error('Cannot delete system templates')
      return
    }

    if (!confirm(`Delete template "${selectedTemplate.name}"?`)) {
      return
    }

    try {
      await deletePromptTemplate(selectedTemplate.id)
      setTemplates((prev) => prev.filter((tpl) => tpl.id !== selectedTemplate.id))

      // Select first available template
      const remaining = templates.filter((tpl) => tpl.id !== selectedTemplate.id)
      if (remaining.length > 0) {
        setSelectedId(remaining[0].id)
        setTemplateDraft(remaining[0].template_text)
        setNameDraft(remaining[0].name)
        setDescriptionDraft(remaining[0].description ?? '')
      } else {
        setSelectedId(null)
        setTemplateDraft('')
        setNameDraft('')
        setDescriptionDraft('')
      }

      toast.success('Template deleted')
    } catch (err) {
      console.error(err)
      toast.error(err instanceof Error ? err.message : 'Failed to delete template')
    }
  }

  const handleBindingSubmit = async () => {
    if (!bindingForm.accountId) {
      toast.error('Please select an AI trader')
      return
    }
    if (!bindingForm.promptTemplateId) {
      toast.error('Please select a prompt template')
      return
    }

    setBindingSaving(true)
    try {
      const payload = await upsertPromptBinding({
        id: bindingForm.id,
        account_id: bindingForm.accountId,
        prompt_template_id: bindingForm.promptTemplateId,
        updated_by: 'ui',
      })

      setBindings((prev) => {
        const existingIndex = prev.findIndex((item) => item.id === payload.id)
        if (existingIndex !== -1) {
          const next = [...prev]
          next[existingIndex] = payload
          return next
        }
        return [...prev, payload]
      })
      setBindingForm(DEFAULT_BINDING_FORM)
      toast.success('Prompt binding saved')
    } catch (err) {
      console.error(err)
      toast.error(err instanceof Error ? err.message : 'Failed to save binding')
    } finally {
      setBindingSaving(false)
    }
  }

  const handleDeleteBinding = async (bindingId: number) => {
    try {
      await deletePromptBinding(bindingId)
      setBindings((prev) => prev.filter((item) => item.id !== bindingId))
      toast.success('Binding deleted')
    } catch (err) {
      console.error(err)
      toast.error(err instanceof Error ? err.message : 'Failed to delete binding')
    }
  }

  const handleEditBinding = (binding: PromptBinding) => {
    setBindingForm({
      id: binding.id,
      accountId: binding.account_id,
      promptTemplateId: binding.prompt_template_id,
    })
  }

  const accountOptions = useMemo(() => {
    return accounts
      .filter((account) => account.account_type === 'AI')
      .sort((a, b) => a.name.localeCompare(b.name))
  }, [accounts])

  return (
    <>
      <div className="h-full w-full overflow-hidden flex flex-col gap-4 p-4">
        <div className="flex flex-col lg:flex-row gap-4 h-full overflow-hidden">
        {/* LEFT COLUMN - Template Selection + Edit Area */}
        <div className="flex-1 flex flex-col h-full gap-4 overflow-hidden">
          <Card className="flex-1 flex flex-col h-full overflow-hidden">
            <CardHeader>
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <CardTitle className="text-base">{t('prompt.templateEditor', 'Prompt Template Editor')}</CardTitle>
                </div>
                <div className="flex gap-2">
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => setNewTemplateDialogOpen(true)}
                  >
                    ➕ {t('prompt.new', 'New')}
                  </Button>
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => setCopyDialogOpen(true)}
                    disabled={!selectedTemplate}
                  >
                    📋 {t('prompt.copy', 'Copy')}
                  </Button>
                  {selectedTemplate && !selectedTemplate.is_system && (
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={handleDeleteTemplate}
                      className="text-red-500 hover:text-red-700"
                    >
                      🗑️ {t('common.delete', 'Delete')}
                    </Button>
                  )}
                </div>
              </div>
            </CardHeader>
            <CardContent className="flex flex-col gap-4 h-[100%] flex-1 overflow-hidden">
              {/* Template Selection Dropdown */}
              <div>
                <label className="text-xs uppercase text-gray-500">{t('prompt.template', 'Template')}</label>
                <Select
                  value={selectedId ? String(selectedId) : ''}
                  onValueChange={handleSelectTemplate}
                  disabled={loading}
                >
                  <SelectTrigger>
                    <SelectValue placeholder={loading ? t('common.loading', 'Loading...') : t('prompt.selectTemplate', 'Select a template')} />
                  </SelectTrigger>
                  <SelectContent>
                    {templates.map((tpl) => (
                      <SelectItem key={tpl.id} value={String(tpl.id)}>
                        <div className="flex flex-col items-start">
                          <span className="font-semibold">
                            {tpl.name}
                            {tpl.is_system && (
                              <span className="ml-2 text-xs text-gray-500">[{t('prompt.system', 'System')}]</span>
                            )}
                          </span>
                          <span className="text-xs text-gray-500">{tpl.key}</span>
                        </div>
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              {/* Name Input */}
              <div>
                <label className="text-xs uppercase text-gray-500">{t('prompt.templateName', 'Template Name')}</label>
                <Input
                  value={nameDraft}
                  onChange={(event) => setNameDraft(event.target.value)}
                  placeholder={t('prompt.templateNamePlaceholder', 'Template name')}
                  disabled={!selectedTemplate || saving}
                />
              </div>

              {/* Description Input */}
              <div>
                <label className="text-xs uppercase text-gray-500">{t('common.description', 'Description')}</label>
                <Input
                  value={descriptionDraft}
                  onChange={(event) => setDescriptionDraft(event.target.value)}
                  placeholder={t('prompt.descriptionPlaceholder', 'Prompt description')}
                  disabled={!selectedTemplate || saving}
                />
              </div>

              {/* Template Text Area */}
              <div className="flex-1 flex flex-col overflow-hidden">
                <label className="text-xs uppercase text-gray-500 mb-2">{t('prompt.templateText', 'Template Text')}</label>
                <Textarea
                  className="flex-1 w-full font-mono text-sm leading-relaxed"
                  value={templateDraft}
                  onChange={(event) => setTemplateDraft(event.target.value)}
                  disabled={!selectedTemplate || saving}
                />
              </div>

              {/* Action Buttons */}
              <div className="flex justify-end mt-2 gap-2">
                <Button onClick={handleSaveTemplate} disabled={!selectedTemplate || saving}>
                  {t('prompt.saveTemplate', 'Save Template')}
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* RIGHT COLUMN - Binding Management */}
        <Card className="flex flex-col w-full lg:w-[40rem] flex-shrink-0 overflow-hidden">
          <CardHeader>
            <CardTitle className="text-base">{t('prompt.accountBindings', 'Account Prompt Bindings')}</CardTitle>
          </CardHeader>
          <CardContent className="flex-1 flex flex-col gap-6">
            {/* Bindings Table */}
            <div className="flex-1 overflow-auto">
              <table className="min-w-full text-sm">
                <thead className="text-left text-gray-500">
                  <tr>
                    <th className="py-2 pr-4">{t('prompt.account', 'Account')}</th>
                    <th className="py-2 pr-4">{t('prompt.template', 'Template')}</th>
                    <th className="py-2 pr-4 text-right">{t('common.actions', 'Actions')}</th>
                  </tr>
                </thead>
                <tbody>
                  {bindings.map((binding) => (
                    <tr key={binding.id} className="border-t">
                      <td className="py-2 pr-4">{binding.account_name}</td>
                      <td className="py-2 pr-4">{binding.prompt_name}</td>
                      <td className="py-2 pr-4 text-right space-x-2">
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => handleEditBinding(binding)}
                        >
                          {t('common.edit', 'Edit')}
                        </Button>
                        <Button
                          variant="ghost"
                          size="sm"
                          className="text-red-500 hover:text-red-700"
                          onClick={() => handleDeleteBinding(binding.id)}
                        >
                          {t('common.delete', 'Delete')}
                        </Button>
                      </td>
                    </tr>
                  ))}
                  {bindings.length === 0 && (
                    <tr>
                      <td colSpan={4} className="py-4 text-center text-gray-500">
                        {t('prompt.noBindings', 'No prompt bindings configured.')}
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>

            {/* Binding Form */}
            <div className="space-y-4 border-t pt-4">
              <div className="grid grid-cols-1 gap-3">
                <div>
                  <label className="text-xs uppercase text-gray-500">
                    {t('prompt.aiTrader', 'AI Trader')}
                  </label>
                  <Select
                    value={
                      bindingForm.accountId !== undefined ? String(bindingForm.accountId) : ''
                    }
                    onValueChange={(value) =>
                      setBindingForm((prev) => ({
                        ...prev,
                        accountId: Number(value),
                      }))
                    }
                    disabled={accountsLoading}
                  >
                    <SelectTrigger>
                      <SelectValue placeholder={accountsLoading ? t('common.loading', 'Loading...') : t('common.select', 'Select')} />
                    </SelectTrigger>
                    <SelectContent>
                      {accountOptions.map((account) => (
                        <SelectItem key={account.id} value={String(account.id)}>
                          {account.name}
                          {account.model ? ` (${account.model})` : ''}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                <div>
                  <label className="text-xs uppercase text-gray-500">{t('prompt.template', 'Template')}</label>
                  <Select
                    value={
                      bindingForm.promptTemplateId !== undefined
                        ? String(bindingForm.promptTemplateId)
                        : ''
                    }
                    onValueChange={(value) =>
                      setBindingForm((prev) => ({
                        ...prev,
                        promptTemplateId: Number(value),
                      }))
                    }
                  >
                    <SelectTrigger>
                      <SelectValue placeholder={t('common.select', 'Select')} />
                    </SelectTrigger>
                    <SelectContent>
                      {templates.map((tpl) => (
                        <SelectItem key={tpl.id} value={String(tpl.id)}>
                          {tpl.name}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
              </div>

              <div className="flex justify-end gap-2">
                <Button
                  variant="outline"
                  onClick={() => setBindingForm(DEFAULT_BINDING_FORM)}
                  disabled={bindingSaving}
                >
                  {t('common.reset', 'Reset')}
                </Button>
                <Button onClick={handleBindingSubmit} disabled={bindingSaving}>
                  {t('prompt.saveBinding', 'Save Binding')}
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>

      {/* New Template Dialog */}
      <Dialog open={newTemplateDialogOpen} onOpenChange={setNewTemplateDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>{t('prompt.createNewTemplate', 'Create New Template')}</DialogTitle>
            <DialogDescription>
              {t('prompt.createNewTemplateDesc', 'Create a new prompt template from scratch.')}
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div>
              <label className="text-sm font-medium">{t('prompt.templateName', 'Template Name')}</label>
              <Input
                value={newTemplateName}
                onChange={(e) => setNewTemplateName(e.target.value)}
                placeholder={t('prompt.myCustomTemplate', 'My Custom Template')}
              />
            </div>
            <div>
              <label className="text-sm font-medium">{t('prompt.descriptionOptional', 'Description (Optional)')}</label>
              <Input
                value={newTemplateDescription}
                onChange={(e) => setNewTemplateDescription(e.target.value)}
                placeholder={t('prompt.templateDescPlaceholder', 'Description of this template')}
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setNewTemplateDialogOpen(false)}>
              {t('common.cancel', 'Cancel')}
            </Button>
            <Button onClick={handleCreateTemplate} disabled={creating}>
              {t('common.create', 'Create')}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Copy Template Dialog */}
      <Dialog open={copyDialogOpen} onOpenChange={setCopyDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>{t('prompt.copyTemplate', 'Copy Template')}</DialogTitle>
            <DialogDescription>
              {t('prompt.copyTemplateDesc', 'Create a copy of "{name}".').replace('{name}', selectedTemplate?.name || '')}
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div>
              <label className="text-sm font-medium">{t('prompt.newNameOptional', 'New Name (Optional)')}</label>
              <Input
                value={copyName}
                onChange={(e) => setCopyName(e.target.value)}
                placeholder={`${selectedTemplate?.name} (Copy)`}
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setCopyDialogOpen(false)}>
              {t('common.cancel', 'Cancel')}
            </Button>
            <Button onClick={handleCopyTemplate} disabled={copying}>
              {t('prompt.copy', 'Copy')}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </>
  )
}

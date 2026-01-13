export interface NavigationItem {
  path: string
  label: string
  icon?: string
  description?: string
  children?: NavigationItem[]
}

export type NavigationItemType = 'link' | 'divider' | 'header'

export interface NavigationGroup {
  title: string
  items: NavigationItem[]
}

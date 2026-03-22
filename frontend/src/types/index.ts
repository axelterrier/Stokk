export interface Location {
  id: string
  name: string
  parent_id: string | null
  color: string | null
}

export interface LocationCreate {
  name: string
  parent_id?: string | null
  color?: string | null
}

export interface LocationUpdate {
  name?: string
  parent_id?: string | null
  color?: string | null
}

export interface Product {
  barcode: string
  name: string
  brand?: string
  category?: string
  image_url?: string
  nutriscore?: 'A' | 'B' | 'C' | 'D' | 'E'
  quantity_str?: string
  energy_kcal?: number
  proteins_g?: number
  carbs_g?: number
  fat_g?: number
}

export interface ScanResponse {
  found: boolean
  source?: 'cache' | 'openfoodfacts'
  product?: Product
}

export interface ExpiryDate {
  id: string
  expiry_date: string
  alert_days_before: number
  alerted: boolean
}

export interface StockItem {
  id: string
  product_barcode: string
  quantity: number
  unit: string
  location?: Location
  opened: boolean
  added_at: string
  product: Product
  expiry_date?: ExpiryDate
}

export interface StockItemUpdate {
  quantity?: number
  unit?: string
  location_id?: string | null
  opened?: boolean
  expiry_date?: string | null
  alert_days_before?: number
  clear_expiry?: boolean
}

export interface StockItemCreate {
  product_barcode: string
  quantity: number
  unit: string
  location_id?: string
  opened: boolean
  expiry_date?: string
  alert_days_before: number
}

export interface AppUser {
  id: string
  username: string
  email: string
  is_admin: boolean
  created_at: string
}

export interface UserCreate {
  username: string
  email: string
  password: string
  is_admin: boolean
}

export interface UserUpdate {
  password?: string
  is_admin?: boolean
}

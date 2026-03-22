export interface Product {
  barcode: string
  name: string
  brand?: string
  category?: string
  image_url?: string
  nutriscore?: 'A' | 'B' | 'C' | 'D' | 'E'
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
  location?: string
  opened: boolean
  added_at: string
  product: Product
  expiry_date?: ExpiryDate
}

export interface StockItemUpdate {
  quantity?: number
  unit?: string
  location?: string | null
  opened?: boolean
  expiry_date?: string | null
  alert_days_before?: number
  clear_expiry?: boolean
}

export interface StockItemCreate {
  product_barcode: string
  quantity: number
  unit: string
  location?: string
  opened: boolean
  expiry_date?: string
  alert_days_before: number
}

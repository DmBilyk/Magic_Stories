export interface BookingSettings {
  base_price_per_hour: string;
  deposit_percentage: string;
  opening_time: string;
  closing_time: string;
  min_booking_hours: number;
  max_booking_hours: number;
  advance_booking_days: number;
  is_booking_enabled: boolean;
  maintenance_message: string;
}

export interface TimeSlot {
  start_time: string;
  end_time: string;
  available: boolean;
}

export interface AdditionalService {
  id: string;
  name: string;
  description: string;
  price: string;
  is_active: boolean;
}

export interface CostCalculation {
  base_cost: string;
  services_cost: string;
  total_amount: string;
  deposit_amount: string;
  deposit_percentage: string;
  clothing_cost?: string;
  prop_cost?: string;
}

export interface BookingFormData {
  first_name: string;
  last_name: string;
  phone_number: string;
  email: string;
  booking_date: string;
  booking_time: string;
  duration_hours: number;
  additional_service_ids: string[];
  clothing_items?: { clothing_item_id: string; quantity: number }[];
  prop_items?: { prop_item_id: string; quantity: number }[];
  notes: string;
}

export interface Booking {
  id: string;
  first_name: string;
  last_name: string;
  phone_number: string;
  email: string;
  booking_date: string;
  booking_time: string;
  duration_hours: number;
  status: string;
  total_amount: string;
  deposit_amount: string;
  base_price_per_hour: string;
  services_total: string;
  payment?: PaymentInfo;
  clothing_summary?: ItemSummary;
  prop_summary?: ItemSummary;
}

export interface PaymentInfo {
  payment_id: string;
  amount: string;
  is_paid: boolean;
  liqpay_status: string;
  liqpay_data?: {
    data: string;
    signature: string;
    checkout_url: string;
  };
}

export interface ItemSummary {
  items: RentalItem[];
  items_count: number;
  total_cost: string;
}

export interface RentalItem {
  id: string;
  name: string;
  quantity: number;
  price: string;
  total: string;
}

export interface ClothingCategory {
  id: string;
  name: string;
  description: string;
  is_active: boolean;
  items_count: number;
}

export interface ClothingImage {
  id: string;
  image_url: string;
  alt_text: string;
  order: number;
}

export interface ClothingItem {
  id: string;
  name: string;
  description: string;
  category: ClothingCategory;
  category_name?: string;
  size: string;
  price: string;
  is_available: boolean;
  is_active: boolean;
  quantity: number;
  images?: ClothingImage[];
  primary_image?: ClothingImage;
}

export interface PropCategory {
  id: string;
  name: string;
  description: string;
  is_active: boolean;
  items_count: number;
}

export interface PropImage {
  id: string;
  image_url: string;
  alt_text: string;
  order: number;
}

export interface PropItem {
  id: string;
  name: string;
  description: string;
  category: PropCategory;
  category_name?: string;
  price: string;
  is_available: boolean;
  is_active: boolean;
  quantity: number;
  images?: PropImage[];
  primary_image?: PropImage;
}

export interface AvailabilityCheck {
  available: boolean;
  available_quantity: number;
  requested_quantity: number;
  message: string;
}

export interface AvailableItemsResponse {
  booking_date: string;
  booking_time: string;
  duration_hours: number;
  available_items: (ClothingItem | PropItem)[];
}

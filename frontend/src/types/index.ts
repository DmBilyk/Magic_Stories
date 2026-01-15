export interface Location {
  id: string;
  name: string;
  description: string;
  hourlyRate: string;
  imageUrl?: string;
  address?: string;
  capacity: number;
  amenities: string[];
  isActive: boolean;
  createdAt: string;
  updatedAt: string;
}

export interface AdditionalService {
  id: string;
  serviceId: string;
  name: string;
  description: string;
  price: string;
  durationMinutes: number;
  isActive: boolean;
}

export interface ClothingCategory {
  id: string;
  name: string;
  description: string;
  isActive: boolean;
}

export interface ClothingItem {
  id: string;
  name: string;
  description: string;
  category: ClothingCategory;
  categoryName?: string;
  size: string;
  price: string;
  isAvailable: boolean;
  isActive: boolean;
  quantity: number;
  primaryImage?: {
    id: string;
    imageUrl: string;
    altText: string;
  };
  images?: ClothingImage[];
}

export interface ClothingImage {
  id: string;
  image: string;
  imageUrl: string;
  altText: string;
  order: number;
}

export interface PropCategory {
  id: string;
  name: string;
  description: string;
  isActive: boolean;
}

export interface PropItem {
  id: string;
  name: string;
  description: string;
  category: PropCategory;
  categoryName?: string;
  price: string;
  isAvailable: boolean;
  isActive: boolean;
  quantity: number;
  primaryImage?: {
    id: string;
    imageUrl: string;
    altText: string;
  };
  images?: PropImage[];
}

export interface PropImage {
  id: string;
  imageUrl: string;
  altText: string;
  order: number;
}

export interface TimeSlot {
  startTime: string;
  endTime: string;
  available: boolean;
}

export interface AvailabilityResponse {
  date: string;
  durationHours: number;
  locationId: string;
  slots: TimeSlot[];
}

export interface BookingCostResponse {
  baseCost: string;
  hourlyRate: string;
  servicesCost: string;
  totalAmount: string;
  depositAmount: string;
  depositPercentage: string;
}

export interface BookingRequest {
  locationId: string;
  firstName: string;
  lastName: string;
  phoneNumber: string;
  email: string;
  bookingDate: string;
  bookingTime: string;
  durationHours: number;
  additionalServiceIds?: string[];
  clothingItems?: { clothingItemId: string; quantity: number }[];
  propItems?: { propItemId: string; quantity: number }[];
  notes?: string;
}

export interface Booking {
  id: string;
  location: Location;
  firstName: string;
  lastName: string;
  phoneNumber: string;
  email: string;
  bookingDate: string;
  bookingTime: string;
  durationHours: number;
  endTime: string;
  totalAmount: string;
  depositAmount: string;
  status: string;
  clothingSummary?: {
    totalItems: number;
    totalCost: string;
  };
  propSummary?: {
    totalItems: number;
    totalCost: string;
  };
}

export interface BookingResponse {
  booking: Booking;
  payment: {
    paymentId: string;
    amount: string;
    liqpayData: {
      data: string;
      signature: string;
    };
  };
}

export interface CartClothingItem {
  item: ClothingItem;
  quantity: number;
}

export interface CartPropItem {
  item: PropItem;
  quantity: number;
}

export interface BookingSettings {
  basePricePerHour: string;
  depositPercentage: string;
  openingTime: string;
  closingTime: string;
  minBookingHours: number;
  maxBookingHours: number;
  advanceBookingDays: number;
  isBookingEnabled: boolean;
  maintenanceMessage: string;
}

export interface AvailabilityParams {
  itemId: string;
  bookingDate: string;
  bookingTime: string;
  durationHours: number;
  quantity: number;
}

export interface ValidationError {
  paramName: string;
  errorMessage: string;
}

export interface AssertAllParamsWithErrorsResult<T> {
  isValid: boolean;
  missingParams: string[];
  params: T;
  errors: ValidationError[];
}
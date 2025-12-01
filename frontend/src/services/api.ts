import { API_ENDPOINTS, fetchAPI } from '../config/api';
import type {
  Location,
  AdditionalService,
  ClothingCategory,
  ClothingItem,
  PropCategory,
  PropItem,
  AvailabilityResponse,
  BookingCostResponse,
  BookingRequest,
  BookingResponse,
  BookingSettings,
} from '../types';


const toCamelCase = (obj: any): any => {
  if (Array.isArray(obj)) {
    return obj.map(v => toCamelCase(v));
  } else if (obj !== null && obj.constructor === Object) {
    return Object.keys(obj).reduce((result, key) => {
      const camelKey = key.replace(/_([a-z])/g, (_, letter) => letter.toUpperCase());
      result[camelKey] = toCamelCase(obj[key]);
      return result;
    }, {} as any);
  }
  return obj;
};

export const locationService = {
  getAll: () => fetchAPI<Location[]>(API_ENDPOINTS.locations),
  getById: (id: string) => fetchAPI<Location>(`${API_ENDPOINTS.locations}${id}/`),
};

export const serviceAPI = {
  getAll: () => fetchAPI<AdditionalService[]>(API_ENDPOINTS.services),
};

export const availabilityService = {
  checkAvailability: (date: string, durationHours: number, locationId?: string) => {
    const requestBody: any = {
      date: date.split('T')[0],
      duration_hours: durationHours,
    };

    if (locationId && locationId.trim() !== '') {
      requestBody.location_id = locationId;
    }

    console.log('Sending availability check:', requestBody);

    return fetchAPI<AvailabilityResponse>(
      `${API_ENDPOINTS.availability}check-availability/`,
      {
        method: 'POST',
        body: JSON.stringify(requestBody),
      }
    );
  },

  isSlotAvailable: (bookingDate: string, bookingTime: string, durationHours: number, locationId: string) =>
    fetchAPI<{ available: boolean; message: string }>(
      `${API_ENDPOINTS.availability}is-slot-available/`,
      {
        method: 'POST',
        body: JSON.stringify({
          booking_date: bookingDate.split('T')[0],
          booking_time: bookingTime,
          duration_hours: durationHours,
          location_id: locationId,
        }),
      }
    ),

  calculateCost: (durationHours: number, locationId?: string, serviceIds?: string[]) => {
    const requestBody: any = {
      duration_hours: durationHours,
      additional_service_ids: serviceIds || [],
    };

    if (locationId && locationId.trim() !== '') {
      requestBody.location_id = locationId;
    }

    console.log('Sending cost calculation:', requestBody);

    return fetchAPI<BookingCostResponse>(
      `${API_ENDPOINTS.availability}calculate-cost/`,
      {
        method: 'POST',
        body: JSON.stringify(requestBody),
      }
    );
  },
};

export const bookingService = {
  create: (data: BookingRequest) =>
    fetchAPI<BookingResponse>(API_ENDPOINTS.bookings, {
      method: 'POST',
      body: JSON.stringify({
        location_id: data.locationId,
        first_name: data.firstName,
        last_name: data.lastName,
        phone_number: data.phoneNumber,
        email: data.email,
        booking_date: data.bookingDate,
        booking_time: data.bookingTime,
        duration_hours: data.durationHours,
        additional_service_ids: data.additionalServiceIds || [],
        clothing_items: data.clothingItems || [],
        prop_items: data.propItems || [],
        notes: data.notes || '',
      }),
    }),

  getSettings: () => fetchAPI<BookingSettings>(API_ENDPOINTS.bookingSettings),
};

export const clothingService = {
  getCategories: () => fetchAPI<ClothingCategory[]>(API_ENDPOINTS.clothingCategories),

  getItems: async (params?: { category?: string; availableOnly?: boolean; search?: string }) => {
    const queryParams = new URLSearchParams();
    if (params?.category) queryParams.append('category', params.category);
    if (params?.availableOnly) queryParams.append('available_only', 'true');
    if (params?.search) queryParams.append('search', params.search);

    const url = queryParams.toString()
      ? `${API_ENDPOINTS.clothingItems}?${queryParams.toString()}`
      : API_ENDPOINTS.clothingItems;

    // 🔧 Fetch and transform snake_case to camelCase
    const data = await fetchAPI<any[]>(url);
    const transformed = toCamelCase(data) as ClothingItem[];

    console.log('🔄 Transformed clothing items:', transformed);
    return transformed;
  },

  getItemById: async (id: string) => {
    const data = await fetchAPI<any>(`${API_ENDPOINTS.clothingItems}${id}/`);
    return toCamelCase(data) as ClothingItem;
  },

  checkAvailability: async (
    itemId: string,
    bookingDate: string,
    bookingTime: string,
    durationHours: number,
    quantity: number
  ) => {
    if (!itemId || !bookingDate || !bookingTime || !durationHours || !quantity) {
      throw new Error('Missing required parameters for availability check');
    }

    const formattedDate = bookingDate.includes('T') ? bookingDate.split('T')[0] : bookingDate;

    const payload = {
      clothing_item_id: itemId,
      booking_date: formattedDate,
      booking_time: bookingTime,
      duration_hours: durationHours,
      quantity,
    };

    console.log('Checking clothing item availability with payload:', payload);

    const data = await fetchAPI<any>(
      `${API_ENDPOINTS.clothingItems}${itemId}/check-availability/`,
      {
        method: 'POST',
        body: JSON.stringify(payload),
      }
    );

    return toCamelCase(data) as {
      itemId: string;
      itemName: string;
      available: boolean;
      availableQuantity: number;
      requestedQuantity: number;
      message: string;
    };
  },

  getAvailableItems: async (bookingDate: string, bookingTime: string, durationHours: number) => {
    const data = await fetchAPI<any>(`${API_ENDPOINTS.clothingAvailability}available-items/`, {
      method: 'POST',
      body: JSON.stringify({
        booking_date: bookingDate,
        booking_time: bookingTime,
        duration_hours: durationHours,
      }),
    });

    return toCamelCase(data) as {
      bookingDate: string;
      bookingTime: string;
      durationHours: number;
      availableItems: ClothingItem[];
    };
  },

  calculateCost: async (items: { clothingItemId: string; quantity: number }[]) => {
    const data = await fetchAPI<any>(`${API_ENDPOINTS.clothingAvailability}calculate-cost/`, {
      method: 'POST',
      body: JSON.stringify({ clothing_items: items }),
    });

    return toCamelCase(data) as {
      clothingCost: string;
      itemsCount: number;
      itemsDetails: Array<{
        itemId: string;
        name: string;
        size: string;
        quantity: number;
        pricePerItem: string;
        total: string;
      }>;
    };
  },
};

export const propService = {
  getCategories: () => fetchAPI<PropCategory[]>(API_ENDPOINTS.propCategories),

  getItems: async (params?: { category?: string; availableOnly?: boolean; search?: string }) => {
    const queryParams = new URLSearchParams();
    if (params?.category) queryParams.append('category', params.category);
    if (params?.availableOnly) queryParams.append('available_only', 'true');
    if (params?.search) queryParams.append('search', params.search);

    const url = queryParams.toString()
      ? `${API_ENDPOINTS.propItems}?${queryParams.toString()}`
      : API_ENDPOINTS.propItems;

    // 🔧 Fetch and transform snake_case to camelCase
    const data = await fetchAPI<any[]>(url);
    return toCamelCase(data) as PropItem[];
  },

  getItemById: async (id: string) => {
    const data = await fetchAPI<any>(`${API_ENDPOINTS.propItems}${id}/`);
    return toCamelCase(data) as PropItem;
  },

  checkAvailability: async (
    itemId: string,
    bookingDate: string,
    bookingTime: string,
    durationHours: number,
    quantity: number
  ) => {
    if (!itemId || !bookingDate || !bookingTime || !durationHours || !quantity) {
      throw new Error('Missing required parameters for availability check');
    }

    const formattedDate = bookingDate.includes('T') ? bookingDate.split('T')[0] : bookingDate;

    const payload = {
      prop_item_id: itemId,
      booking_date: formattedDate,
      booking_time: bookingTime,
      duration_hours: durationHours,
      quantity,
    };

    console.log('Checking prop item availability with payload:', payload);

    const data = await fetchAPI<any>(
      `${API_ENDPOINTS.propItems}${itemId}/check-availability/`,
      {
        method: 'POST',
        body: JSON.stringify(payload),
      }
    );

    return toCamelCase(data) as {
      itemId: string;
      itemName: string;
      available: boolean;
      availableQuantity: number;
      requestedQuantity: number;
      message: string;
    };
  },

  getAvailableItems: async (bookingDate: string, bookingTime: string, durationHours: number) => {
    const data = await fetchAPI<any>(`${API_ENDPOINTS.propAvailability}available-items/`, {
      method: 'POST',
      body: JSON.stringify({
        booking_date: bookingDate,
        booking_time: bookingTime,
        duration_hours: durationHours,
      }),
    });

    return toCamelCase(data) as {
      bookingDate: string;
      bookingTime: string;
      durationHours: number;
      availableItems: PropItem[];
    };
  },

  calculateCost: async (items: { propItemId: string; quantity: number }[]) => {
    const data = await fetchAPI<any>(`${API_ENDPOINTS.propAvailability}calculate-cost/`, {
      method: 'POST',
      body: JSON.stringify({ prop_items: items }),
    });

    return toCamelCase(data) as {
      propCost: string;
      itemsCount: number;
      itemsDetails: Array<{
        itemId: string;
        name: string;
        quantity: number;
        pricePerItem: string;
        total: string;
      }>;
    };
  },
};
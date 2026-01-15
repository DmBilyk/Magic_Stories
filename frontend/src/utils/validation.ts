import type { AssertAllParamsWithErrorsResult, ValidationError } from '../types';


export const validatePhoneNumber = (phone: string): { valid: boolean; message: string } => {
  if (!phone || phone.trim().length === 0) {
    return { valid: false, message: "Номер телефону обов'язковий" };
  }

  // Видаляємо всі символи крім цифр та +
  const cleanPhone = phone.replace(/[\s\-\(\)]/g, '');

  // Перевіряємо базовий формат
  const phoneRegex = /^(\+?380|0)\d{9}$/;

  if (!phoneRegex.test(cleanPhone)) {
    return {
      valid: false,
      message: 'Введіть номер у форматі +380XXXXXXXXX або 0XXXXXXXXX'
    };
  }

  // Перевіряємо що після +380 або 0 йде валідний код оператора
  const operatorCode = cleanPhone.startsWith('+380')
    ? cleanPhone.substring(4, 6)
    : cleanPhone.startsWith('380')
    ? cleanPhone.substring(3, 5)
    : cleanPhone.substring(1, 3);

  const validOperatorCodes = [
    '39', '50', '63', '66', '67', '68', '73', '91', '92', '93', '94', '95', '96', '97', '98', '99'
  ];

  if (!validOperatorCodes.includes(operatorCode)) {
    return {
      valid: false,
      message: 'Невірний код оператора'
    };
  }

  return { valid: true, message: '' };
};

/**
 * Нормалізація номера телефону до формату +380XXXXXXXXX
 */
export const normalizePhoneNumber = (phone: string): string => {
  const cleanPhone = phone.replace(/[\s\-\(\)]/g, '');

  if (cleanPhone.startsWith('+380')) {
    return cleanPhone;
  }

  if (cleanPhone.startsWith('380')) {
    return '+' + cleanPhone;
  }

  if (cleanPhone.startsWith('0')) {
    return '+38' + cleanPhone;
  }

  return cleanPhone;
};

/**
 * Валідація email
 */
export const validateEmail = (email: string): { valid: boolean; message: string } => {
  if (!email || email.trim().length === 0) {
    return { valid: false, message: "Email обов'язковий" };
  }

  // RFC 5322 compliant regex (спрощена версія)
  const emailRegex = /^[a-zA-Z0-9.!#$%&'*+/=?^_`{|}~-]+@[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?(?:\.[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)*$/;

  if (!emailRegex.test(email)) {
    return {
      valid: false,
      message: 'Введіть коректний email (наприклад: ivan@example.com)'
    };
  }

  // Додаткові перевірки
  if (email.length > 254) {
    return { valid: false, message: 'Email занадто довгий' };
  }

  const [localPart, domain] = email.split('@');

  if (localPart.length > 64) {
    return { valid: false, message: 'Email занадто довгий' };
  }

  // Перевіряємо що домен має точку
  if (!domain.includes('.')) {
    return { valid: false, message: 'Невірний формат email (відсутній домен)' };
  }

  // Перевіряємо що немає послідовних крапок
  if (email.includes('..')) {
    return { valid: false, message: 'Email містить недопустимі символи' };
  }

  return { valid: true, message: '' };
};

/**
 * Валідація імені/прізвища
 */
export const validateName = (name: string, fieldName: string): { valid: boolean; message: string } => {
  if (!name || name.trim().length === 0) {
    return { valid: false, message: `${fieldName} обов'язкове` };
  }

  if (name.trim().length < 2) {
    return {
      valid: false,
      message: `${fieldName} має містити мінімум 2 символи`
    };
  }

  if (name.trim().length > 50) {
    return {
      valid: false,
      message: `${fieldName} занадто довге (максимум 50 символів)`
    };
  }

  // Дозволяємо тільки літери (українські, англійські), пробіли, апострофи та дефіси
  const nameRegex = /^[a-zA-Zа-яА-ЯіІїЇєЄґҐ'\s-]+$/;

  if (!nameRegex.test(name)) {
    return {
      valid: false,
      message: `${fieldName} може містити тільки літери, пробіли та дефіси`
    };
  }

  return { valid: true, message: '' };
};

/**
 * Валідація нотаток
 */
export const validateNotes = (notes: string): { valid: boolean; message: string } => {
  if (notes.trim().length > 500) {
    return {
      valid: false,
      message: 'Нотатки занадто довгі (максимум 500 символів)'
    };
  }

  return { valid: true, message: '' };
};

/**
 * Комплексна валідація форми бронювання
 */
export interface BookingFormData {
  firstName: string;
  lastName: string;
  phone: string;
  email: string;
  bookingDate: string;
  bookingTime: string;
  notes?: string;
}

export interface ValidationErrors {
  firstName?: string;
  lastName?: string;
  phone?: string;
  email?: string;
  date?: string;
  time?: string;
  notes?: string;
}

export const validateBookingForm = (data: BookingFormData): {
  valid: boolean;
  errors: ValidationErrors;
  normalizedData?: Partial<BookingFormData>;
} => {
  const errors: ValidationErrors = {};
  const normalizedData: Partial<BookingFormData> = {};

  // Валідація імені
  const firstNameValidation = validateName(data.firstName, "Ім'я");
  if (!firstNameValidation.valid) {
    errors.firstName = firstNameValidation.message;
  } else {
    normalizedData.firstName = data.firstName.trim();
  }

  // Валідація прізвища
  const lastNameValidation = validateName(data.lastName, "Прізвище");
  if (!lastNameValidation.valid) {
    errors.lastName = lastNameValidation.message;
  } else {
    normalizedData.lastName = data.lastName.trim();
  }

  // Валідація телефону
  const phoneValidation = validatePhoneNumber(data.phone);
  if (!phoneValidation.valid) {
    errors.phone = phoneValidation.message;
  } else {
    normalizedData.phone = normalizePhoneNumber(data.phone);
  }

  // Валідація email
  const emailValidation = validateEmail(data.email);
  if (!emailValidation.valid) {
    errors.email = emailValidation.message;
  } else {
    normalizedData.email = data.email.trim().toLowerCase();
  }

  // Валідація дати
  if (!data.bookingDate) {
    errors.date = 'Будь ласка, оберіть дату';
  } else {
    normalizedData.bookingDate = data.bookingDate;
  }

  // Валідація часу
  if (!data.bookingTime) {
    errors.time = 'Будь ласка, оберіть час';
  } else {
    normalizedData.bookingTime = data.bookingTime;
  }

  // Валідація нотаток (опціонально)
  if (data.notes) {
    const notesValidation = validateNotes(data.notes);
    if (!notesValidation.valid) {
      errors.notes = notesValidation.message;
    } else {
      normalizedData.notes = data.notes.trim();
    }
  }

  return {
    valid: Object.keys(errors).length === 0,
    errors,
    normalizedData: Object.keys(errors).length === 0 ? normalizedData : undefined
  };
};

export function assertAllParamsWithErrors<T extends Record<string, any>>(
  params: T,
  requiredParams: string[],
): AssertAllParamsWithErrorsResult<T> {

  const validationErrors: ValidationError[] = [];
  const missingParams: string[] = [];

  for (const param of requiredParams) {
    const value = params[param];


    const isInvalidString = typeof value === "string" && value.trim() === "";


    const isValid = value !== undefined && value !== null && !isInvalidString;

    if (!isValid) {
      missingParams.push(param);
      validationErrors.push({
        paramName: param,
        errorMessage: `Missing or invalid parameter: ${param}`,
      });
    }
  }

  return {
    isValid: missingParams.length === 0,
    missingParams,
    params,
    errors: validationErrors,
  };
}
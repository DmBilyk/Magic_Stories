export const getTodayDate = (): string => {
  const today = new Date();
  const year = today.getFullYear();
  const month = String(today.getMonth() + 1).padStart(2, '0');
  const day = String(today.getDate()).padStart(2, '0');
  return `${year}-${month}-${day}`;
};

export const getMaxBookingDate = (advanceDays: number): string => {
  const maxDate = new Date();
  maxDate.setDate(maxDate.getDate() + advanceDays);
  const year = maxDate.getFullYear();
  const month = String(maxDate.getMonth() + 1).padStart(2, '0');
  const day = String(maxDate.getDate()).padStart(2, '0');
  return `${year}-${month}-${day}`;
};

export const formatTime = (time: string): string => {
  if (!time) return '';
  const [hours, minutes] = time.split(':');
  return `${hours}:${minutes}`;
};

export const formatTimeRange = (startTime: string, durationHours: number): string => {
  const [hours, minutes] = startTime.split(':').map(Number);
  const startDate = new Date();
  startDate.setHours(hours, minutes, 0);

  const endDate = new Date(startDate);
  endDate.setHours(endDate.getHours() + durationHours);

  return `${formatTime(startTime)} - ${formatTime(
    `${String(endDate.getHours()).padStart(2, '0')}:${String(endDate.getMinutes()).padStart(2, '0')}`
  )}`;
};

export const generateTimeSlots = (
  openingTime: string,
  closingTime: string,
  durationHours: number
): string[] => {
  const slots: string[] = [];
  const [openHour, openMin] = openingTime.split(':').map(Number);
  const [closeHour, closeMin] = closingTime.split(':').map(Number);

  const openingMinutes = openHour * 60 + openMin;
  const closingMinutes = closeHour * 60 + closeMin;
  const durationMinutes = durationHours * 60;

  for (let time = openingMinutes; time + durationMinutes <= closingMinutes; time += 60) {
    const hours = Math.floor(time / 60);
    const minutes = time % 60;
    slots.push(`${String(hours).padStart(2, '0')}:${String(minutes).padStart(2, '0')}`);
  }

  return slots;
};

export const isTimeSlotInPast = (date: string, time: string | undefined): boolean => {
  if (!date || !time) return false; // або true, залежно від логіки
  const [year, month, day] = date.split('-').map(Number);
  const [hours, minutes] = time.split(':').map(Number);
  const slotDateTime = new Date(year, month - 1, day, hours, minutes);
  return slotDateTime < new Date();
};


export const formatCurrency = (amount: string | number): string => {
  const num = typeof amount === 'string' ? parseFloat(amount) : amount;
  return `₴${num.toFixed(2)}`;
};

export const formatDate = (dateString: string): string => {
  const date = new Date(dateString);
  return date.toLocaleDateString('uk-UA', {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
  });
};

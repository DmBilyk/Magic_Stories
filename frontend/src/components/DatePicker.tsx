import { useState, useEffect } from 'react';
import { ChevronLeft, ChevronRight, Calendar } from 'lucide-react';

interface DatePickerProps {
  selectedDate: string;
  onChange: (date: string) => void;
  minDate: string;
  maxDate: string;
  error?: string;
}

export const DatePicker = ({ selectedDate, onChange, minDate, maxDate, error }: DatePickerProps) => {
  const [isOpen, setIsOpen] = useState(false);
  const [currentMonth, setCurrentMonth] = useState(() => {
    if (selectedDate) return new Date(selectedDate + 'T00:00:00');
    const today = new Date();
    today.setHours(0, 0, 0, 0);
    return today;
  });

  useEffect(() => {
    if (selectedDate) {
      const date = new Date(selectedDate + 'T00:00:00');
      setCurrentMonth(date);
    }
  }, [selectedDate]);

  const formatDisplayDate = (dateStr: string) => {
    if (!dateStr) return 'Оберіть дату';
    const date = new Date(dateStr);
    return date.toLocaleDateString('uk-UA', {
      day: 'numeric',
      month: 'long',
      year: 'numeric'
    });
  };

  const getDaysInMonth = (date: Date) => {
    const year = date.getFullYear();
    const month = date.getMonth();
    const firstDay = new Date(year, month, 1);
    const lastDay = new Date(year, month + 1, 0);
    const daysInMonth = lastDay.getDate();
    const startingDayOfWeek = firstDay.getDay();

    return { daysInMonth, startingDayOfWeek, year, month };
  };

  const isDateDisabled = (dateStr: string) => {
    return dateStr < minDate || dateStr > maxDate;
  };

  const handlePrevMonth = () => {
    setCurrentMonth(new Date(currentMonth.getFullYear(), currentMonth.getMonth() - 1));
  };

  const handleNextMonth = () => {
    setCurrentMonth(new Date(currentMonth.getFullYear(), currentMonth.getMonth() + 1));
  };

  const handleDateSelect = (day: number) => {
    const year = currentMonth.getFullYear();
    const month = currentMonth.getMonth();
    const dateStr = `${year}-${String(month + 1).padStart(2, '0')}-${String(day).padStart(2, '0')}`;

    if (!isDateDisabled(dateStr)) {
      onChange(dateStr);
      setIsOpen(false);
    }
  };

  const { daysInMonth, startingDayOfWeek, year, month } = getDaysInMonth(currentMonth);
  const monthName = currentMonth.toLocaleDateString('uk-UA', { month: 'long', year: 'numeric' });
  const adjustedStartDay = startingDayOfWeek === 0 ? 6 : startingDayOfWeek - 1;

  return (
    <div className="relative">
      <button
        type="button"
        onClick={() => setIsOpen(!isOpen)}
        className={`w-full px-5 py-4 bg-white border text-left flex items-center justify-between transition-all hover:border-slate-400 focus:outline-none focus:ring-1 focus:ring-slate-900 rounded-none ${
          error ? 'border-red-400 focus:ring-red-100' : 'border-slate-200'
        }`}
      >
        <span className={selectedDate ? 'text-slate-900 font-medium' : 'text-slate-400'}>
          {formatDisplayDate(selectedDate)}
        </span>
        <Calendar className="w-5 h-5 text-slate-500" />
      </button>

      {error && <p className="text-red-600 text-sm mt-2 ml-1">{error}</p>}

      {isOpen && (
        <>
          <div
            className="fixed inset-0 z-10"
            onClick={() => setIsOpen(false)}
          />
          <div className="absolute top-full left-0 mt-2 bg-white shadow-xl border border-slate-100 p-6 z-20 w-80 sm:w-96 rounded-none">
            {/* Month Navigation */}
            <div className="flex items-center justify-between mb-6">
              <button
                type="button"
                onClick={handlePrevMonth}
                className="p-2 hover:bg-slate-100 transition-colors text-slate-600 rounded-none"
              >
                <ChevronLeft className="w-5 h-5" />
              </button>
              <h3 className="font-semibold text-slate-900 capitalize text-lg">
                {monthName}
              </h3>
              <button
                type="button"
                onClick={handleNextMonth}
                className="p-2 hover:bg-slate-100 transition-colors text-slate-600 rounded-none"
              >
                <ChevronRight className="w-5 h-5" />
              </button>
            </div>

            {/* Weekday Headers */}
            <div className="grid grid-cols-7 gap-1 mb-3">
              {['Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб', 'Нд'].map((day) => (
                <div key={day} className="text-center text-xs font-medium text-slate-400 py-2">
                  {day}
                </div>
              ))}
            </div>

            {/* Calendar Days */}
            <div className="grid grid-cols-7 gap-1">
              {Array.from({ length: adjustedStartDay }).map((_, i) => (
                <div key={`empty-${i}`} />
              ))}

              {Array.from({ length: daysInMonth }).map((_, i) => {
                const day = i + 1;
                const dateStr = `${year}-${String(month + 1).padStart(2, '0')}-${String(day).padStart(2, '0')}`;
                const isDisabled = isDateDisabled(dateStr);
                const isSelected = selectedDate === dateStr;
                const isToday = dateStr === new Date().toISOString().split('T')[0];

                return (
                  <button
                    key={day}
                    type="button"
                    onClick={() => handleDateSelect(day)}
                    disabled={isDisabled}
                    className={`
                      aspect-square p-2 text-sm font-medium transition-all rounded-none
                      ${isSelected 
                        ? 'bg-slate-900 text-white' 
                        : isToday && !isDisabled
                        ? 'text-slate-900 font-bold bg-slate-100'
                        : isDisabled
                        ? 'text-slate-200 cursor-not-allowed'
                        : 'text-slate-700 hover:bg-slate-100'
                      }
                    `}
                  >
                    {day}
                  </button>
                );
              })}
            </div>
          </div>
        </>
      )}
    </div>
  );
};
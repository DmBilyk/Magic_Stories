import { useState } from 'react';
import { Menu, X, ChevronDown } from 'lucide-react';
import { useNavigate, useLocation } from 'react-router-dom';

export const Header = () => {
  const [isMenuOpen, setIsMenuOpen] = useState(false);
  const [isDropdownOpen, setIsDropdownOpen] = useState(false); // Стан для випадаючого меню
  const navigate = useNavigate();
  const location = useLocation();

  // Основні пункти меню
  const mainLinks = [
    { label: 'Про нас', id: 'about' },
    { label: 'Галерея', id: 'gallery' },
  ];

  // Пункти випадаючого меню "Інформація"
  const infoLinks = [
    { label: 'Реквізит', id: 'details' }, // Вже є в Home.tsx
    { label: 'Устаткування', id: 'equipment' }, // Заглушка (поки нікуди не скролить або скролить до футера)
    { label: 'Акції', id: 'offers' },
    { label: 'Правила', id: 'rules' },
    { label: 'Заборонено', id: 'prohibitions' }
  ];

  const scrollToSection = (sectionId: string) => {
    // Закриваємо меню після кліку
    setIsMenuOpen(false);
    setIsDropdownOpen(false);

    if (location.pathname !== '/') {
      navigate('/');
      setTimeout(() => {
        const element = document.getElementById(sectionId);
        if (element) element.scrollIntoView({ behavior: 'smooth' });
      }, 100);
    } else {
      const element = document.getElementById(sectionId);
      if (element) {
        element.scrollIntoView({ behavior: 'smooth' });
      }
    }
  };

  const handleBookingClick = () => {
    navigate('/booking');
    setIsMenuOpen(false);
  };

  return (
    <header className="fixed top-0 left-0 right-0 z-50 bg-white border-b border-neutral-200">
      <div className="max-w-7xl mx-auto px-6">
        <div className="flex justify-between items-center h-20">

          {/* Logo */}
          <div
            onClick={() => navigate('/')}
            className="flex items-center cursor-pointer group"
          >
            <img
              src="/assets/logo/logo.PNG"
              alt="Magic Stories Logo"
              className="h-12 w-auto object-contain mr-3"
            />
            <span className="text-xl font-light text-black tracking-wider group-hover:tracking-widest transition-all duration-300">
              Magic Stories
            </span>
          </div>

          {/* Desktop Navigation */}
          <nav className="hidden md:flex items-center space-x-12">
            {/* Рендеримо основні посилання */}
            {mainLinks.map((item) => (
              <button
                key={item.id}
                onClick={() => scrollToSection(item.id)}
                className="text-sm text-neutral-500 hover:text-black transition-colors tracking-wider uppercase font-light"
              >
                {item.label}
              </button>
            ))}

            {/* Випадаюче меню "ІНФОРМАЦІЯ" */}
            <div
              className="relative group h-20 flex items-center"
              onMouseEnter={() => setIsDropdownOpen(true)}
              onMouseLeave={() => setIsDropdownOpen(false)}
            >
              <button
                className={`flex items-center text-sm transition-colors tracking-wider uppercase font-light ${
                  isDropdownOpen ? 'text-black' : 'text-neutral-500 hover:text-black'
                }`}
              >
                Інформація
                <ChevronDown className={`w-4 h-4 ml-1 transition-transform duration-300 ${isDropdownOpen ? 'rotate-180' : ''}`} />
              </button>

              {/* Dropdown Content */}
              <div
                className={`absolute top-full left-1/2 -translate-x-1/2 w-48 bg-white border border-neutral-200 shadow-lg py-2 transition-all duration-200 origin-top ${
                  isDropdownOpen 
                    ? 'opacity-100 scale-100 visible' 
                    : 'opacity-0 scale-95 invisible'
                }`}
              >
                <div className="flex flex-col">
                  {infoLinks.map((item) => (
                    <button
                      key={item.id}
                      onClick={() => scrollToSection(item.id)}
                      className="text-left px-6 py-3 text-xs text-neutral-500 hover:text-black hover:bg-neutral-50 transition-colors tracking-wider uppercase font-light"
                    >
                      {item.label}
                    </button>
                  ))}
                </div>
              </div>
            </div>

            {/* Кнопка Бронювання */}
            <button
              onClick={handleBookingClick}
              className="px-8 py-3 bg-black text-white text-sm font-light tracking-wider hover:bg-neutral-800 transition-colors uppercase"
            >
              Забронювати
            </button>
          </nav>

          {/* Mobile Menu Button */}
          <button
            onClick={() => setIsMenuOpen(!isMenuOpen)}
            className="md:hidden p-2 text-black hover:bg-neutral-50 transition-colors"
            aria-label="Toggle menu"
          >
            {isMenuOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
          </button>
        </div>

        {/* Mobile Navigation */}
        {isMenuOpen && (
          <nav className="md:hidden py-6 border-t border-neutral-200 max-h-[calc(100vh-80px)] overflow-y-auto">
            <div className="flex flex-col space-y-4">

              {/* Основні посилання мобільні */}
              {mainLinks.map((item) => (
                 <button
                   key={item.id}
                   onClick={() => scrollToSection(item.id)}
                   className="text-left text-black font-light tracking-wider uppercase text-sm py-2 hover:translate-x-2 transition-transform"
                 >
                   {item.label}
                 </button>
               ))}

              {/* Роздільник для інфо */}
              <div className="pt-2 pb-1 border-b border-neutral-100">
                <span className="text-xs text-neutral-400 font-light uppercase tracking-widest">
                  Детальна інформація
                </span>
              </div>

              {/* Додаткові посилання мобільні */}
              {infoLinks.map((item) => (
                 <button
                   key={item.id}
                   onClick={() => scrollToSection(item.id)}
                   className="text-left text-neutral-600 font-light tracking-wider uppercase text-sm py-1 pl-4 hover:text-black transition-colors"
                 >
                   {item.label}
                 </button>
               ))}

              <div className="pt-4">
                <button
                  onClick={handleBookingClick}
                  className="w-full py-4 bg-black text-white font-light tracking-wider hover:bg-neutral-800 transition-colors text-sm uppercase"
                >
                  Забронювати
                </button>
              </div>
            </div>
          </nav>
        )}
      </div>
    </header>
  );
};
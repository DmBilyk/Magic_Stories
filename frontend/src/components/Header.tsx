import { useState } from 'react';
import { Menu, X, Calendar } from 'lucide-react';

export const Header = () => {
  const [isMenuOpen, setIsMenuOpen] = useState(false);

  const scrollToSection = (sectionId: string) => {
    const element = document.getElementById(sectionId);
    if (element) {
      element.scrollIntoView({ behavior: 'smooth' });
      setIsMenuOpen(false);
    }
  };

  return (
    <header className="fixed top-0 left-0 right-0 z-50 bg-white border-b border-neutral-200">
      <div className="max-w-7xl mx-auto px-6">
        <div className="flex justify-between items-center h-20">
          {/* Logo */}
          <div className="flex items-center cursor-pointer group">
            <Calendar className="w-5 h-5 text-black mr-3 group-hover:rotate-12 transition-transform duration-300" />
            <span className="text-xl font-light text-black tracking-wider">
              StudioBook
            </span>
          </div>

          {/* Desktop Navigation */}
          <nav className="hidden md:flex items-center space-x-12">
            {[
              { label: 'Про нас', id: 'about' },
              { label: 'Можливості', id: 'amenities' },
              { label: 'Галерея', id: 'gallery' }
            ].map((item) => (
              <button
                key={item.id}
                onClick={() => scrollToSection(item.id)}
                className="text-sm text-neutral-500 hover:text-black transition-colors tracking-wider uppercase font-light"
              >
                {item.label}
              </button>
            ))}

            <button
              onClick={() => scrollToSection('booking')}
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
          <nav className="md:hidden py-6 border-t border-neutral-200">
            <div className="flex flex-col space-y-4">
              {[
                { label: 'Про нас', id: 'about' },
                { label: 'Можливості', id: 'amenities' },
                { label: 'Галерея', id: 'gallery' }
              ].map((item) => (
                <button
                  key={item.id}
                  onClick={() => scrollToSection(item.id)}
                  className="text-left text-black font-light tracking-wider uppercase text-sm py-2 hover:translate-x-2 transition-transform"
                >
                  {item.label}
                </button>
              ))}
              <button
                onClick={() => scrollToSection('booking')}
                className="w-full py-4 bg-black text-white font-light tracking-wider hover:bg-neutral-800 transition-colors text-sm uppercase mt-4"
              >
                Забронювати
              </button>
            </div>
          </nav>
        )}
      </div>
    </header>
  );
};
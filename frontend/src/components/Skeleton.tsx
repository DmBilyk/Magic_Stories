interface SkeletonProps {
  className?: string;
}

export const Skeleton = ({ className = "" }: SkeletonProps) => {
  return <div className={`skeleton ${className}`} />;
};

// Спеціальний скелет для сторінки бронювання, щоб не захаращувати основний файл
export const BookingFormSkeleton = () => {
  return (
    <div className="min-h-screen bg-slate-50">
      {/* Header Skeleton */}
      <div className="bg-white border-b border-slate-200 py-5">
        <div className="max-w-7xl mx-auto px-4">
          <Skeleton className="w-32 h-6" />
        </div>
      </div>

      <div className="max-w-4xl mx-auto px-4 py-10 space-y-10">
        {/* Hero Section Skeleton */}
        <div className="bg-white border border-slate-200 p-8 shadow-sm">
          <div className="flex justify-between items-start mb-4">
            <div className="space-y-3 w-2/3">
              <Skeleton className="w-3/4 h-8" /> {/* Title */}
              <Skeleton className="w-1/2 h-4" /> {/* Address */}
            </div>
            <Skeleton className="w-24 h-10" /> {/* Price */}
          </div>
          <div className="space-y-2">
            <Skeleton className="w-full h-4" />
            <Skeleton className="w-5/6 h-4" />
          </div>
        </div>

        {/* Date & Duration Skeleton */}
        <div>
          <Skeleton className="w-48 h-6 mb-6" /> {/* Section Title */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
            <div>
              <Skeleton className="w-16 h-4 mb-2" /> {/* Label */}
              <Skeleton className="w-full h-[58px]" /> {/* Input height matches real input */}
            </div>
            <div>
              <Skeleton className="w-24 h-4 mb-2" />
              <Skeleton className="w-full h-[58px]" />
            </div>
          </div>
        </div>

        {/* Services Skeleton */}
        <div className="pt-10 border-t border-slate-100">
          <Skeleton className="w-48 h-6 mb-6" />
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            {[1, 2, 3, 4].map((i) => (
              <div key={i} className="bg-white border border-slate-200 p-5 h-32">
                <div className="flex justify-between mb-3">
                  <Skeleton className="w-1/3 h-5" />
                  <Skeleton className="w-16 h-5" />
                </div>
                <Skeleton className="w-full h-4 mb-2" />
                <Skeleton className="w-2/3 h-4" />
              </div>
            ))}
          </div>
        </div>

        {/* Contact Form Skeleton */}
        <div className="pt-10 border-t border-slate-100 mb-20">
          <Skeleton className="w-32 h-6 mb-6" />
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
            {[1, 2, 3, 4].map((i) => (
              <div key={i}>
                <Skeleton className="w-16 h-4 mb-2" />
                <Skeleton className="w-full h-[58px]" />
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};

export const HomeSkeleton = () => {
  return (
    <div className="min-h-screen bg-white">
      {/* Header Placeholder */}
      <div className="h-20 border-b border-neutral-200" />

      {/* Hero Section Skeleton */}
      <div className="relative h-screen w-full bg-neutral-100 flex items-center justify-center">
        <div className="text-center px-6 max-w-4xl w-full flex flex-col items-center">
          <Skeleton className="w-32 h-6 mb-12" /> {/* Label */}
          <Skeleton className="w-3/4 h-20 mb-8" /> {/* Title */}
          <Skeleton className="w-1/2 h-6 mb-16" /> {/* Description */}

          <div className="flex flex-col sm:flex-row gap-6 w-full justify-center">
             <Skeleton className="w-48 h-14" /> {/* Button */}
             <Skeleton className="w-64 h-14" /> {/* Info Box */}
          </div>
        </div>
      </div>
    </div>
  );
};

export const ClothingRentalSkeleton = () => {
  return (
    <div className="min-h-screen bg-white">
      <div className="max-w-7xl mx-auto px-6 py-12">
        {/* Back link */}
        <Skeleton className="w-48 h-5 mb-12" />

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-12">
          {/* Left Column: Catalog */}
          <div className="lg:col-span-2">
            <div className="mb-16">
              <Skeleton className="w-64 h-12 mb-3" /> {/* Title */}
              <Skeleton className="w-48 h-6" /> {/* Subtitle */}
            </div>

            {/* Filters */}
            <div className="flex flex-col sm:flex-row gap-4 mb-12">
              <Skeleton className="flex-1 h-[58px]" />
              <Skeleton className="w-48 h-[58px]" />
            </div>

            {/* Grid of Items */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-8">
              {[1, 2, 3, 4].map((i) => (
                <div key={i}>
                  <div className="aspect-[3/4] mb-4">
                     <Skeleton className="w-full h-full" />
                  </div>
                  <div className="space-y-3">
                    <Skeleton className="w-3/4 h-6" />
                    <Skeleton className="w-full h-4" />
                    <div className="flex justify-between">
                       <Skeleton className="w-20 h-4" />
                       <Skeleton className="w-20 h-4" />
                    </div>
                    <Skeleton className="w-full h-14 mt-2" />
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Right Column: Cart Sidebar */}
          <div className="lg:col-span-1">
             <div className="sticky top-8 border border-neutral-100 p-8 h-[500px]">
                <div className="flex justify-between mb-8">
                   <Skeleton className="w-24 h-8" />
                   <Skeleton className="w-6 h-6" />
                </div>
                <div className="space-y-4">
                   <Skeleton className="w-full h-20" />
                   <Skeleton className="w-full h-20" />
                </div>
                <div className="mt-8 space-y-3">
                   <Skeleton className="w-full h-14" />
                   <Skeleton className="w-full h-14" />
                </div>
             </div>
          </div>
        </div>
      </div>
    </div>
  );
};
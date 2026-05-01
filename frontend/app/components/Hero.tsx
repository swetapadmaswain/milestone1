import { SparklesIcon } from '@heroicons/react/24/outline';
import { SearchForm } from './SearchForm';

export function Hero() {
  return (
    <div className="relative bg-gradient-to-br from-primary-50 via-white to-secondary-50 overflow-hidden">
      {/* Background decoration */}
      <div className="absolute inset-0 opacity-30">
        <div className="absolute top-20 left-10 w-72 h-72 bg-primary-200 rounded-full mix-blend-multiply filter blur-xl animate-pulse" />
        <div className="absolute top-40 right-10 w-72 h-72 bg-secondary-200 rounded-full mix-blend-multiply filter blur-xl animate-pulse delay-700" />
        <div className="absolute -bottom-8 left-20 w-72 h-72 bg-warning-200 rounded-full mix-blend-multiply filter blur-xl animate-pulse delay-1000" />
      </div>

      <div className="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pt-20 pb-24 lg:pt-32 lg:pb-32">
        <div className="text-center">
          {/* Badge */}
          <div className="inline-flex items-center px-4 py-2 rounded-full bg-primary-100 text-primary-700 text-sm font-medium mb-8">
            <SparklesIcon className="w-4 h-4 mr-2" />
            AI-Powered Recommendations
          </div>

          {/* Heading */}
          <h1 className="text-4xl sm:text-5xl lg:text-6xl font-bold text-gray-900 mb-6">
            Discover Your Perfect
            <span className="block text-gradient">Dining Experience</span>
          </h1>

          {/* Subheading */}
          <p className="text-lg sm:text-xl text-gray-600 mb-12 max-w-3xl mx-auto">
            AI-powered restaurant recommendations personalized just for you. 
            Find the best restaurants based on your preferences, budget, and location.
          </p>

          {/* Search Form - Client Component */}
          <SearchForm />

          {/* Trust Indicators */}
          <div className="mt-12 flex flex-wrap justify-center gap-8 text-sm text-gray-500">
            <div className="flex items-center">
              <span className="font-semibold text-gray-900 mr-1">10,000+</span>
              Restaurants
            </div>
            <div className="flex items-center">
              <span className="font-semibold text-gray-900 mr-1">50,000+</span>
              Happy Diners
            </div>
            <div className="flex items-center">
              <span className="font-semibold text-gray-900 mr-1">4.9/5</span>
              Rating
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

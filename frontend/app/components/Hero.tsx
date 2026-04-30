'use client';

import Link from 'next/link';
import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { 
  MapPinIcon, 
  CurrencyDollarIcon, 
  StarIcon,
  MagnifyingGlassIcon,
  SparklesIcon
} from '@heroicons/react/24/outline';

const budgetOptions = [
  { value: 'low', label: 'Low', range: 'â‚¹0 - â‚¹500' },
  { value: 'medium', label: 'Medium', range: 'â‚¹500 - â‚¹1500' },
  { value: 'high', label: 'High', range: 'â‚¹1500+' },
];

const cuisineOptions = [
  'North Indian',
  'South Indian',
  'Chinese',
  'Italian',
  'Mexican',
  'Thai',
  'Continental',
  'Fast Food',
];

export function Hero() {
  const router = useRouter();
  const [location, setLocation] = useState('');
  const [budget, setBudget] = useState('medium');
  const [cuisine, setCuisine] = useState('');
  const [minRating, setMinRating] = useState(3.5);

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    if (location.trim()) {
      const params = new URLSearchParams({
        location,
        budget,
        cuisine,
        minRating: minRating.toString(),
      });
      router.push(`/search?${params.toString()}`);
    }
  };

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

          {/* Search Form */}
          <form onSubmit={handleSearch} className="max-w-4xl mx-auto">
            <div className="bg-white rounded-2xl shadow-xl p-4 sm:p-6">
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
                {/* Location Input */}
                <div className="relative">
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Location
                  </label>
                  <div className="relative">
                    <MapPinIcon className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
                    <input
                      type="text"
                      value={location}
                      onChange={(e) => setLocation(e.target.value)}
                      placeholder="Enter city or locality"
                      className="w-full pl-10 pr-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                    />
                  </div>
                </div>

                {/* Budget Select */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Budget
                  </label>
                  <div className="relative">
                    <CurrencyDollarIcon className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
                    <select
                      value={budget}
                      onChange={(e) => setBudget(e.target.value)}
                      className="w-full pl-10 pr-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent appearance-none bg-white"
                    >
                      {budgetOptions.map((option) => (
                        <option key={option.value} value={option.value}>
                          {option.label} ({option.range})
                        </option>
                      ))}
                    </select>
                  </div>
                </div>

                {/* Cuisine Select */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Cuisine
                  </label>
                  <select
                    value={cuisine}
                    onChange={(e) => setCuisine(e.target.value)}
                    className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent appearance-none bg-white"
                  >
                    <option value="">Any Cuisine</option>
                    {cuisineOptions.map((option) => (
                      <option key={option} value={option}>
                        {option}
                      </option>
                    ))}
                  </select>
                </div>

                {/* Rating Slider */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Min Rating: {minRating}+
                  </label>
                  <div className="relative pt-2">
                    <StarIcon className="absolute left-0 top-1/2 -translate-y-1/2 w-5 h-5 text-yellow-400" />
                    <input
                      type="range"
                      min="1"
                      max="5"
                      step="0.5"
                      value={minRating}
                      onChange={(e) => setMinRating(parseFloat(e.target.value))}
                      className="w-full ml-6 h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer accent-primary-600"
                    />
                  </div>
                </div>
              </div>

              {/* Search Button */}
              <div className="mt-6">
                <button
                  type="submit"
                  className="w-full sm:w-auto inline-flex items-center justify-center px-8 py-4 border border-transparent text-lg font-medium rounded-xl text-white bg-primary-600 hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 transition-all duration-200 shadow-lg hover:shadow-xl"
                >
                  <MagnifyingGlassIcon className="w-5 h-5 mr-2" />
                  Find Restaurants
                </button>
              </div>
            </div>
          </form>

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

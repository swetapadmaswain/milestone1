'use client';

import { useState, useRef, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { 
  MapPinIcon, 
  CurrencyDollarIcon, 
  StarIcon,
  MagnifyingGlassIcon,
} from '@heroicons/react/24/outline';

const budgetOptions = [
  { value: 'low', label: 'Low', range: 'Rs. 0 - Rs. 500' },
  { value: 'medium', label: 'Medium', range: 'Rs. 500 - Rs. 1500' },
  { value: 'high', label: 'High', range: 'Rs. 1500+' },
];

const cuisineOptions = [
  'Any Cuisine',
  'North Indian',
  'South Indian',
  'Chinese',
  'Italian',
  'Mexican',
  'Thai',
  'Continental',
  'Fast Food',
];

const locationSuggestions = [
  'Mumbai', 'Delhi', 'Bangalore', 'Hyderabad', 'Chennai', 'Kolkata', 'Pune', 'Ahmedabad',
  'Jaipur', 'Surat', 'Lucknow', 'Kanpur', 'Nagpur', 'Patna', 'Indore', 'Thane',
  'Bhopal', 'Visakhapatnam', 'Vadodara', 'Ludhiana', 'Rajkot', 'Agra',
  'Chandigarh', 'Coimbatore', 'Mysore', 'Mangalore',
  'Koramangala, Bangalore', 'Indiranagar, Bangalore', 'Whitefield, Bangalore',
  'HSR Layout, Bangalore', 'Jayanagar, Bangalore', 'JP Nagar, Bangalore',
  'Bandra, Mumbai', 'Andheri, Mumbai', 'Juhu, Mumbai', 'Powai, Mumbai',
  'Connaught Place, Delhi', 'Hauz Khas, Delhi', 'South Delhi', 'Dwarka, Delhi',
  'T Nagar, Chennai', 'Anna Nagar, Chennai', 'Adyar, Chennai',
  'Banjara Hills, Hyderabad', 'Jubilee Hills, Hyderabad', 'Gachibowli, Hyderabad',
];

export function SearchForm() {
  const router = useRouter();
  const [location, setLocation] = useState('');
  const [budget, setBudget] = useState('medium');
  const [cuisine, setCuisine] = useState('');
  const [minRating, setMinRating] = useState(3.5);
  const [showSuggestions, setShowSuggestions] = useState(false);
  const [filteredSuggestions, setFilteredSuggestions] = useState<string[]>([]);
  const locationInputRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (location.trim()) {
      const filtered = locationSuggestions.filter(suggestion =>
        suggestion.toLowerCase().includes(location.toLowerCase())
      );
      setFilteredSuggestions(filtered.slice(0, 6));
      setShowSuggestions(filtered.length > 0);
    } else {
      setShowSuggestions(false);
    }
  }, [location]);

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (locationInputRef.current && !locationInputRef.current.contains(event.target as Node)) {
        setShowSuggestions(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const handleSelectSuggestion = (suggestion: string) => {
    setLocation(suggestion);
    setShowSuggestions(false);
  };

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    setShowSuggestions(false);
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
    <form onSubmit={handleSearch} className="max-w-4xl mx-auto">
      <div className="bg-white rounded-2xl shadow-xl p-4 sm:p-6">
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {/* Location Input with Suggestions */}
          <div className="relative" ref={locationInputRef}>
            <label htmlFor="location" className="block text-sm font-medium text-gray-700 mb-2">
              Location
            </label>
            <div className="relative">
              <MapPinIcon className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
              <input
                id="location"
                type="text"
                value={location}
                onChange={(e) => setLocation(e.target.value)}
                onFocus={() => location && setShowSuggestions(filteredSuggestions.length > 0)}
                placeholder="Enter city or locality"
                className="w-full pl-10 pr-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                autoComplete="off"
              />
              {showSuggestions && (
                <div className="absolute z-50 w-full mt-1 bg-white border border-gray-200 rounded-lg shadow-lg max-h-60 overflow-auto">
                  {filteredSuggestions.map((suggestion, index) => (
                    <button
                      key={index}
                      type="button"
                      onClick={() => handleSelectSuggestion(suggestion)}
                      className="w-full px-4 py-2 text-left hover:bg-gray-100 focus:bg-gray-100 focus:outline-none first:rounded-t-lg last:rounded-b-lg"
                    >
                      <div className="flex items-center">
                        <MapPinIcon className="w-4 h-4 mr-2 text-gray-400" />
                        <span className="text-gray-700">{suggestion}</span>
                      </div>
                    </button>
                  ))}
                </div>
              )}
            </div>
          </div>

          {/* Budget Select */}
          <div>
            <label htmlFor="budget" className="block text-sm font-medium text-gray-700 mb-2">
              Budget
            </label>
            <div className="relative">
              <CurrencyDollarIcon className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
              <select
                id="budget"
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
            <label htmlFor="cuisine" className="block text-sm font-medium text-gray-700 mb-2">
              Cuisine
            </label>
            <select
              id="cuisine"
              value={cuisine}
              onChange={(e) => setCuisine(e.target.value)}
              className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent appearance-none bg-white"
            >
              {cuisineOptions.map((option) => (
                <option key={option} value={option === 'Any Cuisine' ? '' : option}>
                  {option}
                </option>
              ))}
            </select>
          </div>

          {/* Rating Slider */}
          <div>
            <label htmlFor="rating" className="block text-sm font-medium text-gray-700 mb-2">
              Min Rating: {minRating}+
            </label>
            <div className="relative pt-2">
              <input
                id="rating"
                type="range"
                min="1"
                max="5"
                step="0.5"
                value={minRating}
                onChange={(e) => setMinRating(parseFloat(e.target.value))}
                className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer accent-primary-600"
              />
              <div className="flex justify-between text-xs text-gray-500 mt-1">
                <span>1</span>
                <span>5</span>
              </div>
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
  );
}

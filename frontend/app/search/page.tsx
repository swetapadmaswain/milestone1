'use client';

import { useEffect, useState, Suspense } from 'react';
import { useSearchParams } from 'next/navigation';
import { apiService } from '../../services/api';
import { RestaurantRecommendation } from '../../types';
import { 
  MapPinIcon, 
  CurrencyDollarIcon, 
  StarIcon,
  ArrowLeftIcon,
  HeartIcon,
} from '@heroicons/react/24/outline';
import Link from 'next/link';

function SearchResults() {
  const searchParams = useSearchParams();
  const [recommendations, setRecommendations] = useState<RestaurantRecommendation[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const location = searchParams.get('location') || '';
  const budget = searchParams.get('budget') || 'medium';
  const cuisine = searchParams.get('cuisine') || '';
  const minRating = parseFloat(searchParams.get('minRating') || '3.5');

  useEffect(() => {
    async function fetchRecommendations() {
      if (!location) return;
      
      try {
        setLoading(true);
        const response = await apiService.getRecommendations({
          location: location.toLowerCase().trim(),
          budget: budget as 'low' | 'medium' | 'high',
          preferred_cuisine: cuisine === 'Any Cuisine' ? '' : cuisine,
          min_rating: minRating,
          top_n: 5,
        });
        setRecommendations(response.recommendations);
        setError(null);
      } catch (err: any) {
        console.error('Error fetching recommendations:', err);
        const errorMessage = err.response?.data?.message || err.message || 'Failed to fetch recommendations. Please try again.';
        setError(errorMessage);
      } finally {
        setLoading(false);
      }
    }

    fetchRecommendations();
  }, [location, budget, cuisine, minRating]);

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 pt-20 pb-12">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-center h-64">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gray-50 pt-20 pb-12">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center py-12">
            <p className="text-red-600 mb-4">{error}</p>
            <Link href="/" className="text-primary-600 hover:text-primary-700 font-medium">
              Go back home
            </Link>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 pt-20 pb-12">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Back Button */}
        <Link 
          href="/" 
          className="inline-flex items-center text-gray-600 hover:text-gray-900 mb-6"
        >
          <ArrowLeftIcon className="w-5 h-5 mr-2" />
          Back to search
        </Link>

        {/* Search Summary */}
        <div className="bg-white rounded-xl shadow-sm p-6 mb-6">
          <h1 className="text-2xl font-bold text-gray-900 mb-2">
            Restaurant Recommendations
          </h1>
          <div className="flex flex-wrap gap-4 text-sm text-gray-600">
            <span className="flex items-center">
              <MapPinIcon className="w-4 h-4 mr-1" />
              {location}
            </span>
            <span className="flex items-center">
              <CurrencyDollarIcon className="w-4 h-4 mr-1" />
              {budget.charAt(0).toUpperCase() + budget.slice(1)} Budget
            </span>
            {cuisine && cuisine !== 'Any Cuisine' && (
              <span className="flex items-center">
                <StarIcon className="w-4 h-4 mr-1" />
                {cuisine}
              </span>
            )}
          </div>
        </div>

        {/* Results */}
        {recommendations.length === 0 ? (
          <div className="bg-white rounded-xl shadow-sm p-8 text-center">
            <p className="text-gray-600 mb-4">
              No restaurants found matching your criteria.
            </p>
            <p className="text-sm text-gray-500">
              Try adjusting your filters or search for a different location.
            </p>
          </div>
        ) : (
          <div className="space-y-4">
            {recommendations.map((restaurant, index) => (
              <div 
                key={restaurant.restaurant_name} 
                className="bg-white rounded-xl shadow-sm p-6 hover:shadow-md transition-shadow"
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center gap-3 mb-2">
                      <span className="bg-primary-100 text-primary-700 text-sm font-semibold px-3 py-1 rounded-full">
                        #{index + 1}
                      </span>
                      <h3 className="text-xl font-bold text-gray-900">
                        {restaurant.restaurant_name}
                      </h3>
                      <span className="text-sm text-gray-500">
                        {restaurant.cuisine}
                      </span>
                    </div>
                    
                    <div className="flex flex-wrap gap-4 text-sm text-gray-600 mb-3">
                      <span className="flex items-center">
                        <MapPinIcon className="w-4 h-4 mr-1" />
                        {restaurant.location}
                      </span>
                      <span className="flex items-center">
                        <StarIcon className="w-4 h-4 mr-1 text-yellow-500" />
                        {restaurant.rating.toFixed(1)}
                      </span>
                      <span className="flex items-center">
                        <CurrencyDollarIcon className="w-4 h-4 mr-1" />
                        Rs. {restaurant.estimated_cost.toFixed(0)}
                      </span>
                    </div>

                    <p className="text-gray-700 mb-2">
                      {restaurant.explanation}
                    </p>

                    <div className="flex items-center gap-2">
                      <span className={`text-xs px-2 py-1 rounded ${
                        restaurant.confidence === 'high' 
                          ? 'bg-green-100 text-green-700' 
                          : restaurant.confidence === 'medium'
                          ? 'bg-yellow-100 text-yellow-700'
                          : 'bg-gray-100 text-gray-700'
                      }`}>
                        {restaurant.confidence} confidence
                      </span>
                      <span className="text-xs text-gray-500">
                        Score: {restaurant.final_score.toFixed(2)}
                      </span>
                    </div>
                  </div>

                  <button className="p-2 text-gray-400 hover:text-red-500 transition-colors">
                    <HeartIcon className="w-6 h-6" />
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

export default function SearchPage() {
  return (
    <Suspense fallback={
      <div className="min-h-screen bg-gray-50 pt-20 pb-12">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-center h-64">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
          </div>
        </div>
      </div>
    }>
      <SearchResults />
    </Suspense>
  );
}

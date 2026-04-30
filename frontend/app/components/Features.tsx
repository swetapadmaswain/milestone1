import { SparklesIcon, HeartIcon, AdjustmentsHorizontalIcon } from '@heroicons/react/24/outline';

const features = [
  {
    name: 'AI-Powered Recommendations',
    description: 'Our advanced AI analyzes thousands of restaurants to find your perfect match based on your preferences.',
    icon: SparklesIcon,
  },
  {
    name: 'Personalized Learning',
    description: 'The more you use DineSmart, the better it understands your taste and dining preferences.',
    icon: HeartIcon,
  },
  {
    name: 'Smart Filters',
    description: 'Filter by budget, cuisine, rating, and location to find exactly what you are looking for.',
    icon: AdjustmentsHorizontalIcon,
  },
];

export function Features() {
  return (
    <div className="py-24 bg-white">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center mb-16">
          <h2 className="text-3xl font-bold text-gray-900">Why Choose DineSmart?</h2>
          <p className="mt-4 text-lg text-gray-600">
            Discover restaurants tailored to your taste with our intelligent recommendation system.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          {features.map((feature) => (
            <div key={feature.name} className="relative p-8 bg-gray-50 rounded-2xl hover:shadow-lg transition-shadow">
              <div className="absolute top-0 left-1/2 -translate-x-1/2 -translate-y-1/2">
                <div className="bg-primary-600 p-3 rounded-xl">
                  <feature.icon className="w-6 h-6 text-white" aria-hidden="true" />
                </div>
              </div>
              <div className="mt-8 text-center">
                <h3 className="text-xl font-semibold text-gray-900">{feature.name}</h3>
                <p className="mt-4 text-gray-600">{feature.description}</p>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

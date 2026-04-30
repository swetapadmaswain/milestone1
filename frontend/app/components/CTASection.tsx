import Link from 'next/link';

export function CTASection() {
  return (
    <div className="py-24 bg-white">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
        <h2 className="text-3xl font-bold text-gray-900">
          Ready to discover your next favorite restaurant?
        </h2>
        <p className="mt-4 text-lg text-gray-600">
          Join thousands of diners who trust DineSmart for personalized restaurant recommendations.
        </p>
        <div className="mt-8">
          <Link
            href="/search"
            className="inline-flex items-center justify-center px-8 py-4 border border-transparent text-lg font-medium rounded-xl text-white bg-primary-600 hover:bg-primary-700 transition-colors"
          >
            Get Started for Free
          </Link>
        </div>
      </div>
    </div>
  );
}

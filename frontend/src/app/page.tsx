'use client';

import { useState } from 'react';
import Link from 'next/link';

export default function Home() {
  const [email, setEmail] = useState('');
  const [submitted, setSubmitted] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    // TODO: Add to waitlist
    setSubmitted(true);
  };

  return (
    <main className="min-h-screen bg-gradient-to-b from-gray-50 to-white">
      {/* Navigation */}
      <nav className="container mx-auto px-6 py-8">
        <div className="flex justify-between items-center">
          <h1 className="text-2xl font-bold text-gray-900">FinOps Little Analyzer</h1>
          <div className="flex gap-4">
            <Link href="/login" className="text-gray-600 hover:text-gray-900">
              Login
            </Link>
            <Link 
              href="/signup" 
              className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700"
            >
              Get Started
            </Link>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="container mx-auto px-6 py-20 text-center">
        <h2 className="text-5xl font-bold text-gray-900 mb-6">
          Cut Your AWS Bill by 40%
          <br />
          <span className="text-blue-600">in 10 Minutes</span>
        </h2>
        
        <p className="text-xl text-gray-600 mb-8 max-w-2xl mx-auto">
          AI-powered cost optimization for startups. Find and eliminate cloud waste automatically.
        </p>

        {/* Email Signup */}
        {!submitted ? (
          <form onSubmit={handleSubmit} className="max-w-md mx-auto">
            <div className="flex gap-2">
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="your@email.com"
                required
                className="flex-1 px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:border-blue-500"
              />
              <button
                type="submit"
                className="bg-blue-600 text-white px-6 py-3 rounded-lg hover:bg-blue-700 font-semibold"
              >
                Get Free Audit
              </button>
            </div>
            <p className="text-sm text-gray-500 mt-2">
              Free cloud cost audit • No credit card required
            </p>
          </form>
        ) : (
          <div className="bg-green-50 border border-green-200 rounded-lg p-4 max-w-md mx-auto">
            <p className="text-green-800">
              🎉 Thanks! Check your email for next steps.
            </p>
          </div>
        )}
      </section>

      {/* Features */}
      <section className="container mx-auto px-6 py-16">
        <div className="grid md:grid-cols-3 gap-8">
          <div className="text-center">
            <div className="text-4xl mb-4">⚡</div>
            <h3 className="text-xl font-semibold mb-2">10-Minute Setup</h3>
            <p className="text-gray-600">
              Connect your AWS account with read-only access. Start saving immediately.
            </p>
          </div>
          
          <div className="text-center">
            <div className="text-4xl mb-4">🤖</div>
            <h3 className="text-xl font-semibold mb-2">AI Analysis</h3>
            <p className="text-gray-600">
              Machine learning detects waste patterns humans miss.
            </p>
          </div>
          
          <div className="text-center">
            <div className="text-4xl mb-4">💰</div>
            <h3 className="text-xl font-semibold mb-2">Guaranteed ROI</h3>
            <p className="text-gray-600">
              Average savings of $15k/month. Pay only if we save you money.
            </p>
          </div>
        </div>
      </section>
    </main>
  );
}
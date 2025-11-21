'use client';

import { useState } from 'react';
import { CheckCircle } from 'lucide-react';

export default function BetaLandingPage() {
  const [email, setEmail] = useState('');
  const [company, setCompany] = useState('');
  const [submitted, setSubmitted] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    // TODO: Save to database or send to your email
    console.log('Beta signup:', { email, company });
    
    setSubmitted(true);
  };

  const testimonials = [
    {
      quote: "Found $18k/month in savings in our first scan",
      author: "Sarah Chen, CTO",
      company: "TechStartup (YC W23)",
      savings: "$18,000/month"
    },
    {
      quote: "Reduced our AWS bill by 43% without any performance impact",
      author: "Mike Rodriguez, VP Eng",
      company: "DataCo (Series A)",
      savings: "$25,000/month"
    }
  ];

  if (submitted) {
    return (
      <div className="min-h-screen bg-gradient-to-b from-blue-50 to-white flex items-center justify-center">
        <div className="bg-white rounded-lg shadow-lg p-8 max-w-md">
          <CheckCircle className="w-12 h-12 text-green-600 mx-auto mb-4" />
          <h2 className="text-2xl font-bold text-center mb-4">You're In!</h2>
          <p className="text-gray-600 text-center">
            We'll send you setup instructions within 24 hours. 
            Get ready to save thousands on your cloud bills!
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-b from-blue-50 to-white">
      {/* Hero Section */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pt-20 pb-16">
        <div className="text-center">
          <h1 className="text-5xl font-bold text-gray-900 mb-6">
            Limited Beta: Save 40% on AWS
            <span className="block text-blue-600 mt-2">First 10 Companies Free</span>
          </h1>
          
          <p className="text-xl text-gray-600 mb-8 max-w-3xl mx-auto">
            We're selecting 10 high-growth startups for our exclusive beta program.
            Get 3 months free access to our AI-powered cloud cost optimizer.
            Most companies save $10-50k per month.
          </p>

          {/* Signup Form */}
          <form onSubmit={handleSubmit} className="max-w-md mx-auto">
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="your@company.com"
              required
              className="w-full px-4 py-3 border border-gray-300 rounded-lg mb-3"
            />
            <input
              type="text"
              value={company}
              onChange={(e) => setCompany(e.target.value)}
              placeholder="Company Name"
              required
              className="w-full px-4 py-3 border border-gray-300 rounded-lg mb-3"
            />
            <button
              type="submit"
              className="w-full bg-blue-600 text-white py-3 px-6 rounded-lg hover:bg-blue-700 font-semibold text-lg"
            >
              Apply for Beta Access
            </button>
            <p className="text-sm text-gray-500 mt-2">
              Only 3 spots remaining • No credit card required
            </p>
          </form>
        </div>
      </div>

      {/* Social Proof */}
      <div className="bg-white py-16">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <h2 className="text-3xl font-bold text-center mb-12">
            Early Beta Users Are Saving Big
          </h2>
          
          <div className="grid md:grid-cols-2 gap-8">
            {testimonials.map((testimonial, index) => (
              <div key={index} className="bg-gray-50 rounded-lg p-6">
                <p className="text-lg text-gray-700 mb-4">"{testimonial.quote}"</p>
                <div className="flex justify-between items-center">
                  <div>
                    <p className="font-semibold">{testimonial.author}</p>
                    <p className="text-sm text-gray-600">{testimonial.company}</p>
                  </div>
                  <div className="text-right">
                    <p className="text-2xl font-bold text-green-600">{testimonial.savings}</p>
                    <p className="text-sm text-gray-600">saved monthly</p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Requirements */}
      <div className="py-16">
        <div className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8">
          <h2 className="text-2xl font-bold mb-6">Beta Requirements</h2>
          <ul className="space-y-2">
            <li className="flex items-start">
              <CheckCircle className="w-5 h-5 text-green-600 mt-0.5 mr-2" />
              <span>Spending $5,000+ per month on AWS</span>
            </li>
            <li className="flex items-start">
              <CheckCircle className="w-5 h-5 text-green-600 mt-0.5 mr-2" />
              <span>Willing to provide feedback and testimonial</span>
            </li>
            <li className="flex items-start">
              <CheckCircle className="w-5 h-5 text-green-600 mt-0.5 mr-2" />
              <span>Can connect AWS account within 48 hours</span>
            </li>
          </ul>
        </div>
      </div>
    </div>
  );
}

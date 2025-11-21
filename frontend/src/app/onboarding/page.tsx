'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { api } from '@/lib/api-client';
import { CheckCircle, Cloud, DollarSign, Shield } from 'lucide-react';

export default function OnboardingPage() {
  const router = useRouter();
  const [step, setStep] = useState(1);
  const [accountData, setAccountData] = useState({
    account_name: '',
    access_key: '',
    secret_key: '',
    region: 'us-east-1',
  });
  const [isConnecting, setIsConnecting] = useState(false);
  const [error, setError] = useState('');

  const handleConnect = async () => {
    setIsConnecting(true);
    setError('');
    
    try {
      await api.cloudAccounts.connect({
        ...accountData,
        provider: 'aws',
      });
      
      // Run initial analysis
      // await api.analysis.run(response.data.id);
      
      router.push('/dashboard');
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to connect AWS account');
      setIsConnecting(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md w-full space-y-8">
        {/* Progress Indicator */}
        <div className="flex justify-center space-x-2">
          {[1, 2, 3].map((i) => (
            <div
              key={i}
              className={`h-2 w-16 rounded ${
                i <= step ? 'bg-blue-600' : 'bg-gray-300'
              }`}
            />
          ))}
        </div>

        {/* Step 1: Welcome */}
        {step === 1 && (
          <div className="bg-white rounded-lg shadow p-8">
            <div className="text-center">
              <Cloud className="mx-auto h-12 w-12 text-blue-600" />
              <h2 className="mt-6 text-3xl font-bold text-gray-900">
                Welcome to FinOps Analyzer
              </h2>
              <p className="mt-2 text-gray-600">
                Let's connect your AWS account to start saving money
              </p>
            </div>
            
            <div className="mt-8 space-y-4">
              <div className="flex items-start">
                <Shield className="w-5 h-5 text-green-600 mt-0.5" />
                <div className="ml-3">
                  <p className="text-sm font-medium">Read-Only Access</p>
                  <p className="text-sm text-gray-500">
                    We only request read permissions to analyze your resources
                  </p>
                </div>
              </div>
              
              <div className="flex items-start">
                <DollarSign className="w-5 h-5 text-green-600 mt-0.5" />
                <div className="ml-3">
                  <p className="text-sm font-medium">Find Instant Savings</p>
                  <p className="text-sm text-gray-500">
                    Average customer saves $15k/month
                  </p>
                </div>
              </div>
              
              <div className="flex items-start">
                <CheckCircle className="w-5 h-5 text-green-600 mt-0.5" />
                <div className="ml-3">
                  <p className="text-sm font-medium">No Code Changes</p>
                  <p className="text-sm text-gray-500">
                    Analysis runs externally, no impact on your systems
                  </p>
                </div>
              </div>
            </div>
            
            <button
              onClick={() => setStep(2)}
              className="mt-8 w-full bg-blue-600 text-white py-2 px-4 rounded-lg hover:bg-blue-700"
            >
              Get Started
            </button>
          </div>
        )}

        {/* Step 2: AWS Credentials */}
        {step === 2 && (
          <div className="bg-white rounded-lg shadow p-8">
            <h2 className="text-2xl font-bold text-gray-900 mb-6">
              Connect Your AWS Account
            </h2>
            
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700">
                  Account Name
                </label>
                <input
                  type="text"
                  value={accountData.account_name}
                  onChange={(e) => setAccountData({...accountData, account_name: e.target.value})}
                  className="mt-1 block w-full border-gray-300 rounded-md shadow-sm p-2 border"
                  placeholder="Production AWS"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700">
                  Access Key ID
                </label>
                <input
                  type="text"
                  value={accountData.access_key}
                  onChange={(e) => setAccountData({...accountData, access_key: e.target.value})}
                  className="mt-1 block w-full border-gray-300 rounded-md shadow-sm p-2 border"
                  placeholder="AKIA..."
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700">
                  Secret Access Key
                </label>
                <input
                  type="password"
                  value={accountData.secret_key}
                  onChange={(e) => setAccountData({...accountData, secret_key: e.target.value})}
                  className="mt-1 block w-full border-gray-300 rounded-md shadow-sm p-2 border"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700">
                  Region
                </label>
                <select
                  value={accountData.region}
                  onChange={(e) => setAccountData({...accountData, region: e.target.value})}
                  className="mt-1 block w-full border-gray-300 rounded-md shadow-sm p-2 border"
                >
                  <option value="us-east-1">US East (N. Virginia)</option>
                  <option value="us-west-2">US West (Oregon)</option>
                  <option value="eu-west-1">EU (Ireland)</option>
                  <option value="ap-southeast-1">Asia Pacific (Singapore)</option>
                </select>
              </div>
              
              {error && (
                <div className="bg-red-50 border border-red-200 rounded p-3">
                  <p className="text-sm text-red-600">{error}</p>
                </div>
              )}
            </div>
            
            <div className="mt-6 flex space-x-3">
              <button
                onClick={() => setStep(1)}
                className="flex-1 bg-gray-200 text-gray-800 py-2 px-4 rounded-lg hover:bg-gray-300"
              >
                Back
              </button>
              <button
                onClick={() => setStep(3)}
                disabled={!accountData.account_name || !accountData.access_key || !accountData.secret_key}
                className="flex-1 bg-blue-600 text-white py-2 px-4 rounded-lg hover:bg-blue-700 disabled:opacity-50"
              >
                Next
              </button>
            </div>
          </div>
        )}

        {/* Step 3: Confirmation */}
        {step === 3 && (
          <div className="bg-white rounded-lg shadow p-8">
            <h2 className="text-2xl font-bold text-gray-900 mb-6">
              Ready to Analyze
            </h2>
            
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-6">
              <p className="text-sm text-blue-800">
                We'll now connect to your AWS account and run our first analysis.
                This typically takes 2-3 minutes.
              </p>
            </div>
            
            <div className="space-y-2 mb-6">
              <div className="flex justify-between text-sm">
                <span className="text-gray-600">Account:</span>
                <span className="font-medium">{accountData.account_name}</span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-gray-600">Region:</span>
                <span className="font-medium">{accountData.region}</span>
              </div>
            </div>
            
            <div className="mt-6 flex space-x-3">
              <button
                onClick={() => setStep(2)}
                className="flex-1 bg-gray-200 text-gray-800 py-2 px-4 rounded-lg hover:bg-gray-300"
                disabled={isConnecting}
              >
                Back
              </button>
              <button
                onClick={handleConnect}
                disabled={isConnecting}
                className="flex-1 bg-blue-600 text-white py-2 px-4 rounded-lg hover:bg-blue-700 disabled:opacity-50"
              >
                {isConnecting ? 'Connecting...' : 'Start Analysis'}
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

'use client';

import { useEffect, useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { api, type DashboardData, type CloudAccount } from '@/lib/api-client';
import { 
  DollarSign, 
  TrendingDown, 
  AlertCircle, 
  CheckCircle,
  RefreshCw,
  ChevronRight,
  type LucideIcon
} from 'lucide-react';
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell
} from 'recharts';

// Metric Card Component
interface MetricCardProps {
  title: string;
  value: string | number;
  subtitle?: string;
  icon: LucideIcon;
  color?: 'blue' | 'green' | 'yellow' | 'purple';
}

function MetricCard({ title, value, subtitle, icon: Icon, color = 'blue' }: MetricCardProps) {
  const colorClasses = {
    blue: 'text-blue-600 bg-blue-50',
    green: 'text-green-600 bg-green-50',
    yellow: 'text-yellow-600 bg-yellow-50',
    purple: 'text-purple-600 bg-purple-50',
  };

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <div className="flex items-center justify-between mb-2">
        <p className="text-sm font-medium text-gray-600">{title}</p>
        <div className={`p-2 rounded-lg ${colorClasses[color]}`}>
          <Icon className="w-4 h-4" />
        </div>
      </div>
      <p className="text-2xl font-bold">{value}</p>
      {subtitle && <p className="text-xs text-gray-500 mt-1">{subtitle}</p>}
    </div>
  );
}

// Recommendation Item Component
interface RecommendationItemProps {
  recommendation: {
    title: string;
    savings: number;
    risk: string;
  };
}

function RecommendationItem({ recommendation }: RecommendationItemProps) {
  const riskColors: Record<string, string> = {
    low: 'bg-green-100 text-green-800',
    medium: 'bg-yellow-100 text-yellow-800',
    high: 'bg-red-100 text-red-800',
  };

  const riskColor = riskColors[recommendation.risk] || riskColors.medium;

  return (
    <div className="flex items-center justify-between p-4 bg-white rounded-lg border hover:shadow-md transition-shadow cursor-pointer">
      <div className="flex-1">
        <h4 className="font-medium">{recommendation.title}</h4>
        <div className="flex items-center gap-2 mt-1">
          <span className={`px-2 py-1 rounded text-xs font-medium ${riskColor}`}>
            {recommendation.risk} risk
          </span>
        </div>
      </div>
      <div className="text-right">
        <p className="font-bold text-green-600">${recommendation.savings.toLocaleString()}/mo</p>
        <ChevronRight className="w-4 h-4 text-gray-400 ml-auto" />
      </div>
    </div>
  );
}

export default function DashboardPage() {
  const [selectedAccount, setSelectedAccount] = useState<string | null>(null);

  // Fetch cloud accounts
  const { data: accounts } = useQuery({
    queryKey: ['cloudAccounts'],
    queryFn: async () => {
      const response = await api.cloudAccounts.list();
      return response.data;
    },
  });

  // Fetch dashboard data
  const { data: dashboard, isLoading, refetch } = useQuery({
    queryKey: ['dashboard'],
    queryFn: async () => {
      const response = await api.analysis.dashboard();
      return response.data;
    },
    refetchInterval: 60000, // Refresh every minute
  });

  // Run analysis
  const runAnalysis = async () => {
    if (!selectedAccount) return;
    
    try {
      await api.analysis.run(selectedAccount);
      // Wait a bit then refresh dashboard
      setTimeout(() => refetch(), 3000);
    } catch (error) {
      console.error('Analysis failed:', error);
    }
  };

  // Service breakdown chart data
  const serviceData = dashboard?.service_breakdown 
    ? Object.entries(dashboard.service_breakdown).map(([name, value]) => ({
        name,
        value,
      }))
    : [];

  const COLORS = ['#3B82F6', '#10B981', '#F59E0B', '#EF4444', '#8B5CF6', '#EC4899'];

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-4">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">Cloud Cost Dashboard</h1>
              <p className="text-sm text-gray-600">
                Real-time insights into your cloud spending
              </p>
            </div>
            <div className="flex gap-2">
              <select
                value={selectedAccount || ''}
                onChange={(e) => setSelectedAccount(e.target.value)}
                className="px-4 py-2 border rounded-lg"
              >
                <option value="">Select AWS Account</option>
                {accounts?.map((account: CloudAccount) => (
                  <option key={account.id} value={account.id}>
                    {account.account_name} ({account.account_id})
                  </option>
                ))}
              </select>
              <button
                onClick={runAnalysis}
                disabled={!selectedAccount}
                className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
              >
                <RefreshCw className="w-4 h-4" />
                Run Analysis
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Metrics Grid */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
          <MetricCard
            title="Monthly Spend"
            value={`$${dashboard?.current_month_spend.toLocaleString() || 0}`}
            subtitle="Current month to date"
            icon={DollarSign}
            color="blue"
          />
          <MetricCard
            title="Potential Savings"
            value={`$${dashboard?.potential_monthly_savings.toLocaleString() || 0}`}
            subtitle={`${dashboard?.savings_percentage.toFixed(1) || 0}% of total spend`}
            icon={TrendingDown}
            color="green"
          />
          <MetricCard
            title="Active Recommendations"
            value={dashboard?.active_recommendations || 0}
            subtitle="Requiring action"
            icon={AlertCircle}
            color="yellow"
          />
          <MetricCard
            title="Optimization Score"
            value={`${Math.round(100 - (dashboard?.savings_percentage || 0))}%`}
            subtitle="Resource efficiency"
            icon={CheckCircle}
            color="purple"
          />
        </div>

        {/* Charts Row */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
          {/* Service Breakdown */}
          <div className="bg-white rounded-lg shadow p-6">
            <h3 className="text-lg font-semibold mb-4">Service Breakdown</h3>
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={serviceData}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  label={(entry) => `${entry.name}: $${entry.value.toFixed(0)}`}
                  outerRadius={80}
                  fill="#8884d8"
                  dataKey="value"
                >
                  {serviceData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </div>

          {/* Top Recommendations */}
          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex justify-between items-center mb-4">
              <h3 className="text-lg font-semibold">Top Recommendations</h3>
              <a href="/recommendations" className="text-sm text-blue-600 hover:underline">
                View all →
              </a>
            </div>
            <div className="space-y-3">
              {dashboard?.top_recommendations.slice(0, 5).map((rec, index) => (
                <RecommendationItem key={index} recommendation={rec} />
              )) || (
                <p className="text-gray-500 text-center py-4">
                  No recommendations yet. Run an analysis to get started.
                </p>
              )}
            </div>
          </div>
        </div>

        {/* Last Analysis Info */}
        {dashboard?.last_analysis && (
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
            <p className="text-sm text-blue-800">
              Last analysis: {new Date(dashboard.last_analysis).toLocaleString()}
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
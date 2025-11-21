"""
Cost prediction and anomaly detection using Prophet
"""
import pandas as pd
import numpy as np
from prophet import Prophet
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import logging
from sklearn.preprocessing import StandardScaler

logger = logging.getLogger(__name__)


class CostPredictor:
    """ML-based cost prediction and anomaly detection"""
    
    def __init__(self):
        self.model = None
        self.scaler = StandardScaler()
        self.forecast = None
        
    def train(self, historical_costs: List[Dict[str, Any]]) -> bool:
        """
        Train Prophet model on historical cost data
        
        Args:
            historical_costs: List of dicts with 'date' and 'cost' keys
        
        Returns:
            bool: True if training successful
        """
        try:
            # Convert to DataFrame
            df = pd.DataFrame(historical_costs)
            df['ds'] = pd.to_datetime(df['date'])
            df['y'] = df['cost'].astype(float)
            
            # Initialize Prophet with custom parameters
            self.model = Prophet(
                daily_seasonality=False,
                weekly_seasonality=True,
                yearly_seasonality=False,
                changepoint_prior_scale=0.05,  # More resistant to outliers
                interval_width=0.95  # 95% confidence interval
            )
            
            # Add US holidays (affects cloud usage)
            self.model.add_country_holidays(country_name='US')
            
            # Fit the model
            self.model.fit(df[['ds', 'y']])
            
            logger.info(f"Trained cost prediction model on {len(df)} data points")
            return True
            
        except Exception as e:
            logger.error(f"Failed to train cost predictor: {str(e)}")
            return False
    
    def predict_next_days(self, days: int = 30) -> List[Dict[str, Any]]:
        """
        Predict costs for the next N days
        
        Args:
            days: Number of days to predict
            
        Returns:
            List of predictions with confidence intervals
        """
        if not self.model:
            logger.warning("Model not trained. Cannot make predictions.")
            return []
        
        try:
            # Create future dataframe
            future = self.model.make_future_dataframe(periods=days)
            
            # Generate forecast
            self.forecast = self.model.predict(future)
            
            # Extract predictions for future dates only
            predictions = []
            future_forecast = self.forecast.tail(days)
            
            for _, row in future_forecast.iterrows():
                predictions.append({
                    'date': row['ds'].strftime('%Y-%m-%d'),
                    'predicted_cost': float(row['yhat']),
                    'lower_bound': float(row['yhat_lower']),
                    'upper_bound': float(row['yhat_upper']),
                    'trend': float(row['trend']),
                })
            
            return predictions
            
        except Exception as e:
            logger.error(f"Failed to generate predictions: {str(e)}")
            return []
    
    def detect_anomalies(self, recent_costs: List[Dict[str, Any]], 
                        threshold_std: float = 2.0) -> List[Dict[str, Any]]:
        """
        Detect anomalies in recent costs compared to predictions
        
        Args:
            recent_costs: Recent actual costs to check
            threshold_std: Number of standard deviations for anomaly threshold
            
        Returns:
            List of detected anomalies
        """
        if not self.model or not self.forecast:
            logger.warning("Model not trained or no forecast available")
            return []
        
        anomalies = []
        
        try:
            for cost_data in recent_costs:
                date = pd.to_datetime(cost_data['date'])
                actual_cost = float(cost_data['cost'])
                
                # Find prediction for this date
                forecast_row = self.forecast[self.forecast['ds'] == date]
                
                if not forecast_row.empty:
                    predicted = float(forecast_row['yhat'].iloc[0])
                    lower = float(forecast_row['yhat_lower'].iloc[0])
                    upper = float(forecast_row['yhat_upper'].iloc[0])
                    
                    # Check if outside confidence interval
                    if actual_cost < lower or actual_cost > upper:
                        deviation_percent = abs((actual_cost - predicted) / predicted * 100)
                        
                        anomalies.append({
                            'date': date.strftime('%Y-%m-%d'),
                            'actual_cost': actual_cost,
                            'expected_cost': predicted,
                            'lower_bound': lower,
                            'upper_bound': upper,
                            'deviation_percent': deviation_percent,
                            'type': 'spike' if actual_cost > upper else 'drop',
                            'severity': self._calculate_severity(deviation_percent),
                            'confidence': 0.95,  # Based on our interval width
                        })
            
            return anomalies
            
        except Exception as e:
            logger.error(f"Failed to detect anomalies: {str(e)}")
            return []
    
    def _calculate_severity(self, deviation_percent: float) -> str:
        """Calculate anomaly severity based on deviation"""
        if deviation_percent > 50:
            return 'critical'
        elif deviation_percent > 30:
            return 'high'
        elif deviation_percent > 20:
            return 'medium'
        else:
            return 'low'
    
    def get_cost_insights(self) -> Dict[str, Any]:
        """
        Generate insights from the trained model
        
        Returns:
            Dictionary containing various insights
        """
        if not self.model or not self.forecast:
            return {}
        
        try:
            # Calculate trend
            recent_trend = self.forecast.tail(30)['trend'].mean()
            month_ago_trend = self.forecast.tail(60).head(30)['trend'].mean()
            trend_change = ((recent_trend - month_ago_trend) / month_ago_trend * 100) if month_ago_trend > 0 else 0
            
            # Weekly patterns
            forecast_with_day = self.forecast.copy()
            forecast_with_day['day_of_week'] = pd.to_datetime(forecast_with_day['ds']).dt.dayofweek
            weekly_pattern = forecast_with_day.groupby('day_of_week')['yhat'].mean().to_dict()
            
            # Find cheapest and most expensive days
            cheapest_day = min(weekly_pattern, key=weekly_pattern.get)
            expensive_day = max(weekly_pattern, key=weekly_pattern.get)
            
            days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
            
            return {
                'trend_direction': 'increasing' if trend_change > 0 else 'decreasing',
                'trend_change_percent': abs(trend_change),
                'cheapest_day': days[cheapest_day],
                'expensive_day': days[expensive_day],
                'weekly_savings_potential': weekly_pattern[expensive_day] - weekly_pattern[cheapest_day],
                'forecast_confidence': 0.95,
            }
            
        except Exception as e:
            logger.error(f"Failed to generate insights: {str(e)}")
            return {}


class ResourceUtilizationPredictor:
    """Predict resource utilization patterns"""
    
    def __init__(self):
        self.models = {}  # One model per resource type
        
    def train_resource_model(self, resource_type: str, 
                            utilization_data: List[Dict[str, Any]]) -> bool:
        """
        Train a model for specific resource type utilization
        
        Args:
            resource_type: Type of resource (ec2, rds, etc.)
            utilization_data: Historical utilization data
        """
        try:
            df = pd.DataFrame(utilization_data)
            df['ds'] = pd.to_datetime(df['timestamp'])
            df['y'] = df['utilization'].astype(float)
            
            # Create model with hourly seasonality for resources
            model = Prophet(
                daily_seasonality=True,
                weekly_seasonality=True,
                changepoint_prior_scale=0.1
            )
            
            model.fit(df[['ds', 'y']])
            self.models[resource_type] = model
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to train {resource_type} model: {str(e)}")
            return False
    
    def predict_underutilization(self, resource_type: str, 
                                threshold: float = 20.0) -> List[Dict[str, Any]]:
        """
        Predict periods of underutilization
        
        Args:
            resource_type: Type of resource
            threshold: Utilization threshold (%)
            
        Returns:
            List of predicted underutilization periods
        """
        if resource_type not in self.models:
            return []
        
        try:
            model = self.models[resource_type]
            
            # Predict next 7 days with hourly granularity
            future = model.make_future_dataframe(periods=168, freq='H')
            forecast = model.predict(future)
            
            # Find underutilized periods
            underutilized = []
            future_forecast = forecast.tail(168)
            
            for _, row in future_forecast.iterrows():
                if row['yhat'] < threshold:
                    underutilized.append({
                        'timestamp': row['ds'].isoformat(),
                        'predicted_utilization': float(row['yhat']),
                        'confidence': float(1 - (row['yhat_upper'] - row['yhat_lower']) / 100),
                        'recommendation': 'Consider scheduling shutdown' if row['yhat'] < 10 else 'Consider downsizing'
                    })
            
            return underutilized
            
        except Exception as e:
            logger.error(f"Failed to predict underutilization: {str(e)}")
            return []

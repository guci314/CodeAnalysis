"""
Data processing module for handling various data transformations and analysis.
"""

import pandas as pd
import numpy as np
from typing import List, Dict, Optional, Tuple, Union
from datetime import datetime, timedelta
import logging
from functools import lru_cache
import json

logger = logging.getLogger(__name__)


class DataProcessor:
    """Main class for processing various types of data."""
    
    def __init__(self, config: Dict[str, any]):
        """Initialize the data processor with configuration."""
        self.config = config
        self.cache = {}
        self.processing_history = []
        logger.info(f"DataProcessor initialized with config: {config}")
    
    def process_csv(self, file_path: str, encoding: str = 'utf-8') -> pd.DataFrame:
        """
        Process CSV file and return cleaned DataFrame.
        
        Args:
            file_path: Path to the CSV file
            encoding: File encoding (default: utf-8)
            
        Returns:
            Processed pandas DataFrame
        """
        try:
            df = pd.read_csv(file_path, encoding=encoding)
            df = self._clean_dataframe(df)
            self.processing_history.append({
                'timestamp': datetime.now(),
                'file': file_path,
                'rows': len(df),
                'columns': len(df.columns)
            })
            return df
        except Exception as e:
            logger.error(f"Error processing CSV file {file_path}: {str(e)}")
            raise
    
    def _clean_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """Clean DataFrame by removing nulls and duplicates."""
        initial_shape = df.shape
        
        # Remove duplicates
        df = df.drop_duplicates()
        
        # Handle missing values based on column type
        for col in df.columns:
            if df[col].dtype in ['float64', 'int64']:
                df[col].fillna(df[col].mean(), inplace=True)
            else:
                df[col].fillna('Unknown', inplace=True)
        
        logger.info(f"Cleaned DataFrame from {initial_shape} to {df.shape}")
        return df
    
    @lru_cache(maxsize=128)
    def calculate_statistics(self, data: Tuple[float, ...]) -> Dict[str, float]:
        """Calculate basic statistics for numeric data."""
        data_array = np.array(data)
        return {
            'mean': np.mean(data_array),
            'median': np.median(data_array),
            'std': np.std(data_array),
            'min': np.min(data_array),
            'max': np.max(data_array),
            'quartiles': {
                'q1': np.percentile(data_array, 25),
                'q2': np.percentile(data_array, 50),
                'q3': np.percentile(data_array, 75)
            }
        }
    
    def aggregate_data(self, df: pd.DataFrame, group_by: List[str], 
                      agg_columns: Dict[str, List[str]]) -> pd.DataFrame:
        """
        Aggregate data based on grouping columns and aggregation rules.
        
        Args:
            df: Input DataFrame
            group_by: Columns to group by
            agg_columns: Dictionary mapping columns to aggregation functions
            
        Returns:
            Aggregated DataFrame
        """
        try:
            result = df.groupby(group_by).agg(agg_columns)
            result.columns = ['_'.join(col).strip() for col in result.columns.values]
            result.reset_index(inplace=True)
            return result
        except KeyError as e:
            logger.error(f"Column not found during aggregation: {str(e)}")
            raise ValueError(f"Invalid column specified: {str(e)}")


class TimeSeriesProcessor(DataProcessor):
    """Specialized processor for time series data."""
    
    def __init__(self, config: Dict[str, any], frequency: str = 'D'):
        """Initialize with time series specific configuration."""
        super().__init__(config)
        self.frequency = frequency
        self.seasonal_decomposition = None
    
    def resample_timeseries(self, df: pd.DataFrame, date_column: str, 
                           target_frequency: str, agg_func: str = 'mean') -> pd.DataFrame:
        """
        Resample time series data to a different frequency.
        
        Args:
            df: DataFrame with time series data
            date_column: Name of the date column
            target_frequency: Target frequency ('D', 'W', 'M', etc.)
            agg_func: Aggregation function to use
            
        Returns:
            Resampled DataFrame
        """
        df_copy = df.copy()
        df_copy[date_column] = pd.to_datetime(df_copy[date_column])
        df_copy.set_index(date_column, inplace=True)
        
        # Get numeric columns only
        numeric_cols = df_copy.select_dtypes(include=[np.number]).columns
        
        if agg_func == 'mean':
            return df_copy[numeric_cols].resample(target_frequency).mean()
        elif agg_func == 'sum':
            return df_copy[numeric_cols].resample(target_frequency).sum()
        elif agg_func == 'last':
            return df_copy[numeric_cols].resample(target_frequency).last()
        else:
            raise ValueError(f"Unsupported aggregation function: {agg_func}")
    
    def detect_anomalies(self, data: pd.Series, threshold: float = 3.0) -> pd.DataFrame:
        """
        Detect anomalies in time series data using z-score method.
        
        Args:
            data: Time series data
            threshold: Z-score threshold for anomaly detection
            
        Returns:
            DataFrame with anomaly flags
        """
        mean = data.mean()
        std = data.std()
        z_scores = np.abs((data - mean) / std)
        
        anomalies = pd.DataFrame({
            'value': data,
            'z_score': z_scores,
            'is_anomaly': z_scores > threshold
        })
        
        logger.info(f"Detected {anomalies['is_anomaly'].sum()} anomalies")
        return anomalies
    
    def calculate_moving_averages(self, df: pd.DataFrame, value_column: str,
                                 windows: List[int]) -> pd.DataFrame:
        """Calculate multiple moving averages for a time series."""
        result = df.copy()
        
        for window in windows:
            result[f'ma_{window}'] = df[value_column].rolling(window=window).mean()
            result[f'ma_std_{window}'] = df[value_column].rolling(window=window).std()
        
        return result


def transform_data(data: List[Dict[str, any]], transformations: List[callable]) -> List[Dict[str, any]]:
    """
    Apply a series of transformations to data.
    
    Args:
        data: List of dictionaries containing data
        transformations: List of transformation functions
        
    Returns:
        Transformed data
    """
    result = data.copy()
    
    for transform in transformations:
        try:
            result = [transform(item) for item in result]
        except Exception as e:
            logger.error(f"Transformation failed: {str(e)}")
            raise
    
    return result


def merge_datasets(primary: pd.DataFrame, secondary: pd.DataFrame, 
                   on: Union[str, List[str]], how: str = 'left') -> pd.DataFrame:
    """
    Merge two datasets with validation.
    
    Args:
        primary: Primary DataFrame
        secondary: Secondary DataFrame
        on: Column(s) to merge on
        how: Type of merge (left, right, inner, outer)
        
    Returns:
        Merged DataFrame
    """
    # Validate merge columns exist
    merge_cols = [on] if isinstance(on, str) else on
    
    for col in merge_cols:
        if col not in primary.columns:
            raise ValueError(f"Column '{col}' not found in primary DataFrame")
        if col not in secondary.columns:
            raise ValueError(f"Column '{col}' not found in secondary DataFrame")
    
    # Perform merge
    result = pd.merge(primary, secondary, on=on, how=how, suffixes=('', '_secondary'))
    
    logger.info(f"Merged datasets: {len(primary)} x {len(secondary)} -> {len(result)} rows")
    return result


class DataValidator:
    """Validate data quality and integrity."""
    
    @staticmethod
    def validate_schema(df: pd.DataFrame, schema: Dict[str, type]) -> List[str]:
        """
        Validate DataFrame against expected schema.
        
        Args:
            df: DataFrame to validate
            schema: Expected schema (column_name: expected_type)
            
        Returns:
            List of validation errors
        """
        errors = []
        
        # Check for missing columns
        for col, expected_type in schema.items():
            if col not in df.columns:
                errors.append(f"Missing required column: {col}")
                continue
            
            # Check data types
            actual_type = df[col].dtype
            if expected_type == str and actual_type != 'object':
                errors.append(f"Column '{col}' expected type str but got {actual_type}")
            elif expected_type in [int, float] and not pd.api.types.is_numeric_dtype(actual_type):
                errors.append(f"Column '{col}' expected numeric type but got {actual_type}")
        
        # Check for unexpected columns
        expected_cols = set(schema.keys())
        actual_cols = set(df.columns)
        unexpected = actual_cols - expected_cols
        
        if unexpected:
            errors.append(f"Unexpected columns found: {unexpected}")
        
        return errors
    
    @staticmethod
    def check_data_quality(df: pd.DataFrame) -> Dict[str, any]:
        """
        Perform comprehensive data quality checks.
        
        Args:
            df: DataFrame to check
            
        Returns:
            Dictionary with quality metrics
        """
        quality_report = {
            'total_rows': len(df),
            'total_columns': len(df.columns),
            'missing_values': {},
            'duplicate_rows': len(df[df.duplicated()]),
            'column_stats': {}
        }
        
        # Check missing values by column
        for col in df.columns:
            missing_count = df[col].isnull().sum()
            if missing_count > 0:
                quality_report['missing_values'][col] = {
                    'count': missing_count,
                    'percentage': (missing_count / len(df)) * 100
                }
        
        # Calculate column statistics
        for col in df.select_dtypes(include=[np.number]).columns:
            quality_report['column_stats'][col] = {
                'unique_values': df[col].nunique(),
                'min': df[col].min(),
                'max': df[col].max(),
                'mean': df[col].mean(),
                'std': df[col].std()
            }
        
        return quality_report
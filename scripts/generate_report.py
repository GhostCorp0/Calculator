#!/usr/bin/env python3
"""
CI/CD Report Generator
Generates visual reports and dashboards from collected metrics
"""

import json
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
import os

class CICDReportGenerator:
    def __init__(self):
        self.reports_dir = 'reports'
        self.analytics_dir = 'analytics'
        
        # Set style for matplotlib
        plt.style.use('seaborn-v0_8')
        sns.set_palette("husl")
        
    def load_data(self):
        """Load the latest metrics data"""
        try:
            with open(f'{self.analytics_dir}/latest_runs.json', 'r') as f:
                runs_data = json.load(f)
            
            with open(f'{self.analytics_dir}/latest_jobs.json', 'r') as f:
                jobs_data = json.load(f)
            
            with open(f'{self.analytics_dir}/summary.json', 'r') as f:
                summary_data = json.load(f)
                
            return runs_data, jobs_data, summary_data
        except FileNotFoundError:
            print("No metrics data found. Run collect_metrics.py first.")
            return [], [], {}
    
    def create_dashboard(self):
        """Create comprehensive dashboard with multiple visualizations"""
        runs_data, jobs_data, summary_data = self.load_data()
        
        if not runs_data:
            print("No data available for dashboard generation")
            return
        
        # Convert to DataFrames
        runs_df = pd.DataFrame(runs_data)
        jobs_df = pd.DataFrame(jobs_data)
        
        # Convert timestamps
        runs_df['created_at'] = pd.to_datetime(runs_df['created_at'])
        runs_df['updated_at'] = pd.to_datetime(runs_df['updated_at'])
        
        if not jobs_df.empty:
            jobs_df['started_at'] = pd.to_datetime(jobs_df['started_at'])
            jobs_df['completed_at'] = pd.to_datetime(jobs_df['completed_at'])
        
        # Create dashboard
        self.create_success_rate_chart(runs_df, summary_data)
        self.create_build_time_trend(runs_df)
        self.create_job_breakdown(jobs_df)
        self.create_daily_activity_chart(runs_df)
        self.create_summary_table(summary_data)
        
        print("Dashboard generated successfully!")
    
    def create_success_rate_chart(self, runs_df, summary_data):
        """Create success rate visualization"""
        fig = go.Figure()
        
        # Success rate pie chart
        if summary_data:
            labels = ['Successful', 'Failed', 'Cancelled']
            values = [
                summary_data.get('successful_runs', 0),
                summary_data.get('failed_runs', 0),
                summary_data.get('cancelled_runs', 0)
            ]
            
            fig.add_trace(go.Pie(
                labels=labels,
                values=values,
                hole=0.4,
                marker_colors=['#2ecc71', '#e74c3c', '#f39c12']
            ))
        
        fig.update_layout(
            title='Build Success Rate',
            showlegend=True,
            height=400
        )
        
        fig.write_html(f'{self.reports_dir}/success_rate.html')
        
        # Try to save PNG, but don't fail if it doesn't work
        try:
            fig.write_image(f'{self.reports_dir}/success_rate.png', width=800, height=400)
        except Exception as e:
            print(f"Warning: Could not save PNG image: {e}")
            print("HTML version will still work fine.")
    
    def create_build_time_trend(self, runs_df):
        """Create build time trend chart"""
        if runs_df.empty:
            return
            
        fig = go.Figure()
        
        # Filter successful builds for trend analysis
        successful_runs = runs_df[runs_df['conclusion'] == 'success'].copy()
        
        if not successful_runs.empty:
            successful_runs = successful_runs.sort_values('created_at')
            
            fig.add_trace(go.Scatter(
                x=successful_runs['created_at'],
                y=successful_runs['duration'],
                mode='lines+markers',
                name='Build Duration',
                line=dict(color='#3498db', width=2),
                marker=dict(size=6)
            ))
            
            # Add trend line
            z = np.polyfit(range(len(successful_runs)), successful_runs['duration'], 1)
            p = np.poly1d(z)
            fig.add_trace(go.Scatter(
                x=successful_runs['created_at'],
                y=p(range(len(successful_runs))),
                mode='lines',
                name='Trend',
                line=dict(color='#e74c3c', width=2, dash='dash')
            ))
        
        fig.update_layout(
            title='Build Time Trend',
            xaxis_title='Date',
            yaxis_title='Duration (seconds)',
            height=400
        )
        
        fig.write_html(f'{self.reports_dir}/build_time_trend.html')
        
        # Try to save PNG, but don't fail if it doesn't work
        try:
            fig.write_image(f'{self.reports_dir}/build_time_trend.png', width=800, height=400)
        except Exception as e:
            print(f"Warning: Could not save PNG image: {e}")
            print("HTML version will still work fine.")
    
    def create_job_breakdown(self, jobs_df):
        """Create job breakdown visualization"""
        if jobs_df.empty:
            return
            
        fig = make_subplots(
            rows=1, cols=2,
            subplot_titles=('Job Success Rate', 'Job Duration Distribution'),
            specs=[[{"type": "pie"}, {"type": "histogram"}]]
        )
        
        # Job success rate
        job_success = jobs_df['conclusion'].value_counts()
        fig.add_trace(
            go.Pie(
                labels=job_success.index,
                values=job_success.values,
                name="Job Success"
            ),
            row=1, col=1
        )
        
        # Job duration distribution
        successful_jobs = jobs_df[jobs_df['conclusion'] == 'success']
        if not successful_jobs.empty:
            fig.add_trace(
                go.Histogram(
                    x=successful_jobs['duration'],
                    nbinsx=20,
                    name="Duration Distribution"
                ),
                row=1, col=2
            )
        
        fig.update_layout(height=400, title_text="Job Analysis")
        fig.write_html(f'{self.reports_dir}/job_breakdown.html')
        
        # Try to save PNG, but don't fail if it doesn't work
        try:
            fig.write_image(f'{self.reports_dir}/job_breakdown.png', width=1200, height=400)
        except Exception as e:
            print(f"Warning: Could not save PNG image: {e}")
            print("HTML version will still work fine.")
    
    def create_daily_activity_chart(self, runs_df):
        """Create daily activity heatmap"""
        if runs_df.empty:
            return
            
        # Group by date and count runs
        runs_df['date'] = runs_df['created_at'].dt.date
        daily_counts = runs_df.groupby('date').size().reset_index(name='count')
        daily_counts['date'] = pd.to_datetime(daily_counts['date'])
        
        fig = go.Figure()
        
        fig.add_trace(go.Bar(
            x=daily_counts['date'],
            y=daily_counts['count'],
            name='Daily Builds',
            marker_color='#9b59b6'
        ))
        
        fig.update_layout(
            title='Daily Build Activity',
            xaxis_title='Date',
            yaxis_title='Number of Builds',
            height=400
        )
        
        fig.write_html(f'{self.reports_dir}/daily_activity.html')
        
        # Try to save PNG, but don't fail if it doesn't work
        try:
            fig.write_image(f'{self.reports_dir}/daily_activity.png', width=800, height=400)
        except Exception as e:
            print(f"Warning: Could not save PNG image: {e}")
            print("HTML version will still work fine.")
    
    def create_summary_table(self, summary_data):
        """Create summary statistics table"""
        if not summary_data:
            return
            
        # Create HTML table
        html_content = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>CI/CD Summary Report</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 20px; }
                .summary-table { border-collapse: collapse; width: 100%; margin: 20px 0; }
                .summary-table th, .summary-table td { 
                    border: 1px solid #ddd; padding: 12px; text-align: left; 
                }
                .summary-table th { background-color: #f2f2f2; font-weight: bold; }
                .metric { font-size: 18px; margin: 10px 0; }
                .success { color: #2ecc71; }
                .warning { color: #f39c12; }
                .error { color: #e74c3c; }
            </style>
        </head>
        <body>
            <h1>CI/CD Analytics Summary Report</h1>
            <p>Generated on: {timestamp}</p>
            
            <div class="metric">
                <strong>Total Runs:</strong> {total_runs}
            </div>
            <div class="metric success">
                <strong>Success Rate:</strong> {success_rate:.1f}%
            </div>
            <div class="metric">
                <strong>Average Build Time:</strong> {avg_duration:.1f} seconds
            </div>
            
            <table class="summary-table">
                <tr>
                    <th>Metric</th>
                    <th>Value</th>
                </tr>
                <tr>
                    <td>Successful Runs</td>
                    <td class="success">{successful_runs}</td>
                </tr>
                <tr>
                    <td>Failed Runs</td>
                    <td class="error">{failed_runs}</td>
                </tr>
                <tr>
                    <td>Cancelled Runs</td>
                    <td class="warning">{cancelled_runs}</td>
                </tr>
                <tr>
                    <td>Total Jobs</td>
                    <td>{total_jobs}</td>
                </tr>
                <tr>
                    <td>Job Success Rate</td>
                    <td class="success">{job_success_rate:.1f}%</td>
                </tr>
                <tr>
                    <td>Average Job Duration</td>
                    <td>{avg_job_duration:.1f} seconds</td>
                </tr>
            </table>
        </body>
        </html>
        """.format(
            timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            total_runs=summary_data.get('total_runs', 0),
            success_rate=summary_data.get('run_success_rate', 0),
            avg_duration=summary_data.get('avg_duration', 0),
            successful_runs=summary_data.get('successful_runs', 0),
            failed_runs=summary_data.get('failed_runs', 0),
            cancelled_runs=summary_data.get('cancelled_runs', 0),
            total_jobs=summary_data.get('total_jobs', 0),
            job_success_rate=summary_data.get('job_success_rate', 0),
            avg_job_duration=summary_data.get('avg_job_duration', 0)
        )
        
        with open(f'{self.reports_dir}/summary_report.html', 'w') as f:
            f.write(html_content)
    
    def create_main_dashboard(self):
        """Create a main dashboard that combines all visualizations"""
        html_content = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>CI/CD Analytics Dashboard</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 0; padding: 20px; background-color: #f5f5f5; }
                .dashboard { max-width: 1200px; margin: 0 auto; }
                .header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; border-radius: 10px; margin-bottom: 20px; }
                .grid { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-bottom: 20px; }
                .card { background: white; padding: 20px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
                .full-width { grid-column: 1 / -1; }
                iframe { width: 100%; height: 400px; border: none; border-radius: 5px; }
            </style>
        </head>
        <body>
            <div class="dashboard">
                <div class="header">
                    <h1>🚀 OpenCalc CI/CD Analytics Dashboard</h1>
                    <p>Real-time insights into your build pipeline performance</p>
                </div>
                
                <div class="grid">
                    <div class="card">
                        <h3>📊 Success Rate</h3>
                        <iframe src="success_rate.html"></iframe>
                    </div>
                    
                    <div class="card">
                        <h3>⏱️ Build Time Trend</h3>
                        <iframe src="build_time_trend.html"></iframe>
                    </div>
                    
                    <div class="card">
                        <h3>🔧 Job Breakdown</h3>
                        <iframe src="job_breakdown.html"></iframe>
                    </div>
                    
                    <div class="card">
                        <h3>📅 Daily Activity</h3>
                        <iframe src="daily_activity.html"></iframe>
                    </div>
                </div>
                
                <div class="card full-width">
                    <h3>📋 Summary Report</h3>
                    <iframe src="summary_report.html"></iframe>
                </div>
            </div>
        </body>
        </html>
        """
        
        with open(f'{self.reports_dir}/dashboard.html', 'w') as f:
            f.write(html_content)

if __name__ == "__main__":
    import numpy as np
    
    generator = CICDReportGenerator()
    generator.create_dashboard()
    generator.create_main_dashboard()
    print("All reports generated successfully!") 
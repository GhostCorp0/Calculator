#!/usr/bin/env python3
"""
CI/CD Metrics Collector
Collects build metrics from GitHub Actions and stores them for analytics
"""

import os
import json
import requests
import pandas as pd
from datetime import datetime, timedelta
import time

class CICDMetricsCollector:
    def __init__(self):
        self.github_token = os.environ.get('GITHUB_TOKEN')
        self.repo = os.environ.get('GITHUB_REPOSITORY')
        self.api_url = f"https://api.github.com/repos/{self.repo}"
        self.headers = {
            'Authorization': f'token {self.github_token}',
            'Accept': 'application/vnd.github.v3+json'
        }
        
        # Create directories if they don't exist
        os.makedirs('analytics', exist_ok=True)
        os.makedirs('reports', exist_ok=True)
        
    def get_workflow_runs(self, workflow_name="Android CI/CD", days_back=30):
        """Get workflow runs for the specified period"""
        since_date = datetime.now() - timedelta(days=days_back)
        since_str = since_date.isoformat()
        
        # First, get the workflow ID
        workflows_url = f"{self.api_url}/actions/workflows"
        response = requests.get(workflows_url, headers=self.headers)
        
        if response.status_code != 200:
            print(f"Error fetching workflows: {response.status_code}")
            return []
        
        workflows = response.json()['workflows']
        workflow_id = None
        
        # Find the workflow by name
        for workflow in workflows:
            if workflow['name'] == workflow_name:
                workflow_id = workflow['id']
                break
        
        if not workflow_id:
            print(f"Workflow '{workflow_name}' not found. Available workflows:")
            for workflow in workflows:
                print(f"  - {workflow['name']}")
            return []
        
        # Now get the runs for this workflow
        url = f"{self.api_url}/actions/workflows/{workflow_id}/runs"
        params = {
            'created': f'>={since_str}',
            'per_page': 100
        }
        
        runs = []
        page = 1
        
        while True:
            params['page'] = page
            response = requests.get(url, headers=self.headers, params=params)
            
            if response.status_code != 200:
                print(f"Error fetching workflow runs: {response.status_code}")
                break
                
            data = response.json()
            runs.extend(data['workflow_runs'])
            
            if len(data['workflow_runs']) < 100:
                break
                
            page += 1
            time.sleep(1)  # Rate limiting
            
        return runs
    
    def get_job_details(self, run_id):
        """Get detailed job information for a workflow run"""
        url = f"{self.api_url}/actions/runs/{run_id}/jobs"
        response = requests.get(url, headers=self.headers)
        
        if response.status_code == 200:
            return response.json()['jobs']
        return []
    
    def collect_metrics(self):
        """Collect comprehensive CI/CD metrics"""
        print("Collecting CI/CD metrics...")
        
        # Get workflow runs
        runs = self.get_workflow_runs()
        
        if not runs:
            print("No workflow runs found. Creating sample data for testing...")
            self.create_sample_data()
            return
        
        metrics_data = []
        
        for run in runs:
            # Basic run metrics
            run_metrics = {
                'run_id': run['id'],
                'run_number': run['run_number'],
                'status': run['status'],
                'conclusion': run['conclusion'],
                'created_at': run['created_at'],
                'updated_at': run['updated_at'],
                'duration': run['duration'],
                'actor': run['actor']['login'],
                'head_branch': run['head_branch'],
                'head_sha': run['head_sha'][:8],
                'event': run['event']
            }
            
            # Get job details
            jobs = self.get_job_details(run['id'])
            job_metrics = []
            
            for job in jobs:
                job_metric = {
                    'run_id': run['id'],
                    'job_id': job['id'],
                    'job_name': job['name'],
                    'status': job['status'],
                    'conclusion': job['conclusion'],
                    'started_at': job['started_at'],
                    'completed_at': job['completed_at'],
                    'duration': job['duration'],
                    'runner_name': job['runner_name'] if job['runner_name'] else 'Unknown'
                }
                job_metrics.append(job_metric)
            
            metrics_data.append({
                'run': run_metrics,
                'jobs': job_metrics
            })
            
            print(f"Collected metrics for run #{run['run_number']}")
        
        # Save metrics to files
        self.save_metrics(metrics_data)
        
        # Generate summary statistics
        self.generate_summary(metrics_data)
        
        print(f"Collected metrics for {len(runs)} workflow runs")
    
    def create_sample_data(self):
        """Create sample data for testing when no real data is available"""
        print("Creating sample analytics data...")
        
        # Create sample run data
        sample_runs = [
            {
                'run_id': 1,
                'run_number': 1,
                'status': 'completed',
                'conclusion': 'success',
                'created_at': (datetime.now() - timedelta(days=1)).isoformat(),
                'updated_at': datetime.now().isoformat(),
                'duration': 180,
                'actor': 'amansingh08088',
                'head_branch': 'master',
                'head_sha': 'abc12345',
                'event': 'push'
            },
            {
                'run_id': 2,
                'run_number': 2,
                'status': 'completed',
                'conclusion': 'success',
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat(),
                'duration': 165,
                'actor': 'amansingh08088',
                'head_branch': 'master',
                'head_sha': 'def67890',
                'event': 'push'
            }
        ]
        
        # Create sample job data
        sample_jobs = [
            {
                'run_id': 1,
                'job_id': 1,
                'job_name': 'Build & Artifact Bundle',
                'status': 'completed',
                'conclusion': 'success',
                'started_at': (datetime.now() - timedelta(hours=1)).isoformat(),
                'completed_at': datetime.now().isoformat(),
                'duration': 180,
                'runner_name': 'ubuntu-latest'
            },
            {
                'run_id': 2,
                'job_id': 2,
                'job_name': 'Build & Artifact Bundle',
                'status': 'completed',
                'conclusion': 'success',
                'started_at': (datetime.now() - timedelta(minutes=30)).isoformat(),
                'completed_at': datetime.now().isoformat(),
                'duration': 165,
                'runner_name': 'ubuntu-latest'
            }
        ]
        
        # Save sample data
        with open('analytics/latest_runs.json', 'w') as f:
            json.dump(sample_runs, f, indent=2)
        
        with open('analytics/latest_jobs.json', 'w') as f:
            json.dump(sample_jobs, f, indent=2)
        
        # Create sample summary
        sample_summary = {
            'total_runs': 2,
            'successful_runs': 2,
            'failed_runs': 0,
            'cancelled_runs': 0,
            'avg_duration': 172.5,
            'total_jobs': 2,
            'successful_jobs': 2,
            'failed_jobs': 0,
            'avg_job_duration': 172.5,
            'run_success_rate': 100.0,
            'job_success_rate': 100.0
        }
        
        with open('analytics/summary.json', 'w') as f:
            json.dump(sample_summary, f, indent=2)
        
        print("Sample data created successfully!")
    
    def save_metrics(self, metrics_data):
        """Save metrics to JSON files"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Save run metrics
        runs_data = [m['run'] for m in metrics_data]
        with open(f'analytics/runs_{timestamp}.json', 'w') as f:
            json.dump(runs_data, f, indent=2)
        
        # Save job metrics
        jobs_data = []
        for m in metrics_data:
            jobs_data.extend(m['jobs'])
        
        with open(f'analytics/jobs_{timestamp}.json', 'w') as f:
            json.dump(jobs_data, f, indent=2)
        
        # Save latest metrics for dashboard
        with open('analytics/latest_runs.json', 'w') as f:
            json.dump(runs_data, f, indent=2)
        
        with open('analytics/latest_jobs.json', 'w') as f:
            json.dump(jobs_data, f, indent=2)
    
    def generate_summary(self, metrics_data):
        """Generate summary statistics"""
        runs = [m['run'] for m in metrics_data]
        jobs = []
        for m in metrics_data:
            jobs.extend(m['jobs'])
        
        # Convert to DataFrames
        runs_df = pd.DataFrame(runs)
        jobs_df = pd.DataFrame(jobs)
        
        # Calculate summary statistics
        summary = {
            'total_runs': len(runs),
            'successful_runs': len([r for r in runs if r['conclusion'] == 'success']),
            'failed_runs': len([r for r in runs if r['conclusion'] == 'failure']),
            'cancelled_runs': len([r for r in runs if r['conclusion'] == 'cancelled']),
            'avg_duration': runs_df['duration'].mean() if not runs_df.empty else 0,
            'total_jobs': len(jobs),
            'successful_jobs': len([j for j in jobs if j['conclusion'] == 'success']),
            'failed_jobs': len([j for j in jobs if j['conclusion'] == 'failure']),
            'avg_job_duration': jobs_df['duration'].mean() if not jobs_df.empty else 0
        }
        
        # Calculate success rates
        summary['run_success_rate'] = (summary['successful_runs'] / summary['total_runs'] * 100) if summary['total_runs'] > 0 else 0
        summary['job_success_rate'] = (summary['successful_jobs'] / summary['total_jobs'] * 100) if summary['total_jobs'] > 0 else 0
        
        # Save summary
        with open('analytics/summary.json', 'w') as f:
            json.dump(summary, f, indent=2)
        
        print("Summary statistics:")
        print(f"Total runs: {summary['total_runs']}")
        print(f"Success rate: {summary['run_success_rate']:.1f}%")
        print(f"Average duration: {summary['avg_duration']:.1f} seconds")

if __name__ == "__main__":
    collector = CICDMetricsCollector()
    collector.collect_metrics() 
import os
import time
import json
from datetime import datetime, timedelta
from pathlib import Path

class CronJobManager:
    """Manage cron jobs and schedule tasks"""
    
    def __init__(self):
        self.job_log_file = Path("/root/.openclaw/workspace/propaganda-pipeline/tests/dashboard/job_log.json")
        self.ensure_log_file()
    
    def ensure_log_file(self):
        """Ensure log file exists"""
        if not self.job_log_file.exists():
            self.job_log_file.write_text(json.dumps({
                "jobs": [],
                "last_run": None
            }, indent=2))
    
    def log_job_run(self, job_name, status):
        """Log a job execution"""
        data = json.loads(self.job_log_file.read_text())
        
        job_entry = {
            "job_name": job_name,
            "status": status,
            "timestamp": datetime.now().isoformat(),
            "message": f"{job_name} executed at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        }
        
        data["jobs"].append(job_entry)
        data["last_run"] = datetime.now().isoformat()
        
        # Keep only last 50 entries
        if len(data["jobs"]) > 50:
            data["jobs"] = data["jobs"][-50:]
        
        self.job_log_file.write_text(json.dumps(data, indent=2))
    
    def get_job_status(self):
        """Get current job status"""
        if not self.job_log_file.exists():
            return {
                "status": "No jobs executed yet",
                "last_run": None,
                "jobs_count": 0
            }
        
        data = json.loads(self.job_log_file.read_text())
        
        return {
            "status": "Active",
            "last_run": data.get("last_run"),
            "jobs_count": len(data.get("jobs", [])),
            "recent_jobs": data.get("jobs", [])[-5:]  # Last 5 jobs
        }

class DashboardManager:
    """Manage dashboard data and updates"""
    
    def __init__(self):
        self.dashboard_file = Path("/root/.openclaw/workspace/propaganda-pipeline/tests/dashboard/dashboard_data.json")
        self.ensure_dashboard_file()
    
    def ensure_dashboard_file(self):
        """Ensure dashboard file exists"""
        if not self.dashboard_file.exists():
            self.dashboard_file.write_text(json.dumps({
                "dashboard": {
                    "title": "Propaganda Pipeline Dashboard",
                    "last_updated": None,
                    "status": "Initializing...",
                    "stats": {
                        "total_jobs": 0,
                        "successful_jobs": 0,
                        "failed_jobs": 0
                    },
                    "recent_activity": []
                }
            }, indent=2))
    
    def update_dashboard(self, job_name, status, message=""):
        """Update dashboard with new data"""
        data = json.loads(self.dashboard_file.read_text())
        dashboard = data["dashboard"]
        
        # Update stats
        dashboard["last_updated"] = datetime.now().isoformat()
        dashboard["status"] = "Active" if status else "Error"
        
        # Update stats
        dashboard["stats"]["total_jobs"] = dashboard["stats"].get("total_jobs", 0) + 1
        if status:
            dashboard["stats"]["successful_jobs"] = dashboard["stats"].get("successful_jobs", 0) + 1
        else:
            dashboard["stats"]["failed_jobs"] = dashboard["stats"].get("failed_jobs", 0) + 1
        
        # Add to recent activity
        activity_entry = {
            "timestamp": datetime.now().isoformat(),
            "job_name": job_name,
            "status": "Success" if status else "Failed",
            "message": message or f"{job_name} {'succeeded' if status else 'failed'}"
        }
        
        dashboard["recent_activity"].append(activity_entry)
        if len(dashboard["recent_activity"]) > 10:
            dashboard["recent_activity"] = dashboard["recent_activity"][-10:]
        
        self.dashboard_file.write_text(json.dumps(data, indent=2))
    
    def get_dashboard_data(self):
        """Get current dashboard data"""
        if not self.dashboard_file.exists():
            return {
                "title": "Propaganda Pipeline Dashboard",
                "last_updated": None,
                "status": "Initializing...",
                "stats": {
                    "total_jobs": 0,
                    "successful_jobs": 0,
                    "failed_jobs": 0
                },
                "recent_activity": []
            }
        
        data = json.loads(self.dashboard_file.read_text())
        return data["dashboard"]

def test_dashboard_update():
    """Test dashboard update functionality"""
    print("📊 Testing Dashboard Update...")
    
    # Initialize managers
    cron_manager = CronJobManager()
    dashboard_manager = DashboardManager()
    
    # Test job execution
    job_name = "test_dashboard_update"
    try:
        # Simulate some work
        print("🔧 Simulating dashboard update...")
        time.sleep(1)
        
        # Log job
        cron_manager.log_job_run(job_name, True)
        
        # Update dashboard
        dashboard_manager.update_dashboard(job_name, True, "Dashboard update test completed successfully")
        
        print("✅ Dashboard update test successful!")
        return True
        
    except Exception as e:
        print(f"❌ Dashboard update test failed: {e}")
        cron_manager.log_job_run(job_name, False)
        dashboard_manager.update_dashboard(job_name, False, f"Error: {str(e)}")
        return False

if __name__ == "__main__":
    print("🚀 Running dashboard test...")
    test_dashboard_update()
    
    # Show current status
    cron_manager = CronJobManager()
    dashboard_manager = DashboardManager()
    
    print("\n📊 Current Dashboard Status:")
    status = dashboard_manager.get_dashboard_data()
    print(json.dumps(status, indent=2, default=str))
    
    print("\n🔔 Current Job Status:")
    job_status = cron_manager.get_job_status()
    print(json.dumps(job_status, indent=2, default=str))
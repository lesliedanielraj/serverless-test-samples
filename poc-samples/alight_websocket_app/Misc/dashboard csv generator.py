import csv
import uuid
from tabulate import tabulate

# Generate sample dashboard data with GUIDs
dashboard_data = [
    {
        "dashboard_id": str(uuid.uuid4()),
        "dashboard_name": "Health Benefits Overview",
        "description": "Comprehensive view of employee health benefits enrollment, claims, and utilization metrics"
    },
    {
        "dashboard_id": str(uuid.uuid4()),
        "dashboard_name": "Healthcare Claims Analysis",
        "description": "Detailed analysis of medical and prescription claims patterns, costs and trends"
    },
    {
        "dashboard_id": str(uuid.uuid4()),
        "dashboard_name": "401k Plan Summary",
        "description": "Overview of 401k plan participation, contribution rates and investment allocations"
    },
    {
        "dashboard_id": str(uuid.uuid4()),
        "dashboard_name": "Financial Wellness Metrics",
        "description": "Key indicators of employee financial health including savings rates and retirement readiness"
    },
    {
        "dashboard_id": str(uuid.uuid4()),
        "dashboard_name": "Leave Management Dashboard",
        "description": "Track employee leave requests, approvals and usage across different leave types"
    },
    {
        "dashboard_id": str(uuid.uuid4()),
        "dashboard_name": "Absence Analytics",
        "description": "Analysis of absence patterns, trends and impact on workforce availability"
    }
]

# Write to CSV file
filename = "quicksight_dashboards.csv"
fields = ["dashboard_id", "dashboard_name", "description"]

with open(filename, 'w', newline='') as csvfile:
    writer = csv.DictWriter(csvfile, fieldnames=fields)
    writer.writeheader()
    writer.writerows(dashboard_data)

# Read and display the CSV file
with open(filename, 'r') as csvfile:
    reader = csv.reader(csvfile)
    headers = next(reader)  # Get the headers
    data = list(reader)  # Get the data rows

print(tabulate(data, headers=headers, tablefmt="grid"))

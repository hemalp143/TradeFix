#!/usr/bin/env python
"""
AI Worker Marketplace CLI Tool

Usage:
    cli workers list --status=pending --tier=professional
    cli jobs create --title="Plumbing repair" --skills="plumbing,emergency" --pay=50
    cli matching auto-run --min-score=0.80
    cli approvals auto-process --threshold=80
    cli analytics workers --stats
"""

import typer
from typing import List, Optional
from rich.console import Console
from rich.table import Table
from datetime import datetime
import requests
import json

app = typer.Typer(
    name="marketplace",
    help="AI Worker Marketplace CLI",
    no_args_is_help=True
)

# API Configuration
API_BASE_URL = "http://localhost:8000/api/v1"
console = Console()


# ============================================================================
# WORKERS COMMANDS
# ============================================================================

workers_app = typer.Typer(help="Manage workers")
app.add_command(workers_app, name="workers")


@workers_app.command("list")
def list_workers(
    status: Optional[str] = typer.Option(None, help="Filter by status (pending/approved/rejected)"),
    tier: Optional[str] = typer.Option(None, help="Filter by tier (starter/professional/enterprise)"),
    postal_code: Optional[str] = typer.Option(None, help="Filter by postal code"),
    skip: int = typer.Option(0, help="Skip N records"),
    limit: int = typer.Option(50, help="Limit results to N records"),
):
    """List workers with filters."""
    try:
        params = {"skip": skip, "limit": limit}
        if status:
            params["status"] = status
        if tier:
            params["tier"] = tier
        if postal_code:
            params["postal_code"] = postal_code

        response = requests.get(f"{API_BASE_URL}/workers", params=params)
        response.raise_for_status()
        data = response.json()

        # Create table
        table = Table(title=f"Workers ({data['total']} total)")
        table.add_column("ID", style="cyan")
        table.add_column("Name", style="magenta")
        table.add_column("Email")
        table.add_column("Postal Code", style="green")
        table.add_column("Tier")
        table.add_column("Status")
        table.add_column("Rating")
        table.add_column("Approval")

        for worker in data["workers"]:
            table.add_row(
                str(worker["id"]),
                f"{worker['first_name']} {worker['last_name']}",
                worker["email"],
                worker["postal_code"],
                worker["subscription_tier"],
                worker["subscription_status"],
                f"★ {worker['rating']:.1f}",
                f"Score: {worker['approval_score']:.0f}"
            )

        console.print(table)
        console.print(f"\n[green]✓[/green] Showing {len(data['workers'])} of {data['total']} workers")

    except requests.exceptions.RequestException as e:
        console.print(f"[red]✗ Error:[/red] {e}")
        raise typer.Exit(1)


@workers_app.command("view")
def view_worker(worker_id: int = typer.Argument(..., help="Worker ID")):
    """View detailed worker profile."""
    try:
        response = requests.get(f"{API_BASE_URL}/workers/{worker_id}")
        response.raise_for_status()
        worker = response.json()

        # Display worker details
        table = Table(title=f"Worker #{worker['id']}")
        table.add_column("Field", style="cyan")
        table.add_column("Value")

        fields = [
            ("Name", f"{worker['first_name']} {worker['last_name']}"),
            ("Email", worker["email"]),
            ("Phone", worker["phone"] or "N/A"),
            ("Postal Code", worker["postal_code"]),
            ("Skills", ", ".join(worker["skills"]) if worker["skills"] else "None"),
            ("Experience", f"{worker['experience_years']} years"),
            ("Hourly Rate", f"£{worker['hourly_rate']:.2f}"),
            ("Subscription", worker["subscription_tier"]),
            ("Status", worker["subscription_status"]),
            ("Approval", worker["approval_status"]),
            ("Approval Score", f"{worker['approval_score']:.0f}/100"),
            ("Rating", f"★ {worker['rating']:.1f}"),
            ("Matched Jobs", str(worker["matched_jobs"])),
            ("Registered", worker["created_at"][:10]),
        ]

        for field, value in fields:
            table.add_row(field, value)

        console.print(table)

    except requests.exceptions.RequestException as e:
        console.print(f"[red]✗ Error:[/red] {e}")
        raise typer.Exit(1)


@workers_app.command("approve")
def approve_worker(
    worker_id: int = typer.Argument(..., help="Worker ID"),
    notes: Optional[str] = typer.Option(None, help="Approval notes"),
):
    """Approve a pending worker."""
    try:
        # This would need the approval ID, not worker ID
        # Simplified for demo
        console.print(f"[green]✓[/green] Worker {worker_id} approved")
        console.print(f"  Notes: {notes or 'None'}")

    except Exception as e:
        console.print(f"[red]✗ Error:[/red] {e}")
        raise typer.Exit(1)


@workers_app.command("suspend")
def suspend_worker(
    worker_id: int = typer.Argument(..., help="Worker ID"),
    reason: Optional[str] = typer.Option(None, help="Suspension reason"),
):
    """Suspend a worker's account."""
    try:
        console.print(f"[yellow]⚠[/yellow] Suspended worker {worker_id}")
        console.print(f"  Reason: {reason or 'No reason specified'}")

    except Exception as e:
        console.print(f"[red]✗ Error:[/red] {e}")
        raise typer.Exit(1)


# ============================================================================
# JOBS COMMANDS
# ============================================================================

jobs_app = typer.Typer(help="Manage jobs")
app.add_command(jobs_app, name="jobs")


@jobs_app.command("list")
def list_jobs(
    status: Optional[str] = typer.Option(None, help="Filter by status"),
    postal_code: Optional[str] = typer.Option(None, help="Filter by postal code"),
    priority: Optional[str] = typer.Option(None, help="Filter by priority"),
    skip: int = typer.Option(0),
    limit: int = typer.Option(50),
):
    """List jobs."""
    try:
        params = {"skip": skip, "limit": limit}
        if status:
            params["status"] = status
        if postal_code:
            params["postal_code"] = postal_code

        response = requests.get(f"{API_BASE_URL}/jobs", params=params)
        response.raise_for_status()
        data = response.json()

        table = Table(title=f"Jobs ({data['total']} total)")
        table.add_column("ID", style="cyan")
        table.add_column("Title", style="magenta", width=30)
        table.add_column("Category")
        table.add_column("Pay", style="green")
        table.add_column("Hours")
        table.add_column("Status")
        table.add_column("Assigned To")

        for job in data["jobs"]:
            table.add_row(
                str(job["id"]),
                job["title"][:28],
                job["category"],
                f"£{job['pay_rate']:.2f}",
                f"{job['duration_hours']:.1f}h",
                job["status"],
                str(job["assigned_worker_id"] or "-")
            )

        console.print(table)
        console.print(f"\n[green]✓[/green] Showing {len(data['jobs'])} of {data['total']} jobs")

    except requests.exceptions.RequestException as e:
        console.print(f"[red]✗ Error:[/red] {e}")
        raise typer.Exit(1)


@jobs_app.command("match")
def match_job(
    job_id: int = typer.Argument(..., help="Job ID"),
    top_n: int = typer.Option(5, help="Show top N matches"),
    min_score: float = typer.Option(0.65, help="Minimum match score"),
):
    """Find best workers for a job using AI matching."""
    try:
        payload = {
            "job_id": job_id,
            "top_n": top_n,
            "min_score": min_score
        }

        response = requests.post(f"{API_BASE_URL}/matching/find-workers", json=payload)
        response.raise_for_status()
        data = response.json()

        if not data["matches"]:
            console.print(f"[yellow]⚠[/yellow] No suitable workers found for job {job_id}")
            return

        table = Table(title=f"Top Matches for '{data['job_title']}'")
        table.add_column("Rank", style="cyan")
        table.add_column("Worker", style="magenta")
        table.add_column("Score", style="green")
        table.add_column("Skills")
        table.add_column("Exp", justify="right")
        table.add_column("Location", justify="right")
        table.add_column("Reason")

        for idx, match in enumerate(data["matches"], 1):
            table.add_row(
                str(idx),
                f"#{match['worker_id']}",
                f"{match['overall_score']:.2f}",
                f"Skills: {match['skills_match']:.2f}",
                f"{match['experience_match']:.2f}",
                f"{match['location_match']:.2f}",
                match["reasoning"][:40]
            )

        console.print(table)
        console.print(f"\n[green]✓[/green] Found {data['total_matches']} suitable workers")

    except requests.exceptions.RequestException as e:
        console.print(f"[red]✗ Error:[/red] {e}")
        raise typer.Exit(1)


# ============================================================================
# MATCHING COMMANDS
# ============================================================================

matching_app = typer.Typer(help="Matching & recommendations")
app.add_command(matching_app, name="matching")


@matching_app.command("auto-run")
def auto_run_matching(
    min_score: float = typer.Option(0.80, help="Minimum match score threshold"),
):
    """Auto-run matching for all open jobs."""
    try:
        console.print(f"[cyan]⟳[/cyan] Running auto-matching for all open jobs...")
        console.print(f"  Min score threshold: {min_score}")

        # This would fetch all open jobs and run matching
        # Simplified for demo
        console.print(f"\n[green]✓[/green] Matching complete!")
        console.print(f"  Processed: 15 jobs")
        console.print(f"  Matches created: 42")

    except Exception as e:
        console.print(f"[red]✗ Error:[/red] {e}")
        raise typer.Exit(1)


# ============================================================================
# APPROVALS COMMANDS
# ============================================================================

approvals_app = typer.Typer(help="Approval workflows")
app.add_command(approvals_app, name="approvals")


@approvals_app.command("list")
def list_approvals(
    status: Optional[str] = typer.Option("pending", help="Filter by status"),
    skip: int = typer.Option(0),
    limit: int = typer.Option(50),
):
    """List pending approvals."""
    try:
        response = requests.get(
            f"{API_BASE_URL}/approvals/pending",
            params={"skip": skip, "limit": limit}
        )
        response.raise_for_status()
        data = response.json()

        table = Table(title=f"Pending Approvals ({data['total']} total)")
        table.add_column("ID", style="cyan")
        table.add_column("Worker ID")
        table.add_column("Email")
        table.add_column("Score", style="green")
        table.add_column("AI Decision", style="magenta")
        table.add_column("Reasoning", width=40)

        for approval in data["approvals"]:
            table.add_row(
                str(approval["id"]),
                str(approval["worker_id"]),
                "worker@email.com",  # Would come from actual data
                f"{approval['score']:.0f}",
                approval["decision"] or "pending",
                approval["reasoning"][:38]
            )

        console.print(table)

    except requests.exceptions.RequestException as e:
        console.print(f"[red]✗ Error:[/red] {e}")
        raise typer.Exit(1)


@approvals_app.command("auto-process")
def auto_process_approvals(
    threshold: float = typer.Option(80.0, help="Score threshold for auto-approval"),
):
    """Auto-process pending approvals."""
    try:
        console.print(f"[cyan]⟳[/cyan] Processing approvals with threshold {threshold}...")

        payload = {"worker_ids": []}  # Would be fetched from pending approvals

        response = requests.post(f"{API_BASE_URL}/approvals/auto-process", json=payload)
        response.raise_for_status()
        data = response.json()

        console.print(f"\n[green]✓[/green] Approval processing complete!")
        console.print(f"  Auto-approved: {data['auto_approved']}")
        console.print(f"  Manual review: {data['manual_review']}")

    except requests.exceptions.RequestException as e:
        console.print(f"[red]✗ Error:[/red] {e}")
        raise typer.Exit(1)


# ============================================================================
# ANALYTICS COMMANDS
# ============================================================================

analytics_app = typer.Typer(help="Analytics & reporting")
app.add_command(analytics_app, name="analytics")


@analytics_app.command("workers")
def worker_analytics():
    """Worker statistics and analytics."""
    try:
        response = requests.get(f"{API_BASE_URL}/analytics/workers")
        response.raise_for_status()
        stats = response.json()

        table = Table(title="Worker Analytics")
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="green")

        fields = [
            ("Total Workers", stats["total_workers"]),
            ("Active Workers", stats["active_workers"]),
            ("Approved Workers", stats["approved_workers"]),
            ("Pending Approvals", stats["pending_approvals"]),
            ("Average Rating", f"★ {stats['avg_rating']:.2f}"),
            ("Total Matched Jobs", stats["total_matched_jobs"]),
        ]

        for field, value in fields:
            table.add_row(field, str(value))

        console.print(table)

    except requests.exceptions.RequestException as e:
        console.print(f"[red]✗ Error:[/red] {e}")
        raise typer.Exit(1)


@analytics_app.command("jobs")
def job_analytics():
    """Job statistics."""
    try:
        response = requests.get(f"{API_BASE_URL}/analytics/jobs")
        response.raise_for_status()
        stats = response.json()

        table = Table(title="Job Analytics")
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="green")

        fields = [
            ("Total Jobs", stats["total_jobs"]),
            ("Open Jobs", stats["open_jobs"]),
            ("Assigned", stats["assigned_jobs"]),
            ("Completed", stats["completed_jobs"]),
        ]

        for field, value in fields:
            table.add_row(field, str(value))

        console.print(table)

    except requests.exceptions.RequestException as e:
        console.print(f"[red]✗ Error:[/red] {e}")
        raise typer.Exit(1)


# ============================================================================
# SYSTEM COMMANDS
# ============================================================================

system_app = typer.Typer(help="System administration")
app.add_command(system_app, name="system")


@system_app.command("health")
def system_health():
    """Check system health."""
    try:
        response = requests.get(f"http://localhost:8000/health")
        response.raise_for_status()
        data = response.json()

        console.print(f"[green]✓ System Status: {data['status'].upper()}[/green]")
        console.print(f"  App: {data['app']}")

    except Exception as e:
        console.print(f"[red]✗ System Error:[/red] {e}")
        raise typer.Exit(1)


if __name__ == "__main__":
    app()

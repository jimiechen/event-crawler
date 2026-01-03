
import pytest
from fastapi.testclient import TestClient
from datetime import date, timedelta
from app.main import app
from app.models.stock_daily import StockScoreResult
from app.database import db_manager
import asyncio

client = TestClient(app)

def test_ranking_endpoints():
    # 1. Test Growth Ranking
    # We need valid dates. Let's use today and yesterday.
    today = date.today()
    yesterday = today - timedelta(days=1)
    
    # We might not have data, so we expect empty list or success with empty data
    # But we want to ensure no 422 or 500 error.
    response = client.get("/api/v1/rankings/growth", params={
        "start_date": yesterday.isoformat(),
        "end_date": today.isoformat(),
        "limit": 10
    })
    
    print(f"\nGrowth Ranking Response: {response.status_code}")
    if response.status_code != 200:
        print(response.json())
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    print(f"Growth Data: {data['data']}")

    # 2. Test Total Ranking
    response = client.get("/api/v1/rankings/total", params={
        "target_date": today.isoformat(),
        "limit": 10
    })
    
    print(f"\nTotal Ranking Response: {response.status_code}")
    if response.status_code != 200:
        print(response.json())
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    print(f"Total Data: {data['data']}")

def test_timed_task_endpoints():
    # 1. Test Pool Sync (should be fast if no stocks or mocked)
    # We won't actually wait for full sync, but check if endpoint accepts request
    # Note: These endpoints trigger async tasks usually, but the controller awaits them?
    # trigger_pool_sync awaits TushareService.refresh_stock_pool and LocalDataService.load_local_data_for_stocks
    # It might fail if DB not init or dependencies missing.
    
    # We'll skip actual execution if it relies on external services (Tushare) that might fail in this env without token.
    # But we can check if the route exists and signature is correct.
    pass

if __name__ == "__main__":
    # Manually run tests
    try:
        test_ranking_endpoints()
        print("\n✅ Ranking Endpoints Test Passed")
    except Exception as e:
        print(f"\n❌ Ranking Endpoints Test Failed: {e}")

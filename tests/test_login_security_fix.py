import os
import sys
import pytest
import asyncio
import httpx
from sqlalchemy.future import select
from sqlalchemy import func

# Ensure backend and root are in python path
sys.path.insert(0, os.path.abspath("backend"))
sys.path.insert(0, os.path.abspath("."))

from app.main import app
from app.core.database import AsyncSessionLocal, init_db
from app.models.user import User
from app.core.security import verify_password

@pytest.mark.asyncio
async def test_demo_user_seeded_in_backend_database():
    """Verify demo account is automatically seeded in backend database with bcrypt hash."""
    await init_db()
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(User).where(func.lower(User.email) == "demo_creator@polygen.ai")
        )
        user = result.scalars().first()
        assert user is not None, "Demo account 'demo_creator@polygen.ai' not found in database!"
        assert user.username == "demo_creator"
        assert user.password_hash.startswith("$2b$") or user.password_hash.startswith("$2a$")
        assert "PolyGen2026Secure!" not in user.password_hash
        assert verify_password("PolyGen2026Secure!", user.password_hash) is True

@pytest.mark.asyncio
async def test_login_variations_case_and_whitespace():
    """Verify login handles case-insensitivity and whitespace cleanly."""
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        # 1. Exact email
        r1 = await client.post("/api/auth/login", json={
            "username_or_email": "demo_creator@polygen.ai",
            "password": "PolyGen2026Secure!"
        })
        assert r1.status_code == 200, f"Failed exact email login: {r1.text}"
        data1 = r1.json()
        assert data1["user"]["email"] == "demo_creator@polygen.ai"
        assert "access_token" in data1
        assert "refresh_token" in data1

        # 2. Username
        r2 = await client.post("/api/auth/login", json={
            "username_or_email": "demo_creator",
            "password": "PolyGen2026Secure!"
        })
        assert r2.status_code == 200, f"Failed username login: {r2.text}"

        # 3. Uppercase email
        r3 = await client.post("/api/auth/login", json={
            "username_or_email": "DEMO_CREATOR@POLYGEN.AI",
            "password": "PolyGen2026Secure!"
        })
        assert r3.status_code == 200, f"Failed uppercase email login: {r3.text}"

        # 4. Leading and trailing whitespace
        r4 = await client.post("/api/auth/login", json={
            "username_or_email": "   demo_creator@polygen.ai   ",
            "password": "PolyGen2026Secure!"
        })
        assert r4.status_code == 200, f"Failed whitespace email login: {r4.text}"

        # 5. Wrong password rejected
        r5 = await client.post("/api/auth/login", json={
            "username_or_email": "demo_creator@polygen.ai",
            "password": "WrongPassword2026!"
        })
        assert r5.status_code == 401

@pytest.mark.asyncio
async def test_password_security_requirements_enforced():
    """Verify strict password requirements: min 8 chars, uppercase, lowercase, number/symbol."""
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        # Too short (< 8 chars)
        r1 = await client.post("/api/auth/register", json={
            "username": "sec_test_1",
            "email": "sec1@polygen.ai",
            "password": "Short1!"
        })
        assert r1.status_code == 422

        # Missing uppercase
        r2 = await client.post("/api/auth/register", json={
            "username": "sec_test_2",
            "email": "sec2@polygen.ai",
            "password": "lowercaseonly123!"
        })
        assert r2.status_code == 422

        # Missing lowercase
        r3 = await client.post("/api/auth/register", json={
            "username": "sec_test_3",
            "email": "sec3@polygen.ai",
            "password": "UPPERCASEONLY123!"
        })
        assert r3.status_code == 422

        # Missing number or symbol
        r4 = await client.post("/api/auth/register", json={
            "username": "sec_test_4",
            "email": "sec4@polygen.ai",
            "password": "NoDigitsOrSymbolsHere"
        })
        assert r4.status_code == 422

        # Valid password registered and stored securely in backend
        import uuid
        unique_suffix = str(uuid.uuid4())[:8]
        valid_email = f"verified_user_{unique_suffix}@polygen.ai"
        valid_user = f"vuser_{unique_suffix}"
        valid_pass = "ValidP@ssword2026!"

        r5 = await client.post("/api/auth/register", json={
            "username": valid_user,
            "email": valid_email,
            "password": valid_pass
        })
        assert r5.status_code == 201
        token_data = r5.json()
        assert token_data["user"]["username"] == valid_user

        # Verify data is stored in backend database
        async with AsyncSessionLocal() as session:
            db_res = await session.execute(select(User).where(User.email == valid_email))
            stored_user = db_res.scalars().first()
            assert stored_user is not None
            assert stored_user.email == valid_email
            assert stored_user.password_hash.startswith("$2b$")
            assert valid_pass not in stored_user.password_hash
            assert verify_password(valid_pass, stored_user.password_hash) is True

if __name__ == "__main__":
    asyncio.run(test_demo_user_seeded_in_backend_database())
    asyncio.run(test_login_variations_case_and_whitespace())
    asyncio.run(test_password_security_requirements_enforced())
    print("\nALL LOGIN, SECURITY & BACKEND STORAGE TESTS COMPLETED SUCCESSFULLY!")

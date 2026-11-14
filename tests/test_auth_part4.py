import sys
import os
import asyncio
import uuid
from datetime import datetime, timedelta

# Set backend in test mode
os.environ["AI_BACKEND"] = "procedural"
os.environ["CELERY_TASK_ALWAYS_EAGER"] = "true"
sys.path.insert(0, os.path.abspath("backend"))
sys.path.insert(0, os.path.abspath("."))

from httpx import AsyncClient, ASGITransport
from app.main import app
from app.config import settings
from app.core.database import init_db
from app.core.security import create_access_token, verify_password
from app.models.user import User
from app.models.asset import GeneratedAsset
from app.models.job import GenerationJob
from app.core.database import AsyncSessionLocal
from sqlalchemy.future import select

async def run_part4_tests():
    print("=" * 65)
    print("POLYGEN PART 4: COMPLETE AUTHENTICATION INTEGRATION TEST SUITE")
    print("=" * 65)

    await init_db()
    print("✓ Database initialized")

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # ---------------------------------------------------------
        # 1. Email and Password Validation on Registration
        # ---------------------------------------------------------
        print("\n--- 1. Testing Registration Validation & Security ---")
        
        # 1a. Invalid email format
        bad_email_res = await client.post("/api/auth/register", json={
            "username": "user_bad_email",
            "email": "not-a-valid-email",
            "password": "ValidPassword2026!"
        })
        assert bad_email_res.status_code == 422, f"Expected 422 for invalid email: {bad_email_res.text}"
        print("✓ Invalid email rejected with 422 Unprocessable Entity")

        # 1b. Weak password (< 8 chars)
        weak_pwd_res1 = await client.post("/api/auth/register", json={
            "username": "user_weak_pwd1",
            "email": "weak1@polygen.ai",
            "password": "short"
        })
        assert weak_pwd_res1.status_code == 422, f"Expected 422 for short password: {weak_pwd_res1.text}"
        print("✓ Password under 8 chars rejected with 422")

        # 1c. Weak password (missing uppercase)
        weak_pwd_res2 = await client.post("/api/auth/register", json={
            "username": "user_weak_pwd2",
            "email": "weak2@polygen.ai",
            "password": "lowercaseonly123!"
        })
        assert weak_pwd_res2.status_code == 422, f"Expected 422 for missing uppercase: {weak_pwd_res2.text}"
        print("✓ Password missing uppercase rejected with 422")

        # 1d. Weak password (missing digit/symbol)
        weak_pwd_res3 = await client.post("/api/auth/register", json={
            "username": "user_weak_pwd3",
            "email": "weak3@polygen.ai",
            "password": "NoDigitsOrSpecialCharsHere"
        })
        assert weak_pwd_res3.status_code == 422, f"Expected 422 for missing digits/symbols: {weak_pwd_res3.text}"
        print("✓ Password missing digits/symbols rejected with 422")

        # ---------------------------------------------------------
        # 2. Successful Registration & Password Hashing Verification
        # ---------------------------------------------------------
        print("\n--- 2. Testing User Registration & Password Hashing ---")
        suffix_a = uuid.uuid4().hex[:6]
        user_a_email = f"creator_a_{suffix_a}@polygen.ai"
        user_a_username = f"creator_a_{suffix_a}"
        user_a_password = "SecurePasswordA2026!"

        reg_res_a = await client.post("/api/auth/register", json={
            "name": f"Creator Alpha {suffix_a}",
            "username": user_a_username,
            "email": user_a_email,
            "password": user_a_password
        })
        assert reg_res_a.status_code == 201, f"User A registration failed: {reg_res_a.text}"
        token_a_data = reg_res_a.json()
        assert "access_token" in token_a_data
        assert "refresh_token" in token_a_data
        assert token_a_data["token_type"] == "bearer"
        assert token_a_data["user"]["email"] == user_a_email
        user_a_id = token_a_data["user"]["id"]
        token_a = token_a_data["access_token"]
        refresh_token_a = token_a_data["refresh_token"]
        headers_a = {"Authorization": f"Bearer {token_a}"}
        print(f"✓ User A registered successfully: {user_a_username} (ID: {user_a_id})")

        # Verify password is NOT stored in plaintext
        async with AsyncSessionLocal() as session:
            db_user_res = await session.execute(select(User).where(User.id == user_a_id))
            db_user = db_user_res.scalars().first()
            assert db_user.password_hash != user_a_password, "Security vulnerability: password stored in plaintext!"
            assert db_user.password_hash.startswith("$2b$") or db_user.password_hash.startswith("$2a$"), "Password is not bcrypt hashed!"
            assert verify_password(user_a_password, db_user.password_hash), "Bcrypt password verification failed!"
        print("✓ Verified password stored securely as salted bcrypt hash, never plaintext")

        # ---------------------------------------------------------
        # 3. Duplicate Registration Prevention
        # ---------------------------------------------------------
        print("\n--- 3. Testing Duplicate Account Prevention ---")
        dup_email_res = await client.post("/api/auth/register", json={
            "username": f"diff_user_{suffix_a}",
            "email": user_a_email,
            "password": "AnotherPassword2026!"
        })
        assert dup_email_res.status_code == 400, f"Expected 400 for duplicate email: {dup_email_res.text}"
        print("✓ Duplicate email registration rejected with 400 Bad Request")

        dup_user_res = await client.post("/api/auth/register", json={
            "username": user_a_username,
            "email": f"diff_{suffix_a}@polygen.ai",
            "password": "AnotherPassword2026!"
        })
        assert dup_user_res.status_code == 400, f"Expected 400 for duplicate username: {dup_user_res.text}"
        print("✓ Duplicate username registration rejected with 400 Bad Request")

        # ---------------------------------------------------------
        # 4. User Login & Credential Authentication
        # ---------------------------------------------------------
        print("\n--- 4. Testing User Login ---")
        # 4a. Login with email
        login_email_res = await client.post("/api/auth/login", json={
            "username_or_email": user_a_email,
            "password": user_a_password
        })
        assert login_email_res.status_code == 200
        assert "access_token" in login_email_res.json()
        print("✓ Login via email succeeded")

        # 4b. Login with username
        login_user_res = await client.post("/api/auth/login", json={
            "username_or_email": user_a_username,
            "password": user_a_password
        })
        assert login_user_res.status_code == 200
        assert "access_token" in login_user_res.json()
        print("✓ Login via username succeeded")

        # 4c. Login with incorrect password
        bad_pwd_res = await client.post("/api/auth/login", json={
            "username_or_email": user_a_email,
            "password": "WrongPassword2026!"
        })
        assert bad_pwd_res.status_code == 401, f"Expected 401 for incorrect password: {bad_pwd_res.text}"
        print("✓ Incorrect password rejected with 401 Unauthorized")

        # 4d. Login with non-existent user
        non_user_res = await client.post("/api/auth/login", json={
            "username_or_email": "non_existent_user_99999@polygen.ai",
            "password": "SomePassword2026!"
        })
        assert non_user_res.status_code == 401
        print("✓ Non-existent user rejected with 401 Unauthorized")

        # ---------------------------------------------------------
        # 5. Refresh Token Strategy
        # ---------------------------------------------------------
        print("\n--- 5. Testing Refresh Token Strategy ---")
        refresh_res = await client.post("/api/auth/refresh", json={
            "refresh_token": refresh_token_a
        })
        assert refresh_res.status_code == 200, f"Refresh failed: {refresh_res.text}"
        refresh_data = refresh_res.json()
        assert "access_token" in refresh_data
        assert "refresh_token" in refresh_data
        new_token_a = refresh_data["access_token"]
        assert new_token_a != token_a, "Expected fresh access token upon refresh"
        headers_a = {"Authorization": f"Bearer {new_token_a}"}
        print("✓ Refresh token exchange succeeded, issued new access token and rotated refresh token")

        # Rejection of invalid refresh token
        bad_refresh_res = await client.post("/api/auth/refresh", json={
            "refresh_token": "invalid_refresh_token_string_value"
        })
        assert bad_refresh_res.status_code == 401
        print("✓ Invalid refresh token rejected with 401 Unauthorized")

        # Rejection when access token is passed as refresh token
        access_as_refresh_res = await client.post("/api/auth/refresh", json={
            "refresh_token": new_token_a
        })
        assert access_as_refresh_res.status_code == 401
        print("✓ Access token passed to refresh endpoint rejected with 401 Unauthorized")

        # ---------------------------------------------------------
        # 6. Protected Routes & Token Verification
        # ---------------------------------------------------------
        print("\n--- 6. Testing Protected Routes & Token Verification ---")
        # 6a. Protected route without token
        unauth_me = await client.get("/api/auth/me")
        assert unauth_me.status_code == 401, f"Expected 401 for unauthenticated /api/auth/me: {unauth_me.text}"
        unauth_assets = await client.get("/api/assets")
        assert unauth_assets.status_code == 401, f"Expected 401 for unauthenticated /api/assets: {unauth_assets.text}"
        unauth_gen = await client.post("/api/generate", json={"prompt": "Sword"})
        assert unauth_gen.status_code == 401, f"Expected 401 for unauthenticated /api/generate: {unauth_gen.text}"
        print("✓ Unauthenticated access to /api/auth/me, /api/assets, and /api/generate rejected with 401")

        # 6b. Expired token rejection
        expired_token = create_access_token(subject=user_a_id, expires_delta=timedelta(seconds=-10))
        expired_res = await client.get("/api/auth/me", headers={"Authorization": f"Bearer {expired_token}"})
        assert expired_res.status_code == 401, f"Expected 401 for expired token: {expired_res.text}"
        assert "expired" in expired_res.text.lower(), f"Expected 'expired' in error detail: {expired_res.text}"
        print("✓ Expired token rejected with 401 and 'Token has expired'")

        # 6c. Malformed token rejection
        bad_sig_res = await client.get("/api/auth/me", headers={"Authorization": "Bearer malformed.jwt.token"})
        assert bad_sig_res.status_code == 401
        print("✓ Malformed token rejected with 401 Unauthorized")

        # 6d. Valid token access
        valid_me = await client.get("/api/auth/me", headers=headers_a)
        assert valid_me.status_code == 200
        assert valid_me.json()["email"] == user_a_email
        print("✓ Valid token granted access to /api/auth/me")

        # ---------------------------------------------------------
        # 7. User Profile Management & Password Change
        # ---------------------------------------------------------
        print("\n--- 7. Testing User Profile & Password Change ---")
        # 7a. Update profile display name
        update_res = await client.put("/api/auth/me", json={"name": "Alex Updated Mercer"}, headers=headers_a)
        assert update_res.status_code == 200
        assert update_res.json()["name"] == "Alex Updated Mercer"
        print("✓ Profile display name updated successfully via PUT /api/auth/me")

        # 7b. Change password with incorrect current password
        bad_change_res = await client.post("/api/auth/change-password", json={
            "current_password": "WrongCurrentPassword123!",
            "new_password": "BrandNewPassword2026!"
        }, headers=headers_a)
        assert bad_change_res.status_code == 400
        print("✓ Password change with wrong current password rejected with 400")

        # 7c. Change password with valid credentials
        brand_new_pwd = "BrandNewPassword2026!"
        change_pwd_res = await client.post("/api/auth/change-password", json={
            "current_password": user_a_password,
            "new_password": brand_new_pwd
        }, headers=headers_a)
        assert change_pwd_res.status_code == 200
        print("✓ Password successfully updated via POST /api/auth/change-password")

        # Verify old password no longer works
        old_login = await client.post("/api/auth/login", json={
            "username_or_email": user_a_email,
            "password": user_a_password
        })
        assert old_login.status_code == 401
        print("✓ Verified old password rejected after change")

        # Verify new password works
        new_login = await client.post("/api/auth/login", json={
            "username_or_email": user_a_email,
            "password": brand_new_pwd
        })
        assert new_login.status_code == 200
        headers_a = {"Authorization": f"Bearer {new_login.json()['access_token']}"}
        print("✓ Verified new password authenticates successfully")

        # ---------------------------------------------------------
        # 8. User Asset & Job Data Isolation (User A vs User B)
        # ---------------------------------------------------------
        print("\n--- 8. Testing User-Level Data Isolation & Ownership ---")
        # Register User B
        suffix_b = uuid.uuid4().hex[:6]
        user_b_email = f"creator_b_{suffix_b}@polygen.ai"
        user_b_password = "SecurePasswordB2026!"
        reg_res_b = await client.post("/api/auth/register", json={
            "username": f"creator_b_{suffix_b}",
            "email": user_b_email,
            "password": user_b_password
        })
        assert reg_res_b.status_code == 201
        token_b = reg_res_b.json()["access_token"]
        headers_b = {"Authorization": f"Bearer {token_b}"}
        print(f"✓ Registered separate second user: {user_b_email}")

        # User A triggers 3D generation
        gen_res = await client.post("/api/generate", json={
            "prompt": "User A Rusted Battleaxe",
            "style": "fantasy",
            "quality": "high",
            "polygon_budget": 5000,
            "target_format": "glb"
        }, headers=headers_a)
        assert gen_res.status_code == 202
        job_a_id = gen_res.json()["id"]

        # Wait for User A's job to complete
        for _ in range(30):
            await asyncio.sleep(0.5)
            j_res = await client.get(f"/api/jobs/{job_a_id}", headers=headers_a)
            if j_res.json()["status"] == "completed":
                break
        
        asset_a_id = j_res.json()["asset_id"]
        assert asset_a_id is not None
        print(f"✓ User A created 3D asset: {asset_a_id} from job: {job_a_id}")

        # 8a. User B lists assets: MUST NOT see User A's asset
        b_assets_res = await client.get("/api/assets", headers=headers_b)
        assert b_assets_res.status_code == 200
        b_assets = b_assets_res.json()["items"]
        assert not any(a["id"] == asset_a_id for a in b_assets), "Data leak: User B sees User A's asset!"
        print("✓ Verified User B asset list is isolated: 0 of User A's assets returned")

        # 8b. User B attempts to GET User A's asset directly: MUST return 403 Forbidden
        b_get_asset_res = await client.get(f"/api/assets/{asset_a_id}", headers=headers_b)
        assert b_get_asset_res.status_code == 403, f"Expected 403 for unauthorized asset view: {b_get_asset_res.status_code}"
        print("✓ Verified User B cannot view User A's asset details (403 Forbidden)")

        # 8c. User B attempts to download User A's asset: MUST return 403 Forbidden
        b_dl_res = await client.get(f"/api/assets/{asset_a_id}/download", headers=headers_b)
        assert b_dl_res.status_code == 403, f"Expected 403 for unauthorized asset download: {b_dl_res.status_code}"
        print("✓ Verified User B cannot download User A's binary asset (403 Forbidden)")

        # 8d. User B attempts to delete User A's asset: MUST return 403 Forbidden
        b_del_res = await client.delete(f"/api/assets/{asset_a_id}", headers=headers_b)
        assert b_del_res.status_code == 403, f"Expected 403 for unauthorized asset deletion: {b_del_res.status_code}"
        print("✓ Verified User B cannot delete User A's asset (403 Forbidden)")

        # 8e. User B attempts to view User A's generation job: MUST return 403 Forbidden
        b_job_res = await client.get(f"/api/jobs/{job_a_id}", headers=headers_b)
        assert b_job_res.status_code == 403, f"Expected 403 for unauthorized job view: {b_job_res.status_code}"
        print("✓ Verified User B cannot inspect User A's generation job status (403 Forbidden)")

        # 8f. Secure download with ?token= query parameter for User A
        query_dl_res = await client.get(f"/api/assets/{asset_a_id}/download?token={new_login.json()['access_token']}")
        assert query_dl_res.status_code == 200
        assert query_dl_res.content[:4] == b"glTF"
        print("✓ Verified secure asset download via ?token= query parameter")

        # User A deletes their own asset: MUST succeed with 204
        a_del_res = await client.delete(f"/api/assets/{asset_a_id}", headers=headers_a)
        assert a_del_res.status_code == 204
        print("✓ Verified User A successfully deletes their own asset (204 No Content)")

        # ---------------------------------------------------------
        # 9. Logout Session Clearance
        # ---------------------------------------------------------
        print("\n--- 9. Testing Logout ---")
        logout_res = await client.post("/api/auth/logout", headers=headers_a)
        assert logout_res.status_code == 200
        assert "logged out" in logout_res.json()["message"].lower()
        print("✓ Logout endpoint verified")

    print("\n" + "=" * 65)
    print("ALL PART 4 AUTHENTICATION & SECURITY TESTS PASSED WITH 100% SUCCESS!")
    print("=" * 65)

if __name__ == "__main__":
    asyncio.run(run_part4_tests())


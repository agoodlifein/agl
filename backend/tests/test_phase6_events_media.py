"""
Phase 6 Backend Tests: Events & Media
Tests for Event CRUD, Media Upload, RBAC, and Auth endpoints
"""
import pytest
import requests
import os
import io
from datetime import date, timedelta
from PIL import Image

# Base URL from environment
BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
SUPER_ADMIN_EMAIL = "admin@agoodlife.com"
SUPER_ADMIN_PASSWORD = "Admin@123"
TEST_COMMUNITY_SLUG = "event-test"


# ============ FIXTURES ============

@pytest.fixture(scope="module")
def api_client():
    """Shared requests session"""
    session = requests.Session()
    session.headers.update({"Content-Type": "application/json"})
    return session


@pytest.fixture(scope="module")
def admin_token(api_client):
    """Get super admin JWT token"""
    response = api_client.post(
        f"{BASE_URL}/api/auth/login",
        json={"email": SUPER_ADMIN_EMAIL, "password": SUPER_ADMIN_PASSWORD}
    )
    assert response.status_code == 200, f"Admin login failed: {response.text}"
    data = response.json()
    assert "token" in data, "No token in login response"
    return data["token"]


@pytest.fixture(scope="module")
def admin_user_id(api_client, admin_token):
    """Get admin user ID"""
    response = api_client.get(
        f"{BASE_URL}/api/auth/me",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 200
    return response.json()["user_id"]


@pytest.fixture(scope="module")
def test_member_credentials():
    """Generate unique test member credentials"""
    import uuid
    unique_id = uuid.uuid4().hex[:8]
    return {
        "email": f"TEST_member_{unique_id}@example.com",
        "name": f"Test Member {unique_id}",
        "password": "TestPass123!"
    }


@pytest.fixture(scope="module")
def member_token(api_client, test_member_credentials):
    """Register and get token for a regular member (non-manager)"""
    response = api_client.post(
        f"{BASE_URL}/api/auth/register",
        json=test_member_credentials
    )
    assert response.status_code == 200, f"Member registration failed: {response.text}"
    data = response.json()
    assert "token" in data
    return data["token"]


def create_test_image(width=100, height=100, format='JPEG'):
    """Create a test image in memory"""
    img = Image.new('RGB', (width, height), color='red')
    img_bytes = io.BytesIO()
    img.save(img_bytes, format=format)
    img_bytes.seek(0)
    return img_bytes


# ============ AUTH ENDPOINT TESTS ============

class TestAuthEndpoints:
    """Authentication endpoint tests"""
    
    def test_login_success(self, api_client):
        """Test successful login with valid credentials"""
        response = api_client.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": SUPER_ADMIN_EMAIL, "password": SUPER_ADMIN_PASSWORD}
        )
        assert response.status_code == 200
        data = response.json()
        assert "token" in data
        assert "user" in data
        assert data["user"]["email"] == SUPER_ADMIN_EMAIL
        assert data["user"]["is_super_admin"] == True
        print("✓ Login success test passed")
    
    def test_login_invalid_credentials(self, api_client):
        """Test login with invalid credentials"""
        response = api_client.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": "wrong@example.com", "password": "wrongpass"}
        )
        assert response.status_code == 401
        print("✓ Login invalid credentials test passed")
    
    def test_register_new_user(self, api_client):
        """Test user registration"""
        import uuid
        unique_email = f"TEST_register_{uuid.uuid4().hex[:8]}@example.com"
        response = api_client.post(
            f"{BASE_URL}/api/auth/register",
            json={
                "email": unique_email,
                "name": "Test Register User",
                "password": "TestPass123!"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert "token" in data
        assert data["user"]["email"] == unique_email
        print("✓ Register new user test passed")
    
    def test_register_duplicate_email(self, api_client):
        """Test registration with existing email"""
        response = api_client.post(
            f"{BASE_URL}/api/auth/register",
            json={
                "email": SUPER_ADMIN_EMAIL,
                "name": "Duplicate User",
                "password": "TestPass123!"
            }
        )
        assert response.status_code == 400
        assert "already registered" in response.json().get("detail", "").lower()
        print("✓ Register duplicate email test passed")
    
    def test_get_me_with_jwt(self, api_client, admin_token):
        """Test /auth/me with JWT token"""
        response = api_client.get(
            f"{BASE_URL}/api/auth/me",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == SUPER_ADMIN_EMAIL
        assert "user_id" in data
        print("✓ Get me with JWT test passed")
    
    def test_get_me_without_auth(self, api_client):
        """Test /auth/me without authentication"""
        response = api_client.get(f"{BASE_URL}/api/auth/me")
        assert response.status_code == 401
        print("✓ Get me without auth test passed")
    
    def test_session_exchange_invalid(self, api_client):
        """Test session exchange with invalid session_id"""
        response = api_client.post(
            f"{BASE_URL}/api/auth/session?session_id=fake_session_123"
        )
        assert response.status_code == 401
        print("✓ Session exchange invalid test passed")
    
    def test_logout(self, api_client, admin_token):
        """Test logout endpoint"""
        response = api_client.post(
            f"{BASE_URL}/api/auth/logout",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        assert "logged out" in response.json().get("message", "").lower()
        print("✓ Logout test passed")


# ============ EVENT CRUD TESTS ============

class TestEventCRUD:
    """Event CRUD operation tests"""
    
    @pytest.fixture(autouse=True)
    def setup(self, api_client, admin_token):
        """Setup for each test"""
        self.client = api_client
        self.token = admin_token
        self.headers = {"Authorization": f"Bearer {admin_token}"}
    
    def test_create_event_success(self):
        """Test creating an event as super admin"""
        future_date = (date.today() + timedelta(days=30)).isoformat()
        event_data = {
            "title": "TEST_Event Creation Test",
            "description": "This is a test event description for testing purposes",
            "event_date": future_date,
            "venue": "Test Venue",
            "status": "published"
        }
        
        response = self.client.post(
            f"{BASE_URL}/api/manager/communities/{TEST_COMMUNITY_SLUG}/events",
            json=event_data,
            headers=self.headers
        )
        
        assert response.status_code == 200, f"Create event failed: {response.text}"
        data = response.json()
        assert data["title"] == event_data["title"]
        assert data["description"] == event_data["description"]
        assert data["status"] == "published"
        assert "event_id" in data
        print(f"✓ Create event success test passed - event_id: {data['event_id']}")
        return data["event_id"]
    
    def test_create_event_draft_status(self):
        """Test creating a draft event"""
        future_date = (date.today() + timedelta(days=45)).isoformat()
        event_data = {
            "title": "TEST_Draft Event",
            "description": "This is a draft event for testing",
            "event_date": future_date,
            "status": "draft"
        }
        
        response = self.client.post(
            f"{BASE_URL}/api/manager/communities/{TEST_COMMUNITY_SLUG}/events",
            json=event_data,
            headers=self.headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "draft"
        print("✓ Create draft event test passed")
    
    def test_create_event_validation_title_too_short(self):
        """Test event creation with title too short (< 5 chars)"""
        future_date = (date.today() + timedelta(days=30)).isoformat()
        event_data = {
            "title": "Hi",  # Too short
            "description": "Valid description for testing",
            "event_date": future_date
        }
        
        response = self.client.post(
            f"{BASE_URL}/api/manager/communities/{TEST_COMMUNITY_SLUG}/events",
            json=event_data,
            headers=self.headers
        )
        
        assert response.status_code == 422
        print("✓ Title too short validation test passed")
    
    def test_create_event_validation_description_too_short(self):
        """Test event creation with description too short (< 10 chars)"""
        future_date = (date.today() + timedelta(days=30)).isoformat()
        event_data = {
            "title": "Valid Title Here",
            "description": "Short",  # Too short
            "event_date": future_date
        }
        
        response = self.client.post(
            f"{BASE_URL}/api/manager/communities/{TEST_COMMUNITY_SLUG}/events",
            json=event_data,
            headers=self.headers
        )
        
        assert response.status_code == 422
        print("✓ Description too short validation test passed")
    
    def test_create_event_validation_past_date(self):
        """Test event creation with past date"""
        past_date = (date.today() - timedelta(days=1)).isoformat()
        event_data = {
            "title": "Past Event Test",
            "description": "This event has a past date",
            "event_date": past_date
        }
        
        response = self.client.post(
            f"{BASE_URL}/api/manager/communities/{TEST_COMMUNITY_SLUG}/events",
            json=event_data,
            headers=self.headers
        )
        
        assert response.status_code == 422
        print("✓ Past date validation test passed")
    
    def test_create_event_validation_invalid_status(self):
        """Test event creation with invalid status"""
        future_date = (date.today() + timedelta(days=30)).isoformat()
        event_data = {
            "title": "Invalid Status Event",
            "description": "This event has an invalid status",
            "event_date": future_date,
            "status": "invalid_status"
        }
        
        response = self.client.post(
            f"{BASE_URL}/api/manager/communities/{TEST_COMMUNITY_SLUG}/events",
            json=event_data,
            headers=self.headers
        )
        
        assert response.status_code == 422
        print("✓ Invalid status validation test passed")
    
    def test_list_manager_events(self):
        """Test listing all events (including drafts) as manager"""
        response = self.client.get(
            f"{BASE_URL}/api/manager/communities/{TEST_COMMUNITY_SLUG}/events",
            headers=self.headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ List manager events test passed - found {len(data)} events")
    
    def test_list_public_events(self):
        """Test listing published events (public endpoint)"""
        response = self.client.get(
            f"{BASE_URL}/api/communities/{TEST_COMMUNITY_SLUG}/events",
            headers=self.headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        # All returned events should be published
        for event in data:
            assert event["status"] == "published"
        print(f"✓ List public events test passed - found {len(data)} published events")
    
    def test_update_event(self):
        """Test updating an event"""
        # First create an event
        future_date = (date.today() + timedelta(days=60)).isoformat()
        create_response = self.client.post(
            f"{BASE_URL}/api/manager/communities/{TEST_COMMUNITY_SLUG}/events",
            json={
                "title": "TEST_Event to Update",
                "description": "Original description for update test",
                "event_date": future_date
            },
            headers=self.headers
        )
        assert create_response.status_code == 200
        event_id = create_response.json()["event_id"]
        
        # Update the event
        update_response = self.client.patch(
            f"{BASE_URL}/api/manager/communities/{TEST_COMMUNITY_SLUG}/events/{event_id}",
            json={
                "title": "TEST_Updated Event Title",
                "status": "cancelled"
            },
            headers=self.headers
        )
        
        assert update_response.status_code == 200
        updated_data = update_response.json()
        assert updated_data["title"] == "TEST_Updated Event Title"
        assert updated_data["status"] == "cancelled"
        
        # Verify with GET
        get_response = self.client.get(
            f"{BASE_URL}/api/communities/{TEST_COMMUNITY_SLUG}/events/{event_id}",
            headers=self.headers
        )
        assert get_response.status_code == 200
        assert get_response.json()["title"] == "TEST_Updated Event Title"
        print("✓ Update event test passed")
    
    def test_delete_event(self):
        """Test deleting an event"""
        # First create an event
        future_date = (date.today() + timedelta(days=90)).isoformat()
        create_response = self.client.post(
            f"{BASE_URL}/api/manager/communities/{TEST_COMMUNITY_SLUG}/events",
            json={
                "title": "TEST_Event to Delete",
                "description": "This event will be deleted",
                "event_date": future_date
            },
            headers=self.headers
        )
        assert create_response.status_code == 200
        event_id = create_response.json()["event_id"]
        
        # Delete the event
        delete_response = self.client.delete(
            f"{BASE_URL}/api/manager/communities/{TEST_COMMUNITY_SLUG}/events/{event_id}",
            headers=self.headers
        )
        
        assert delete_response.status_code == 200
        assert "deleted" in delete_response.json().get("message", "").lower()
        
        # Verify event is gone
        get_response = self.client.get(
            f"{BASE_URL}/api/communities/{TEST_COMMUNITY_SLUG}/events/{event_id}",
            headers=self.headers
        )
        assert get_response.status_code == 404
        print("✓ Delete event test passed")
    
    def test_get_nonexistent_event(self):
        """Test getting a non-existent event"""
        response = self.client.get(
            f"{BASE_URL}/api/communities/{TEST_COMMUNITY_SLUG}/events/nonexistent_event_id",
            headers=self.headers
        )
        assert response.status_code == 404
        print("✓ Get nonexistent event test passed")


# ============ MEDIA UPLOAD TESTS ============

class TestMediaUpload:
    """Media upload and management tests"""
    
    @pytest.fixture(autouse=True)
    def setup(self, api_client, admin_token):
        """Setup for each test"""
        self.client = api_client
        self.token = admin_token
        self.headers = {"Authorization": f"Bearer {admin_token}"}
        
        # Create a test event for media uploads
        future_date = (date.today() + timedelta(days=120)).isoformat()
        response = self.client.post(
            f"{BASE_URL}/api/manager/communities/{TEST_COMMUNITY_SLUG}/events",
            json={
                "title": "TEST_Media Upload Event",
                "description": "Event for testing media uploads",
                "event_date": future_date
            },
            headers=self.headers
        )
        assert response.status_code == 200
        self.event_id = response.json()["event_id"]
    
    def test_upload_jpeg_image(self):
        """Test uploading a JPEG image"""
        img_bytes = create_test_image(format='JPEG')
        
        # Note: Don't include Content-Type header when uploading files
        response = requests.post(
            f"{BASE_URL}/api/manager/communities/{TEST_COMMUNITY_SLUG}/events/{self.event_id}/upload-media",
            files={"file": ("test_image.jpg", img_bytes, "image/jpeg")},
            headers={"Authorization": f"Bearer {self.token}"}
        )
        
        assert response.status_code == 200, f"Upload failed: {response.text}"
        data = response.json()
        assert "media_id" in data
        assert "url" in data
        assert data["file_type"] == "image/jpeg"
        print(f"✓ Upload JPEG test passed - media_id: {data['media_id']}")
        return data
    
    def test_upload_png_image(self):
        """Test uploading a PNG image"""
        img_bytes = create_test_image(format='PNG')
        
        response = requests.post(
            f"{BASE_URL}/api/manager/communities/{TEST_COMMUNITY_SLUG}/events/{self.event_id}/upload-media",
            files={"file": ("test_image.png", img_bytes, "image/png")},
            headers={"Authorization": f"Bearer {self.token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["file_type"] == "image/png"
        print("✓ Upload PNG test passed")
    
    def test_upload_invalid_file_type(self):
        """Test uploading an invalid file type"""
        response = requests.post(
            f"{BASE_URL}/api/manager/communities/{TEST_COMMUNITY_SLUG}/events/{self.event_id}/upload-media",
            files={"file": ("test.txt", b"This is not an image", "text/plain")},
            headers={"Authorization": f"Bearer {self.token}"}
        )
        
        assert response.status_code == 400
        assert "invalid file type" in response.json().get("detail", "").lower()
        print("✓ Invalid file type test passed")
    
    def test_upload_file_too_large(self):
        """Test uploading a file larger than 5MB"""
        # Create a large image (> 5MB)
        large_img = Image.new('RGB', (3000, 3000), color='blue')
        img_bytes = io.BytesIO()
        large_img.save(img_bytes, format='JPEG', quality=100)
        img_bytes.seek(0)
        
        # Check if it's actually > 5MB, if not, pad it
        content = img_bytes.read()
        if len(content) < 5 * 1024 * 1024:
            content = content + b'\x00' * (5 * 1024 * 1024 - len(content) + 1)
        
        response = requests.post(
            f"{BASE_URL}/api/manager/communities/{TEST_COMMUNITY_SLUG}/events/{self.event_id}/upload-media",
            files={"file": ("large_image.jpg", io.BytesIO(content), "image/jpeg")},
            headers={"Authorization": f"Bearer {self.token}"}
        )
        
        assert response.status_code == 400
        assert "too large" in response.json().get("detail", "").lower()
        print("✓ File too large test passed")
    
    def test_media_served_via_static_files(self):
        """Test that uploaded media is served via static files endpoint"""
        # Upload an image first
        img_bytes = create_test_image(format='JPEG')
        upload_response = requests.post(
            f"{BASE_URL}/api/manager/communities/{TEST_COMMUNITY_SLUG}/events/{self.event_id}/upload-media",
            files={"file": ("test_serve.jpg", img_bytes, "image/jpeg")},
            headers={"Authorization": f"Bearer {self.token}"}
        )
        assert upload_response.status_code == 200
        media_url = upload_response.json()["url"]
        
        # Fetch the media via the static files endpoint
        full_url = f"{BASE_URL}{media_url}"
        get_response = self.client.get(full_url)
        
        assert get_response.status_code == 200
        assert get_response.headers.get("content-type", "").startswith("image/")
        print("✓ Media served via static files test passed")
    
    def test_delete_media(self):
        """Test deleting media from an event"""
        # Upload an image first
        img_bytes = create_test_image(format='JPEG')
        upload_response = requests.post(
            f"{BASE_URL}/api/manager/communities/{TEST_COMMUNITY_SLUG}/events/{self.event_id}/upload-media",
            files={"file": ("test_delete.jpg", img_bytes, "image/jpeg")},
            headers={"Authorization": f"Bearer {self.token}"}
        )
        assert upload_response.status_code == 200
        media_id = upload_response.json()["media_id"]
        
        # Delete the media
        delete_response = self.client.delete(
            f"{BASE_URL}/api/manager/communities/{TEST_COMMUNITY_SLUG}/events/{self.event_id}/media/{media_id}",
            headers=self.headers
        )
        
        assert delete_response.status_code == 200
        assert "deleted" in delete_response.json().get("message", "").lower()
        print("✓ Delete media test passed")
    
    def test_event_media_count_in_response(self):
        """Test that event response includes media count and URLs"""
        # Upload multiple images
        for i in range(2):
            img_bytes = create_test_image(format='JPEG')
            requests.post(
                f"{BASE_URL}/api/manager/communities/{TEST_COMMUNITY_SLUG}/events/{self.event_id}/upload-media",
                files={"file": (f"test_{i}.jpg", img_bytes, "image/jpeg")},
                headers={"Authorization": f"Bearer {self.token}"}
            )
        
        # Get event and check media info
        response = self.client.get(
            f"{BASE_URL}/api/communities/{TEST_COMMUNITY_SLUG}/events/{self.event_id}",
            headers=self.headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "media_count" in data
        assert "media_urls" in data
        assert data["media_count"] >= 2
        assert len(data["media_urls"]) >= 2
        print(f"✓ Event media count test passed - media_count: {data['media_count']}")


# ============ RBAC TESTS ============

class TestRBAC:
    """Role-based access control tests"""
    
    def test_regular_member_cannot_create_event(self, api_client, member_token):
        """Test that regular members cannot create events"""
        future_date = (date.today() + timedelta(days=30)).isoformat()
        response = api_client.post(
            f"{BASE_URL}/api/manager/communities/{TEST_COMMUNITY_SLUG}/events",
            json={
                "title": "Unauthorized Event",
                "description": "This should not be created",
                "event_date": future_date
            },
            headers={"Authorization": f"Bearer {member_token}"}
        )
        
        assert response.status_code == 403
        print("✓ Regular member cannot create event test passed")
    
    def test_regular_member_cannot_update_event(self, api_client, admin_token, member_token):
        """Test that regular members cannot update events"""
        # First create an event as admin
        future_date = (date.today() + timedelta(days=30)).isoformat()
        create_response = api_client.post(
            f"{BASE_URL}/api/manager/communities/{TEST_COMMUNITY_SLUG}/events",
            json={
                "title": "TEST_RBAC Update Test Event",
                "description": "Event for RBAC update testing",
                "event_date": future_date
            },
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert create_response.status_code == 200
        event_id = create_response.json()["event_id"]
        
        # Try to update as regular member
        update_response = api_client.patch(
            f"{BASE_URL}/api/manager/communities/{TEST_COMMUNITY_SLUG}/events/{event_id}",
            json={"title": "Unauthorized Update"},
            headers={"Authorization": f"Bearer {member_token}"}
        )
        
        assert update_response.status_code == 403
        print("✓ Regular member cannot update event test passed")
    
    def test_regular_member_cannot_delete_event(self, api_client, admin_token, member_token):
        """Test that regular members cannot delete events"""
        # First create an event as admin
        future_date = (date.today() + timedelta(days=30)).isoformat()
        create_response = api_client.post(
            f"{BASE_URL}/api/manager/communities/{TEST_COMMUNITY_SLUG}/events",
            json={
                "title": "TEST_RBAC Delete Test Event",
                "description": "Event for RBAC delete testing",
                "event_date": future_date
            },
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert create_response.status_code == 200
        event_id = create_response.json()["event_id"]
        
        # Try to delete as regular member
        delete_response = api_client.delete(
            f"{BASE_URL}/api/manager/communities/{TEST_COMMUNITY_SLUG}/events/{event_id}",
            headers={"Authorization": f"Bearer {member_token}"}
        )
        
        assert delete_response.status_code == 403
        print("✓ Regular member cannot delete event test passed")
    
    def test_regular_member_cannot_upload_media(self, api_client, admin_token, member_token):
        """Test that regular members cannot upload media"""
        # First create an event as admin
        future_date = (date.today() + timedelta(days=30)).isoformat()
        create_response = api_client.post(
            f"{BASE_URL}/api/manager/communities/{TEST_COMMUNITY_SLUG}/events",
            json={
                "title": "TEST_RBAC Media Test Event",
                "description": "Event for RBAC media testing",
                "event_date": future_date
            },
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert create_response.status_code == 200
        event_id = create_response.json()["event_id"]
        
        # Try to upload media as regular member
        img_bytes = create_test_image(format='JPEG')
        upload_response = requests.post(
            f"{BASE_URL}/api/manager/communities/{TEST_COMMUNITY_SLUG}/events/{event_id}/upload-media",
            files={"file": ("test.jpg", img_bytes, "image/jpeg")},
            headers={"Authorization": f"Bearer {member_token}"}
        )
        
        assert upload_response.status_code == 403
        print("✓ Regular member cannot upload media test passed")
    
    def test_super_admin_can_manage_events(self, api_client, admin_token):
        """Test that super admin can manage events in any community"""
        future_date = (date.today() + timedelta(days=30)).isoformat()
        
        # Create
        create_response = api_client.post(
            f"{BASE_URL}/api/manager/communities/{TEST_COMMUNITY_SLUG}/events",
            json={
                "title": "TEST_Super Admin Event",
                "description": "Event created by super admin",
                "event_date": future_date
            },
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert create_response.status_code == 200
        event_id = create_response.json()["event_id"]
        
        # Update
        update_response = api_client.patch(
            f"{BASE_URL}/api/manager/communities/{TEST_COMMUNITY_SLUG}/events/{event_id}",
            json={"title": "TEST_Super Admin Updated Event"},
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert update_response.status_code == 200
        
        # Delete
        delete_response = api_client.delete(
            f"{BASE_URL}/api/manager/communities/{TEST_COMMUNITY_SLUG}/events/{event_id}",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert delete_response.status_code == 200
        
        print("✓ Super admin can manage events test passed")


# ============ COMMUNITY NOT FOUND TESTS ============

class TestCommunityNotFound:
    """Tests for non-existent community handling"""
    
    def test_create_event_nonexistent_community(self, api_client, admin_token):
        """Test creating event in non-existent community"""
        future_date = (date.today() + timedelta(days=30)).isoformat()
        response = api_client.post(
            f"{BASE_URL}/api/manager/communities/nonexistent-community/events",
            json={
                "title": "Test Event",
                "description": "Test description here",
                "event_date": future_date
            },
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 404
        print("✓ Create event in nonexistent community test passed")
    
    def test_list_events_nonexistent_community(self, api_client, admin_token):
        """Test listing events in non-existent community"""
        response = api_client.get(
            f"{BASE_URL}/api/communities/nonexistent-community/events",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 404
        print("✓ List events in nonexistent community test passed")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])

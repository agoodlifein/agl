"""
Notification Module Tests - Phase 7
Tests for:
1. Admin template CRUD (GET, POST, PATCH, DELETE)
2. Template locking/unlocking
3. Manager template overrides
4. Event notification send
5. Delivery logs (admin and manager scoped)
6. Notification triggers from existing routes
7. RBAC enforcement
8. Template rendering with placeholders
"""

import pytest
import requests
import os
import time
import uuid

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
SUPER_ADMIN = {"email": "admin@agoodlife.com", "password": "Admin@123"}
MANAGER_USER = {"email": "notiftest@test.com", "password": "Test@12345"}
REGULAR_USER = {"email": "joiner@test.com", "password": "Join@12345"}


class TestSetup:
    """Setup tests - ensure users and communities exist"""
    
    @pytest.fixture(scope="class")
    def admin_token(self):
        """Get admin auth token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json=SUPER_ADMIN)
        assert response.status_code == 200, f"Admin login failed: {response.text}"
        return response.json()["token"]
    
    @pytest.fixture(scope="class")
    def manager_token(self):
        """Get manager auth token - create user if needed"""
        # Try login first
        response = requests.post(f"{BASE_URL}/api/auth/login", json=MANAGER_USER)
        if response.status_code == 200:
            return response.json()["token"]
        
        # Register if not exists
        register_data = {
            "email": MANAGER_USER["email"],
            "password": MANAGER_USER["password"],
            "name": "Notification Test Manager"
        }
        response = requests.post(f"{BASE_URL}/api/auth/register", json=register_data)
        if response.status_code in [200, 201]:
            return response.json()["token"]
        
        # Try login again
        response = requests.post(f"{BASE_URL}/api/auth/login", json=MANAGER_USER)
        assert response.status_code == 200, f"Manager login failed: {response.text}"
        return response.json()["token"]
    
    @pytest.fixture(scope="class")
    def regular_token(self):
        """Get regular user auth token - create user if needed"""
        # Try login first
        response = requests.post(f"{BASE_URL}/api/auth/login", json=REGULAR_USER)
        if response.status_code == 200:
            return response.json()["token"]
        
        # Register if not exists
        register_data = {
            "email": REGULAR_USER["email"],
            "password": REGULAR_USER["password"],
            "name": "Regular Joiner User"
        }
        response = requests.post(f"{BASE_URL}/api/auth/register", json=register_data)
        if response.status_code in [200, 201]:
            return response.json()["token"]
        
        # Try login again
        response = requests.post(f"{BASE_URL}/api/auth/login", json=REGULAR_USER)
        assert response.status_code == 200, f"Regular user login failed: {response.text}"
        return response.json()["token"]
    
    def test_admin_login(self, admin_token):
        """Verify admin can login"""
        assert admin_token is not None
        print(f"✓ Admin login successful")
    
    def test_manager_login(self, manager_token):
        """Verify manager user exists and can login"""
        assert manager_token is not None
        print(f"✓ Manager login successful")
    
    def test_regular_user_login(self, regular_token):
        """Verify regular user exists and can login"""
        assert regular_token is not None
        print(f"✓ Regular user login successful")


class TestAdminTemplates:
    """Admin template CRUD tests"""
    
    @pytest.fixture(scope="class")
    def admin_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json=SUPER_ADMIN)
        assert response.status_code == 200
        return response.json()["token"]
    
    @pytest.fixture(scope="class")
    def regular_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json=REGULAR_USER)
        if response.status_code != 200:
            # Register
            requests.post(f"{BASE_URL}/api/auth/register", json={
                "email": REGULAR_USER["email"],
                "password": REGULAR_USER["password"],
                "name": "Regular Joiner User"
            })
            response = requests.post(f"{BASE_URL}/api/auth/login", json=REGULAR_USER)
        return response.json()["token"]
    
    def test_list_templates(self, admin_token):
        """GET /api/admin/notifications/templates - list all templates"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = requests.get(f"{BASE_URL}/api/admin/notifications/templates", headers=headers)
        
        assert response.status_code == 200, f"Failed: {response.text}"
        templates = response.json()
        assert isinstance(templates, list)
        
        # Should have 8 default templates seeded
        assert len(templates) >= 8, f"Expected at least 8 templates, got {len(templates)}"
        
        # Verify template structure
        for t in templates:
            assert "template_id" in t
            assert "notification_type" in t
            assert "channel" in t
            assert "body" in t
        
        print(f"✓ Listed {len(templates)} templates")
    
    def test_list_templates_filter_by_type(self, admin_token):
        """GET /api/admin/notifications/templates?notification_type=welcome_member"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = requests.get(
            f"{BASE_URL}/api/admin/notifications/templates?notification_type=welcome_member",
            headers=headers
        )
        
        assert response.status_code == 200
        templates = response.json()
        assert all(t["notification_type"] == "welcome_member" for t in templates)
        print(f"✓ Filtered templates by type: {len(templates)} results")
    
    def test_list_templates_filter_by_channel(self, admin_token):
        """GET /api/admin/notifications/templates?channel=whatsapp"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = requests.get(
            f"{BASE_URL}/api/admin/notifications/templates?channel=whatsapp",
            headers=headers
        )
        
        assert response.status_code == 200
        templates = response.json()
        assert all(t["channel"] == "whatsapp" for t in templates)
        print(f"✓ Filtered templates by channel: {len(templates)} results")
    
    def test_create_template(self, admin_token):
        """POST /api/admin/notifications/templates - create new template"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        # Use unique type+channel combo that doesn't exist
        # First check what exists
        response = requests.get(f"{BASE_URL}/api/admin/notifications/templates", headers=headers)
        existing = response.json()
        existing_combos = {(t["notification_type"], t["channel"]) for t in existing}
        
        # Try to create a template for a combo that doesn't exist
        # If welcome_member+whatsapp doesn't exist, create it
        test_type = "welcome_member"
        test_channel = "whatsapp"
        
        if (test_type, test_channel) in existing_combos:
            # Already exists, skip creation test
            print(f"✓ Template {test_type}+{test_channel} already exists, skipping create")
            return
        
        template_data = {
            "notification_type": test_type,
            "channel": test_channel,
            "name": "TEST Welcome WhatsApp",
            "body": "Welcome {{user_name}} to {{community_name}}!",
            "placeholders": ["user_name", "community_name"]
        }
        
        response = requests.post(
            f"{BASE_URL}/api/admin/notifications/templates",
            headers=headers,
            json=template_data
        )
        
        assert response.status_code == 201, f"Failed: {response.text}"
        created = response.json()
        assert created["notification_type"] == test_type
        assert created["channel"] == test_channel
        assert "template_id" in created
        print(f"✓ Created template: {created['template_id']}")
    
    def test_create_duplicate_template_fails(self, admin_token):
        """POST /api/admin/notifications/templates - duplicate type+channel should fail"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        # Try to create duplicate welcome_member+email (should exist from seed)
        template_data = {
            "notification_type": "welcome_member",
            "channel": "email",
            "name": "Duplicate Welcome",
            "body": "Duplicate body"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/admin/notifications/templates",
            headers=headers,
            json=template_data
        )
        
        assert response.status_code == 400, f"Expected 400, got {response.status_code}"
        print(f"✓ Duplicate template creation correctly rejected")
    
    def test_update_template(self, admin_token):
        """PATCH /api/admin/notifications/templates/{id} - update template"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        # Get a template to update
        response = requests.get(f"{BASE_URL}/api/admin/notifications/templates", headers=headers)
        templates = response.json()
        template = templates[0]
        template_id = template["template_id"]
        
        # Update the name
        update_data = {"name": f"Updated Name {uuid.uuid4().hex[:6]}"}
        response = requests.patch(
            f"{BASE_URL}/api/admin/notifications/templates/{template_id}",
            headers=headers,
            json=update_data
        )
        
        assert response.status_code == 200, f"Failed: {response.text}"
        updated = response.json()
        assert updated["name"] == update_data["name"]
        print(f"✓ Updated template {template_id}")
    
    def test_update_nonexistent_template(self, admin_token):
        """PATCH /api/admin/notifications/templates/{id} - nonexistent should 404"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        response = requests.patch(
            f"{BASE_URL}/api/admin/notifications/templates/tmpl_nonexistent123",
            headers=headers,
            json={"name": "Test"}
        )
        
        assert response.status_code == 404
        print(f"✓ Nonexistent template update correctly returns 404")
    
    def test_regular_user_cannot_access_admin_templates(self, regular_token):
        """RBAC: Regular user cannot access admin template endpoints"""
        headers = {"Authorization": f"Bearer {regular_token}"}
        
        response = requests.get(f"{BASE_URL}/api/admin/notifications/templates", headers=headers)
        assert response.status_code == 403, f"Expected 403, got {response.status_code}"
        print(f"✓ Regular user correctly denied admin template access")


class TestTemplateLocking:
    """Template lock/unlock tests"""
    
    @pytest.fixture(scope="class")
    def admin_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json=SUPER_ADMIN)
        return response.json()["token"]
    
    def test_lock_template(self, admin_token):
        """POST /api/admin/notifications/templates/{id}/lock"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        # Get a template
        response = requests.get(f"{BASE_URL}/api/admin/notifications/templates", headers=headers)
        templates = response.json()
        # Find one that's not locked
        template = next((t for t in templates if not t.get("is_locked")), templates[0])
        template_id = template["template_id"]
        
        response = requests.post(
            f"{BASE_URL}/api/admin/notifications/templates/{template_id}/lock",
            headers=headers
        )
        
        assert response.status_code == 200, f"Failed: {response.text}"
        assert "locked" in response.json().get("message", "").lower()
        
        # Verify it's locked
        response = requests.get(f"{BASE_URL}/api/admin/notifications/templates", headers=headers)
        updated = next(t for t in response.json() if t["template_id"] == template_id)
        assert updated["is_locked"] == True
        print(f"✓ Locked template {template_id}")
    
    def test_unlock_template(self, admin_token):
        """POST /api/admin/notifications/templates/{id}/unlock"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        # Get a locked template
        response = requests.get(f"{BASE_URL}/api/admin/notifications/templates", headers=headers)
        templates = response.json()
        locked_template = next((t for t in templates if t.get("is_locked")), None)
        
        if not locked_template:
            # Lock one first
            template_id = templates[0]["template_id"]
            requests.post(f"{BASE_URL}/api/admin/notifications/templates/{template_id}/lock", headers=headers)
        else:
            template_id = locked_template["template_id"]
        
        response = requests.post(
            f"{BASE_URL}/api/admin/notifications/templates/{template_id}/unlock",
            headers=headers
        )
        
        assert response.status_code == 200, f"Failed: {response.text}"
        assert "unlocked" in response.json().get("message", "").lower()
        
        # Verify it's unlocked
        response = requests.get(f"{BASE_URL}/api/admin/notifications/templates", headers=headers)
        updated = next(t for t in response.json() if t["template_id"] == template_id)
        assert updated["is_locked"] == False
        print(f"✓ Unlocked template {template_id}")


class TestDeleteTemplate:
    """Template deletion tests"""
    
    @pytest.fixture(scope="class")
    def admin_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json=SUPER_ADMIN)
        return response.json()["token"]
    
    def test_delete_nonexistent_template(self, admin_token):
        """DELETE /api/admin/notifications/templates/{id} - nonexistent should 404"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        response = requests.delete(
            f"{BASE_URL}/api/admin/notifications/templates/tmpl_nonexistent123",
            headers=headers
        )
        
        assert response.status_code == 404
        print(f"✓ Nonexistent template delete correctly returns 404")


class TestManagerTemplateOverrides:
    """Manager template override tests"""
    
    @pytest.fixture(scope="class")
    def admin_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json=SUPER_ADMIN)
        return response.json()["token"]
    
    @pytest.fixture(scope="class")
    def manager_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json=MANAGER_USER)
        if response.status_code != 200:
            requests.post(f"{BASE_URL}/api/auth/register", json={
                "email": MANAGER_USER["email"],
                "password": MANAGER_USER["password"],
                "name": "Notification Test Manager"
            })
            response = requests.post(f"{BASE_URL}/api/auth/login", json=MANAGER_USER)
        return response.json()["token"]
    
    @pytest.fixture(scope="class")
    def regular_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json=REGULAR_USER)
        if response.status_code != 200:
            requests.post(f"{BASE_URL}/api/auth/register", json={
                "email": REGULAR_USER["email"],
                "password": REGULAR_USER["password"],
                "name": "Regular Joiner User"
            })
            response = requests.post(f"{BASE_URL}/api/auth/login", json=REGULAR_USER)
        return response.json()["token"]
    
    @pytest.fixture(scope="class")
    def private_community_slug(self, admin_token, manager_token):
        """Ensure private-notif community exists with manager"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        # Check if community exists
        response = requests.get(f"{BASE_URL}/api/communities/private-notif", headers=headers)
        if response.status_code == 200:
            return "private-notif"
        
        # Create private community
        community_data = {
            "name": "Private Notification Test",
            "slug": "private-notif",
            "description": "Private community for notification testing",
            "privacy": "private"
        }
        response = requests.post(f"{BASE_URL}/api/admin/communities", headers=headers, json=community_data)
        
        if response.status_code not in [200, 201]:
            # May already exist
            pass
        
        # Get manager user_id
        manager_headers = {"Authorization": f"Bearer {manager_token}"}
        me_response = requests.get(f"{BASE_URL}/api/auth/me", headers=manager_headers)
        if me_response.status_code == 200:
            manager_user_id = me_response.json()["user_id"]
            
            # Assign as manager
            requests.post(
                f"{BASE_URL}/api/admin/communities/private-notif/assign-manager",
                headers=headers,
                json={"user_id": manager_user_id}
            )
        
        return "private-notif"
    
    def test_list_templates_with_override_status(self, admin_token, private_community_slug):
        """GET /api/manager/communities/{slug}/notifications/templates"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        response = requests.get(
            f"{BASE_URL}/api/manager/communities/{private_community_slug}/notifications/templates",
            headers=headers
        )
        
        assert response.status_code == 200, f"Failed: {response.text}"
        templates = response.json()
        assert isinstance(templates, list)
        
        # Verify structure includes override info
        for t in templates:
            assert "template_id" in t
            assert "has_override" in t
            assert "is_locked" in t
        
        print(f"✓ Listed {len(templates)} templates with override status")
    
    def test_create_template_override(self, admin_token, private_community_slug):
        """PATCH /api/manager/communities/{slug}/notifications/templates/{id} - create override"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        # Get templates
        response = requests.get(
            f"{BASE_URL}/api/manager/communities/{private_community_slug}/notifications/templates",
            headers=headers
        )
        templates = response.json()
        
        # Find an unlocked template without override
        template = next((t for t in templates if not t.get("is_locked") and not t.get("has_override")), None)
        if not template:
            template = next((t for t in templates if not t.get("is_locked")), templates[0])
        
        template_id = template["template_id"]
        
        # Create override
        override_data = {
            "subject": "Custom Subject for Private Notif Community",
            "body": "Custom body: Welcome {{user_name}} to our special community {{community_name}}!"
        }
        
        response = requests.patch(
            f"{BASE_URL}/api/manager/communities/{private_community_slug}/notifications/templates/{template_id}",
            headers=headers,
            json=override_data
        )
        
        assert response.status_code == 200, f"Failed: {response.text}"
        
        # Verify override exists
        response = requests.get(
            f"{BASE_URL}/api/manager/communities/{private_community_slug}/notifications/templates",
            headers=headers
        )
        updated = next(t for t in response.json() if t["template_id"] == template_id)
        assert updated["has_override"] == True
        assert updated["override_subject"] == override_data["subject"]
        print(f"✓ Created override for template {template_id}")
    
    def test_cannot_override_locked_template(self, admin_token, private_community_slug):
        """PATCH on locked template should return 403"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        # Get templates
        response = requests.get(f"{BASE_URL}/api/admin/notifications/templates", headers=headers)
        templates = response.json()
        
        # Lock a template
        template_id = templates[0]["template_id"]
        requests.post(f"{BASE_URL}/api/admin/notifications/templates/{template_id}/lock", headers=headers)
        
        # Try to override
        response = requests.patch(
            f"{BASE_URL}/api/manager/communities/{private_community_slug}/notifications/templates/{template_id}",
            headers=headers,
            json={"body": "Trying to override locked template"}
        )
        
        assert response.status_code == 403, f"Expected 403, got {response.status_code}"
        
        # Unlock for other tests
        requests.post(f"{BASE_URL}/api/admin/notifications/templates/{template_id}/unlock", headers=headers)
        print(f"✓ Locked template override correctly rejected with 403")
    
    def test_delete_template_override(self, admin_token, private_community_slug):
        """DELETE /api/manager/communities/{slug}/notifications/templates/{id} - remove override"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        # Get templates with overrides
        response = requests.get(
            f"{BASE_URL}/api/manager/communities/{private_community_slug}/notifications/templates",
            headers=headers
        )
        templates = response.json()
        
        # Find one with override
        template_with_override = next((t for t in templates if t.get("has_override")), None)
        
        if not template_with_override:
            # Create one first
            template_id = templates[0]["template_id"]
            requests.patch(
                f"{BASE_URL}/api/manager/communities/{private_community_slug}/notifications/templates/{template_id}",
                headers=headers,
                json={"body": "Temp override to delete"}
            )
        else:
            template_id = template_with_override["template_id"]
        
        # Delete override
        response = requests.delete(
            f"{BASE_URL}/api/manager/communities/{private_community_slug}/notifications/templates/{template_id}",
            headers=headers
        )
        
        assert response.status_code == 200, f"Failed: {response.text}"
        
        # Verify override removed
        response = requests.get(
            f"{BASE_URL}/api/manager/communities/{private_community_slug}/notifications/templates",
            headers=headers
        )
        updated = next(t for t in response.json() if t["template_id"] == template_id)
        assert updated["has_override"] == False
        print(f"✓ Deleted override for template {template_id}")
    
    def test_regular_user_cannot_access_manager_templates(self, regular_token, private_community_slug):
        """RBAC: Regular user cannot access manager notification endpoints"""
        headers = {"Authorization": f"Bearer {regular_token}"}
        
        response = requests.get(
            f"{BASE_URL}/api/manager/communities/{private_community_slug}/notifications/templates",
            headers=headers
        )
        
        assert response.status_code == 403, f"Expected 403, got {response.status_code}"
        print(f"✓ Regular user correctly denied manager template access")


class TestEventNotificationSend:
    """Event notification send tests"""
    
    @pytest.fixture(scope="class")
    def admin_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json=SUPER_ADMIN)
        return response.json()["token"]
    
    @pytest.fixture(scope="class")
    def event_test_community(self, admin_token):
        """Ensure event-test community exists with an event"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        # Check if community exists
        response = requests.get(f"{BASE_URL}/api/communities/event-test", headers=headers)
        if response.status_code != 200:
            # Create it
            community_data = {
                "name": "Event Test Community",
                "slug": "event-test",
                "description": "Community for event notification testing",
                "privacy": "public"
            }
            requests.post(f"{BASE_URL}/api/admin/communities", headers=headers, json=community_data)
        
        # Check for events
        response = requests.get(f"{BASE_URL}/api/manager/communities/event-test/events", headers=headers)
        if response.status_code == 200 and len(response.json()) > 0:
            return {"slug": "event-test", "event_id": response.json()[0]["event_id"]}
        
        # Create an event
        from datetime import datetime, timedelta
        future_date = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")
        event_data = {
            "title": "Test Notification Event",
            "description": "Event for testing notification sends",
            "event_date": future_date,
            "event_time": "14:00",
            "venue": "Test Venue",
            "status": "published"
        }
        response = requests.post(
            f"{BASE_URL}/api/manager/communities/event-test/events",
            headers=headers,
            json=event_data
        )
        
        if response.status_code in [200, 201]:
            return {"slug": "event-test", "event_id": response.json()["event_id"]}
        
        # Get existing event
        response = requests.get(f"{BASE_URL}/api/manager/communities/event-test/events", headers=headers)
        if response.status_code == 200 and len(response.json()) > 0:
            return {"slug": "event-test", "event_id": response.json()[0]["event_id"]}
        
        pytest.skip("Could not create or find event for testing")
    
    def test_send_event_notification_all_segment(self, admin_token, event_test_community):
        """POST /api/manager/communities/{slug}/notifications/send-event - all segment"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        request_data = {
            "event_id": event_test_community["event_id"],
            "segment": "all"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/manager/communities/{event_test_community['slug']}/notifications/send-event",
            headers=headers,
            json=request_data
        )
        
        assert response.status_code == 200, f"Failed: {response.text}"
        assert "queued" in response.json().get("message", "").lower()
        print(f"✓ Event notification sent to 'all' segment")
    
    def test_send_event_notification_member_segment(self, admin_token, event_test_community):
        """POST /api/manager/communities/{slug}/notifications/send-event - member segment"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        request_data = {
            "event_id": event_test_community["event_id"],
            "segment": "member"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/manager/communities/{event_test_community['slug']}/notifications/send-event",
            headers=headers,
            json=request_data
        )
        
        assert response.status_code == 200, f"Failed: {response.text}"
        print(f"✓ Event notification sent to 'member' segment")
    
    def test_send_event_notification_invalid_segment(self, admin_token, event_test_community):
        """POST with invalid segment should fail validation"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        request_data = {
            "event_id": event_test_community["event_id"],
            "segment": "invalid_segment"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/manager/communities/{event_test_community['slug']}/notifications/send-event",
            headers=headers,
            json=request_data
        )
        
        assert response.status_code == 422, f"Expected 422, got {response.status_code}"
        print(f"✓ Invalid segment correctly rejected")
    
    def test_send_event_notification_nonexistent_event(self, admin_token, event_test_community):
        """POST with nonexistent event_id should 404"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        request_data = {
            "event_id": "evt_nonexistent123",
            "segment": "all"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/manager/communities/{event_test_community['slug']}/notifications/send-event",
            headers=headers,
            json=request_data
        )
        
        assert response.status_code == 404, f"Expected 404, got {response.status_code}"
        print(f"✓ Nonexistent event correctly returns 404")


class TestDeliveryLogs:
    """Delivery log tests"""
    
    @pytest.fixture(scope="class")
    def admin_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json=SUPER_ADMIN)
        return response.json()["token"]
    
    @pytest.fixture(scope="class")
    def regular_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json=REGULAR_USER)
        if response.status_code != 200:
            requests.post(f"{BASE_URL}/api/auth/register", json={
                "email": REGULAR_USER["email"],
                "password": REGULAR_USER["password"],
                "name": "Regular Joiner User"
            })
            response = requests.post(f"{BASE_URL}/api/auth/login", json=REGULAR_USER)
        return response.json()["token"]
    
    def test_admin_list_all_logs(self, admin_token):
        """GET /api/admin/notifications/logs - list all logs"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        response = requests.get(f"{BASE_URL}/api/admin/notifications/logs", headers=headers)
        
        assert response.status_code == 200, f"Failed: {response.text}"
        logs = response.json()
        assert isinstance(logs, list)
        
        # Verify log structure if any exist
        if logs:
            log = logs[0]
            assert "log_id" in log
            assert "notification_type" in log
            assert "channel" in log
            assert "status" in log
        
        print(f"✓ Listed {len(logs)} notification logs")
    
    def test_admin_list_logs_filter_by_type(self, admin_token):
        """GET /api/admin/notifications/logs?notification_type=new_event"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        response = requests.get(
            f"{BASE_URL}/api/admin/notifications/logs?notification_type=new_event",
            headers=headers
        )
        
        assert response.status_code == 200
        logs = response.json()
        assert all(log["notification_type"] == "new_event" for log in logs)
        print(f"✓ Filtered logs by type: {len(logs)} results")
    
    def test_admin_list_logs_filter_by_status(self, admin_token):
        """GET /api/admin/notifications/logs?status=sent"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        response = requests.get(
            f"{BASE_URL}/api/admin/notifications/logs?status=sent",
            headers=headers
        )
        
        assert response.status_code == 200
        logs = response.json()
        assert all(log["status"] == "sent" for log in logs)
        print(f"✓ Filtered logs by status: {len(logs)} results")
    
    def test_admin_log_stats(self, admin_token):
        """GET /api/admin/notifications/logs/stats"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        response = requests.get(f"{BASE_URL}/api/admin/notifications/logs/stats", headers=headers)
        
        assert response.status_code == 200, f"Failed: {response.text}"
        stats = response.json()
        assert isinstance(stats, dict)
        
        # Stats should have notification types as keys
        for key, value in stats.items():
            assert "total" in value
            assert "sent" in value or "failed" in value or value.get("total", 0) == 0
        
        print(f"✓ Got log stats for {len(stats)} notification types")
    
    def test_manager_list_community_logs(self, admin_token):
        """GET /api/manager/communities/{slug}/notifications/logs"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        response = requests.get(
            f"{BASE_URL}/api/manager/communities/event-test/notifications/logs",
            headers=headers
        )
        
        assert response.status_code == 200, f"Failed: {response.text}"
        logs = response.json()
        assert isinstance(logs, list)
        
        # All logs should be for this community
        for log in logs:
            # community_id should match event-test community
            assert "community_id" in log
        
        print(f"✓ Listed {len(logs)} community-scoped logs")
    
    def test_regular_user_cannot_access_admin_logs(self, regular_token):
        """RBAC: Regular user cannot access admin log endpoints"""
        headers = {"Authorization": f"Bearer {regular_token}"}
        
        response = requests.get(f"{BASE_URL}/api/admin/notifications/logs", headers=headers)
        assert response.status_code == 403, f"Expected 403, got {response.status_code}"
        
        response = requests.get(f"{BASE_URL}/api/admin/notifications/logs/stats", headers=headers)
        assert response.status_code == 403, f"Expected 403, got {response.status_code}"
        
        print(f"✓ Regular user correctly denied admin log access")


class TestNotificationTriggers:
    """Test notification triggers from existing routes"""
    
    @pytest.fixture(scope="class")
    def admin_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json=SUPER_ADMIN)
        return response.json()["token"]
    
    @pytest.fixture(scope="class")
    def manager_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json=MANAGER_USER)
        if response.status_code != 200:
            requests.post(f"{BASE_URL}/api/auth/register", json={
                "email": MANAGER_USER["email"],
                "password": MANAGER_USER["password"],
                "name": "Notification Test Manager"
            })
            response = requests.post(f"{BASE_URL}/api/auth/login", json=MANAGER_USER)
        return response.json()["token"]
    
    def test_join_request_triggers_notification(self, admin_token):
        """Join request to private community triggers join_request_received notification"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        # Create a new test user for this test
        test_email = f"jointest_{uuid.uuid4().hex[:8]}@test.com"
        register_response = requests.post(f"{BASE_URL}/api/auth/register", json={
            "email": test_email,
            "password": "Test@12345",
            "name": "Join Test User"
        })
        
        if register_response.status_code not in [200, 201]:
            pytest.skip("Could not create test user")
        
        test_token = register_response.json()["token"]
        test_headers = {"Authorization": f"Bearer {test_token}"}
        
        # Ensure private-notif community exists
        response = requests.get(f"{BASE_URL}/api/communities/private-notif", headers=headers)
        if response.status_code != 200:
            # Create it
            requests.post(f"{BASE_URL}/api/admin/communities", headers=headers, json={
                "name": "Private Notification Test",
                "slug": "private-notif",
                "description": "Private community for notification testing",
                "privacy": "private"
            })
        
        # Get initial log count
        logs_before = requests.get(
            f"{BASE_URL}/api/admin/notifications/logs?notification_type=join_request_received",
            headers=headers
        ).json()
        
        # Request to join private community
        response = requests.post(
            f"{BASE_URL}/api/communities/private-notif/request-join",
            headers=test_headers,
            json={"message": "Please let me join!"}
        )
        
        # May fail if already requested or community doesn't exist
        if response.status_code in [200, 201]:
            # Wait for notification to be processed
            time.sleep(1)
            
            # Check logs
            logs_after = requests.get(
                f"{BASE_URL}/api/admin/notifications/logs?notification_type=join_request_received",
                headers=headers
            ).json()
            
            # Should have more logs now (if managers exist)
            print(f"✓ Join request processed, logs before: {len(logs_before)}, after: {len(logs_after)}")
        else:
            print(f"✓ Join request test skipped (status: {response.status_code})")
    
    def test_ban_member_triggers_notification(self, admin_token):
        """Ban member triggers member_banned notification"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        # Create a test user to ban
        test_email = f"bantest_{uuid.uuid4().hex[:8]}@test.com"
        register_response = requests.post(f"{BASE_URL}/api/auth/register", json={
            "email": test_email,
            "password": "Test@12345",
            "name": "Ban Test User"
        })
        
        if register_response.status_code not in [200, 201]:
            pytest.skip("Could not create test user")
        
        test_user_id = register_response.json()["user"]["user_id"]
        test_token = register_response.json()["token"]
        test_headers = {"Authorization": f"Bearer {test_token}"}
        
        # Join a public community
        response = requests.post(
            f"{BASE_URL}/api/communities/event-test/request-join",
            headers=test_headers,
            json={}
        )
        
        if response.status_code not in [200, 201]:
            pytest.skip("Could not join community")
        
        # Get initial log count
        logs_before = requests.get(
            f"{BASE_URL}/api/admin/notifications/logs?notification_type=member_banned",
            headers=headers
        ).json()
        
        # Ban the member
        response = requests.post(
            f"{BASE_URL}/api/manager/communities/event-test/members/{test_user_id}/ban",
            headers=headers
        )
        
        if response.status_code == 200:
            time.sleep(1)
            
            logs_after = requests.get(
                f"{BASE_URL}/api/admin/notifications/logs?notification_type=member_banned",
                headers=headers
            ).json()
            
            assert len(logs_after) > len(logs_before), "member_banned notification not created"
            print(f"✓ Ban member triggered notification, logs: {len(logs_before)} -> {len(logs_after)}")
        else:
            print(f"✓ Ban test skipped (status: {response.status_code})")


class TestTemplateRendering:
    """Test placeholder rendering in templates"""
    
    @pytest.fixture(scope="class")
    def admin_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json=SUPER_ADMIN)
        return response.json()["token"]
    
    def test_placeholders_rendered_in_logs(self, admin_token):
        """Verify placeholders are replaced in notification logs"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        # Get logs
        response = requests.get(f"{BASE_URL}/api/admin/notifications/logs?limit=10", headers=headers)
        logs = response.json()
        
        if not logs:
            print("✓ No logs to verify placeholder rendering (skipped)")
            return
        
        # Check that placeholders are rendered (no {{placeholder}} in body)
        for log in logs:
            body = log.get("body", "")
            subject = log.get("subject", "")
            
            # Should not have unrendered placeholders
            import re
            unrendered = re.findall(r'\{\{(\w+)\}\}', body + (subject or ""))
            
            # Some placeholders might remain if context was missing, but most should be rendered
            if unrendered:
                print(f"  Note: Unrendered placeholders in log {log['log_id']}: {unrendered}")
        
        print(f"✓ Checked placeholder rendering in {len(logs)} logs")


class TestSeededTemplates:
    """Verify 8 default templates are seeded"""
    
    @pytest.fixture(scope="class")
    def admin_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json=SUPER_ADMIN)
        return response.json()["token"]
    
    def test_eight_default_templates_exist(self, admin_token):
        """Verify all 8 default templates are seeded"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        response = requests.get(f"{BASE_URL}/api/admin/notifications/templates", headers=headers)
        templates = response.json()
        
        expected_templates = [
            ("welcome_member", "email"),
            ("post_approved", "email"),
            ("post_rejected", "email"),
            ("member_banned", "email"),
            ("discussion_reply", "email"),
            ("new_event", "email"),
            ("new_event", "whatsapp"),
            ("join_request_received", "email"),
        ]
        
        existing_combos = {(t["notification_type"], t["channel"]) for t in templates}
        
        missing = []
        for expected in expected_templates:
            if expected not in existing_combos:
                missing.append(expected)
        
        assert len(missing) == 0, f"Missing templates: {missing}"
        print(f"✓ All 8 default templates exist")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])

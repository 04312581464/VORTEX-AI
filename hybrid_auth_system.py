"""
Vortex Hybrid Authentication System
Supports both Supabase cloud storage and local JSON fallback
"""

from __future__ import annotations
import os
import sys
import asyncio
from pathlib import Path
from typing import Optional, Tuple

try:
    from supabase_device_authenticator import get_supabase_device_authenticator
    SUPABASE_AVAILABLE = True
except ImportError:
    print("⚠️ Supabase not available. Using local authentication only.")
    SUPABASE_AVAILABLE = False

try:
    from device_authenticator import get_device_authenticator
    LOCAL_AUTH_AVAILABLE = True
except ImportError:
    print("⚠️ Local authenticator not available.")
    LOCAL_AUTH_AVAILABLE = False

import uuid as uuid_lib


class HybridAuthSystem:
    """Hybrid authentication system with Supabase cloud and local JSON fallback"""
    
    def __init__(self):
        self.auth_file = Path("json/.authenticated")
        self.auth_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Initialize with local authentication by default
        self.local_auth = get_device_authenticator()
        self.use_supabase = False
        self._supabase_initialized = False
        
        # Try Supabase first, fallback to local
        if SUPABASE_AVAILABLE:
            print("🌐 Supabase available - will try cloud authentication")
        else:
            print("📁 Using local JSON authentication")
    
    async def _init_supabase(self):
        """Initialize Supabase authenticator"""
        if not self._supabase_initialized:
            try:
                self.supabase_auth = await get_supabase_device_authenticator()
                status = self.supabase_auth.get_system_status()
                
                if status.get('supabase_connected') and status.get('client_configured'):
                    self.use_supabase = True
                    print("✅ Supabase authentication initialized")
                    print(f"📊 Storage: {status.get('storage_type')}")
                else:
                    print("⚠️ Supabase not properly configured, using local")
                    self.use_supabase = False
            except Exception as e:
                print(f"⚠️ Supabase initialization failed: {e}")
                print("📁 Falling back to local authentication...")
                self.use_supabase = False
            finally:
                self._supabase_initialized = True
    
    def is_first_time_setup(self) -> bool:
        """Check if this is first-time setup"""
        if not self.auth_file.exists():
            return True
        
        # Check if file has valid content
        try:
            with open(self.auth_file, 'r') as f:
                data = f.read().strip()
                if not data:
                    return True
                import json
                auth_data = json.loads(data)
                return not auth_data.get('uuid')
        except (json.JSONDecodeError, Exception):
            return True
    
    def get_stored_uuid(self) -> Optional[str]:
        """Get stored UUID from authentication file"""
        if not self.auth_file.exists():
            return None
        
        try:
            with open(self.auth_file, 'r') as f:
                data = f.read().strip()
                if data:
                    import json
                    auth_data = json.loads(data)
                    return auth_data.get('uuid')
        except Exception as e:
            print(f"⚠️ Error reading stored UUID: {e}")
        
        return None
    
    def save_authentication(self, uuid_str: str, device_info: dict) -> None:
        """Save authentication data"""
        try:
            import json
            auth_data = {
                'uuid': uuid_str,
                'device_info': device_info,
                'timestamp': str(datetime.datetime.now())
            }
            
            with open(self.auth_file, 'w') as f:
                json.dump(auth_data, f, indent=2)
                
            print(f"✅ Authentication saved for UUID: {uuid_str[:8]}...")
            
        except Exception as e:
            print(f"❌ Error saving authentication: {e}")
    
    def validate_uuid_format(self, uuid_str: str) -> bool:
        """Validate UUID format"""
        try:
            # Check if it's a valid UUID string
            parsed = uuid_lib.UUID(uuid_str)
            return str(parsed) == uuid_str.lower()
        except ValueError:
            return False
    
    async def is_uuid_available(self, uuid_str: str) -> bool:
        """Check if UUID is available for binding"""
        if self.use_supabase:
            return await self.supabase_auth.is_uuid_available(uuid_str)
        else:
            return self.local_auth.is_uuid_available(uuid_str)
    
    async def bind_uuid_to_device(self, uuid_str: str) -> Tuple[bool, str]:
        """Bind UUID to current device"""
        if self.use_supabase:
            return await self.supabase_auth.bind_uuid_to_device(uuid_str)
        else:
            return self.local_auth.bind_uuid_to_device(uuid_str)
    
    async def verify_device_access(self, uuid_str: str) -> Tuple[bool, str]:
        """Verify device access for UUID"""
        if self.use_supabase:
            return await self.supabase_auth.verify_device_access(uuid_str)
        else:
            return self.local_auth.verify_device_access(uuid_str)
    
    async def get_binding_info(self, uuid_str: str) -> Optional[dict]:
        """Get information about UUID binding"""
        if self.use_supabase:
            return await self.supabase_auth.get_binding_info(uuid_str)
        else:
            return self.local_auth.get_binding_info(uuid_str)
    
    async def prompt_uuid_input(self) -> str:
        """Prompt user for existing UUID input with validation"""
        storage_type = "Supabase Cloud" if self.use_supabase else "Local JSON"
        
        print("\n" + "="*60)
        print("🔐 VORTEX AI - DEVICE AUTHENTICATION")
        print("="*60)
        print()
        print("Welcome to Vortex AI!")
        print(f"Storage Type: {storage_type}")
        print()
        print("📝 Please enter your provided UUID:")
        print("🔑 This UUID is required for authentication")
        print("-" * 60)
        
        while True:
            # Use asyncio to get input without blocking
            loop = asyncio.get_event_loop()
            uuid_input = await loop.run_in_executor(None, input, "🔑 Enter your UUID: ")
            uuid_input = uuid_input.strip()
            
            if not uuid_input:
                print("❌ UUID cannot be empty. Please try again.")
                continue
            
            # Validate UUID format
            if self.validate_uuid_format(uuid_input):
                print(f"✅ UUID format validated: {uuid_input[:8]}...")
                return uuid_input
            else:
                print("❌ Invalid UUID format. Please enter a valid UUID.")
                print("   Example: 550e8400-e29b-41d4-a716-446655440000")
                print("   Contact your administrator if you need assistance.")
                print()
    
    def display_binding_result(self, success: bool, message: str, uuid_str: str) -> None:
        """Display binding result to user"""
        storage_type = "Supabase Cloud" if self.use_supabase else "Local JSON"
        
        print("\n" + "="*60)
        if success:
            print("✅ SUCCESS - DEVICE BINDING COMPLETE")
            print("="*60)
            print(f"🔐 UUID: {uuid_str}")
            print(f"🌐 Storage: {storage_type}")
            print(f"💻 Device: This computer")
            print("🎉 Status: Successfully bound and authenticated")
        else:
            print("❌ FAILED - DEVICE BINDING ERROR")
            print("="*60)
            print(f"🔐 UUID: {uuid_str}")
            print(f"🌐 Storage: {storage_type}")
            print(f"💻 Device: This computer")
            print(f"❌ Error: {message}")
            print("🔄 Status: Binding failed - please try again")
        print("="*60)
    
    def display_access_result(self, success: bool, message: str, uuid_str: str) -> None:
        """Display access verification result"""
        storage_type = "Supabase Cloud" if self.use_supabase else "Local JSON"
        
        print("\n" + "="*60)
        if success:
            print("✅ SUCCESS - ACCESS VERIFIED")
            print("="*60)
            print(f"🔐 UUID: {uuid_str}")
            print(f"🌐 Storage: {storage_type}")
            print(f"💻 Device: This computer")
            print("🎉 Status: Device authenticated - access granted")
        else:
            print("🚫 ACCESS DENIED")
            print("="*60)
            print(f"🔐 UUID: {uuid_str}")
            print(f"🌐 Storage: {storage_type}")
            print(f"💻 Device: This computer")
            print(f"❌ Error: {message}")
            print("🔐 This UUID is locked to another device.")
            print("🚫 Each UUID can only be used on ONE machine.")
            print()
            print("Possible solutions:")
            print("1. Use the correct machine where this UUID was bound")
            print("2. Contact support for UUID reset (if authorized)")
            print("3. Use a different UUID for this machine")
            print("!"*60)
            
            # Exit the application
            print("\n🔄 Exiting Vortex AI...")
            sys.exit(1)
    
    async def perform_first_time_setup(self) -> bool:
        """Perform first-time UUID setup"""
        print("🔍 Starting first-time setup...")
        
        # Get UUID from user
        uuid_str = await self.prompt_uuid_input()
        
        # Check if UUID is available
        if not await self.is_uuid_available(uuid_str):
            self.display_binding_result(False, "UUID is already bound to another device", uuid_str)
            return False
        
        # Bind UUID to device
        success, message = await self.bind_uuid_to_device(uuid_str)
        
        if success:
            # Save authentication locally
            device_info = {
                'computer_name': os.environ.get('COMPUTERNAME', 'Unknown'),
                'username': os.environ.get('USERNAME', 'Unknown'),
                'platform': sys.platform
            }
            self.save_authentication(uuid_str, device_info)
        
        # Display result
        self.display_binding_result(success, message, uuid_str)
        return success
    
    async def verify_existing_session(self) -> bool:
        """Verify existing authentication session"""
        print("🔍 Verifying existing authentication...")
        
        stored_uuid = self.get_stored_uuid()
        
        if not stored_uuid:
            return False
        
        # Verify device access
        success, message = await self.verify_device_access(stored_uuid)
        self.display_access_result(success, message, stored_uuid)
        
        return success
    
    async def authenticate(self) -> bool:
        """Main authentication flow"""
        print("🔐 Vortex AI Hybrid Authentication System")
        print("="*50)
        
        # Try to initialize Supabase if available
        if SUPABASE_AVAILABLE and not self._supabase_initialized:
            await self._init_supabase()
        
        storage_type = "Supabase Cloud" if self.use_supabase else "Local JSON"
        print(f"🌐 Storage Type: {storage_type}")
        
        # Check if first-time setup
        if self.is_first_time_setup():
            return await self.perform_first_time_setup()
        else:
            return await self.verify_existing_session()


# Import datetime for timestamp
import datetime


async def authenticate_vortex_hybrid() -> bool:
    """Main authentication function"""
    try:
        auth_system = HybridAuthSystem()
        return await auth_system.authenticate()
    except Exception as e:
        print(f"❌ Authentication error: {e}")
        return False


if __name__ == "__main__":
    # Test the authentication system
    asyncio.run(authenticate_vortex_hybrid())

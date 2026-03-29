"""
Supabase UUID Authentication System for Vortex AI
Business-grade authentication with one-time use UUIDs
"""

import os
import sys
import asyncio
import tkinter as tk
from tkinter import messagebox, simpledialog, font
import uuid as uuid_lib
import threading
import concurrent.futures
import json
import hashlib
from pathlib import Path
from typing import Optional, Tuple, Dict, Any
from datetime import datetime

# Supabase imports
try:
    from supabase import create_client, Client
    from dotenv import load_dotenv
    SUPABASE_AVAILABLE = True
    load_dotenv()
except ImportError:
    print("⚠️ Supabase not available. Install: pip install supabase python-dotenv")
    SUPABASE_AVAILABLE = False


class SupabaseUUIDAuthenticator:
    """Business-grade Supabase UUID authentication"""
    
    def __init__(self):
        self.supabase: Optional[Client] = None
        self.auth_file = Path("json/.authenticated")
        self.auth_file.parent.mkdir(parents=True, exist_ok=True)
        
        if SUPABASE_AVAILABLE:
            self._initialize_supabase()
    
    def _initialize_supabase(self):
        """Initialize Supabase client"""
        try:
            supabase_url = os.getenv("SUPABASE_URL")
            supabase_key = os.getenv("SUPABASE_ANON_KEY")
            
            if not supabase_url or not supabase_key:
                raise ValueError("Missing SUPABASE_URL or SUPABASE_ANON_KEY in .env file")
            
            self.supabase = create_client(supabase_url, supabase_key)
            print("✅ Supabase client initialized")
            
        except Exception as e:
            print(f"❌ Supabase initialization failed: {e}")
            self.supabase = None
    
    def _get_device_id(self) -> str:
        """Generate unique device fingerprint"""
        import platform
        import socket
        
        # Create device fingerprint
        machine_info = f"{platform.node()}-{platform.system()}-{platform.processor()}"
        try:
            mac = ':'.join(['{:02x}'.format((uuid_lib.getnode() >> elements) & 0xff) 
                           for elements in range(0,2*6,2)][::-1])
            machine_info += f"-{mac}"
        except:
            pass
        
        try:
            hostname = socket.gethostname()
            machine_info += f"-{hostname}"
        except:
            pass
        
        # Hash for consistency
        return hashlib.sha256(machine_info.encode()).hexdigest()[:16]
    
    async def validate_uuid_business(self, uuid_input: str) -> Tuple[bool, str, Dict[str, Any]]:
        """
        Business UUID validation with one-time use enforcement
        Returns: (success, message, customer_data)
        """
        if not self.supabase:
            return False, "Supabase not available", {}
        
        try:
            device_id = self._get_device_id()
            print(f"🔍 Validating UUID: {uuid_input}")
            print(f"🖥️ Device ID: {device_id}")
            
            # Check if UUID exists in database
            response = self.supabase.table('customer_uuids').select('*').eq('uuid', uuid_input).execute()
            
            if not response.data:
                return False, "❌ Invalid UUID - Not found in our database", {}
            
            uuid_data = response.data[0]
            print(f"📊 UUID Status: {uuid_data.get('status', 'unknown')}")
            
            # Business validation rules
            status = uuid_data.get('status', 'unknown')
            
            if status == 'revoked':
                return False, "❌ UUID has been revoked by administrator", {}
            
            if status == 'used':
                # Check if same device
                if uuid_data.get('device_id') == device_id:
                    print("✅ Same device - allowing re-authentication")
                    return True, "✅ Welcome back!", uuid_data
                else:
                    return False, "❌ UUID already used on another device", {}
            
            if status != 'active':
                return False, f"❌ UUID status: {status}", {}
            
            # Check usage limits
            usage_count = uuid_data.get('usage_count', 0)
            max_usage = uuid_data.get('max_usage', 1)
            
            if usage_count >= max_usage:
                return False, "❌ UUID usage limit exceeded", {}
            
            # Check expiration
            expires_at = uuid_data.get('expires_at')
            if expires_at:
                if datetime.fromisoformat(expires_at.replace('Z', '+00:00')) < datetime.now():
                    return False, "❌ UUID has expired", {}
            
            # All checks passed - activate UUID
            print("✅ UUID validation successful - activating...")
            
            # Update database - mark as used
            update_data = {
                'status': 'used',
                'device_id': device_id,
                'usage_count': usage_count + 1,
                'activated_at': datetime.now().isoformat(),
                'last_seen': datetime.now().isoformat()
            }
            
            update_response = self.supabase.table('customer_uuids').update(update_data).eq('uuid', uuid_input).execute()
            
            if update_response.data:
                print("✅ UUID activated successfully")
                return True, f"✅ Welcome to Vortex AI! Customer: {uuid_data.get('customer_email', 'Unknown')}", uuid_data
            else:
                return False, "❌ Failed to activate UUID", {}
                
        except Exception as e:
            print(f"❌ Validation error: {e}")
            return False, f"❌ Network error: {str(e)}", {}
    
    async def check_uuid_exists(self, uuid_input: str) -> bool:
        """Check if UUID exists in database"""
        if not self.supabase:
            return False
        
        try:
            response = self.supabase.table('customer_uuids').select('uuid').eq('uuid', uuid_input).execute()
            return len(response.data) > 0
        except:
            return False
    
    def save_authentication(self, uuid_input: str, customer_data: Dict[str, Any]):
        """Save authentication to local file"""
        try:
            auth_data = {
                "uuid": uuid_input,
                "customer_email": customer_data.get('customer_email', ''),
                "device_id": self._get_device_id(),
                "authenticated_at": datetime.now().isoformat(),
                "method": "supabase_business",
                "status": "active"
            }
            
            with open(self.auth_file, 'w') as f:
                json.dump(auth_data, f, indent=2)
            
            print(f"✅ Authentication saved for {customer_data.get('customer_email', 'Customer')}")
            
        except Exception as e:
            print(f"⚠️ Error saving authentication: {e}")


class UUIDAuthDialog:
    """Professional UUID authentication dialog"""
    
    def __init__(self):
        self.root = None
        self.result = None
        
    def show_dialog(self) -> Optional[str]:
        """Show professional UUID authentication dialog"""
        try:
            self.root = tk.Tk()
            self.root.title("Vortex AI - License Authentication")
            self.root.geometry("500x450")
            self.root.resizable(False, False)
            self.root.eval('tk::PlaceWindow . center')
            
            # Style
            self.root.configure(bg='#1e1e1e')
            
            # Title
            title_font = font.Font(family="Arial", size=18, weight="bold")
            title_label = tk.Label(
                self.root,
                text="🔐 Vortex AI License",
                font=title_font,
                bg='#1e1e1e',
                fg='#00ff00'
            )
            title_label.pack(pady=30)
            
            # Instructions
            info_font = font.Font(family="Arial", size=11)
            info_label = tk.Label(
                self.root,
                text="Enter your license UUID to activate Vortex AI\nThis UUID is one-time use and device-specific",
                font=info_font,
                bg='#1e1e1e',
                fg='#ffffff',
                justify=tk.CENTER
            )
            info_label.pack(pady=10)
            
            # Warning
            warning_label = tk.Label(
                self.root,
                text="⚠️ Each UUID can only be used once\n⚠️ UUID will be locked to this device",
                font=info_font,
                bg='#1e1e1e',
                fg='#ffaa00',
                justify=tk.CENTER
            )
            warning_label.pack(pady=5)
            
            # UUID Entry
            entry_frame = tk.Frame(self.root, bg='#1e1e1e')
            entry_frame.pack(pady=20)
            
            tk.Label(
                entry_frame,
                text="License UUID:",
                font=info_font,
                bg='#1e1e1e',
                fg='#ffffff'
            ).pack(side=tk.LEFT, padx=5)
            
            self.uuid_entry = tk.Entry(
                entry_frame,
                font=info_font,
                width=40,
                bg='#2d2d2d',
                fg='#ffffff',
                insertbackground='#00ff00',
                relief=tk.FLAT,
                bd=5
            )
            self.uuid_entry.pack(side=tk.LEFT, padx=5)
            self.uuid_entry.focus()
            
            # Buttons
            button_frame = tk.Frame(self.root, bg='#1e1e1e')
            button_frame.pack(pady=30)
            
            activate_btn = tk.Button(
                button_frame,
                text="🚀 Activate",
                font=info_font,
                bg='#00ff00',
                fg='#1e1e1e',
                width=15,
                height=2,
                relief=tk.FLAT,
                cursor="hand2",
                command=self._submit_uuid
            )
            activate_btn.pack(side=tk.LEFT, padx=10)
            
            cancel_btn = tk.Button(
                button_frame,
                text="✗ Cancel",
                font=info_font,
                bg='#ff4444',
                fg='#ffffff',
                width=15,
                height=2,
                relief=tk.FLAT,
                cursor="hand2",
                command=self._cancel_uuid
            )
            cancel_btn.pack(side=tk.LEFT, padx=10)
            
            # Bind keys
            self.uuid_entry.bind('<Return>', lambda e: self._submit_uuid())
            self.uuid_entry.bind('<Escape>', lambda e: self._cancel_uuid())
            
            # Make modal
            self.root.transient()
            self.root.grab_set()
            
            self.root.mainloop()
            return self.result
            
        except Exception as e:
            print(f"❌ Dialog error: {e}")
            return None
    
    def _submit_uuid(self):
        """Handle UUID submission"""
        uuid_input = self.uuid_entry.get().strip()
        if uuid_input:
            self.result = uuid_input
        else:
            messagebox.showerror("Error", "Please enter a valid License UUID")
            return
        self.root.destroy()
    
    def _cancel_uuid(self):
        """Handle cancellation"""
        self.result = None
        self.root.destroy()


class BusinessUUIDSystem:
    """Main business UUID authentication system"""
    
    def __init__(self):
        self.authenticator = SupabaseUUIDAuthenticator()
        self.auth_file = Path("json/.authenticated")
    
    def is_authenticated(self) -> bool:
        """Check if already authenticated"""
        return self.auth_file.exists()
    
    def get_stored_auth(self) -> Optional[Dict[str, Any]]:
        """Get stored authentication data"""
        if self.is_authenticated():
            try:
                with open(self.auth_file, 'r') as f:
                    return json.load(f)
            except:
                return None
        return None
    
    def _validate_uuid_format(self, uuid_str: str) -> bool:
        """Validate UUID format"""
        try:
            uuid_lib.UUID(uuid_str)
            return True
        except ValueError:
            return False
    
    def _run_async_in_thread(self, coro):
        """Run async coroutine in thread"""
        def run_in_thread():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                return loop.run_until_complete(coro)
            finally:
                loop.close()
        
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future = executor.submit(run_in_thread)
            return future.result()
    
    def authenticate_user(self) -> Optional[Dict[str, Any]]:
        """Main authentication flow"""
        print("🔐 Starting Vortex AI License Authentication...")
        
        # Check if already authenticated
        if self.is_authenticated():
            auth_data = self.get_stored_auth()
            if auth_data:
                device_id = self.authenticator._get_device_id()
                if auth_data.get('device_id') == device_id:
                    print(f"✅ Already authenticated: {auth_data.get('customer_email', 'Customer')}")
                    return auth_data
                else:
                    print("⚠️ Authentication exists for different device")
        
        # Show authentication dialog
        dialog = UUIDAuthDialog()
        uuid_input = dialog.show_dialog()
        
        if not uuid_input:
            print("❌ Authentication cancelled")
            return None
        
        print(f"🔑 License UUID entered: {uuid_input}")
        
        # Validate UUID format
        if not self._validate_uuid_format(uuid_input):
            self._show_error("Invalid UUID format. Please check your license UUID.")
            return None
        
        # Validate with Supabase
        print("🌐 Connecting to license server...")
        success, message, customer_data = self._run_async_in_thread(
            self.authenticator.validate_uuid_business(uuid_input)
        )
        
        if success:
            print(f"✅ {message}")
            self.authenticator.save_authentication(uuid_input, customer_data)
            return customer_data
        else:
            print(f"❌ {message}")
            self._show_error(message)
            return None
    
    def _show_error(self, message: str):
        """Show error dialog"""
        try:
            root = tk.Tk()
            root.withdraw()
            root.attributes('-topmost', True)
            
            messagebox.showerror(
                "Authentication Failed",
                f"{message}\n\nPlease contact support if you believe this is an error.",
                parent=root
            )
            
            root.destroy()
        except Exception as e:
            print(f"⚠️ Error showing dialog: {e}")


# Global instance
_business_auth_system = None

def get_business_auth_system() -> BusinessUUIDSystem:
    """Get business authentication system instance"""
    global _business_auth_system
    if _business_auth_system is None:
        _business_auth_system = BusinessUUIDSystem()
    return _business_auth_system

def authenticate_vortex_business() -> Optional[Dict[str, Any]]:
    """Main entry point for business authentication"""
    try:
        auth_system = get_business_auth_system()
        return auth_system.authenticate_user()
    except Exception as e:
        print(f"❌ Authentication error: {e}")
        return None


if __name__ == "__main__":
    # Test business authentication system
    print("🔐 Testing Vortex AI Business Authentication")
    print("=" * 60)
    
    auth_system = get_business_auth_system()
    
    if auth_system.is_authenticated():
        auth_data = auth_system.get_stored_auth()
        print(f"✅ Already authenticated: {auth_data.get('customer_email', 'Customer')}")
    else:
        print("❌ Not authenticated")
        result = auth_system.authenticate_user()
        if result:
            print(f"✅ Authentication successful: {result.get('customer_email', 'Customer')}")
        else:
            print("❌ Authentication failed")

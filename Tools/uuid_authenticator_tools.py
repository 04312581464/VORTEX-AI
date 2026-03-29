"""
UUID Authenticator Tools for Vortex AI
Provides function tools for device authentication using UUID
"""

import asyncio
from typing import Dict, Any, Optional, Tuple
from livekit.agents import function_tool
import uuid
import sys
from pathlib import Path

# Import authentication modules
try:
    from device_authenticator import get_device_authenticator
    from supabase_device_authenticator import SupabaseDeviceAuthenticator
    from hybrid_auth_system import HybridAuthSystem
    AUTH_AVAILABLE = True
except ImportError as e:
    print(f"⚠️ Authentication modules not available: {e}")
    AUTH_AVAILABLE = False

@function_tool()
async def bind_uuid_to_device(uuid_str: str) -> str:
    """
    Bind a UUID to the current device for authentication
    
    Args:
        uuid_str: The UUID string to bind to this device
        
    Returns:
        Status message about the binding operation
    """
    try:
        if not AUTH_AVAILABLE:
            return "❌ Authentication modules not available"
            
        auth_system = HybridAuthSystem()
        
        # Validate UUID format
        if not auth_system.validate_uuid_format(uuid_str):
            return "❌ Invalid UUID format. Please provide a valid UUID string."
        
        # Check if UUID is available
        is_available = await auth_system.is_uuid_available(uuid_str)
        if not is_available:
            return "❌ UUID is not available for binding (already in use or invalid)."
        
        # Bind UUID to device
        success, message = await auth_system.bind_uuid_to_device(uuid_str)
        
        if success:
            return f"✅ {message}\n🔐 Device binding successful! You can now use this UUID for authentication."
        else:
            return f"❌ Binding failed: {message}"
            
    except Exception as e:
        return f"❌ Error binding UUID: {str(e)}"

@function_tool()
async def verify_device_access(uuid_str: str) -> str:
    """
    Verify if the current device has access for the given UUID
    
    Args:
        uuid_str: The UUID string to verify access for
        
    Returns:
        Status message about the access verification
    """
    try:
        if not AUTH_AVAILABLE:
            return "❌ Authentication modules not available"
            
        auth_system = HybridAuthSystem()
        
        # Validate UUID format
        if not auth_system.validate_uuid_format(uuid_str):
            return "❌ Invalid UUID format. Please provide a valid UUID string."
        
        # Verify device access
        success, message = await auth_system.verify_device_access(uuid_str)
        
        if success:
            return f"✅ {message}\n🔓 Device access verified! You can use Vortex AI on this device."
        else:
            return f"❌ Access denied: {message}"
            
    except Exception as e:
        return f"❌ Error verifying access: {str(e)}"

@function_tool()
async def get_uuid_binding_info(uuid_str: str) -> str:
    """
    Get detailed information about a UUID binding
    
    Args:
        uuid_str: The UUID string to get information about
        
    Returns:
        Detailed information about the UUID binding
    """
    try:
        if not AUTH_AVAILABLE:
            return "❌ Authentication modules not available"
            
        auth_system = HybridAuthSystem()
        
        # Validate UUID format
        if not auth_system.validate_uuid_format(uuid_str):
            return "❌ Invalid UUID format. Please provide a valid UUID string."
        
        # Get binding information
        info = await auth_system.get_binding_info(uuid_str)
        
        if info:
            return f"""
📋 UUID Binding Information:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🔑 UUID: {info.get('uuid', 'N/A')}
🖥️ Device ID: {info.get('device_id', 'N/A')[:16]}...
📅 Created: {info.get('created_at', 'N/A')}
🔄 Last Used: {info.get('last_used', 'N/A')}
✅ Active: {info.get('in_use', False)}
📁 Storage: {info.get('storage', 'Local JSON')}
🎯 Current Device: {info.get('is_current_device', False)}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
        else:
            return "❌ No binding information found for this UUID."
            
    except Exception as e:
        return f"❌ Error getting binding info: {str(e)}"

@function_tool()
async def generate_new_uuid() -> str:
    """
    Generate a new UUID for device binding
    
    Returns:
        A newly generated UUID string
    """
    try:
        new_uuid = str(uuid.uuid4())
        return f"""
🎲 New UUID Generated:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🔑 UUID: {new_uuid}
📝 Copy this UUID and use it with bind_uuid_to_device
🔐 This UUID can be used for device authentication
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
    except Exception as e:
        return f"❌ Error generating UUID: {str(e)}"

@function_tool()
async def check_uuid_format(uuid_str: str) -> str:
    """
    Check if a UUID string has the correct format
    
    Args:
        uuid_str: The UUID string to validate
        
    Returns:
        Validation result for the UUID format
    """
    try:
        if not AUTH_AVAILABLE:
            return "❌ Authentication modules not available"
            
        auth_system = HybridAuthSystem()
        
        if auth_system.validate_uuid_format(uuid_str):
            return f"✅ Valid UUID format: {uuid_str}"
        else:
            return f"❌ Invalid UUID format: {uuid_str}\n💡 UUID should be in format: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
            
    except Exception as e:
        return f"❌ Error checking UUID format: {str(e)}"

@function_tool()
async def list_device_bindings() -> str:
    """
    List all UUID bindings for the current device
    
    Returns:
        List of all UUID bindings on this device
    """
    try:
        if not AUTH_AVAILABLE:
            return "❌ Authentication modules not available"
            
        auth_system = HybridAuthSystem()
        local_auth = get_device_authenticator()
        
        # Get current device ID
        current_device_id = local_auth._generate_device_id()
        
        # List all bindings
        bindings_info = []
        
        if hasattr(local_auth, 'bindings'):
            for uuid_str, binding in local_auth.bindings.items():
                if binding.device_id == current_device_id:
                    bindings_info.append({
                        'uuid': uuid_str,
                        'created': binding.created_at,
                        'active': binding.in_use
                    })
        
        if bindings_info:
            result = "📋 Device UUID Bindings:\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            for i, binding in enumerate(bindings_info, 1):
                status = "✅ Active" if binding['active'] else "❌ Inactive"
                result += f"{i}. 🔑 {binding['uuid'][:8]}...{binding['uuid'][-8:]}\n"
                result += f"   📅 Created: {binding['created']}\n"
                result += f"   {status}\n\n"
            result += f"🖥️ Device ID: {current_device_id[:16]}...\n"
            result += f"📊 Total bindings: {len(bindings_info)}\n"
            return result
        else:
            return f"📋 No UUID bindings found for this device.\n🖥️ Device ID: {current_device_id[:16]}..."
            
    except Exception as e:
        return f"❌ Error listing bindings: {str(e)}"

@function_tool()
async def deactivate_uuid(uuid_str: str) -> str:
    """
    Deactivate a UUID binding (admin function)
    
    Args:
        uuid_str: The UUID string to deactivate
        
    Returns:
        Status message about the deactivation
    """
    try:
        if not AUTH_AVAILABLE:
            return "❌ Authentication modules not available"
            
        auth_system = HybridAuthSystem()
        
        # Validate UUID format
        if not auth_system.validate_uuid_format(uuid_str):
            return "❌ Invalid UUID format. Please provide a valid UUID string."
        
        # Deactivate UUID
        success, message = await auth_system.deactivate_uuid(uuid_str)
        
        if success:
            return f"✅ {message}\n🔒 UUID has been deactivated and can no longer be used for authentication."
        else:
            return f"❌ Deactivation failed: {message}"
            
    except Exception as e:
        return f"❌ Error deactivating UUID: {str(e)}"

@function_tool()
async def reactivate_uuid(uuid_str: str) -> str:
    """
    Reactivate a UUID binding (admin function)
    
    Args:
        uuid_str: The UUID string to reactivate
        
    Returns:
        Status message about the reactivation
    """
    try:
        if not AUTH_AVAILABLE:
            return "❌ Authentication modules not available"
            
        auth_system = HybridAuthSystem()
        
        # Validate UUID format
        if not auth_system.validate_uuid_format(uuid_str):
            return "❌ Invalid UUID format. Please provide a valid UUID string."
        
        # Reactivate UUID
        success, message = await auth_system.reactivate_uuid(uuid_str)
        
        if success:
            return f"✅ {message}\n🔓 UUID has been reactivated and can be used for authentication again."
        else:
            return f"❌ Reactivation failed: {message}"
            
    except Exception as e:
        return f"❌ Error reactivating UUID: {str(e)}"

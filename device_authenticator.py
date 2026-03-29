"""
Vortex Device Authenticator
UUID-based device locking system with one-time binding
"""

from __future__ import annotations
import json
import hashlib
import platform
import subprocess
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Optional, Tuple


@dataclass
class DeviceBinding:
    """Device binding information"""
    uuid: str
    device_id: str
    device_fingerprint: Dict[str, str]
    bound_at: str
    last_access: str
    in_use: bool = True


class DeviceAuthenticator:
    """UUID-based device authentication system"""
    
    def __init__(self, data_path: Optional[Path] = None):
        self.data_path = data_path or Path("json/device_bindings.json")
        self.data_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Load existing bindings
        self.bindings = self._load_bindings()
    
    def _load_bindings(self) -> Dict[str, DeviceBinding]:
        """Load device bindings from file"""
        try:
            if self.data_path.exists():
                with open(self.data_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return {
                        uuid_str: DeviceBinding(**binding_data) 
                        for uuid_str, binding_data in data.items()
                    }
        except Exception:
            pass
        
        return {}
    
    def _save_bindings(self) -> None:
        """Save device bindings to file"""
        try:
            data = {
                uuid_str: {
                    'uuid': binding.uuid,
                    'device_id': binding.device_id,
                    'device_fingerprint': binding.device_fingerprint,
                    'bound_at': binding.bound_at,
                    'last_access': binding.last_access,
                    'in_use': binding.in_use
                }
                for uuid_str, binding in self.bindings.items()
            }
            
            with open(self.data_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error saving device bindings: {e}")
    
    def _generate_device_fingerprint(self) -> Dict[str, str]:
        """Generate unique device fingerprint from system attributes"""
        try:
            # Get machine name
            machine_name = platform.node()
            
            # Get processor info
            processor = platform.processor()
            if not processor:
                # Try alternative method
                try:
                    result = subprocess.run(['wmic', 'cpu', 'get', 'processorid'], 
                                      capture_output=True, text=True, timeout=10)
                    if result.returncode == 0:
                        lines = result.stdout.strip().split('\n')
                        if len(lines) > 1:
                            processor = lines[1].strip()
                except:
                    processor = "unknown"
            
            # Get MAC address
            try:
                result = subprocess.run(['getmac', '--output', 'json'], 
                                      capture_output=True, text=True, timeout=10)
                if result.returncode == 0:
                    import ast
                    mac_data = ast.literal_eval(result.stdout)
                    if isinstance(mac_data, list) and len(mac_data) > 0:
                        mac_address = mac_data[0].get('mac', 'unknown')
                    else:
                        mac_address = "unknown"
                else:
                    # Fallback method
                    import uuid as uuid_lib
                    mac_address = ':'.join(['{:02x}'.format((uuid_lib.getnode() >> elements) & 0xff) 
                                           for elements in range(0, 48, 8)][::-1])
            except:
                mac_address = "unknown"
            
            # Get motherboard serial
            try:
                result = subprocess.run(['wmic', 'baseboard', 'get', 'serialnumber'], 
                                      capture_output=True, text=True, timeout=10)
                if result.returncode == 0:
                    lines = result.stdout.strip().split('\n')
                    if len(lines) > 1:
                        motherboard_serial = lines[1].strip()
                    else:
                        motherboard_serial = "unknown"
                else:
                    motherboard_serial = "unknown"
            except:
                motherboard_serial = "unknown"
            
            # Combine system info for fingerprint
            system_info = f"{machine_name}|{processor}|{mac_address}|{motherboard_serial}"
            
            # Create multiple hashes for different aspects
            fingerprint = {
                'machine_hash': hashlib.sha256(machine_name.encode()).hexdigest()[:16],
                'processor_hash': hashlib.sha256(processor.encode()).hexdigest()[:16],
                'mac_hash': hashlib.sha256(mac_address.encode()).hexdigest()[:16],
                'motherboard_hash': hashlib.sha256(motherboard_serial.encode()).hexdigest()[:16],
                'combined_hash': hashlib.sha256(system_info.encode()).hexdigest()
            }
            
            return fingerprint
            
        except Exception as e:
            print(f"Error generating device fingerprint: {e}")
            return {
                'machine_hash': 'error',
                'processor_hash': 'error',
                'mac_hash': 'error',
                'motherboard_hash': 'error',
                'combined_hash': 'error'
            }
    
    def _generate_device_id(self) -> str:
        """Generate unique device ID from fingerprint"""
        fingerprint = self._generate_device_fingerprint()
        return fingerprint['combined_hash']
    
    def validate_uuid_format(self, uuid_str: str) -> bool:
        """Validate UUID format"""
        try:
            uuid.UUID(uuid_str)
            return True
        except ValueError:
            return False
    
    def check_uuid_exists(self, uuid_str: str) -> bool:
        """Check if UUID exists in bindings"""
        return uuid_str in self.bindings
    
    def is_uuid_available(self, uuid_str: str) -> bool:
        """Check if UUID is available for binding (exists and not in use)"""
        if not self.check_uuid_exists(uuid_str):
            return True
        
        binding = self.bindings[uuid_str]
        return not binding.in_use
    
    def bind_uuid_to_device(self, uuid_str: str) -> Tuple[bool, str]:
        """Bind UUID to current device"""
        if not self.validate_uuid_format(uuid_str):
            return False, "Invalid UUID format"
        
        if not self.is_uuid_available(uuid_str):
            return False, "UUID is already in use or invalid"
        
        # Generate device fingerprint and ID
        device_fingerprint = self._generate_device_fingerprint()
        device_id = self._generate_device_id()
        
        # Create binding
        current_time = datetime.now(timezone.utc).isoformat()
        binding = DeviceBinding(
            uuid=uuid_str,
            device_id=device_id,
            device_fingerprint=device_fingerprint,
            bound_at=current_time,
            last_access=current_time,
            in_use=True
        )
        
        # Store binding
        self.bindings[uuid_str] = binding
        self._save_bindings()
        
        return True, f"UUID successfully bound to device {device_id[:16]}..."
    
    def verify_device_access(self, uuid_str: str) -> Tuple[bool, str]:
        """Verify if UUID can access from current device"""
        if not self.validate_uuid_format(uuid_str):
            return False, "Invalid UUID format"
        
        if not self.check_uuid_exists(uuid_str):
            return False, "UUID not found in system"
        
        binding = self.bindings[uuid_str]
        
        if not binding.in_use:
            return False, "UUID has been deactivated"
        
        # Generate current device fingerprint
        current_fingerprint = self._generate_device_fingerprint()
        current_device_id = self._generate_device_id()
        
        # Verify device binding
        if binding.device_id != current_device_id:
            return False, "This UUID is locked to another device"
        
        # Additional fingerprint verification for extra security
        if (binding.device_fingerprint.get('combined_hash') != current_fingerprint.get('combined_hash')):
            return False, "Device fingerprint mismatch - possible tampering detected"
        
        # Update last access
        binding.last_access = datetime.now(timezone.utc).isoformat()
        self._save_bindings()
        
        return True, "Access granted"
    
    def get_binding_info(self, uuid_str: str) -> Optional[Dict]:
        """Get information about UUID binding"""
        if not self.check_uuid_exists(uuid_str):
            return None
        
        binding = self.bindings[uuid_str]
        return {
            'uuid': binding.uuid,
            'device_id': binding.device_id[:16] + "...",  # Show partial for security
            'bound_at': binding.bound_at,
            'last_access': binding.last_access,
            'in_use': binding.in_use,
            'is_current_device': binding.device_id == self._generate_device_id()
        }
    
    def deactivate_uuid(self, uuid_str: str) -> Tuple[bool, str]:
        """Deactivate a UUID (admin function)"""
        if not self.check_uuid_exists(uuid_str):
            return False, "UUID not found"
        
        self.bindings[uuid_str].in_use = False
        self._save_bindings()
        
        return True, "UUID deactivated successfully"
    
    def reactivate_uuid(self, uuid_str: str) -> Tuple[bool, str]:
        """Reactivate a UUID (admin function)"""
        if not self.check_uuid_exists(uuid_str):
            return False, "UUID not found"
        
        self.bindings[uuid_str].in_use = True
        self.bindings[uuid_str].last_access = datetime.now(timezone.utc).isoformat()
        self._save_bindings()
        
        return True, "UUID reactivated successfully"


# Global authenticator instance
_device_authenticator = None

def get_device_authenticator() -> DeviceAuthenticator:
    """Get global device authenticator instance"""
    global _device_authenticator
    if _device_authenticator is None:
        _device_authenticator = DeviceAuthenticator()
    return _device_authenticator

"""
External Diagnostics Tool - Virus Scanning for External Devices
Provides comprehensive virus scanning for pendrives, hard disks, and external storage
"""

import os
import subprocess
import json
import logging
import asyncio
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from livekit.agents import function_tool
from livekit.agents import RunContext

@dataclass
class ScanResult:
    """Represents a virus scan result"""
    scan_time: datetime
    target_path: str
    scan_type: str
    total_files: int
    infected_files: List[str]
    suspicious_files: List[str]
    scanned_files: int
    scan_duration: float
    status: str  # 'completed', 'interrupted', 'error'
    error_message: Optional[str] = None
    threats_found: int = 0
    threats_cleaned: int = 0

class ExternalDiagnostics:
    """External device diagnostics and virus scanning"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.scan_reports_dir = Path("json/diagnostics_reports")
        self.scan_reports_dir.mkdir(parents=True, exist_ok=True)
        
        # Available antivirus engines
        self.av_engines = {
            'windows_defender': self._scan_with_windows_defender,
            'microsoft_security_essentials': self._scan_with_windows_defender,  # Same as defender
            'custom_scan': self._scan_with_custom_method
        }
        
        # Common virus signatures and suspicious patterns
        self.suspicious_extensions = [
            '.exe', '.scr', '.bat', '.cmd', '.com', '.pif', '.vbs', '.js', '.jar',
            '.msi', '.deb', '.rpm', '.dmg', '.app', '.pkg', '.iso', '.img'
        ]
        
        self.suspicious_names = [
            'autorun.inf', 'desktop.ini', 'folder.htt', 'thumbs.db',
            'recycler', 'system volume information', '$recycle.bin'
        ]
    
    def get_available_drives(self) -> List[Dict[str, Any]]:
        """Get list of available drives with their information"""
        drives = []
        
        try:
            # Get drive information using Windows commands
            result = subprocess.run(['wmic', 'logicaldisk', 'get', 'size,freespace,caption,drivetype,description,volumename'], 
                                  capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')[1:]  # Skip header
                for line in lines:
                    if line.strip():
                        parts = line.split()
                        if len(parts) >= 5:
                            caption = parts[0]
                            try:
                                size = int(parts[1]) if parts[1] else 0
                                free_space = int(parts[2]) if parts[2] else 0
                                drive_type = int(parts[3]) if parts[3] else 0
                                description = ' '.join(parts[4:])
                                
                                # Drive type mapping
                                type_names = {
                                    0: 'Unknown',
                                    1: 'No Root Directory',
                                    2: 'Removable Disk',
                                    3: 'Local Disk',
                                    4: 'Network Drive',
                                    5: 'Compact Disc',
                                    6: 'RAM Disk'
                                }
                                
                                # Better external drive detection
                                is_external = False
                                if drive_type == 2:  # Removable Disk
                                    is_external = True
                                elif drive_type == 3 and 'usb' in description.lower():
                                    is_external = True
                                elif drive_type == 3 and caption not in ['C:\\']:
                                    # Check if it's an external HDD by size and other factors
                                    if size > 0:  # Has size info
                                        # External HDDs often have specific characteristics
                                        volume_name = self._get_volume_name(caption)
                                        if any(keyword in volume_name.lower() for keyword in ['external', 'usb', 'backup', 'portable']):
                                            is_external = True
                                
                                drives.append({
                                    'letter': caption,
                                    'name': description,
                                    'volume_name': self._get_volume_name(caption),
                                    'type': type_names.get(drive_type, 'Unknown'),
                                    'size_bytes': size,
                                    'free_bytes': free_space,
                                    'size_gb': round(size / (1024**3), 2) if size else 0,
                                    'free_gb': round(free_space / (1024**3), 2) if free_space else 0,
                                    'is_external': is_external,
                                    'drive_type': drive_type
                                })
                            except (ValueError, IndexError):
                                continue
            
        except Exception as e:
            self.logger.error(f"Error getting drive information: {e}")
            # Fallback to basic drive detection
            import string
            for letter in string.ascii_uppercase:
                drive = f"{letter}:\\"
                if os.path.exists(drive):
                    try:
                        drives.append({
                            'letter': drive,
                            'name': f'Drive {letter}',
                            'volume_name': self._get_volume_name(drive),
                            'type': 'Unknown',
                            'size_bytes': 0,
                            'free_bytes': 0,
                            'size_gb': 0,
                            'free_gb': 0,
                            'is_external': letter not in ['C'],  # Assume non-C drives are external
                            'drive_type': 3
                        })
                    except:
                        continue
        
        return drives
    
    def _get_volume_name(self, drive_letter: str) -> str:
        """Get the volume name of a drive"""
        try:
            import win32api
            return win32api.GetVolumeInformation(drive_letter)[0]
        except:
            try:
                # Fallback using subprocess
                result = subprocess.run(['vol', drive_letter], capture_output=True, text=True)
                if result.returncode == 0:
                    lines = result.stdout.split('\n')
                    for line in lines:
                        if 'Volume in drive' in line or 'Volume Serial Number' in line:
                            return line.strip()
                return "Unknown"
            except:
                return "Unknown"
    
    async def scan_for_viruses(self, target_path: str, scan_type: str = 'quick', 
                              engine: str = 'windows_defender') -> ScanResult:
        """
        Scan target path for viruses
        
        Args:
            target_path: Path to scan (drive letter or folder)
            scan_type: 'quick' or 'full'
            engine: Antivirus engine to use
        
        Returns:
            ScanResult object with scan details
        """
        start_time = time.time()
        scan_result = ScanResult(
            scan_time=datetime.now(),
            target_path=target_path,
            scan_type=scan_type,
            total_files=0,
            infected_files=[],
            suspicious_files=[],
            scanned_files=0,
            scan_duration=0,
            status='running'
        )
        
        try:
            # Validate target path
            if not os.path.exists(target_path):
                scan_result.status = 'error'
                scan_result.error_message = f"Target path does not exist: {target_path}"
                return scan_result
            
            # Count total files
            scan_result.total_files = self._count_files(target_path)
            
            # Perform scan based on selected engine
            if engine in self.av_engines:
                scan_result = await self.av_engines[engine](target_path, scan_type, scan_result)
            else:
                scan_result.status = 'error'
                scan_result.error_message = f"Unsupported antivirus engine: {engine}"
            
        except Exception as e:
            scan_result.status = 'error'
            scan_result.error_message = f"Scan failed: {str(e)}"
            self.logger.error(f"Virus scan error: {e}")
        
        finally:
            scan_result.scan_duration = time.time() - start_time
            scan_result.threats_found = len(scan_result.infected_files)
            
            # Save scan report
            self._save_scan_report(scan_result)
        
        return scan_result
    
    async def _scan_with_windows_defender(self, target_path: str, scan_type: str, 
                                        scan_result: ScanResult) -> ScanResult:
        """Scan using Windows Defender"""
        try:
            # Use Windows Defender via PowerShell
            if scan_type == 'quick':
                command = ['powershell', '-Command', 
                          f'Start-MpScan -ScanType QuickScan -ScanPath "{target_path}"']
            else:
                command = ['powershell', '-Command', 
                          f'Start-MpScan -ScanType FullScan -ScanPath "{target_path}"']
            
            # Start the scan
            process = await asyncio.create_subprocess_exec(
                *command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            # Wait for completion with timeout
            try:
                stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=300)  # 5 minutes max
            except asyncio.TimeoutError:
                process.kill()
                scan_result.status = 'interrupted'
                scan_result.error_message = "Scan timed out after 5 minutes"
                return scan_result
            
            # Get scan results
            await self._get_defender_results(scan_result)
            
            # Additional custom scan for suspicious files
            await self._custom_suspicious_scan(target_path, scan_result)
            
            scan_result.status = 'completed'
            
        except Exception as e:
            scan_result.status = 'error'
            scan_result.error_message = f"Windows Defender scan failed: {str(e)}"
        
        return scan_result
    
    async def _scan_with_custom_method(self, target_path: str, scan_type: str, 
                                     scan_result: ScanResult) -> ScanResult:
        """Custom scanning method using heuristics and pattern matching"""
        try:
            await self._custom_suspicious_scan(target_path, scan_result)
            await self._scan_for_suspicious_patterns(target_path, scan_result)
            scan_result.status = 'completed'
            
        except Exception as e:
            scan_result.status = 'error'
            scan_result.error_message = f"Custom scan failed: {str(e)}"
        
        return scan_result
    
    async def _custom_suspicious_scan(self, target_path: str, scan_result: ScanResult):
        """Custom scan for suspicious files and patterns"""
        suspicious_count = 0
        scanned_count = 0
        
        try:
            for root, dirs, files in os.walk(target_path):
                # Skip system directories
                dirs[:] = [d for d in dirs if not d.startswith('.') and 
                          d.lower() not in ['system volume information', '$recycle.bin', 'recycler']]
                
                for file in files:
                    try:
                        file_path = os.path.join(root, file)
                        scanned_count += 1
                        
                        # Update progress every 100 files
                        if scanned_count % 100 == 0:
                            scan_result.scanned_files = scanned_count
                            await asyncio.sleep(0.01)  # Small delay to prevent blocking
                        
                        # Check for suspicious extensions
                        file_ext = os.path.splitext(file)[1].lower()
                        if file_ext in self.suspicious_extensions:
                            # Additional heuristics
                            if self._is_suspicious_file(file_path):
                                scan_result.suspicious_files.append(file_path)
                                suspicious_count += 1
                        
                        # Check for suspicious names
                        if file.lower() in self.suspicious_names:
                            scan_result.suspicious_files.append(file_path)
                            suspicious_count += 1
                        
                        # Check for double extension files
                        if '.' in file and file.count('.') > 1:
                            parts = file.split('.')
                            if len(parts) >= 3 and parts[-2].lower() in ['exe', 'scr', 'bat', 'cmd']:
                                scan_result.suspicious_files.append(file_path)
                                suspicious_count += 1
                    
                    except (OSError, PermissionError):
                        continue
                    except Exception:
                        continue
                    
                    # Prevent infinite scanning
                    if scanned_count > 10000:  # Limit to 10k files for performance
                        break
                
                if scanned_count > 10000:
                    break
        
        except Exception as e:
            self.logger.error(f"Error in custom suspicious scan: {e}")
        
        scan_result.scanned_files = scanned_count
    
    async def _scan_for_suspicious_patterns(self, target_path: str, scan_result: ScanResult):
        """Scan for suspicious patterns in files"""
        suspicious_patterns = [
            b'virus', b'trojan', b'malware', b'backdoor', b'keylogger',
            b'spyware', b'rootkit', b'worm', b'botnet'
        ]
        
        try:
            for root, dirs, files in os.walk(target_path):
                for file in files:
                    if len(scan_result.suspicious_files) > 50:  # Limit results
                        break
                    
                    file_path = os.path.join(root, file)
                    try:
                        # Only scan text-like files
                        file_ext = os.path.splitext(file)[1].lower()
                        if file_ext in ['.txt', '.log', '.ini', '.cfg', '.conf', '.xml', '.json']:
                            with open(file_path, 'rb') as f:
                                content = f.read(1024)  # Read first 1KB
                                for pattern in suspicious_patterns:
                                    if pattern in content.lower():
                                        scan_result.suspicious_files.append(file_path)
                                        break
                    
                    except (OSError, PermissionError, UnicodeDecodeError):
                        continue
                
                if len(scan_result.suspicious_files) > 50:
                    break
        
        except Exception as e:
            self.logger.error(f"Error in pattern scanning: {e}")
    
    async def _get_defender_results(self, scan_result: ScanResult):
        """Get Windows Defender scan results"""
        try:
            # Get threat history from Windows Defender
            command = ['powershell', '-Command', 
                      'Get-MpThreatDetection | Select-Object ThreatName, Resources, DetectionTime | ConvertTo-Json']
            
            process = await asyncio.create_subprocess_exec(
                *command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode == 0 and stdout:
                try:
                    threats = json.loads(stdout.decode())
                    if isinstance(threats, dict):
                        threats = [threats]  # Convert single threat to list
                    
                    for threat in threats:
                        if threat.get('Resources'):
                            resources = threat['Resources'].split(';') if isinstance(threat['Resources'], str) else [threat['Resources']]
                            scan_result.infected_files.extend(resources)
                
                except json.JSONDecodeError:
                    pass
        
        except Exception as e:
            self.logger.error(f"Error getting Defender results: {e}")
    
    def _is_suspicious_file(self, file_path: str) -> bool:
        """Check if a file is suspicious based on heuristics"""
        try:
            # Check file size (very small executables are often suspicious)
            if os.path.getsize(file_path) < 1024 and os.path.splitext(file_path)[1].lower() == '.exe':
                return True
            
            # Check for hidden executables
            if os.path.splitext(file_path)[1].lower() in ['.exe', '.scr'] and \
               os.path.basename(file_path).startswith('.'):
                return True
            
            return False
        
        except:
            return False
    
    def _count_files(self, path: str) -> int:
        """Count total files in path (with limit for performance)"""
        count = 0
        try:
            for root, dirs, files in os.walk(path):
                count += len(files)
                if count > 50000:  # Limit count for performance
                    break
        except:
            pass
        return count
    
    def _save_scan_report(self, scan_result: ScanResult):
        """Save scan report to file"""
        try:
            report = {
                'scan_time': scan_result.scan_time.isoformat(),
                'target_path': scan_result.target_path,
                'scan_type': scan_result.scan_type,
                'total_files': scan_result.total_files,
                'scanned_files': scan_result.scanned_files,
                'infected_files': scan_result.infected_files,
                'suspicious_files': scan_result.suspicious_files,
                'threats_found': scan_result.threats_found,
                'threats_cleaned': scan_result.threats_cleaned,
                'scan_duration': scan_result.scan_duration,
                'status': scan_result.status,
                'error_message': scan_result.error_message
            }
            
            filename = f"scan_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            filepath = self.scan_reports_dir / filename
            
            with open(filepath, 'w') as f:
                json.dump(report, f, indent=2)
        
        except Exception as e:
            self.logger.error(f"Error saving scan report: {e}")
    
    def format_scan_report(self, scan_result: ScanResult) -> str:
        """Format scan result into readable report"""
        lines = [
            "🔍 EXTERNAL DIAGNOSTICS - VIRUS SCAN REPORT",
            "=" * 50,
            f"📅 Scan Time: {scan_result.scan_time.strftime('%Y-%m-%d %H:%M:%S')}",
            f"🎯 Target: {scan_result.target_path}",
            f"⚡ Scan Type: {scan_result.scan_type.title()}",
            f"📊 Status: {scan_result.status.upper()}",
            f"⏱️ Duration: {scan_result.scan_duration:.2f} seconds",
            "",
            f"📁 Files Scanned: {scan_result.scanned_files:,} / {scan_result.total_files:,}",
            f"🦠 Threats Found: {scan_result.threats_found}",
            f"⚠️ Suspicious Files: {len(scan_result.suspicious_files)}",
        ]
        
        if scan_result.error_message:
            lines.extend([
                "",
                "❌ Error:",
                scan_result.error_message
            ])
        
        if scan_result.infected_files:
            lines.extend([
                "",
                "🚨 INFECTED FILES:",
                "-" * 20
            ])
            for i, file in enumerate(scan_result.infected_files[:10], 1):
                lines.append(f"{i}. {file}")
            if len(scan_result.infected_files) > 10:
                lines.append(f"... and {len(scan_result.infected_files) - 10} more")
        
        if scan_result.suspicious_files:
            lines.extend([
                "",
                "⚠️ SUSPICIOUS FILES:",
                "-" * 25
            ])
            for i, file in enumerate(scan_result.suspicious_files[:15], 1):
                lines.append(f"{i}. {file}")
            if len(scan_result.suspicious_files) > 15:
                lines.append(f"... and {len(scan_result.suspicious_files) - 15} more")
        
        if scan_result.status == 'completed' and scan_result.threats_found == 0:
            lines.extend([
                "",
                "✅ RESULT: No threats detected!",
                "🛡️ Your device appears to be safe."
            ])
        elif scan_result.status == 'completed' and scan_result.threats_found > 0:
            lines.extend([
                "",
                "⚠️ RESULT: Threats detected!",
                f"🔧 Found {scan_result.threats_found} potential threat(s)",
                "💡 Recommendation: Run full antivirus scan and remove threats"
            ])
        
        lines.extend([
            "",
            "📋 Report saved to diagnostics_reports folder"
        ])
        
        return "\n".join(lines)

# Global diagnostics instance
_diagnostics: Optional[ExternalDiagnostics] = None

def get_diagnostics() -> ExternalDiagnostics:
    """Get the global diagnostics instance"""
    global _diagnostics
    if _diagnostics is None:
        _diagnostics = ExternalDiagnostics()
    return _diagnostics

# =========================
# TOOL FUNCTIONS
# =========================

@function_tool()
async def external_diagnostics(context: RunContext, target: str, scan_type: str = 'quick') -> str:
    """
    Perform external diagnostics and virus scanning
    
    Args:
        target: Target to scan (e.g., 'D:', 'E:', 'pendrive', 'hard disk')
        scan_type: Type of scan ('quick' or 'full')
    
    Returns:
        Detailed scan report
    """
    diagnostics = get_diagnostics()
    
    try:
        # Get available drives
        drives = diagnostics.get_available_drives()
        
        # Determine target path
        target_path = None
        target_info = None
        
        if target.lower() in ['pendrive', 'usb', 'external']:
            # Find all external/removable drives
            external_drives = [d for d in drives if d['is_external']]
            
            if not external_drives:
                return "❌ No external/pendrive found. Please connect a pendrive or external drive and try again."
            
            # If multiple external drives, scan all of them
            if len(external_drives) == 1:
                target_path = external_drives[0]['letter']
                target_info = external_drives[0]
                scan_multiple = False
            else:
                # Multiple external drives found - scan all
                return await scan_multiple_drives(external_drives, scan_type, diagnostics)
        
        elif target.lower() in ['external hard disk', 'external harddrive', 'external hdd']:
            # Find external hard disks specifically (not USB sticks)
            external_hdds = []
            for drive in drives:
                if drive['is_external'] and drive['drive_type'] == 3:  # Local Disk type but external
                    external_hdds.append(drive)
                elif drive['is_external'] and drive['size_gb'] > 32:  # Larger than 32GB, likely HDD not USB stick
                    external_hdds.append(drive)
            
            if not external_hdds:
                # Fallback to any external drive
                external_drives = [d for d in drives if d['is_external']]
                if external_drives:
                    external_hdds = external_drives
            
            if not external_hdds:
                return "❌ No external hard disk found. Please connect an external hard drive and try again."
            
            # Scan external HDD(s)
            if len(external_hdds) == 1:
                target_path = external_hdds[0]['letter']
                target_info = external_hdds[0]
                scan_multiple = False
            else:
                return await scan_multiple_drives(external_hdds, scan_type, diagnostics)
        
        elif target.lower() in ['hard disk', 'harddrive', 'hdd', 'internal']:
            # Find internal hard disks (exclude C: if it's system drive)
            internal_drives = []
            for drive in drives:
                if not drive['is_external'] and drive['type'] == 'Local Disk':
                    if drive['letter'] == 'C:\\':
                        continue  # Skip system drive unless it's the only one
                    internal_drives.append(drive)
            
            # If no non-C internal drives, include C:
            if not internal_drives:
                for drive in drives:
                    if not drive['is_external'] and drive['type'] == 'Local Disk':
                        internal_drives.append(drive)
            
            if not internal_drives:
                return "❌ No internal hard disk found."
            
            # Scan internal drives
            if len(internal_drives) == 1:
                target_path = internal_drives[0]['letter']
                target_info = internal_drives[0]
                scan_multiple = False
            else:
                return await scan_multiple_drives(internal_drives, scan_type, diagnostics)
        
        elif len(target) == 2 and target[1] == ':':  # Drive letter like 'D:' or 'E:'
            target_path = target.upper() + '\\'
            target_info = next((d for d in drives if d['letter'] == target_path), None)
            if not target_info:
                return f"❌ Drive {target} not found."
        
        else:
            return f"❌ Invalid target: {target}. Use 'pendrive', 'external hard disk', 'hard disk', or drive letter (e.g., 'D:')."
        
        # Handle single drive scan
        if target_path and target_info:
            return await perform_single_scan(target_info, scan_type, diagnostics)
    
    except Exception as e:
        return f"❌ External diagnostics failed: {str(e)}"

async def scan_multiple_drives(drives: List[Dict[str, Any]], scan_type: str, diagnostics) -> str:
    """Scan multiple drives and return combined report"""
    lines = [
        f"🔍 SCANNING MULTIPLE DRIVES ({len(drives)} drives found)",
        "=" * 60,
        ""
    ]
    
    all_results = []
    total_threats = 0
    total_suspicious = 0
    
    for i, drive in enumerate(drives, 1):
        lines.extend([
            f"📁 Drive {i}: {drive['name']} ({drive['letter']})",
            f"   Volume: {drive.get('volume_name', 'Unknown')}",
            f"   Size: {drive['size_gb']} GB | Type: {drive['type']}",
            ""
        ])
        
        try:
            scan_result = await diagnostics.scan_for_viruses(drive['letter'], scan_type)
            all_results.append(scan_result)
            total_threats += scan_result.threats_found
            total_suspicious += len(scan_result.suspicious_files)
            
            lines.append(f"   ✅ Scan completed - Threats: {scan_result.threats_found}, Suspicious: {len(scan_result.suspicious_files)}")
            
        except Exception as e:
            lines.append(f"   ❌ Scan failed: {str(e)}")
        
        lines.append("")
    
    # Summary
    lines.extend([
        "📊 SUMMARY",
        "=" * 20,
        f"Total drives scanned: {len(drives)}",
        f"Total threats found: {total_threats}",
        f"Total suspicious files: {total_suspicious}",
        ""
    ])
    
    if total_threats == 0 and total_suspicious == 0:
        lines.append("✅ ALL DRIVES CLEAN - No threats detected!")
    else:
        lines.append("⚠️ THREATS DETECTED - Review detailed reports")
    
    lines.extend([
        "",
        "📋 Detailed reports saved to diagnostics_reports folder"
    ])
    
    return "\n".join(lines)

async def perform_single_scan(target_info: Dict[str, Any], scan_type: str, diagnostics) -> str:
    """Perform scan on a single drive"""
    # Display target information
    lines = [
        f"🎯 Starting virus scan on: {target_info['name']} ({target_info['letter']})",
        f"💾 Volume: {target_info.get('volume_name', 'Unknown')}",
        f"💾 Size: {target_info['size_gb']} GB (Free: {target_info['free_gb']} GB)",
        f"⚡ Scan type: {scan_type}",
        f"🔍 Engine: Windows Defender + Custom Analysis",
        "",
        "⏳ Scanning in progress... This may take several minutes...",
        ""
    ]
    
    # Perform scan
    scan_result = await diagnostics.scan_for_viruses(target_info['letter'], scan_type)
    
    # Format and return report
    report = diagnostics.format_scan_report(scan_result)
    return "\n".join(lines) + "\n\n" + report

@function_tool()
async def list_external_devices(context: RunContext) -> str:
    """
    List all available external devices and drives
    
    Returns:
        List of connected devices with their information
    """
    diagnostics = get_diagnostics()
    
    try:
        drives = diagnostics.get_available_drives()
        
        lines = [
            "💾 AVAILABLE DEVICES AND DRIVES",
            "=" * 40
        ]
        
        if not drives:
            lines.append("❌ No drives found")
            return "\n".join(lines)
        
        for drive in drives:
            icon = "🔌" if drive['is_external'] else "💻"
            status = "External" if drive['is_external'] else "Internal"
            volume_name = drive.get('volume_name', 'Unknown')
            
            lines.extend([
                f"{icon} {drive['letter']} - {drive['name']}",
                f"   Volume: {volume_name}",
                f"   Type: {drive['type']} ({status})",
                f"   Size: {drive['size_gb']} GB | Free: {drive['free_gb']} GB",
                ""
            ])
        
        lines.extend([
            "💡 Usage:",
            "• 'external_diagnostics pendrive' - Scan pendrive for viruses",
            "• 'external_diagnostics external hard disk' - Scan external hard disk",
            "• 'external_diagnostics hard disk' - Scan internal hard disk",
            "• 'external_diagnostics D:' - Scan specific drive"
        ])
        
        return "\n".join(lines)
    
    except Exception as e:
        return f"❌ Failed to list devices: {str(e)}"

@function_tool()
async def get_scan_history(context: RunContext) -> str:
    """
    Get history of previous virus scans
    
    Returns:
        List of previous scan reports
    """
    diagnostics = get_diagnostics()
    
    try:
        reports_dir = diagnostics.scan_reports_dir
        
        if not reports_dir.exists():
            return "📋 No scan reports found."
        
        reports = list(reports_dir.glob("scan_report_*.json"))
        reports.sort(key=lambda x: x.stat().st_mtime, reverse=True)
        
        if not reports:
            return "📋 No scan reports found."
        
        lines = [
            "📋 VIRUS SCAN HISTORY",
            "=" * 30,
            f"Found {len(reports)} previous scan(s):",
            ""
        ]
        
        for i, report_file in enumerate(reports[:10], 1):  # Show last 10 reports
            try:
                with open(report_file, 'r') as f:
                    report = json.load(f)
                
                scan_time = datetime.fromisoformat(report['scan_time'])
                status_emoji = "✅" if report['threats_found'] == 0 else "⚠️"
                
                lines.extend([
                    f"{i}. {status_emoji} {scan_time.strftime('%Y-%m-%d %H:%M')}",
                    f"   Target: {report['target_path']}",
                    f"   Threats: {report['threats_found']} | Duration: {report['scan_duration']:.1f}s",
                    ""
                ])
            
            except Exception:
                lines.append(f"{i}. ❌ Corrupted report: {report_file.name}")
                lines.append("")
        
        if len(reports) > 10:
            lines.append(f"... and {len(reports) - 10} more reports")
        
        return "\n".join(lines)
    
    except Exception as e:
        return f"❌ Failed to get scan history: {str(e)}"

"""
Vortex AI Business Dashboard
Customer UUID management and analytics
"""

import asyncio
import os
import sys
from datetime import datetime, timedelta
from typing import List, Dict, Any
import json

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from business_uuid_auth import SupabaseUUIDAuthenticator
    from supabase import create_client
    from dotenv import load_dotenv
    load_dotenv()
    BUSINESS_AVAILABLE = True
except ImportError as e:
    print(f"⚠️ Business modules not available: {e}")
    BUSINESS_AVAILABLE = False


class VortexBusinessDashboard:
    """Business management dashboard for Vortex AI"""
    
    def __init__(self):
        if BUSINESS_AVAILABLE:
            self.supabase_url = os.getenv("SUPABASE_URL")
            self.supabase_key = os.getenv("SUPABASE_ANON_KEY")
            if self.supabase_url and self.supabase_key:
                self.supabase = create_client(self.supabase_url, self.supabase_key)
            else:
                print("❌ Missing Supabase credentials in .env file")
                self.supabase = None
        else:
            self.supabase = None
    
    def show_menu(self):
        """Display main menu"""
        print("\n" + "="*60)
        print("🚀 VORTEX AI BUSINESS DASHBOARD")
        print("="*60)
        print("1. 📊 Generate New Customer UUID")
        print("2. 👥 View All Customers")
        print("3. 🔍 Search Customer by UUID")
        print("4. 📈 Business Analytics")
        print("5. 🔄 Revoke Customer UUID")
        print("6. 📋 View Authentication Logs")
        print("7. 💰 Revenue Summary")
        print("8. ⚙️ Settings")
        print("9. 🚪 Exit")
        print("-"*60)
    
    async def generate_customer_uuid(self):
        """Generate new UUID for customer"""
        print("\n🎯 Generate New Customer UUID")
        print("-"*40)
        
        try:
            customer_email = input("📧 Customer Email: ").strip()
            if not customer_email:
                print("❌ Email is required")
                return
            
            customer_name = input("👤 Customer Name (optional): ").strip() or None
            
            print("\n⚙️ UUID Settings:")
            max_usage = input("💳 Max Usage (default 1): ").strip()
            max_usage = int(max_usage) if max_usage.isdigit() else 1
            
            expires_days = input("📅 Expires in days (optional): ").strip()
            expires_days = int(expires_days) if expires_days.isdigit() else None
            
            # Generate UUID using direct table insert
            if self.supabase:
                import uuid as uuid_lib
                
                # Generate new UUID
                new_uuid = str(uuid_lib.uuid4())
                
                # Calculate expiration if specified
                expires_date = None
                if expires_days:
                    expires_date = (datetime.now() + timedelta(days=expires_days)).isoformat()
                
                # Insert directly into table
                insert_data = {
                    'uuid': new_uuid,
                    'customer_email': customer_email,
                    'customer_name': customer_name,
                    'max_usage': max_usage,
                    'expires_at': expires_date,
                    'status': 'active',
                    'created_by': 'dashboard'
                }
                
                response = self.supabase.table('customer_uuids').insert(insert_data).execute()
                
                if response.data:
                    print(f"\n✅ Customer UUID Generated Successfully!")
                    print(f"🔑 UUID: {new_uuid}")
                    print(f"📧 Email: {customer_email}")
                    print(f"👤 Name: {customer_name or 'Not provided'}")
                    print(f"💳 Max Usage: {max_usage}")
                    if expires_days:
                        print(f"📅 Expires: {expires_days} days from now")
                    print(f"\n📋 Send this UUID to the customer: {new_uuid}")
                    print("⚠️ This UUID can only be used once and will be locked to their device")
                else:
                    print("❌ Failed to generate UUID")
                    print(f"Response: {response}")
            else:
                print("❌ Supabase not available")
                
        except Exception as e:
            print(f"❌ Error: {e}")
    
    async def view_all_customers(self):
        """View all customers"""
        print("\n👥 All Customers")
        print("-"*40)
        
        try:
            if self.supabase:
                response = self.supabase.table('customer_uuids').select('*').order('created_at', desc=True).execute()
                
                if response.data:
                    print(f"📊 Total Customers: {len(response.data)}")
                    print("\n{:<36} {:<25} {:<10} {:<8} {:<12}".format(
                        "UUID", "Email", "Status", "Usage", "Created"
                    ))
                    print("-"*100)
                    
                    for customer in response.data[:20]:  # Show first 20
                        uuid_short = customer['uuid'][:8] + "..."
                        email = customer.get('customer_email', 'N/A')[:24]
                        status = customer.get('status', 'unknown')
                        usage = f"{customer.get('usage_count', 0)}/{customer.get('max_usage', 1)}"
                        created = customer.get('created_at', '')[:10]
                        
                        print("{:<36} {:<25} {:<10} {:<8} {:<12}".format(
                            customer['uuid'], email, status, usage, created
                        ))
                    
                    if len(response.data) > 20:
                        print(f"\n... and {len(response.data) - 20} more customers")
                else:
                    print("📭 No customers found")
            else:
                print("❌ Supabase not available")
                
        except Exception as e:
            print(f"❌ Error: {e}")
    
    async def search_customer(self):
        """Search customer by UUID"""
        print("\n🔍 Search Customer")
        print("-"*40)
        
        try:
            search_uuid = input("🔑 Enter UUID to search: ").strip()
            if not search_uuid:
                print("❌ UUID is required")
                return
            
            if self.supabase:
                response = self.supabase.table('customer_uuids').select('*').eq('uuid', search_uuid).execute()
                
                if response.data:
                    customer = response.data[0]
                    print(f"\n✅ Customer Found:")
                    print(f"🔑 UUID: {customer['uuid']}")
                    print(f"📧 Email: {customer.get('customer_email', 'N/A')}")
                    print(f"👤 Name: {customer.get('customer_name', 'N/A')}")
                    print(f"📊 Status: {customer.get('status', 'unknown')}")
                    print(f"💳 Usage: {customer.get('usage_count', 0)}/{customer.get('max_usage', 1)}")
                    print(f"🖥️ Device ID: {customer.get('device_id', 'Not bound')}")
                    print(f"📅 Purchase Date: {customer.get('purchase_date', 'N/A')}")
                    print(f"⏰ Activated At: {customer.get('activated_at', 'Not activated')}")
                    print(f"🔒 Expires At: {customer.get('expires_at', 'Never')}")
                    print(f"📝 Notes: {customer.get('notes', 'None')}")
                else:
                    print("❌ Customer not found")
            else:
                print("❌ Supabase not available")
                
        except Exception as e:
            print(f"❌ Error: {e}")
    
    async def show_analytics(self):
        """Show business analytics"""
        print("\n📈 Business Analytics")
        print("-"*40)
        
        try:
            if self.supabase:
                # Get analytics view
                response = self.supabase.table('customer_analytics').select('*').execute()
                
                if response.data:
                    analytics = response.data[0]
                    print(f"📊 Total Customers: {analytics.get('total_customers', 0)}")
                    print(f"✅ Active Customers: {analytics.get('active_customers', 0)}")
                    print(f"🎯 Used Customers: {analytics.get('used_customers', 0)}")
                    print(f"🚫 Revoked Customers: {analytics.get('revoked_customers', 0)}")
                    print(f"🔥 Activated Customers: {analytics.get('activated_customers', 0)}")
                    
                    if analytics.get('avg_activation_hours'):
                        print(f"⏱️ Avg Activation Time: {analytics.get('avg_activation_hours', 0):.1f} hours")
                    
                    print(f"📅 First Purchase: {analytics.get('first_purchase', 'N/A')}")
                    print(f"📅 Last Purchase: {analytics.get('last_purchase', 'N/A')}")
                    
                    # Recent activity
                    print(f"\n📊 Recent Activity (Last 7 Days):")
                    week_ago = datetime.now() - timedelta(days=7)
                    recent_response = self.supabase.table('customer_uuids').select('*').gte('created_at', week_ago.isoformat()).execute()
                    
                    if recent_response.data:
                        print(f"🆕 New Customers: {len(recent_response.data)}")
                        
                        # Status breakdown
                        active_count = sum(1 for c in recent_response.data if c.get('status') == 'active')
                        used_count = sum(1 for c in recent_response.data if c.get('status') == 'used')
                        
                        print(f"✅ Still Active: {active_count}")
                        print(f"🎯 Already Used: {used_count}")
                    else:
                        print("📭 No new customers in the last 7 days")
                        
                else:
                    print("📭 No analytics data available")
            else:
                print("❌ Supabase not available")
                
        except Exception as e:
            print(f"❌ Error: {e}")
    
    async def revoke_customer(self):
        """Revoke customer UUID"""
        print("\n🔄 Revoke Customer UUID")
        print("-"*40)
        print("⚠️ This will immediately disable the customer's access")
        
        try:
            revoke_uuid = input("🔑 Enter UUID to revoke: ").strip()
            if not revoke_uuid:
                print("❌ UUID is required")
                return
            
            confirm = input(f"⚠️ Are you sure you want to revoke {revoke_uuid}? (yes/no): ").strip().lower()
            if confirm != 'yes':
                print("❌ Revocation cancelled")
                return
            
            if self.supabase:
                response = self.supabase.table('customer_uuids').update({
                    'status': 'revoked',
                    'notes': f"Revoked on {datetime.now().isoformat()} via dashboard"
                }).eq('uuid', revoke_uuid).execute()
                
                if response.data:
                    print(f"✅ UUID {revoke_uuid} has been revoked")
                    print("🚫 Customer will no longer be able to use Vortex AI")
                else:
                    print("❌ Failed to revoke UUID (not found or already revoked)")
            else:
                print("❌ Supabase not available")
                
        except Exception as e:
            print(f"❌ Error: {e}")
    
    async def view_auth_logs(self):
        """View authentication logs"""
        print("\n📋 Authentication Logs")
        print("-"*40)
        
        try:
            if self.supabase:
                response = self.supabase.table('authentication_logs').select('*').order('timestamp', desc=True).limit(50).execute()
                
                if response.data:
                    print(f"📊 Recent Authentication Attempts (Last 50):")
                    print("\n{:<8} {:<36} {:<10} {:<15} {:<20}".format(
                        "Result", "UUID", "Device", "IP Address", "Timestamp"
                    ))
                    print("-"*100)
                    
                    for log in response.data:
                        result = "✅ Success" if log['success'] else "❌ Failed"
                        uuid_short = log['uuid'][:8] + "..."
                        device = log.get('device_id', 'Unknown')[:8] + "..."
                        ip = log.get('ip_address', 'Unknown')[:14]
                        timestamp = log.get('timestamp', '')[:19]
                        
                        print("{:<8} {:<36} {:<10} {:<15} {:<20}".format(
                            result, log['uuid'], device, ip, timestamp
                        ))
                        
                        if not log['success'] and log.get('error_message'):
                            print(f"         Error: {log['error_message']}")
                else:
                    print("📭 No authentication logs found")
            else:
                print("❌ Supabase not available")
                
        except Exception as e:
            print(f"❌ Error: {e}")
    
    async def revenue_summary(self):
        """Show revenue summary"""
        print("\n💰 Revenue Summary")
        print("-"*40)
        
        try:
            if self.supabase:
                # Get all customers
                response = self.supabase.table('customer_uuids').select('*').execute()
                
                if response.data:
                    customers = response.data
                    total_customers = len(customers)
                    active_customers = len([c for c in customers if c['status'] == 'active'])
                    used_customers = len([c for c in customers if c['status'] == 'used'])
                    
                    print(f"📊 Total Licenses Sold: {total_customers}")
                    print(f"🎯 Licenses Activated: {used_customers}")
                    print(f"✅ Licenses Available: {active_customers}")
                    print(f"📈 Activation Rate: {(used_customers/total_customers*100):.1f}%" if total_customers > 0 else "0%")
                    
                    # Monthly breakdown
                    print(f"\n📅 Monthly Sales:")
                    monthly_data = {}
                    for customer in customers:
                        month = customer.get('created_at', '')[:7]  # YYYY-MM
                        if month:
                            monthly_data[month] = monthly_data.get(month, 0) + 1
                    
                    for month, count in sorted(monthly_data.items()):
                        print(f"  {month}: {count} licenses")
                        
                    # Recent sales
                    print(f"\n🆕 Recent Sales (Last 30 Days):")
                    thirty_days_ago = datetime.now() - timedelta(days=30)
                    recent_sales = [c for c in customers if c.get('created_at', '') > thirty_days_ago.isoformat()]
                    
                    print(f"  New Customers: {len(recent_sales)}")
                    if recent_sales:
                        print(f"  Daily Average: {len(recent_sales)/30:.1f}")
                        
                else:
                    print("📭 No customer data available")
            else:
                print("❌ Supabase not available")
                
        except Exception as e:
            print(f"❌ Error: {e}")
    
    async def settings(self):
        """Show settings"""
        print("\n⚙️ Settings")
        print("-"*40)
        
        print(f"🌐 Supabase URL: {os.getenv('SUPABASE_URL', 'Not set')}")
        print(f"🔑 Supabase Key: {'Set' if os.getenv('SUPABASE_ANON_KEY') else 'Not set'}")
        print(f"📊 Database Connection: {'✅ Connected' if self.supabase else '❌ Not connected'}")
        
        print(f"\n💡 Tips:")
        print(f"1. Set up your .env file with Supabase credentials")
        print(f"2. Run the database schema in Supabase SQL Editor")
        print(f"3. Generate UUIDs for customers here")
        print(f"4. Monitor analytics and revenue regularly")
    
    async def run(self):
        """Run the dashboard"""
        if not BUSINESS_AVAILABLE or not self.supabase:
            print("❌ Dashboard not available - check dependencies and Supabase connection")
            return
        
        while True:
            self.show_menu()
            choice = input("\n🎯 Enter your choice (1-9): ").strip()
            
            if choice == '1':
                await self.generate_customer_uuid()
            elif choice == '2':
                await self.view_all_customers()
            elif choice == '3':
                await self.search_customer()
            elif choice == '4':
                await self.show_analytics()
            elif choice == '5':
                await self.revoke_customer()
            elif choice == '6':
                await self.view_auth_logs()
            elif choice == '7':
                await self.revenue_summary()
            elif choice == '8':
                await self.settings()
            elif choice == '9':
                print("\n👋 Goodbye!")
                break
            else:
                print("❌ Invalid choice. Please try again.")
            
            input("\nPress Enter to continue...")


async def main():
    """Main dashboard entry point"""
    print("🚀 Starting Vortex AI Business Dashboard...")
    
    dashboard = VortexBusinessDashboard()
    await dashboard.run()


if __name__ == "__main__":
    asyncio.run(main())

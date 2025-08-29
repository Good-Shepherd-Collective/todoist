"""
Turso database connection handler
"""

import os
import sqlite3
from typing import Optional, List, Dict, Any
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Try to import libsql for Turso
try:
    import libsql_experimental as libsql
    LIBSQL_AVAILABLE = True
except ImportError:
    LIBSQL_AVAILABLE = False

class TursoConnection:
    """Handle connections to Turso database"""
    
    def __init__(self):
        self.turso_url = os.getenv('TURSO_DB')
        self.turso_token = os.getenv('TURSO_API_KEY')
        self.connection = None
        
        if not self.turso_url or not self.turso_token:
            raise ValueError("TURSO_DB and TURSO_API_KEY must be set in environment variables")
    
    def connect(self) -> bool:
        """Establish connection to Turso database"""
        try:
            if not LIBSQL_AVAILABLE:
                print("❌ libsql_experimental not available. Install with: pip install libsql-experimental")
                return False
            
            print(f"🔌 Connecting to Turso database...")
            print(f"   URL: {self.turso_url}")
            
            # Connect to Turso using libsql
            self.connection = libsql.connect(
                self.turso_url,
                auth_token=self.turso_token
            )
            
            print("✅ Successfully connected to Turso database!")
            return True
            
        except Exception as e:
            print(f"❌ Failed to connect to Turso database: {e}")
            return False
    
    def execute_query(self, query: str, params: Optional[tuple] = None) -> Optional[List[Dict[str, Any]]]:
        """Execute a query and return results"""
        if not self.connection:
            if not self.connect():
                return None
        
        try:
            cursor = self.connection.cursor()
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            
            # Get column names
            columns = [description[0] for description in cursor.description] if cursor.description else []
            
            # Fetch results
            rows = cursor.fetchall()
            
            # Convert to list of dictionaries
            results = []
            for row in rows:
                row_dict = {}
                for i, value in enumerate(row):
                    if i < len(columns):
                        row_dict[columns[i]] = value
                results.append(row_dict)
            
            return results
            
        except Exception as e:
            print(f"❌ Query execution failed: {e}")
            return None
    
    def execute_command(self, command: str, params: Optional[tuple] = None) -> bool:
        """Execute a command (INSERT, UPDATE, DELETE) and return success status"""
        if not self.connection:
            if not self.connect():
                return False
        
        try:
            cursor = self.connection.cursor()
            if params:
                cursor.execute(command, params)
            else:
                cursor.execute(command)
            
            self.connection.commit()
            print(f"✅ Command executed successfully: {cursor.rowcount} rows affected")
            return True
            
        except Exception as e:
            print(f"❌ Command execution failed: {e}")
            return False
    
    def create_test_table(self) -> bool:
        """Create a test table for connection verification"""
        create_table_sql = """
        CREATE TABLE IF NOT EXISTS test_connection (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            message TEXT NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        """
        
        return self.execute_command(create_table_sql)
    
    def insert_test_data(self) -> bool:
        """Insert test data to verify write operations"""
        insert_sql = "INSERT INTO test_connection (message) VALUES (?)"
        return self.execute_command(insert_sql, ("Connection test successful!",))
    
    def get_test_data(self) -> Optional[List[Dict[str, Any]]]:
        """Retrieve test data to verify read operations"""
        select_sql = "SELECT * FROM test_connection ORDER BY created_at DESC LIMIT 5"
        return self.execute_query(select_sql)
    
    def close(self):
        """Close the database connection"""
        if self.connection:
            self.connection.close()
            self.connection = None
            print("🔌 Database connection closed")


def test_connection() -> bool:
    """Test Turso database connection with full CRUD operations"""
    print("\n" + "="*60)
    print("🚀 TURSO DATABASE CONNECTION TEST")
    print("="*60)
    
    try:
        # Initialize connection
        db = TursoConnection()
        
        # Test connection
        if not db.connect():
            return False
        
        print("\n📋 Testing database operations...")
        
        # Test 1: Create table
        print("1️⃣  Creating test table...")
        if not db.create_test_table():
            return False
        
        # Test 2: Insert data
        print("2️⃣  Inserting test data...")
        if not db.insert_test_data():
            return False
        
        # Test 3: Read data
        print("3️⃣  Reading test data...")
        results = db.get_test_data()
        if results is None:
            return False
        
        print(f"✅ Retrieved {len(results)} records:")
        for i, record in enumerate(results, 1):
            print(f"   {i}. ID: {record.get('id')}, Message: {record.get('message')}")
            print(f"      Created: {record.get('created_at')}")
        
        # Test 4: Check database info
        print("\n4️⃣  Checking database info...")
        tables = db.execute_query("SELECT name FROM sqlite_master WHERE type='table'")
        if tables:
            print("📊 Available tables:")
            for table in tables:
                print(f"   - {table.get('name')}")
        
        # Close connection
        db.close()
        
        print("\n🎉 All tests passed! Turso database connection is working perfectly.")
        return True
        
    except Exception as e:
        print(f"❌ Connection test failed: {e}")
        return False


if __name__ == "__main__":
    test_connection()
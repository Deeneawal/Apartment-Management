import mysql.connector
import os
import logging
from hashlib import sha256
from contextlib import contextmanager
from getpass import getpass

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Constants for table and column names
TABLE_APARTMENT_UNIT = "ApartmentUnit"
TABLE_TENANT_OWNER = "TenantOwner"
TABLE_PARKING = "Parking"

# Admin password hash (replace this with the hashed password for production)
ADMIN_PASSWORD_HASH = sha256("admin123".encode()).hexdigest()

@contextmanager
def connect_to_database():
    try:
        connection = mysql.connector.connect(
            host="localhost",
            user="root",
            password="#Quantum123",
            database="Apartment"
        )
        yield connection
    except mysql.connector.Error as e:
        logging.error(f"Error connecting to database: {e}")
        yield None
    finally:
        if connection and connection.is_connected():
            connection.close()

@contextmanager
def get_cursor(connection):
    try:
        cursor = connection.cursor()
        yield cursor
    except mysql.connector.Error as e:
        logging.error(f"Error with cursor: {e}")
    finally:
        cursor.close()

def validate_input(prompt, validator, error_message):
    while True:
        user_input = input(prompt).strip()
        if validator(user_input):
            return user_input
        else:
            print(error_message)

def is_valid_integer(value):
    return value.isdigit()

def is_valid_date(value):
    try:
        datetime.strptime(value, '%Y-%m-%d')
        return True
    except ValueError:
        return False

def secure_admin_login():
    password = getpass("Enter admin password: ")
    return sha256(password.encode()).hexdigest() == ADMIN_PASSWORD_HASH

def display_menu(options):
    for i, option in enumerate(options, 1):
        print(f"{i}. {option}")
    return validate_input("Enter your choice: ", is_valid_integer, "Invalid choice. Please enter a number.")

def execute_query(connection, query, data=None):
    with get_cursor(connection) as cursor:
        cursor.execute(query, data)
        connection.commit()
        return cursor

def view_table(connection, table_name):
    query = f"SELECT * FROM {table_name}"
    with get_cursor(connection) as cursor:
        cursor.execute(query)
        rows = cursor.fetchall()
        if rows:
            for row in rows:
                print(row)
        else:
            print(f"No data found in {table_name}.")

def search_apartments(connection):
    filters = {
        "1": ("floor_number", "Enter floor number: "),
        "2": ("bedrooms", "Enter number of bedrooms: "),
        "3": ("bathrooms", "Enter number of bathrooms: "),
        "4": ("square_footage", "Enter square footage: "),
        "5": ("occupancy_status", "Enter occupancy status: ")
    }

    choice = display_menu([
        "By Floor Number", 
        "By Number of Bedrooms", 
        "By Number of Bathrooms", 
        "By Square Footage", 
        "By Occupancy Status", 
        "Cancel"
    ])

    if choice == "6":
        return

    column, prompt = filters.get(choice, (None, None))
    if column:
        value = validate_input(prompt, str.isdigit if column != "occupancy_status" else str.isalnum, "Invalid input.")
        query = f"SELECT * FROM {TABLE_APARTMENT_UNIT} WHERE {column} = %s"
        with get_cursor(connection) as cursor:
            cursor.execute(query, (value,))
            apartments = cursor.fetchall()
            for apartment in apartments:
                print(apartment)
    else:
        print("Invalid choice. Please try again.")

def add_details(connection, table_name, fields):
    data = []
    for field, prompt, validator, error_msg in fields:
        value = validate_input(prompt, validator, error_msg)
        data.append(value)
    placeholders = ", ".join(["%s"] * len(data))
    columns = ", ".join([field for field, _, _, _ in fields])
    query = f"INSERT INTO {table_name} ({columns}) VALUES ({placeholders})"
    execute_query(connection, query, tuple(data))
    print(f"{table_name[:-1]} details added successfully.")

def update_details(connection, table_name, primary_key, primary_value, fields):
    choice = display_menu([f"Update {field}" for field, _, _, _ in fields])
    field, prompt, validator, error_msg = fields[int(choice) - 1]
    new_value = validate_input(prompt, validator, error_msg)
    query = f"UPDATE {table_name} SET {field} = %s WHERE {primary_key} = %s"
    execute_query(connection, query, (new_value, primary_value))
    print(f"{field} updated successfully.")

def delete_details(connection, table_name, primary_key):
    primary_value = validate_input(f"Enter {primary_key} of the record to delete: ", str.isdigit, "Invalid input.")
    query = f"DELETE FROM {table_name} WHERE {primary_key} = %s"
    execute_query(connection, query, (primary_value,))
    print(f"Record deleted from {table_name}.")

def main():
    with connect_to_database() as connection:
        if connection:
            while True:
                user_choice = display_menu(["Regular User", "Admin", "Exit"])

                if user_choice == "1":
                    while True:
                        choice = display_menu(["View Apartment Details", "View Tenant Details", "View Parking Details", "Search Apartments", "Exit"])
                        if choice == "1":
                            view_table(connection, TABLE_APARTMENT_UNIT)
                        elif choice == "2":
                            view_table(connection, TABLE_TENANT_OWNER)
                        elif choice == "3":
                            view_table(connection, TABLE_PARKING)
                        elif choice == "4":
                            search_apartments(connection)
                        elif choice == "5":
                            break
                        else:
                            print("Invalid choice. Please try again.")

                elif user_choice == "2":
                    if secure_admin_login():
                        while True:
                            choice = display_menu([
                                "View Apartment Details", "View Tenant Details", 
                                "View Parking Details", "Search Apartments", 
                                "Add Apartment Details", "Add Tenant Details", 
                                "Add Parking Details", "Update Apartment Details", 
                                "Update Tenant Details", "Update Parking Details", 
                                "Delete Apartment Details", "Delete Tenant Details", 
                                "Delete Parking Details", "Exit"
                            ])

                            if choice == "1":
                                view_table(connection, TABLE_APARTMENT_UNIT)
                            elif choice == "2":
                                view_table(connection, TABLE_TENANT_OWNER)
                            elif choice == "3":
                                view_table(connection, TABLE_PARKING)
                            elif choice == "4":
                                search_apartments(connection)
                            elif choice == "5":
                                fields = [
                                    ("unit_number", "Enter unit number: ", str.isdigit, "Invalid unit number."),
                                    ("floor_number", "Enter floor number: ", str.isdigit, "Invalid floor number."),
                                    ("bedrooms", "Enter number of bedrooms: ", str.isdigit, "Invalid number."),
                                    ("bathrooms", "Enter number of bathrooms: ", str.isdigit, "Invalid number."),
                                    ("square_footage", "Enter square footage: ", str.isdigit, "Invalid square footage."),
                                    ("rent_ownership_details", "Enter rent/ownership details: ", str.isalnum, "Invalid details."),
                                    ("occupancy_status", "Enter occupancy status: ", str.isalnum, "Invalid status.")
                                ]
                                add_details(connection, TABLE_APARTMENT_UNIT, fields)
                            elif choice == "6":
                                fields = [
                                    ("name", "Enter tenant name: ", str.isalnum, "Invalid name."),
                                    ("contact_info", "Enter contact information: ", str.isdigit, "Invalid contact info."),
                                    ("lease_start_date", "Enter lease start date (YYYY-MM-DD): ", is_valid_date, "Invalid date format."),
                                    ("lease_end_date", "Enter lease end date (YYYY-MM-DD): ", is_valid_date, "Invalid date format."),
                                    ("emergency_contact", "Enter emergency contact: ", str.isalnum, "Invalid contact."),
                                    ("rent_payment_history", "Enter rent/payment history: ", str.isalnum, "Invalid history.")
                                ]
                                add_details(connection, TABLE_TENANT_OWNER, fields)
                            elif choice == "7":
                                fields = [
                                    ("parking_space_number", "Enter parking space number: ", str.isdigit, "Invalid number."),
                                    ("vehicle_details", "Enter vehicle details: ", str.isalnum, "Invalid details."),
                                    ("availability_status", "Enter availability status: ", str.isalnum, "Invalid status.")
                                ]
                                add_details(connection, TABLE_PARKING, fields)
                            elif choice == "8":
                                primary_value = validate_input("Enter unit number to update: ", str.isdigit, "Invalid unit number.")
                                fields = [
                                    ("floor_number", "Enter new floor number: ", str.isdigit, "Invalid floor number."),
                                    ("bedrooms", "Enter new number of bedrooms: ", str.isdigit, "Invalid number."),
                                    ("bathrooms", "Enter new number of bathrooms: ", str.isdigit, "Invalid number."),
                                    ("square_footage", "Enter new square footage: ", str.isdigit, "Invalid square footage."),
                                    ("rent_ownership_details", "Enter new rent/ownership details: ", str.isalnum, "Invalid details."),
                                    ("occupancy_status", "Enter new occupancy status: ", str.isalnum, "Invalid status.")
                                ]
                                update_details(connection, TABLE_APARTMENT_UNIT, "unit_number", primary_value, fields)
                            elif choice == "9":
                                primary_value = validate_input("Enter tenant ID to update: ", str.isdigit, "Invalid tenant ID.")
                                fields = [
                                    ("name", "Enter new tenant name: ", str.isalnum, "Invalid name."),
                                    ("contact_info", "Enter new contact information: ", str.isdigit, "Invalid contact info."),
                                    ("lease_start_date", "Enter new lease start date (YYYY-MM-DD): ", is_valid_date, "Invalid date format."),
                                    ("lease_end_date", "Enter new lease end date (YYYY-MM-DD): ", is_valid_date, "Invalid date format."),
                                    ("emergency_contact", "Enter new emergency contact: ", str.isalnum, "Invalid contact."),
                                    ("rent_payment_history", "Enter new rent/payment history: ", str.isalnum, "Invalid history.")
                                ]
                                update_details(connection, TABLE_TENANT_OWNER, "tenant_id", primary_value, fields)
                            elif choice == "10":
                                primary_value = validate_input("Enter parking ID to update: ", str.isdigit, "Invalid parking ID.")
                                fields = [
                                    ("parking_space_number", "Enter new parking space number: ", str.isdigit, "Invalid number."),
                                    ("vehicle_details", "Enter new vehicle details: ", str.isalnum, "Invalid details."),
                                    ("availability_status", "Enter new availability status: ", str.isalnum, "Invalid status.")
                                ]
                                update_details(connection, TABLE_PARKING, "parking_id", primary_value, fields)
                            elif choice == "11":
                                delete_details(connection, TABLE_APARTMENT_UNIT, "unit_number")
                            elif choice == "12":
                                delete_details(connection, TABLE_TENANT_OWNER, "tenant_id")
                            elif choice == "13":
                                delete_details(connection, TABLE_PARKING, "parking_id")
                            elif choice == "14":
                                break
                            else:
                                print("Invalid choice. Please try again.")
                    else:
                        print("Invalid password. Access denied.")
                elif user_choice == "3":
                    break
                else:
                    print("Invalid choice. Please try again.")

if __name__ == "__main__":
    main()
import mysql.connector
import os
import logging
from hashlib import sha256
from contextlib import contextmanager
from getpass import getpass

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Constants for table and column names
TABLE_APARTMENT_UNIT = "ApartmentUnit"
TABLE_TENANT_OWNER = "TenantOwner"
TABLE_PARKING = "Parking"

# Admin password hash (replace this with the hashed password for production)
ADMIN_PASSWORD_HASH = sha256("admin123".encode()).hexdigest()

@contextmanager
def connect_to_database():
    try:
        connection = mysql.connector.connect(
            host="localhost",
            user="root",
            password="#Quantum123",
            database="Apartment"
        )
        yield connection
    except mysql.connector.Error as e:
        logging.error(f"Error connecting to database: {e}")
        yield None
    finally:
        if connection and connection.is_connected():
            connection.close()

@contextmanager
def get_cursor(connection):
    try:
        cursor = connection.cursor()
        yield cursor
    except mysql.connector.Error as e:
        logging.error(f"Error with cursor: {e}")
    finally:
        cursor.close()

def validate_input(prompt, validator, error_message):
    while True:
        user_input = input(prompt).strip()
        if validator(user_input):
            return user_input
        else:
            print(error_message)

def is_valid_integer(value):
    return value.isdigit()

def is_valid_date(value):
    try:
        datetime.strptime(value, '%Y-%m-%d')
        return True
    except ValueError:
        return False

def secure_admin_login():
    password = getpass("Enter admin password: ")
    return sha256(password.encode()).hexdigest() == ADMIN_PASSWORD_HASH

def display_menu(options):
    for i, option in enumerate(options, 1):
        print(f"{i}. {option}")
    return validate_input("Enter your choice: ", is_valid_integer, "Invalid choice. Please enter a number.")

def execute_query(connection, query, data=None):
    with get_cursor(connection) as cursor:
        cursor.execute(query, data)
        connection.commit()
        return cursor

def view_table(connection, table_name):
    query = f"SELECT * FROM {table_name}"
    with get_cursor(connection) as cursor:
        cursor.execute(query)
        rows = cursor.fetchall()
        if rows:
            for row in rows:
                print(row)
        else:
            print(f"No data found in {table_name}.")

def search_apartments(connection):
    filters = {
        "1": ("floor_number", "Enter floor number: "),
        "2": ("bedrooms", "Enter number of bedrooms: "),
        "3": ("bathrooms", "Enter number of bathrooms: "),
        "4": ("square_footage", "Enter square footage: "),
        "5": ("occupancy_status", "Enter occupancy status: ")
    }

    choice = display_menu([
        "By Floor Number", 
        "By Number of Bedrooms", 
        "By Number of Bathrooms", 
        "By Square Footage", 
        "By Occupancy Status", 
        "Cancel"
    ])

    if choice == "6":
        return

    column, prompt = filters.get(choice, (None, None))
    if column:
        value = validate_input(prompt, str.isdigit if column != "occupancy_status" else str.isalnum, "Invalid input.")
        query = f"SELECT * FROM {TABLE_APARTMENT_UNIT} WHERE {column} = %s"
        with get_cursor(connection) as cursor:
            cursor.execute(query, (value,))
            apartments = cursor.fetchall()
            for apartment in apartments:
                print(apartment)
    else:
        print("Invalid choice. Please try again.")

def add_details(connection, table_name, fields):
    data = []
    for field, prompt, validator, error_msg in fields:
        value = validate_input(prompt, validator, error_msg)
        data.append(value)
    placeholders = ", ".join(["%s"] * len(data))
    columns = ", ".join([field for field, _, _, _ in fields])
    query = f"INSERT INTO {table_name} ({columns}) VALUES ({placeholders})"
    execute_query(connection, query, tuple(data))
    print(f"{table_name[:-1]} details added successfully.")

def update_details(connection, table_name, primary_key, primary_value, fields):
    choice = display_menu([f"Update {field}" for field, _, _, _ in fields])
    field, prompt, validator, error_msg = fields[int(choice) - 1]
    new_value = validate_input(prompt, validator, error_msg)
    query = f"UPDATE {table_name} SET {field} = %s WHERE {primary_key} = %s"
    execute_query(connection, query, (new_value, primary_value))
    print(f"{field} updated successfully.")

def delete_details(connection, table_name, primary_key):
    primary_value = validate_input(f"Enter {primary_key} of the record to delete: ", str.isdigit, "Invalid input.")
    query = f"DELETE FROM {table_name} WHERE {primary_key} = %s"
    execute_query(connection, query, (primary_value,))
    print(f"Record deleted from {table_name}.")

def main():
    with connect_to_database() as connection:
        if connection:
            while True:
                user_choice = display_menu(["Regular User", "Admin", "Exit"])

                if user_choice == "1":
                    while True:
                        choice = display_menu(["View Apartment Details", "View Tenant Details", "View Parking Details", "Search Apartments", "Exit"])
                        if choice == "1":
                            view_table(connection, TABLE_APARTMENT_UNIT)
                        elif choice == "2":
                            view_table(connection, TABLE_TENANT_OWNER)
                        elif choice == "3":
                            view_table(connection, TABLE_PARKING)
                        elif choice == "4":
                            search_apartments(connection)
                        elif choice == "5":
                            break
                        else:
                            print("Invalid choice. Please try again.")

                elif user_choice == "2":
                    if secure_admin_login():
                        while True:
                            choice = display_menu([
                                "View Apartment Details", "View Tenant Details", 
                                "View Parking Details", "Search Apartments", 
                                "Add Apartment Details", "Add Tenant Details", 
                                "Add Parking Details", "Update Apartment Details", 
                                "Update Tenant Details", "Update Parking Details", 
                                "Delete Apartment Details", "Delete Tenant Details", 
                                "Delete Parking Details", "Exit"
                            ])

                            if choice == "1":
                                view_table(connection, TABLE_APARTMENT_UNIT)
                            elif choice == "2":
                                view_table(connection, TABLE_TENANT_OWNER)
                            elif choice == "3":
                                view_table(connection, TABLE_PARKING)
                            elif choice == "4":
                                search_apartments(connection)
                            elif choice == "5":
                                fields = [
                                    ("unit_number", "Enter unit number: ", str.isdigit, "Invalid unit number."),
                                    ("floor_number", "Enter floor number: ", str.isdigit, "Invalid floor number."),
                                    ("bedrooms", "Enter number of bedrooms: ", str.isdigit, "Invalid number."),
                                    ("bathrooms", "Enter number of bathrooms: ", str.isdigit, "Invalid number."),
                                    ("square_footage", "Enter square footage: ", str.isdigit, "Invalid square footage."),
                                    ("rent_ownership_details", "Enter rent/ownership details: ", str.isalnum, "Invalid details."),
                                    ("occupancy_status", "Enter occupancy status: ", str.isalnum, "Invalid status.")
                                ]
                                add_details(connection, TABLE_APARTMENT_UNIT, fields)
                            elif choice == "6":
                                fields = [
                                    ("name", "Enter tenant name: ", str.isalnum, "Invalid name."),
                                    ("contact_info", "Enter contact information: ", str.isdigit, "Invalid contact info."),
                                    ("lease_start_date", "Enter lease start date (YYYY-MM-DD): ", is_valid_date, "Invalid date format."),
                                    ("lease_end_date", "Enter lease end date (YYYY-MM-DD): ", is_valid_date, "Invalid date format."),
                                    ("emergency_contact", "Enter emergency contact: ", str.isalnum, "Invalid contact."),
                                    ("rent_payment_history", "Enter rent/payment history: ", str.isalnum, "Invalid history.")
                                ]
                                add_details(connection, TABLE_TENANT_OWNER, fields)
                            elif choice == "7":
                                fields = [
                                    ("parking_space_number", "Enter parking space number: ", str.isdigit, "Invalid number."),
                                    ("vehicle_details", "Enter vehicle details: ", str.isalnum, "Invalid details."),
                                    ("availability_status", "Enter availability status: ", str.isalnum, "Invalid status.")
                                ]
                                add_details(connection, TABLE_PARKING, fields)
                            elif choice == "8":
                                primary_value = validate_input("Enter unit number to update: ", str.isdigit, "Invalid unit number.")
                                fields = [
                                    ("floor_number", "Enter new floor number: ", str.isdigit, "Invalid floor number."),
                                    ("bedrooms", "Enter new number of bedrooms: ", str.isdigit, "Invalid number."),
                                    ("bathrooms", "Enter new number of bathrooms: ", str.isdigit, "Invalid number."),
                                    ("square_footage", "Enter new square footage: ", str.isdigit, "Invalid square footage."),
                                    ("rent_ownership_details", "Enter new rent/ownership details: ", str.isalnum, "Invalid details."),
                                    ("occupancy_status", "Enter new occupancy status: ", str.isalnum, "Invalid status.")
                                ]
                                update_details(connection, TABLE_APARTMENT_UNIT, "unit_number", primary_value, fields)
                            elif choice == "9":
                                primary_value = validate_input("Enter tenant ID to update: ", str.isdigit, "Invalid tenant ID.")
                                fields = [
                                    ("name", "Enter new tenant name: ", str.isalnum, "Invalid name."),
                                    ("contact_info", "Enter new contact information: ", str.isdigit, "Invalid contact info."),
                                    ("lease_start_date", "Enter new lease start date (YYYY-MM-DD): ", is_valid_date, "Invalid date format."),
                                    ("lease_end_date", "Enter new lease end date (YYYY-MM-DD): ", is_valid_date, "Invalid date format."),
                                    ("emergency_contact", "Enter new emergency contact: ", str.isalnum, "Invalid contact."),
                                    ("rent_payment_history", "Enter new rent/payment history: ", str.isalnum, "Invalid history.")
                                ]
                                update_details(connection, TABLE_TENANT_OWNER, "tenant_id", primary_value, fields)
                            elif choice == "10":
                                primary_value = validate_input("Enter parking ID to update: ", str.isdigit, "Invalid parking ID.")
                                fields = [
                                    ("parking_space_number", "Enter new parking space number: ", str.isdigit, "Invalid number."),
                                    ("vehicle_details", "Enter new vehicle details: ", str.isalnum, "Invalid details."),
                                    ("availability_status", "Enter new availability status: ", str.isalnum, "Invalid status.")
                                ]
                                update_details(connection, TABLE_PARKING, "parking_id", primary_value, fields)
                            elif choice == "11":
                                delete_details(connection, TABLE_APARTMENT_UNIT, "unit_number")
                            elif choice == "12":
                                delete_details(connection, TABLE_TENANT_OWNER, "tenant_id")
                            elif choice == "13":
                                delete_details(connection, TABLE_PARKING, "parking_id")
                            elif choice == "14":
                                break
                            else:
                                print("Invalid choice. Please try again.")
                    else:
                        print("Invalid password. Access denied.")
                elif user_choice == "3":
                    break
                else:
                    print("Invalid choice. Please try again.")

if __name__ == "__main__":
    main()


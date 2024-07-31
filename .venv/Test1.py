import csv, os
from datetime import datetime
import os.path
from collections import Counter
import random

date_logged_in = None


class User:
    def __init__(self, id, name, password, age, is_admin):
        self.id = id
        self.name = name
        self.password = password
        self.age = age
        self.is_admin = is_admin


class WorktimeLog:
    def __init__(self, id, date_logged_in, date_logged_out, session_time):
        self.id = id
        self.date_logged_in = date_logged_in
        self.date_logged_out = date_logged_out
        self.session_time = session_time


class Sales:
    def __init__(self, id, product_name, amount):
        self.id = id
        self.product_name = product_name
        self.amount = amount


class CsvHelper:
    def __init__(self, file_path, data_class=None, dtypes=None, newline="", encoding="utf-8"):
        self.file_path = file_path
        self.data_class = data_class
        self.dtypes = dtypes
        self.newline = newline
        self.encoding = encoding

    def row_to_obj(self, row):
        cls = globals()[self.data_class]
        return cls(**row)

    def row_apply_datatypes(self, row):
        for col_index, col_type in self.dtypes.items():
            col_value = row[col_index]

            if col_type == "int":
                row[col_index] = int(col_value)
            elif col_type == "float":
                row[col_index] = float(col_value)
            elif col_type == "bool":
                row[col_index] = col_value.lower() in ("true", "1")
            elif col_type == "str":
                row[col_index] = str(col_value)

        return row

    def read(self):
        try:
            with open(self.file_path, "r", newline=self.newline, encoding=self.encoding) as file:
                rows = list(csv.DictReader(file))
                for index, row in enumerate(rows):
                    if self.dtypes:
                        rows[index] = self.row_apply_datatypes(row)
                    if self.data_class:
                        rows[index] = self.row_to_obj(row)

            return rows
        except FileNotFoundError:
            return []

    def save(self, data):
        if self.data_class:
            keys = data[0].__dict__.keys() if len(data) > 0 else None
        else:
            keys = data[0].keys() if len(data) > 0 else None

        with open(self.file_path, "w", newline=self.newline, encoding=self.encoding) as output_file:
            dict_writer = csv.DictWriter(output_file, fieldnames=keys)
            if keys:
                dict_writer.writeheader()

            for row in data:
                if self.data_class:
                    dict_writer.writerow(row.__dict__)
                else:
                    dict_writer.writerow(row)

    def delete(self):
        os.remove(self.file_path)


def generate_user_id(users):
    id = str(random.randint(1, 10))
    users_list = users.read()
    for user in users_list:
        if user.id == id:
            generate_user_id(users)

    return id


def get_info_for_new_user(users):
    id = generate_user_id(users)
    name = input("Iveskite prisijungimo varda: ")
    password = input("Iveskite prisijungimo slaptazodi: ")
    age = int(input("Iveskite amziu: "))
    is_admin = input("Ar tures admino teises True / False: ")

    return {"id": id, "name": name, "password": password, "age": age, "is_admin": is_admin}


def add_user():
    user_file_obj = CsvHelper("users.csv", data_class="User", dtypes={"age": "int", "is_admin": "bool"})
    user_data = get_info_for_new_user(user_file_obj)
    user = User(**user_data)
    users_list = user_file_obj.read()
    users_list.append(user)
    user_file_obj.save(users_list)
    print("Darbuotojas sukurtas")


def find_user(user_name, user_password):
    user_file_obj = CsvHelper("users.csv", data_class="User", dtypes={"age": "int", "is_admin": "bool"})
    users_list = user_file_obj.read()
    for user in users_list:
        if user.name == user_name and user.password == user_password:
            return ({"user_id": user.id, "is_admin": user.is_admin})


def worker_sales_menu(user_id):
    product_name = input("Iveskite produkto pavadinima: ")
    amount = input("Iveskite produkto kaina: ")
    sale_file_obj = CsvHelper("sales.csv", data_class="Sales")
    sale = Sales(user_id, product_name, amount)
    sales_list = sale_file_obj.read()
    sales_list.append(sale)
    sale_file_obj.save(sales_list)
    print("Pardavimas ivestas")


def worker_menu(user_id):
    worker_choice = input("Darbuotojo menu\n1.Ivesti pardavima: \n2.Atsijungti:\n: ")
    if worker_choice == "1":
        worker_sales_menu(user_id)
        worker_menu(user_id)
    elif worker_choice == "2":
        worker_log_out(user_id)


def worker_log_out(user_id):
    global date_logged_in

    date_logged_out = datetime.now()
    session_time = date_logged_out - date_logged_in
    session_time = session_time.total_seconds()

    worktime_file_obj = CsvHelper("worktime_log.csv", data_class="WorktimeLog")
    worktime = WorktimeLog(user_id, date_logged_in, date_logged_out, session_time)
    worktime_list = worktime_file_obj.read()
    worktime_list.append(worktime)
    worktime_file_obj.save(worktime_list)


def print_workers_by_work_time():
    user_dict = CsvHelper("users.csv", dtypes={"is_admin": "bool"})
    users_list = user_dict.read()

    worktime_dict = CsvHelper("worktime_log.csv", dtypes={"session_time": "float"})
    worktime_list = worktime_dict.read()

    count = Counter()
    [count.update({d["id"]: d["session_time"]}) for d in worktime_list]
    total_session_time = [{"id": k, "session_time": v} for k, v in count.items()]
    sorted_total_session_time = sorted(total_session_time, key=lambda d: d['session_time'], reverse=True)

    for user in users_list:
        for session_time in sorted_total_session_time:
            if session_time["id"] == user["id"]:
                print(f"{user["name"]} - darbo laikas: {session_time["session_time"]}")


def print_workers_by_sales():
    user_dict = CsvHelper("users.csv", dtypes={"is_admin": "bool"})
    users_list = user_dict.read()

    sales_dict = CsvHelper("sales.csv", dtypes={"amount": "float"})
    sales_list = sales_dict.read()

    count = Counter()
    [count.update({d["id"]: d["amount"]}) for d in sales_list]
    total_sales = [{"id": k, "amount": v} for k, v in count.items()]
    sorted_sales_list = sorted(total_sales, key=lambda d: d["amount"], reverse=True)

    for user in users_list:
        for sale in sorted_sales_list:
            if sale["id"] == user["id"]:
                print(f"{user["name"]} - pardavimu suma: {sale["amount"]}")


def print_sold_products_list():
    sales_dict = CsvHelper("sales.csv", dtypes={"amount": "float"})
    sales_list = sales_dict.read()
    sold_products = []
    print("Pardutu produktu sarasas:")
    for sale in sales_list:
        print(sale["product_name"])


def admin_menu():
    admin_choice = input(
        "Administratoriaus menu \n""Pasirinkite: \n1.Sukurti vartotoja\n2.Geriausi darbuotojai pagal isdirbta laika\n"
        "3.Geriausi darbuotojai pagal pardavimus\n4.Visu parduotu produktu sarsas"
        "\n5.Atsijungti\n: ")
    if admin_choice == "1":
        add_user()
    elif admin_choice == "2":
        print_workers_by_work_time()
    elif admin_choice == "3":
        print_workers_by_sales()
    elif admin_choice == "4":
        print_sold_products_list()
    elif admin_choice == "5":
        log_in()

    admin_menu()


def log_in():
    global date_logged_in

    path = 'users.csv'
    check_file = os.path.isfile(path)
    if not check_file:
        print("Nera nei vieno darbuotojo, pirma sukurkite darbuotoja su admino teisemis")
        add_user()

    else:
        user_name = input("Iveskite prisijungimo varda: ")
        user_password = input("Iveskite prisijungimo slaptazodi: ")
        user = find_user(user_name, user_password)
        if user:
            if not bool(user["is_admin"]):
                date_logged_in = datetime.now()
                worker_menu(user["user_id"])
                log_in()
            else:
                admin_menu()

        else:
            print("Tokio vartotojo nera!!!")
            log_in()


def main():
    log_in()


if __name__ == "__main__":
    main()

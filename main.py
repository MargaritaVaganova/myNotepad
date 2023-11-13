import sqlite3
import sys
from PyQt5 import uic
from PyQt5.QtSql import QSqlDatabase, QSqlTableModel
from PyQt5.QtWidgets import QApplication, QMainWindow
from PyQt5.QtWidgets import QTableWidgetItem
from PyQt5.QtWidgets import QInputDialog, QLabel
from PyQt5.QtGui import QPixmap
from PIL import Image


# Основная форма
class MainPage(QMainWindow):
    def __init__(self):
        super().__init__()
        uic.loadUi('mainPage.ui', self)
        self.initUI()

    def initUI(self):
        self.update()

        self.find_pushButton.clicked.connect(self.find)
        self.change_pushButton.clicked.connect(self.change)
        self.del_pushButton.clicked.connect(self.dell)
        self.add_pushButton.clicked.connect(self.add)
        self.update_pushButton.clicked.connect(self.update)

        image1 = Image.open("feather.png")
        image2 = image1.resize((30, 30))
        image2.save('feather2.png')
        # Картинка пера
        self.pixmap = QPixmap('feather2.png')
        self.image = QLabel(self)
        self.image.move(20, 25)
        self.image.setPixmap(self.pixmap)

    # Обновление всех в record_tableView записей
    def update(self):
        all_records = QSqlDatabase.addDatabase('QSQLITE')
        all_records.setDatabaseName('records.sqlite')
        all_records.open()

        model = QSqlTableModel(self, all_records)
        model.setTable('records')
        model.select()

        self.record_tableView.setModel(model)

    # Переход на форму поиска записи по id
    def find(self):
        self.find_form = Find(self)
        self.find_form.show()

    # Переход на форму изменения записи по id
    def change(self):
        self.change_form = Change(self)
        self.change_form.show()

    # Переход на форму удаления записи по id
    def dell(self):
        self.dell_form = Dell(self)
        self.dell_form.show()

    # Переход на форму добавления записи
    def add(self):
        self.add_form = Add(self)
        self.add_form.show()


# Форма поиска записи
class Find(QMainWindow):
    def __init__(self, *args):
        super().__init__()
        uic.loadUi('find.ui', self)
        self.con = sqlite3.connect("records.sqlite")
        self.initUI(args)

    def initUI(self, args):
        self.find_pushButton.clicked.connect(self.find)

    # Поиск записи и вывод на record_tableWidget(при наличии)
    def find(self):
        cur = self.con.cursor()
        result = cur.execute("SELECT * FROM records WHERE id=?",
                             (item_id := self.id_spinBox.text(),)).fetchall()

        self.record_tableWidget.setRowCount(len(result))
        if not result or len(result) == 0:
            self.label.setText("Запись не найдена!")
            return
        else:
            self.label.setText("")
        self.record_tableWidget.setColumnCount(len(result[0]))
        for i, elem in enumerate(result):
            for j, val in enumerate(elem):
                self.record_tableWidget.setItem(i, j, QTableWidgetItem(str(val)))


# Форма изменения записи
class Change(QMainWindow):
    def __init__(self, *args):
        super().__init__()
        uic.loadUi('change.ui', self)
        self.con = sqlite3.connect("records.sqlite")
        self.initUI(args)

    def initUI(self, args):
        self.find_pushButton.clicked.connect(self.find)
        self.record_tableWidget.itemChanged.connect(self.item_changed)
        self.save_pushButton.clicked.connect(self.save)
        self.modified = {}
        self.titles = None

    # Поиск записи для изменения по id
    def find(self):
        cur = self.con.cursor()
        result = cur.execute("SELECT * FROM records WHERE id=?",
                             (item_id := self.id_spinBox.text(),)).fetchall()
        self.record_tableWidget.setRowCount(len(result))
        if not result or len(result) == 0:
            self.label.setText("Запись не найдена!")
            return
        else:
            self.label.setText("")
        self.record_tableWidget.setColumnCount(len(result[0]))
        self.titles = [description[0] for description in cur.description]

        for i, elem in enumerate(result):
            for j, val in enumerate(elem):
                self.record_tableWidget.setItem(i, j, QTableWidgetItem(str(val)))
        self.modified = {}

    # Если произошло изменение
    def item_changed(self, item):
        self.modified[self.titles[item.column()]] = item.text()

    # Сохранение после изменения
    def save(self):
        if self.modified:
            cur = self.con.cursor()
            que = "UPDATE records SET\n"
            que += ", ".join([f"{key}='{self.modified.get(key)}'"
                              for key in self.modified.keys()])
            que += "WHERE id = ?"
            print(que)
            cur.execute(que, (self.id_spinBox.text(),))
            self.con.commit()
            self.modified.clear()


# Форма удаления записи
class Dell(QMainWindow):
    def __init__(self, *args):
        super().__init__()
        uic.loadUi('del.ui', self)
        self.con = sqlite3.connect("records.sqlite")
        self.initUI(args)

    def initUI(self, args):
        self.find_pushButton.clicked.connect(self.find)
        self.del_pushButton.clicked.connect(self.dell)

    # Поиск записи по id
    def find(self):
        cur = self.con.cursor()
        result = cur.execute("SELECT * FROM records WHERE id=?",
                             (item_id := self.id_spinBox.text(),)).fetchall()
        self.record_tableWidget.setRowCount(len(result))
        if not result or len(result) == 0:
            self.label.setText("Запись не найдена!")
            return
        else:
            self.label.setText("")
        self.record_tableWidget.setColumnCount(len(result[0]))
        self.titles = [description[0] for description in cur.description]

        for i, elem in enumerate(result):
            for j, val in enumerate(elem):
                self.record_tableWidget.setItem(i, j, QTableWidgetItem(str(val)))
        self.modified = {}

    # Удаление записей
    def dell(self):
        rows = list(set([i.row() for i in self.record_tableWidget.selectedItems()]))
        ids = [self.record_tableWidget.item(i, 0).text() for i in rows]

        # Диалог с подтверждением удаления
        answer, ok_pressed = QInputDialog.getItem(
            self, "Подтверждение удаления",
            "Вы точно хотите удалить элементы с id " + ",".join(ids),
            ("нет", "да"))

        if answer == "да":
            cur = self.con.cursor()
            cur.execute("DELETE FROM records WHERE id IN (" + ", ".join(
                '?' * len(ids)) + ")", ids)
            self.con.commit()


# Форма добавления записи
class Add(QMainWindow):
    def __init__(self, *args):
        super().__init__()
        uic.loadUi('add.ui', self)
        self.initUI(args)
        self.con = sqlite3.connect("records.sqlite")

    def initUI(self, args):
        self.save_pushButton.clicked.connect(self.save)

    # Добавление новой записи
    def save(self):
        cur = self.con.cursor()
        text = self.record_textEdit.toPlainText()
        cur.execute("INSERT INTO records VALUES(NULL,'" + str(text) + "')")
        self.con.commit()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = MainPage()
    ex.show()
    sys.exit(app.exec_())

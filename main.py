import PyQt6.QtGui
from PyQt6.QtSql import *
from PyQt6.QtWidgets import QApplication, QWidget, QDialog, QMessageBox, QPushButton, QTableWidgetItem, QLabel, QFileDialog
from datetime import datetime, timedelta, date
import pandas as pd
import re
import string
from pandas.io.excel import ExcelWriter
from openpyxl.workbook import Workbook
import scipy
from scipy.stats import lognorm
from scipy.stats import kstest
import matplotlib.pyplot as plt
from PyQt6 import QtCore
from Main_menu import *
from edit_info_fu import Ui_Dialog1
from record_market import Ui_Dialog2
from choice import Ui_Dialog3
from edit_market import *
from filter import Ui_MainWindow1
from stat_shar import Ui_MainWindow2
import math
import sys
db_name = 'futures.db'

def connect_db(db_name):
    db = QSqlDatabase.addDatabase('QSQLITE')
    db.setDatabaseName(db_name)
    if not db.open():
        print('Не удалось подключиться к базе')
        return False
    else:
        print('connection OK')
        return db

def trans_date(test_str1):
    test_str1 = test_str1.replace(" ", "")

    if test_str1 == '':
        str1_1 = 'Ошибка. Поле пустое.'
        return str1_1
    else:

        regex_1 = re.compile('[%s]' % re.escape(string.punctuation))
        test_str1_edit = regex_1.sub('.', test_str1)

        spis1 = test_str1_edit.split('.')
        if len(spis1[0]) == 1:
            spis1[0] = '0' + spis1[0]
        if len(spis1[1]) == 1:
            spis1[1] = '0' + spis1[1]
        test_str1_edit_1 = '.'.join(spis1)  # дата для пользователя
        format_us = '%d.%m.%Y'
        format_bd = '%Y-%m-%d'
        try:
            res1 = bool(datetime.strptime(test_str1_edit_1, format_us))
        except ValueError:
            res1 = False
        if res1 == False:
            str1 = 'Ошибка. Неверный формат введнной даты.'
            return str1

        else:
            date_1 = datetime.strptime(test_str1_edit_1, format_us)  # объект класса datetime (не трогаем)
            date_1_1 = date_1.strftime(format_bd)  # дата для бд
            spis1 = [test_str1_edit_1, date_1_1]
            return spis1

class ModelMarket (QSqlTableModel):
    def __init__(self, db):
        super().__init__()
        self.db = db
        self.setTable("market")
        self.select()

class ModelStruc_fut (QSqlTableModel):
    def __init__(self, db):
        super().__init__()
        self.db = db
        self.setTable("struc_futures")
        self.select()

def recalculation_of_the_main_indicator(sqltablemark:ModelMarket, sqltablestruc:ModelStruc_fut,window:QtWidgets.QTableView,name_fu,filter):
    format_bd = '%Y-%m-%d'
    filterOnName = "name = '{}'".format(name_fu)
    sqltablemark.setFilter(filterOnName)
    window.horizontalHeader().setSortIndicator(3,QtCore.Qt.SortOrder.AscendingOrder)
    sqlForExec_date ="SELECT exec_date from struc_futures WHERE name = '{}'".format(name_fu)
    val_exec_date = QSqlQuery(sqlForExec_date)
    val_exec_date.first()
    exec_date = val_exec_date.value(0)
    for i in range(sqltablemark.rowCount(window.rootIndex())):
        Fk_2 = 0
        Fk = float(sqltablemark.index(i, 5).data())
        day_end = sqltablemark.index(i, 4).data()
        if sqltablemark.index(i - 1, 4).data() == None:
            xk = 0
        else:
            if sqltablemark.index(i - 2, 4).data() == None or not Fk:
                xk = 0
            else:
                Fk_2 = float(sqltablemark.index(i - 2, 5).data())
                if not Fk_2:
                    xk = 0
                else:
                    day_end_2 = sqltablemark.index(i - 2, 4).data()
                    deffe_date = datetime.strptime(exec_date, format_bd) - datetime.strptime(day_end, format_bd)
                    rk = math.log(abs(Fk / 100)) / abs((deffe_date.days + 1))
                    deffe_data_2 = datetime.strptime(exec_date, format_bd) - datetime.strptime(day_end_2,
                                                                                                     format_bd)
                    rk_2 = math.log(abs(Fk_2 / 100)) / abs((deffe_data_2.days + 1))
                    xk = round(abs(math.log(abs(rk / rk_2))), 6)
        record = sqltablemark.record(i)
        record.setValue('contrl_id', xk)
        sqltablemark.setRecord(i, record)
        sqltablemark.select()
    sqltablemark.setFilter(filter)

class EditStrucFu(QtWidgets.QDialog):
    def __init__(self, sqltable: ModelMarket, sqltable_1: ModelStruc_fut, name_fut):
        super().__init__()
        self.marketTable = sqltable
        self.strucTable = sqltable_1
        self.code_fut = name_fut
        self.x = QDialog()
        self.x_root = Ui_Dialog1()
        self.x_root.setupUi(self.x)
        self.x.setWindowFlags(
            QtCore.Qt.WindowType.WindowCloseButtonHint | QtCore.Qt.WindowType.MSWindowsFixedSizeDialogHint)
        self.x.show()

class EditMarket(QtWidgets.QDialog): #ДОБАВЛЕНИЕ
    def __init__(self, sqltable:ModelMarket, sqltable_1:ModelStruc_fut,window:QtWidgets.QTableView):
        super().__init__()
        self.ql_table = sqltable
        self.ql_table_1 = sqltable_1
        self.window_tabl = window
        self.s = QDialog()
        self.s_root = Ui_Dialog()
        self.s_root.setupUi(self.s)
        self.msgBox = QMessageBox()
        self.s.setWindowFlags(QtCore.Qt.WindowType.WindowCloseButtonHint | QtCore.Qt.WindowType.MSWindowsFixedSizeDialogHint)

        sql = f"""SELECT name from struc_futures"""
        query = QSqlQuery(sql)
        self.name_futures = []
        while query.next():
            self.name_futures.append(query.value(0))
        # self.s_root.comboBox.currentIndexChanged(-1)
        for name in self.name_futures:
            self.s_root.comboBox.addItem(name)
        self.s_root.pushButton_2.clicked.connect(self.s.close)
        self.s_root.pushButton.clicked.connect(self.add_row)

        self.s.show()

    def add_row(self):
        format_bd = '%Y-%d-%m'
        format_us = '%m.%d.%Y'
        msg_box_text = ''
        self.new_row = []
        self.name = self.s_root.comboBox.currentText()
        self.new_row.append(self.name) #код фьючерса 0

        date_torg = trans_date(self.s_root.textEdit_2.toPlainText())
        if type(date_torg) == list:
            self.new_row.append(date_torg[0])  # дата торгов для пользователя 1
            self.new_row.append(date_torg[1])  # дата торгов для бд 2
        else: msg_box_text = msg_box_text + date_torg + ' (Дата торгов)\n'
        day_end = trans_date(self.s_root.textEdit_3.toPlainText())
        if type(day_end) == list:
            self.new_row.append(day_end[0])  # дата погашения для пользователя 3
            self.new_row.append(day_end[1])  # дата погашения для бд 4
        else: msg_box_text = msg_box_text + day_end + ' (Дата погашения)\n'
        if type(date_torg) == list and type(day_end) == list:
            differe_dat = datetime.strptime(day_end[1], format_bd) - datetime.strptime(date_torg[1], format_bd)
            if differe_dat.days <= 0:
                msg_box_text = msg_box_text + 'Ошибка. Дата торгов позже даты исполнения.\n'
        quati = self.s_root.textEdit_4.toPlainText()
        min_pr = self.s_root.textEdit_5.toPlainText()
        max_pr = self.s_root.textEdit_6.toPlainText()
        prodano = self.s_root.textEdit_7.toPlainText()
        if quati == '':
            quati = 0
        else: quati = abs(float(quati))
        if min_pr == '':
            min_pr = 0
        else: min_pr = abs(float(min_pr))
        if max_pr == '':
            max_pr = 0
        else: max_pr = abs(float(max_pr))
        if prodano == '':
            prodano = 0
        if min_pr > max_pr or quati < min_pr or quati > max_pr:
            msg_box_text = msg_box_text + 'Ошибка. Задан неверный ценовой диапазон.\n'
        else:
            if abs(float(quati)) >= 100:
                msg_box_text = msg_box_text + 'Ошибка.Недопустимое значение текущей цены.\n'
            self.new_row.append(abs(float(quati))) #текущая цена 5
            self.new_row.append(abs(float(min_pr))) # мин цена 6
            self.new_row.append(abs(float(max_pr))) # макс цена 7
        try:
            abs(int(prodano)) # продано 8
        except ValueError:
            msg_box_text = msg_box_text + "Ошибка. Поле: 'Продано'. Введите целое число.\n"
        else:
            self.new_row.append(abs(int(prodano))) # продано 8
        if len(self.name) > 12:
            msg_box_text = msg_box_text + 'Код фьючесра не должен превышать 12 символов.\n'

        if len(msg_box_text) != 0:
            self.msgBox.warning(self,'Warning',msg_box_text)
        else:
            if self.name not in self.name_futures:
                self.editStruc = EditStrucFu(self.ql_table, self.ql_table_1, self.name)
                self.editStruc.x_root.pushButton.clicked.connect(self.get_info)
            else:
                QSqlQuery(f"""INSERT INTO market(name,torg_date_us,day_end_us,torg_date,day_end,quotation,min_quot,max_quot,num_contr)
                        VALUES ('{self.new_row[0]}','{self.new_row[1]}','{self.new_row[3]}','{self.new_row[2]}','{self.new_row[4]}',{self.new_row[5]},{self.new_row[6]},{self.new_row[7]},{self.new_row[8]})""")
                self.msgBox.information(self,'Information','Запись успешно занесена')
                self.ql_table.select()
                self.s.close()
                recalculation_of_the_main_indicator(sqltablemark=self.ql_table, sqltablestruc=self.ql_table_1,
                                                    window=self.window_tabl,
                                                    name_fu=self.name, filter=self.ql_table.filter())

        # print(self.new_row)

    def get_info(self):
        format_bd = '%Y-%d-%m'
        format_us = '%m.%d.%Y'
        msg_box_text_struc = ''
        self.new_row_struc = []
        cod_ser = self.editStruc.x_root.textEdit_2.toPlainText()
        exet_date = trans_date(self.editStruc.x_root.textEdit_3.toPlainText())
        self.new_row_struc.append(self.name) # имя фьючерса 0
        if cod_ser == '':
            msg_box_text_struc = 'Ошибка. Не введен код серии фьючерса.\n'
        else:
            self.new_row_struc.append(cod_ser) # код серии 1
        if type(exet_date) == list:
            self.new_row_struc.append(exet_date[0])  # дата торгов для пользователя 2
            self.new_row_struc.append(exet_date[1])  # дата торгов для бд 3
        else: msg_box_text_struc = msg_box_text_struc + exet_date + ' (Дата исполнения)\n'
        if len(msg_box_text_struc) != 0:
            self.msgBox.warning(self,'Warning',msg_box_text_struc)
        else:
            QSqlQuery(f"""INSERT INTO market(name,torg_date_us,day_end_us,torg_date,day_end,quotation,min_quot,max_quot,num_contr)
                                    VALUES ('{self.new_row[0]}','{self.new_row[1]}','{self.new_row[3]}','{self.new_row[2]}','{self.new_row[4]}',{self.new_row[5]},{self.new_row[6]},{self.new_row[7]},{self.new_row[8]})""")
            QSqlQuery(f"""INSERT INTO struc_futures(name,base,exec_date_us,exec_date)
                                    VALUES ('{self.new_row_struc[0]}','{self.new_row_struc[1]}','{self.new_row_struc[2]}','{self.new_row_struc[3]}')""")
            self.msgBox.information(self,'Information','Запись успешно внесена')
            self.ql_table.select()
            self.ql_table_1.select()
            self.editStruc.x.close()
            self.s.close()
            recalculation_of_the_main_indicator(sqltablemark=self.ql_table, sqltablestruc=self.ql_table_1,
                                                window=self.window_tabl,
                                                name_fu=self.name, filter=self.ql_table.filter())
            # print(self.new_row_struc)

class Record(QtWidgets.QDialog): # РЕДАКТИРОВАНИЕ
    def __init__(self, sqltable: ModelMarket, sqltable_1: ModelStruc_fut, window:QtWidgets.QTableView):
        super().__init__()
        self.marketTable = sqltable
        self.srtucTable = sqltable_1
        self.windoqMa = window
        self.r = QDialog()
        self.r_root = Ui_Dialog2()
        self.r_root.setupUi(self.r)
        self.msgBox = QMessageBox()
        self.r.setWindowFlags(
            QtCore.Qt.WindowType.WindowCloseButtonHint | QtCore.Qt.WindowType.MSWindowsFixedSizeDialogHint)

        self.sel = self.windoqMa.selectedIndexes()
        self.row = []
        for i in self.sel:
            self.row.append(self.marketTable.data(i))
        self.r_root.label_8.setText(self.row[0])
        self.r_root.label_9.setText(self.row[1])
        self.r_root.label_10.setText(self.row[2])
        self.r_root.textEdit_4.setText(str(self.row[3]))
        self.r_root.textEdit_5.setText(str(self.row[4]))
        self.r_root.textEdit_6.setText(str(self.row[5]))
        self.r_root.textEdit_7.setText(str(self.row[6]))
        self.r_root.pushButton.clicked.connect(self.save)
        self.r_root.pushButton_2.clicked.connect(self.r.close)
        self.r.show()

    def save(self):
        self.new_row = []
        msg_box_text = ''
        quati = self.r_root.textEdit_4.toPlainText()
        min_pr = self.r_root.textEdit_5.toPlainText()
        max_pr = self.r_root.textEdit_6.toPlainText()
        prodano = self.r_root.textEdit_7.toPlainText()
        if abs(float(quati)) >= 100:
            msg_box_text = 'Ошибка.Недопустимое значение текущей цены.\n'
        if quati == '':
            quati = 0
        else: quati = abs(float(quati))
        if min_pr == '':
            min_pr = 0
        else: min_pr = abs(float(min_pr))
        if max_pr == '':
            max_pr = 0
        else: max_pr = abs(float(max_pr))
        if prodano == '':
            prodano = 0
        if min_pr > max_pr or quati < min_pr or quati > max_pr:
            msg_box_text = msg_box_text + 'Ошибка. Задан неверный ценовой диапазон.\n'
        else:
            self.new_row.append(abs(float(quati))) #текущая цена 0
            self.new_row.append(abs(float(min_pr))) # мин цена 1
            self.new_row.append(abs(float(max_pr))) # макс цена 2
        try:
            abs(int(prodano)) # продано 4
        except ValueError:
            msg_box_text = msg_box_text + "Ошибка. Поле: 'Продано'. Введите целое число."
        else:
            self.new_row.append(abs(int(prodano))) # продано 4
        if len(msg_box_text) != 0:
            self.msgBox.warning(self,'Warning',msg_box_text)
        else:
            QSqlQuery(f"""UPDATE market SET quotation = {self.new_row[0]}, min_quot = {self.new_row[1]}, 
            max_quot = {self.new_row[2]}, num_contr = {self.new_row[3]} WHERE name = '{self.row[0]}' AND
            torg_date_us = '{self.row[1]}' AND day_end_us = '{self.row[2]}'""")
            self.msgBox.information(self,'Information','Запись успешно отредактирована.')
            self.marketTable.select()
            self.r.close()
            recalculation_of_the_main_indicator(sqltablemark=self.marketTable, sqltablestruc=self.srtucTable,
                                                window=self.windoqMa,
                                                name_fu=self.row[0],filter=self.marketTable.filter())

class Filter(QtWidgets.QMainWindow):
    def __init__(self, sqltable: ModelMarket, sqltable_1: ModelStruc_fut,window:QtWidgets.QTableView):
        super().__init__()
        self.marketTable = sqltable
        self.strucTable = sqltable_1
        self.window_tabl = window
        self.f = QtWidgets.QMainWindow()
        self.f_root = Ui_MainWindow1()
        self.f_root.setupUi(self.f)
        self.msgBox = QMessageBox()
        self.f.setWindowFlags(
            QtCore.Qt.WindowType.WindowCloseButtonHint | QtCore.Qt.WindowType.MSWindowsFixedSizeDialogHint)

        self.f_root.pushButton_4.clicked.connect(self.f.close)
        sql = f"""SELECT name from struc_futures"""
        query = QSqlQuery(sql)
        # self.f_root.
        self.name_futures = []
        while query.next():
            self.name_futures.append(query.value(0))
        # self.f_root.comboBox_2.addItem('')
        for name in self.name_futures:
            self.f_root.comboBox_2.addItem(name)

        self.f_root.pushButton_6.clicked.connect(self.start_filter)
        self.f_root.pushButton_7.clicked.connect(self.unfilter)
        self.lFiltr = self.get_filter(self.marketTable.filter())

        self.f.show()

    def get_filter(self, s):
        l = len(s)
        list_filt = []
        i = 0
        while i < l:
            row_filter = ''
            a = s[i]
            while '0' <= a <= '9' or a == '.' or a == '-':
                row_filter += a
                i += 1
                if i < l:
                    a = s[i]
                else:
                    break
            i += 1
            if row_filter != '':
                list_filt.append(row_filter)
        return list_filt

    def unfilter(self):
        self.marketTable.setFilter("")
        self.f_root.comboBox_2.setCurrentIndex(0)
        self.f_root.textEdit.clear()
        self.f_root.textEdit_2.clear()
        self.f_root.textEdit_3.clear()
        self.f_root.textEdit_4.clear()

    def start_filter(self):
        format_bd = '%Y-%m-%d'
        msg_box_text = ''
        # self.row_filter = []
        self.date_start = self.f_root.textEdit.toPlainText()
        self.date_end = self.f_root.textEdit_3.toPlainText()
        self.name = self.f_root.comboBox_2.currentText()
        self.priece_start = self.f_root.textEdit_2.toPlainText()
        self.priece_end = self.f_root.textEdit_4.toPlainText()

        f = "name = '{0}' ".format(self.name)
        if self.priece_start == '' and not self.priece_end == '':
            msg_box_text = 'Ошибка. Некорректно введен диапазон для текущей цены.\n'
        if not self.priece_start == '' and self.priece_end == '':
            msg_box_text = 'Ошибка. Некорректно введен диапазон для текущей цены.\n'
        if not self.priece_start == '' and not self.priece_end == '':
            if not self.priece_start == '' and not self.priece_end == '' and abs(float(self.priece_start)) <= abs(float(self.priece_end)):
                self.priece_start_mo=abs(float(self.priece_start))
                self.priece_end_mo=abs(float(self.priece_end))
                f = f + 'AND quotation BETWEEN {0} and {1} '.format(self.priece_start_mo,self.priece_end_mo)
            else: msg_box_text = 'Ошибка. Некорректно введен диапазон для текущей цены.\n'

        if not self.date_end == '' and self.date_start == '':
            msg_box_text = msg_box_text +  'Ошибка. Диапазон дат не задан.'
        if self.date_end == '' and not self.date_start == '':
            msg_box_text = msg_box_text +  'Ошибка. Диапазон дат не задан.'
        if not self.date_end == '' and not self.date_start == '':
            date_start__= trans_date(self.date_start)
            if type(date_start__) == list:
                start_d = date_start__[1]
                # self.row_filter.append(date_start__[1]) #3
            else: msg_box_text = msg_box_text + date_start__ + ' (Значение От:...)\n'

            date_end__=trans_date(self.date_end)
            if type(date_end__) == list:
                end_d = date_end__[1]
                # self.row_filter.append(date_end__[1]) #4
            else:
                msg_box_text = msg_box_text + date_end__ + ' (Значение До:...)\n'
            if type(date_start__) == list and type(date_end__) == list:
                differe_dat = datetime.strptime(date_end__[1], format_bd)-datetime.strptime(date_start__[1], format_bd)
                if differe_dat.days > 0:
                    f = f + "AND torg_date BETWEEN '{0}' and '{1}'".format(start_d, end_d)
                else: msg_box_text = msg_box_text + 'Ошибка. Неверный диапазон дат.\n'

        if len(msg_box_text) == 0:
            self.marketTable.setFilter(f)
        else:
            self.msgBox.warning(self,'Warning', msg_box_text)



        # print(f)

    def date_for_user(self, date_input):

        format_input = '%Y-%m-%d'
        format_output = '%d.%m.%Y'

        date = datetime.strptime(date_input, format_input)
        date_output = date.strftime(format_output)

        return date_output

    def see_filter(self):
        if not len(self.lFiltr) == 0:
            self.f_root.comboBox_2.setCurrentText(self.lFiltr[0])
            if len(self.lFiltr) > 1:
                if len(self.lFiltr) == 5:
                    self.f_root.textEdit_2.setText(self.lFiltr[1])
                    self.f_root.textEdit_4.setText(self.lFiltr[2])
                    self.f_root.textEdit.setText(self.date_for_user(self.lFiltr[3]))
                    self.f_root.textEdit_3.setText(self.date_for_user(self.lFiltr[4]))
                else:
                    if self.lFiltr[1].find('.') != -1:
                        self.f_root.textEdit_2.setText(self.lFiltr[1])
                        self.f_root.textEdit_4.setText(self.lFiltr[2])
                    else:
                        qwe = trans_date(self.lFiltr[1])
                        self.f_root.textEdit.setText(self.date_for_user(self.lFiltr[1]))
                        self.f_root.textEdit_3.setText(self.date_for_user(self.lFiltr[2]))

class Dictribut_law(QtWidgets.QDialog):
    def __init__(self, sqltable: ModelMarket):
        super().__init__()
        self.marketTable = sqltable
        self.d = QDialog()
        self.d_root = Ui_Dialog3()
        self.d_root.setupUi(self.d)
        # Window | Qt::WindowTitleHint | Qt::CustomizeWindowHint
        self.d.setWindowFlags(
            QtCore.Qt.WindowType.WindowCloseButtonHint | QtCore.Qt.WindowType.MSWindowsFixedSizeDialogHint)
        self.d.show()

class Stat_shar(QtWidgets.QMainWindow):
    def __init__(self, sqltable: ModelMarket,window:QtWidgets.QTableView):
        super().__init__()
        self.marketTable = sqltable
        self.windowTable = window
        self.m = QtWidgets.QMainWindow()
        self.m_root = Ui_MainWindow2()
        self.m_root.setupUi(self.m)
        self.msgBox = QMessageBox()
        self.m.setWindowFlags(
            QtCore.Qt.WindowType.WindowCloseButtonHint | QtCore.Qt.WindowType.MSWindowsFixedSizeDialogHint)
        self.m_root.pushButton_5.clicked.connect(self.m.close)
        self.m_root.pushButton_4.clicked.connect(self.math_chart)
        self.m_root.pushButton_6.clicked.connect(self.export_excel_stat_char)
        self.m_root.tableWidget.resizeColumnsToContents()
        self.m.show()

    def math_chart(self):
        self.msg_box_text = ''
        format_bd = '%Y-%m-%d'
        if self.m_root.textEdit.toPlainText()== '' and self.m_root.textEdit_2.toPlainText()== '':
            msg = self.msgBox.information(self,'Information','Диапазон дат для расчета не задан.')
        else:
            self.date_start = self.m_root.textEdit.toPlainText()
            self.date_end = self.m_root.textEdit_2.toPlainText()
            if not self.date_end == '' and self.date_start == '':
                self.msg_box_text = self.msg_box_text + 'Ошибка. Диапазон дат не задан.'
            if self.date_end == '' and not self.date_start == '':
                self.msg_box_text = self.msg_box_text + 'Ошибка. Диапазон дат не задан.'
            if not self.date_end == '' and not self.date_start == '':
                self.date_start__ = trans_date(self.date_start)
                if type(self.date_start__) == list:
                    self.start_d = self.date_start__[1]
                else:
                    self.msg_box_text = self.msg_box_text + self.date_start__ + ' (Значение От:...)\n'

                self.date_end__ = trans_date(self.date_end)
                if type(self.date_end__) == list:
                    self.end_d = self.date_end__[1]
                else:
                    self.msg_box_text = self.msg_box_text + self.date_end__ + ' (Значение До:...)\n'
                if type(self.date_start__) == list and type(self.date_end__) == list:
                    differe_dat = datetime.strptime(self.date_end__[1], format_bd) - datetime.strptime(self.date_start__[1],
                                                                                                  format_bd)
                    if differe_dat.days > 0:
                        # print(self.date_start, self.date_end)
                        self.info = 'Расчет для даты {}'.format(self.date_end__[0])
                        self.f = "torg_date BETWEEN '{0}' and '{1}'".format(self.start_d, self.end_d)
                        # self.m_root.label_4.setText(info)
                    else:
                        self.msg_box_text = self.msg_box_text + 'Ошибка. Неверный диапазон дат.\n'
            if len(self.msg_box_text) == 0:
                # print(self.m_root.tableWidget.rowCount())
                if self.m_root.tableWidget.rowCount() == 0:
                    self.marketTable.setFilter(self.f)
                    self.windowTable.horizontalHeader().setSortIndicator(3, QtCore.Qt.SortOrder.AscendingOrder)
                    format_bd = '%Y-%m-%d'
                    sNamefu = "SELECT name FROM market WHERE torg_date = '{}'".format(self.end_d)
                    sqlNamefu = QSqlQuery(sNamefu)
                    name_fut = []
                    sqlNamefu.first()
                    if sqlNamefu.value(0) == None:
                        msg_st = 'В дату {} не один фьючерс не продавался.'.format(self.date_end__[0])
                        msg = self.msgBox.information(self,'Information',msg_st)
                    else:
                        self.m_root.label_4.setText(self.info)
                        name_fut.append(sqlNamefu.value(0))
                        while sqlNamefu.size():
                            sqlNamefu.next()
                            if sqlNamefu.value(0) == None:
                                break
                            else:
                                name_fut.append(sqlNamefu.value(0))
                        # print(name_fut)
                    self.marketTable.setFilter("")
                    if not len(name_fut) == 0:
                        self.msg_st = ""
                        numd_row = 0
                        self.dNameDay = {}
                        for name in name_fut:
                            self.f1=" AND name = '{0}' and NOT torg_date = '{1}'".format(name,self.end_d)
                            self.f_final = self.f + self.f1
                            # self.marketTable.setFilter("")
                            # self.marketTable.setFilter(self.f_final)
                            # print(self.f_final)
                            s = "SELECT contrl_id FROM market WHERE " + self.f_final
                            # print(s)
                            sqlContr = QSqlQuery(s)
                            contl_id = []
                            sqlContr.first()
                            if sqlContr.value(0) == None:
                                self.msg_st = 'В заданный диапозон дат для фючерса {0}\nвходит только дата {1}.\nНевозможно провести расчет.\n'.format(name,self.date_end__[0])
                                # msg = self.msgBox.information(self, 'Information', msg_st)
                            else:
                                amount = 1
                                contl_id.append(sqlContr.value(0))
                                self.dNameDay[name] = amount
                                amount+=1
                                while sqlContr.size():
                                    sqlContr.next()
                                    if sqlContr.value(0) == None:
                                        break
                                    else:
                                        contl_id.append(sqlContr.value(0))
                                        self.dNameDay[name] = amount
                                        amount+=1
                                sum_m = 0
                                sum_d = 0
                                for mi in contl_id:
                                    sum_m = sum_m + mi
                                mat_o = round(sum_m/len(contl_id),6)
                                for mi in contl_id:
                                    sum_d = sum_d + (mat_o - mi)**2
                                disp = round(sum_d/len(contl_id),6)
                                max_f = max(contl_id)
                                min_f = min(contl_id)
                                self.razmah = round(max_f-min_f,6)
                                self.m_root.tableWidget.insertRow(self.m_root.tableWidget.rowCount())
                                self.m_root.tableWidget.setItem(numd_row,0,QTableWidgetItem(name))
                                self.m_root.tableWidget.setItem(numd_row,1,QTableWidgetItem(str(mat_o)))
                                self.m_root.tableWidget.setItem(numd_row, 2, QTableWidgetItem(str(disp)))
                                self.m_root.tableWidget.setItem(numd_row, 3, QTableWidgetItem(str(self.razmah)))
                                numd_row+=1


                        if not len(self.msg_st) == 0:
                              msg = self.msgBox.information(self, 'Information', self.msg_st)

                        self.marketTable.setFilter('')
                        self.dNameDay_fi = {k: v for k, v in self.dNameDay.items() if v == max(self.dNameDay.values())}
                        print(self.dNameDay_fi)

                        if len(self.dNameDay_fi) > 1:
                            self.selection_fut = Dictribut_law(self.marketTable)
                            for name in self.dNameDay_fi.keys():
                                self.selection_fut.d_root.comboBox.addItem(name)
                            self.selection_fut.d_root.pushButton.clicked.connect(self.click_name)
                        else:
                            name_key = iter(self.dNameDay_fi.keys())
                            self.name_dis_la = next(name_key)
                            cont_str = "SELECT contrl_id FROM market WHERE name = '{0}' AND torg_date BETWEEN '{1}' and '{2}' " \
                                       "AND NOT torg_date = '{3}'".format(self.name_dis_la, self.start_d, self.end_d,
                                                                          self.end_d)
                            zapros = QSqlQuery(cont_str)
                            self.contr_law = []
                            while zapros.next():
                                self.contr_law.append(zapros.value(0))
                            if len(self.contr_law) > 0:
                                data1 = [float(item) for item in self.contr_law]
                                alpha = 0.05
                                plt.hist(data1, density=True, edgecolor='black', bins=20)
                                plt.savefig("histogram_normal_law.png", bbox_inches='tight', dpi=60)
                                self.m_root.label_10.setPixmap(QtGui.QPixmap("histogram_normal_law.png"))
                                stat1, p1 = kstest(data1, 'norm')
                                if p1 > alpha:
                                    self.res1_txt = 'Принять гипотезу о нормальности'

                                else:
                                    self.res1_txt = 'Отклонить гипотезу о нормальности'
                                self.res = [stat1, p1, self.res1_txt]
                                res1 = 'Значение статистики = %.3f, p-value = %.3f' % (self.res[0], self.res[1])
                                resulna = 'Для фьючерса {0}.'.format(self.name_dis_la)
                                self.m_root.label_11.setText(resulna)
                                self.m_root.label_8.setText(res1)
                                self.m_root.label_9.setText(self.res1_txt)
                                plt.clf()
                else:
                    while self.m_root.tableWidget.rowCount() > 0:
                        self.m_root.tableWidget.removeRow(0)
                    self.m_root.label_4.clear()
                    self.m_root.label_9.clear()
                    self.m_root.label_8.clear()
                    self.m_root.label_11.clear()
                    self.m_root.label_10.clear()
                    self.m_root.textEdit.clear()
                    self.m_root.textEdit_2.clear()
                    # plt.clf()
            else:
                self.msgBox.warning(self, 'Warning', self.msg_box_text)

    def click_name(self):
        self.name_dis_la = self.selection_fut.d_root.comboBox.currentText()
        cont_str = "SELECT contrl_id FROM market WHERE name = '{0}' AND torg_date BETWEEN '{1}' and '{2}' " \
                   "AND NOT torg_date = '{3}'".format(self.name_dis_la, self.start_d, self.end_d, self.end_d)
        zapros = QSqlQuery(cont_str)
        self.contr_law = []
        while zapros.next():
            self.contr_law.append(zapros.value(0))
        if len(self.contr_law) > 0:
            data1 = [float(item) for item in self.contr_law]
            alpha = 0.05
            plt.hist(data1, density=True, edgecolor='black', bins=20)
            plt.savefig("histogram_normal_law.png",bbox_inches = 'tight',dpi = 60)
            self.m_root.label_10.setPixmap(QtGui.QPixmap("histogram_normal_law.png"))
            stat1, p1 = kstest(data1, 'norm')
            if p1 > alpha:
                self.res1_txt = 'Принять гипотезу о нормальности'

            else:
                self.res1_txt = 'Отклонить гипотезу о нормальности'
            self.res = [stat1, p1, self.res1_txt]
            res1 = 'Значение статистики = %.3f, p-value = %.3f' % (self.res[0], self.res[1])
            resulna='Для фьючерса {0}.'.format(self.name_dis_la)
            self.m_root.label_11.setText(resulna)
            self.m_root.label_8.setText(res1)
            self.m_root.label_9.setText(self.res1_txt)
            plt.clf()
            self.selection_fut.d.close()

    def date_for_user(self, date_input):

        format_input = '%Y-%m-%d'
        format_output = '%d.%m.%Y'

        date = datetime.strptime(date_input, format_input)
        date_output = date.strftime(format_output)

        return date_output

    def export_excel_stat_char(self):
        rows = self.m_root.tableWidget.rowCount()
        if not rows:
            msg = QMessageBox.information(self, 'Information', 'Нечего сохранять.')
            return
        path, _ = QFileDialog.getSaveFileName(self, 'Save Excel', '.', 'Excel(*.xlsx)')
        if not path:
            msg = QMessageBox.information(self, 'Information', 'Не указан файл для сохранения.')
            return
        columnHeaders = []
        for j in range(self.m_root.tableWidget.model().columnCount()):
            columnHeaders.append(self.m_root.tableWidget.horizontalHeaderItem(j).text())
        df = pd.DataFrame()
        info = ['Дата формирования', 'Имя таблицы','Значение даты "от"', 'Значение даты "до"','Имя фьючерса для гипотезы',
                'Значение статистики','p-value','Решение']
        document = []
        dataUs = date.today()
        document.append(self.date_for_user(str(dataUs)))
        document.append('Расчеты')
        document.append(self.date_start__[0])
        document.append(self.date_end__[0])
        document.append(self.name_dis_la)
        document.append(round(self.res[0],6))
        document.append(round(self.res[1],6))
        document.append(self.res1_txt)
        for polosa in range(1):
            for inf in range(len(info)):
                df.at[polosa, info[inf]] = document[inf]
        df1 = pd.DataFrame()
        for row in range(rows):
            for col in range(self.m_root.tableWidget.columnCount()):
                df1.at[row, columnHeaders[col]] = self.m_root.tableWidget.item(row, col).text()
        with ExcelWriter(path) as writer:
            df.to_excel(writer, sheet_name='Отчетность', index=False)
            df1.to_excel(writer, sheet_name='Данные', index=False)

        msg = QMessageBox.information(self, 'Information', 'Отчет сформирован.\nГистограмма сохранена в рабочем каталоге с именем "histogram_normal_law.png"')

class App(QWidget):
    def __init__(self):
        super().__init__()
        self.flag_market = True
        self.flag_struc = True
        self.flag_market2 = True
        self.w = QtWidgets.QMainWindow()
        self.w_root = Ui_MainWindow()
        self.w_root.setupUi(self.w)
        # self.dialog = EditMarket() #наследуем класс
        self.db = connect_db(db_name)
        self.market = ModelMarket(self.db)
        self.struc_fu = ModelStruc_fut(self.db)
        self.msgBox = QMessageBox()
        self.w_root.tableView.allowsMultipleSelection = False

        self.w.setWindowFlags(QtCore.Qt.WindowType.WindowCloseButtonHint | QtCore.Qt.WindowType.MSWindowsFixedSizeDialogHint)

        self.select_table(0)


        self.w_root.pushButton_2.setEnabled(False)
        self.w_root.pushButton_5.setEnabled(False)
        self.w_root.tableView.setEditTriggers(QtWidgets.QTableView.EditTrigger.NoEditTriggers)
        self.w_root.tableView.selectionModel().selectionChanged.connect(self.activation_button)
        self.w_root.pushButton_2.clicked.connect(self.delete_row)
        self.w_root.comboBox.activated.connect(self.select_table)
        self.w_root.pushButton_4.clicked.connect(self.open_edit_market)
        self.w_root.pushButton_5.clicked.connect(self.open_record_market)
        self.w_root.pushButton_6.clicked.connect(self.open_filter)
        self.w_root.pushButton_7.clicked.connect(self.unfilter)
        self.w_root.pushButton_9.clicked.connect(self.open_stat_shar)
        self.w_root.pushButton_3.clicked.connect(self.exportToExcel)

        if self.market.index(0,9).data() == None:
            lName_futuressql = QSqlQuery(f"""SELECT name from struc_futures""")
            kod_fu = []
            lName_futuressql.first()
            kod_fu.append(lName_futuressql.value(0))
            while lName_futuressql.size():
                lName_futuressql.next()
                if lName_futuressql.value(0) == None:
                    break
                else: kod_fu.append(lName_futuressql.value(0))
            lDate_futuressql = QSqlQuery(f"""SELECT exec_date from struc_futures""")
            dStruc_fu = {}
            lDate_futuressql.first()
            dStruc_fu[kod_fu[0]]= lDate_futuressql.value(0)
            for name in kod_fu[1:]:
                lDate_futuressql.next()
                dStruc_fu[name] = lDate_futuressql.value(0)
            self.w_root.tableView.horizontalHeader().setSortIndicator(3, QtCore.Qt.SortOrder.AscendingOrder)
            list = []

            for name in dStruc_fu.keys():
                val_fil = "name = '{}'".format(name)
                # print(val_fil)
                self.market.setFilter(val_fil)
                format_bd = '%Y-%m-%d'
                self.w_root.tableView.horizontalHeader().setSortIndicator(3, QtCore.Qt.SortOrder.AscendingOrder)
                for i in range(self.market.rowCount(self.w_root.tableView.rootIndex())):
                    Fk_2=0
                    Fk = float(self.market.index(i,5).data())
                    day_end = self.market.index(i,4).data()
                    if self.market.index(i-2,4).data() == None or not Fk:
                        xk=0
                    else:
                        Fk_2 = float(self.market.index(i-2,5).data())
                        if not Fk_2:
                            xk = 0
                        else:
                            day_end_2 = self.market.index(i-2, 4).data()
                            deffe_date = datetime.strptime(dStruc_fu[name],format_bd) - datetime.strptime(day_end,format_bd)
                            rk = math.log(abs(Fk/100))/abs((deffe_date.days+1))
                            deffe_data_2= datetime.strptime(dStruc_fu[name],format_bd) - datetime.strptime(day_end_2,format_bd)
                            rk_2 = math.log(abs(Fk_2/100))/abs((deffe_data_2.days+1))
                            xk = round(abs(math.log(abs(rk/rk_2))),6)
                    record = self.market.record(i)
                    record.setValue('contrl_id', xk)
                    self.market.setRecord(i,record)
                    self.market.select()
            self.market.setFilter("")
                    # print (xk)

        self.w.show()

    def date_for_user(self, date_input):

        format_input = '%Y-%m-%d'
        format_output = '%d.%m.%Y'

        date = datetime.strptime(date_input, format_input)
        date_output = date.strftime(format_output)

        return date_output

    def exportToExcel(self):
        if self.w_root.comboBox.currentIndex() == 0:
            rows = self.market.rowCount()
            if not rows:
                msg = QMessageBox.information(self, 'Information', 'Нечего сохранять.')
                return
            while self.market.canFetchMore():
                self.market.fetchMore()
            r = self.market.rowCount()
            path, _ = QFileDialog.getSaveFileName(self, 'Save Excel', '.', 'Excel(*.xlsx)')
            if not path:
                msg = QMessageBox.information(self, 'Information', 'Не указан файл для сохранения.')
                return
            columnHeaders = []
            for j in range(self.market.columnCount()):
                if not j == 3 and not j == 4:
                    if j == 9:
                        columnHeaders.append('Основной показатель')
                    else:
                        columnHeaders.append(self.market.headerData(j, QtCore.Qt.Orientation.Horizontal,
                                                            QtCore.Qt.ItemDataRole.DisplayRole))
            df = pd.DataFrame()
            info = ['Дата формирования','Имя таблицы','Фильтр имени','Фильтр даты "от"','Фильтр даты "до"','Фильтр цены "от"','Фильтр цены "до"']
            document = []
            dataUs = date.today()
            document.append(self.date_for_user(str(dataUs)))
            document.append('Торги')
            filter = self.get_filter(self.market.filter())
            val = 'None'
            if len(filter) == 0:
                for i in range(5): document.append(val)
            if len(filter) == 1:
                document.append(filter[0])
                for i in range(4): document.append(val)
            if len(filter) >1:
                if len(filter) == 5:
                    document.append(filter[0])
                    document.append(self.date_for_user(filter[3]))
                    document.append(self.date_for_user(filter[4]))
                    document.append(filter[1])
                    document.append(filter[2])
                else:
                    if filter[1].find('.') != -1:
                        document.append(filter[0])
                        for i in range(2): document.append(val)
                        document.append(filter[1])
                        document.append(filter[2])
                    else:
                        document.append(filter[0])
                        document.append(self.date_for_user(filter[1]))
                        document.append(self.date_for_user(filter[2]))
                        for i in range(2): document.append(val)

            for polosa in range(1):
                for inf in range(len(info)):
                    df.at[polosa, info[inf]] = document[inf]
            df1 = pd.DataFrame()
            for row in range(r):
                i = 0
                for col in range(self.market.columnCount()):
                    if not col == 3 and not col == 4:
                        df1.at[row, columnHeaders[i]] = self.market.index(row, col).data()
                        i+=1
            with ExcelWriter(path) as writer:
                df.to_excel(writer, sheet_name='Отчетность',index=False)
                df1.to_excel(writer, sheet_name='Данные', index= False)

            msg = QMessageBox.information(self, 'Information', 'Отчет сформирован')
        if self.w_root.comboBox.currentIndex() == 1:
            rows = self.struc_fu.rowCount()
            if not rows:
                msg = QMessageBox.information(self, 'Information', 'Нечего сохранять.')
                return
            r = self.struc_fu.rowCount()
            path, _ = QFileDialog.getSaveFileName(self, 'Save Excel', '.', 'Excel(*.xlsx)')
            if not path:
                msg = QMessageBox.information(self, 'Information', 'Не указан файл для сохранения.')
                return
            columnHeaders = []
            for j in range(self.struc_fu.columnCount()):
                if not j == 3:
                    columnHeaders.append(self.struc_fu.headerData(j, QtCore.Qt.Orientation.Horizontal,
                                                                    QtCore.Qt.ItemDataRole.DisplayRole))
            df = pd.DataFrame()
            info = ['Дата формирования', 'Имя таблицы']
            document = []
            dataUs = date.today()
            document.append(self.date_for_user(str(dataUs)))
            document.append('Фьючесры')
            for polosa in range(1):
                for inf in range(len(info)):
                    df.at[polosa, info[inf]] = document[inf]
            df1 = pd.DataFrame()
            for row in range(r):
                i = 0
                for col in range(self.struc_fu.columnCount()):
                    if not col == 3:
                        df1.at[row, columnHeaders[i]] = self.struc_fu.index(row, col).data()
                        i += 1
            with ExcelWriter(path) as writer:
                df.to_excel(writer, sheet_name='Отчетность', index=False)
                df1.to_excel(writer, sheet_name='Данные', index=False)

            msg = QMessageBox.information(self, 'Information', 'Отчет сформирован')

    def get_filter(self, s):
        l = len(s)
        list_filt = []
        i = 0
        while i < l:
            row_filter = ''
            a = s[i]
            while '0' <= a <= '9' or a == '.' or a == '-':
                row_filter += a
                i += 1
                if i < l:
                    a = s[i]
                else:
                    break
            i += 1
            if row_filter != '':
                list_filt.append(row_filter)
        return list_filt

    def unfilter(self):
        self.market.setFilter("")

    def open_filter(self):
        self.filter_market = Filter(self.market, self.struc_fu, self.w_root.tableView)
        self.filter_market.see_filter()

    def open_record_market(self):
        self.record_market = Record(self.market, self.struc_fu, self.w_root.tableView)

    def open_edit_market(self):
        self.dialog_market = EditMarket(self.market, self.struc_fu, self.w_root.tableView)

    def open_stat_shar(self):
        self.stat_shar = Stat_shar(self.market,self.w_root.tableView)

    def select_table (self, value):
        # if self.w_root.comboBox.currentIndex() == 0:
        if not value:
            self.w_root.tableView.setModel(self.market)
            header_lables_market = ["Код фьючерса", "Дата торгов", "Дата погашения", "Текущая цена", "Мин. цена", "Макс. цена",
                                    "Продано"]
            columns_market = [0, 1, 2, 5, 6, 7, 8]
            i=0
            for header in header_lables_market:
                self.market.setHeaderData(columns_market[i], QtCore.Qt.Orientation.Horizontal, header)
                i+=1
            self.w_root.tableView.setGeometry(QtCore.QRect(50, 150, 750, 451))
            self.w_root.tableView.setFixedWidth(750)
            self.w_root.tableView.setEditTriggers(QtWidgets.QTableView.EditTrigger.AllEditTriggers)
            self.w_root.tableView.setEditTriggers(QtWidgets.QTableView.EditTrigger.NoEditTriggers)
            self.w_root.pushButton_2.setEnabled(False)
            self.w_root.pushButton_5.setEnabled(False)
            self.w_root.pushButton_4.setEnabled(True)
            self.w_root.pushButton_6.setEnabled(True)
            self.w_root.pushButton_7.setEnabled(True)
            self.w_root.pushButton_8.setEnabled(True)
            self.w_root.pushButton_9.setEnabled(True)
            self.w_root.tableView.selectionModel().selectionChanged.connect(self.activation_button)
            self.w_root.pushButton_8.clicked.connect(self.contrl_id)
        # if self.w_root.comboBox.currentIndex() == 1:
        if value:
            self.w_root.tableView.setModel(self.struc_fu)
            header_lables_struc_futures = ["Код фьючерса", "Код серии", "Дата исполнения"]
            columns_struc_futures = [0, 1, 2]
            i=0
            for header in header_lables_struc_futures:
                self.struc_fu.setHeaderData(columns_struc_futures[i], QtCore.Qt.Orientation.Horizontal, header)
                i+=1
            self.w_root.tableView.setGeometry(QtCore.QRect(245, 150, 360, 451))
            self.w_root.tableView.setFixedWidth(350)
            self.w_root.tableView.setEditTriggers(QtWidgets.QTableView.EditTrigger.NoEditTriggers)
            self.w_root.pushButton_2.setEnabled(False)
            self.w_root.pushButton_4.setEnabled(False)
            self.w_root.pushButton_5.setEnabled(False)
            self.w_root.pushButton_6.setEnabled(False)
            self.w_root.pushButton_7.setEnabled(False)
            self.w_root.pushButton_8.setEnabled(False)
            self.w_root.pushButton_9.setEnabled(False)
            # self.w_root.tableView.horizontalHeader().sectionClicked.connect(self.sorting_strucFu)
            self.w_root.tableView.selectionModel().selectionChanged.connect(self.activation_button)
        self.w_root.tableView.setSortingEnabled(True)
        self.w_root.tableView.horizontalHeader().sectionClicked.connect(self.sorting_market)
        columns_to_hide = [3, 4,9]
        for number in columns_to_hide:
            self.w_root.tableView.hideColumn(number)

    def sorting_market(self, index):
        if self.w_root.comboBox.currentIndex() == 0:
            self.flag_market = not self.flag_market
            if index == 1:
                if self.flag_market:
                    self.w_root.tableView.sortByColumn(3, QtCore.Qt.SortOrder.AscendingOrder)
                else:
                    self.w_root.tableView.sortByColumn(3, QtCore.Qt.SortOrder.DescendingOrder)
            self.flag_market2 = not self.flag_market2
            if index == 2:
                if self.flag_market2:
                    self.w_root.tableView.sortByColumn(4, QtCore.Qt.SortOrder.AscendingOrder)
                else:
                    self.w_root.tableView.sortByColumn(4, QtCore.Qt.SortOrder.DescendingOrder)
        if self.w_root.comboBox.currentIndex() == 1:
            # self.flag_struc = not self.flag_struc
            if index == 2:
                # if self.flag_struc:
                self.w_root.tableView.sortByColumn(3, QtCore.Qt.SortOrder.AscendingOrder)
                # else:
                #     self.w_root.tableView.sortByColumn(3,QtCore.Qt.SortOrder.DescendingOrder)

    def contrl_id(self):
        self.w_root.tableView.showColumn(9)
        self.market.setHeaderData(9, QtCore.Qt.Orientation.Horizontal, 'Основной\nпоказатель')
        self.w_root.tableView.setGeometry(QtCore.QRect(0, 150, 855, 451))
        self.w_root.tableView.setFixedWidth(855)

    def activation_button(self):
        if self.w_root.tableView.selectionModel().selectedRows():
            self.w_root.pushButton_2.setEnabled(True)
        else:
            self.w_root.pushButton_2.setEnabled(False)
            self.w_root.pushButton_5.setEnabled(False)
        if not self.w_root.comboBox.currentIndex():
            if self.w_root.tableView.selectionModel().selectedRows():
                self.w_root.pushButton_5.setEnabled(True)
            else:
                self.w_root.pushButton_5.setEnabled(False)

    def delete_row(self):
        if not self.w_root.comboBox.currentIndex():
            index = self.w_root.tableView.currentIndex().row()
            msb_box_text = "Вы действительно хотите удалить выбранную запись?\nНомер выбранной строки: {}".format(index+1)
            warning = self.msgBox.question(self, "Warning", msb_box_text)
            self.name_fut = ''
            if warning == self.msgBox.StandardButton.Yes:
                self.name_fut = self.market.index(index,0).data()
                self.market.removeRow(index)
                self.market.select()
                print(self.name_fut)
                recalculation_of_the_main_indicator(sqltablemark=self.market, sqltablestruc=self.struc_fu,
                                                    window=self.w_root.tableView,
                                                    name_fu=self.name_fut,filter=self.market.filter())
        if self.w_root.comboBox.currentIndex():
            index = self.w_root.tableView.currentIndex().row()
            msb_box_text = "Вы действительно хотите удалить выбранную запись?\nНомер выбранной строки: {}\nВсе записи, содержащие информацию по данному фьючерсу, будут так же удалены из таблицы торги.".format(index + 1)
            warning_1 = self.msgBox.question(self, "Warning",  msb_box_text)
            if warning_1 == self.msgBox.StandardButton.Yes:
                self.name_list= self.struc_fu.index(index,0).data()
                self.struc_fu.removeRow(index)
                self.struc_fu.select()
                self.sql = """DELETE FROM market WHERE name='{0}'""".format(self.name_list)
                QSqlQuery(self.sql)
                self.market.select()
                print(self.name_list)

        self.w_root.pushButton_2.setEnabled(False)

app = QApplication(sys.argv)
ex = App()
app.exec()
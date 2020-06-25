from PyQt5.QtWidgets import QApplication, QMainWindow, QTableWidgetItem, QTableView, QAbstractItemView
from PyQt5.QtCore import QThread, pyqtSignal, QDateTime, QObject, QRegExp
from PyQt5.QtGui import *

import win10toast
import sys
import time
import datetime
from playhouse.shortcuts import model_to_dict

from ui import Ui_MainWindow
from event_model import *

event_content = []


class Main_backend(QThread):
    update_html = pyqtSignal(str)
    update_date = pyqtSignal(QDateTime)

    color_flag = True
    content = []

    start_color = (255, 0, 0)
    start_size = (22, 18)
    blink_color = (237, 174, 73)
    end_color = (32, 129, 195)
    end_size = (15, 11)
    duration = (3600, 39600)

    def construct_html(self):
        def style_construct(font_size, color, font_family, content):
            html = '''<span style="font-size:%dpx;color:%s;font-family:'%s';"> %s<br/></span>
            <span style="font-size:%dpx;color:%s;font-family:'%s';">%s<br/></span></span>
            <span style="font-size:2px"> <br/></span>''' \
                   % (font_size[0], color, font_family, content[0][:15], font_size[1], color, font_family, content[1])
            return html

        def color_translate(color):
            s = '#'
            for each in color:
                s += hex(each)[2:] + '0' * (2 - len(hex(each)[2:]))
            return s

        html = \
            '''<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.0//EN" "http://www.w3.org/TR/REC-html40/strict.dtd">
<html>
    <head>
        <meta name="qrichtext" content="1" />
        <style type="text/css">
            p, li { white-space: pre-wrap; }
        </style>
    </head>
    <body>
'''
        for each in self.content:
            if each['countdown'] < 0:
                each['countdown'] *= -1
                content = [each['title'], '+']
                k = 0.8
            else:
                content = [each['title'], '-']
                if each['countdown'] < self.duration[0]:
                    k = 0
                elif each['countdown'] > self.duration[1]:
                    k = 1
                else:
                    k = (each['countdown'] - self.duration[0]) / (self.duration[1] - self.duration[0])
            font_size = [int(self.start_size[0] - k * (self.start_size[0]-self.end_size[0])),
                         int(self.start_size[1] - k * (self.start_size[1]-self.end_size[1]))]
            color = color_translate([int(self.start_color[0] - k * (self.start_color[0]-self.end_color[0])),
                                     int(self.start_color[1] - k * (self.start_color[1]-self.end_color[1])),
                                     int(self.start_color[2] - k * (self.start_color[2]-self.end_color[2]))])
            if k == 0 and self.color_flag:
                color = color_translate(self.blink_color)
            content[1] += str(each['countdown'] // 86400) + '天'
            content[1] += str(each['countdown'] % 86400 // 3600) + '时'
            content[1] += str(each['countdown'] % 3600 // 60) + '分'
            content[1] += str(each['countdown'] % 60) + '秒'
            html += style_construct(font_size, color, '楷体', content)
        html += \
        '''</body>
</html>'''
        self.update_html.emit(html)

    def calculate(self):
        self.content = []
        for each in event_content:
            self.content.append(each)
            self.content[-1]['ori_id'] = event_content.index(each)
            cal_time = datetime.datetime.strptime(each['start_time'], '%Y-%m-%d %H:%M:%S')
            if each['end_time'] == '':
                end = datetime.datetime.strptime('9999-12-31', '%Y-%m-%d')
            else:
                end = datetime.datetime.strptime(each['end_time'], '%Y-%m-%d')
            try:
                tmp = list(map(int, each['duration'].split(':')))
                dutation_time = datetime.timedelta(hours=tmp[0], minutes=tmp[1], seconds=tmp[2])
            except:
                dutation_time = datetime.timedelta(hours=1)
            while cal_time < datetime.datetime.now() - dutation_time and cal_time < end and each['is_loop'] != 'N':
                if each['is_loop'] == 'D':
                    cal_time += datetime.timedelta(days=1)
                elif each['is_loop'] == 'W':
                    cal_time += datetime.timedelta(weeks=1)
            self.content[-1]['countdown'] = cal_time - datetime.datetime.now()
            self.content[-1]['countdown'] = \
                self.content[-1]['countdown'].days * 86400 + self.content[-1]['countdown'].seconds
        self.content.sort(key=lambda item: item['countdown'])

    def run(self):
        while True:
            try:
                # print(event_content)
                self.calculate()
                self.construct_html()
                self.update_date.emit(QDateTime.currentDateTime())
                self.color_flag = not self.color_flag
                time.sleep(1)
            except Exception as e:
                print(e)


class Main_ui(QMainWindow, Ui_MainWindow):
    row_count = 0
    select_item = None
    loop_stat = 'N'
    end_stat = 'N'

    def table_resolver(self, data):
        loop_remapper = {'N': '不循环', 'D': '每日', 'W': '每周', 'M': '每月', 'Y': '每年'}
        result = [
            data.id,
            data.title,
            data.start_time,
            loop_remapper[data.is_loop]
        ]
        if data.end_time == '':
            result.append('不终止')
        else:
            result.append(data.end_time)
        result.append(data.duration)
        return result

    def load_table(self):
        cursor = Events.select()
        self.row_count = len(cursor)
        self.Data_Table.setRowCount(self.row_count)
        for row in range(self.row_count):
            event_content.append(model_to_dict(cursor[row]))
            data = self.table_resolver(cursor[row])
            for col in range(len(data)):
                one = QTableWidgetItem(str(data[col]))
                self.Data_Table.setItem(row, col, one)

    def init_Inputfield(self):
        self.Input_Title.setText('')
        self.Input_Times.setText('1')
        self.End_Ctrl_Never.setChecked(True)
        self.Loop_Ctrl_Never.setChecked(True)
        self.Input_Startdate.setDateTime(QDateTime.currentDateTime())

    def init_interface(self):
        self.Input_Times.setValidator(QRegExpValidator(QRegExp('[0-9]+$'), self))

        self.Data_Table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.Data_Table.setEditTriggers(QTableView.NoEditTriggers)
        self.Data_Table.setColumnCount(6)
        self.Data_Table.setHorizontalHeaderLabels(['id', '标题', '开始时间', '循环', '终止时间', '持续时间'])
        self.Data_Table.verticalHeader().setVisible(False)
        self.Data_Table.setColumnWidth(0, 20)
        self.Data_Table.setColumnWidth(1, 110)
        self.Data_Table.setColumnWidth(2, 110)
        self.Data_Table.setColumnWidth(3, 30)
        self.Data_Table.setColumnWidth(4, 110)

        self.input_date_update(QDateTime.currentDateTime())
        self.load_table()

    def input_date_update(self, data):
        self.Input_Startdate.setMinimumDateTime(data)

    def input_date_change_event(self):
        self.Input_Enddate.setMinimumDate(self.Input_Startdate.date())

    def duration_check_event(self):
        self.Input_Duration_hours.setEnabled(self.Duration_Ctrl.isChecked())
        self.Input_Duration_minutes.setEnabled(self.Duration_Ctrl.isChecked())
        self.Input_Duration_seconds.setEnabled(self.Duration_Ctrl.isChecked())

    def table_select_event(self, data):
        self.select_item = (int(self.Data_Table.item(data.row(), 0).text()), data.row())
        self.FN0_Delete.setEnabled(True)
        # self.FN1_Modify.setEnabled(True)

    def fn_delitem(self):
        event_content.pop(self.select_item[1])
        Events.delete().where(Events.id == self.select_item[0]).execute()
        self.Data_Table.removeRow(self.select_item[1])
        self.row_count -= 1
        self.Data_Table.setRowCount(self.row_count)
        self.select_item = None
        self.FN1_Modify.setEnabled(False)
        self.FN0_Delete.setEnabled(False)

    def fn_modifyitem(self):
        self.Input_Title.setText(event_content[self.select_item[1]]['title'])

    def fn_additem(self):
        title = self.Input_Title.text()
        start_time = self.Input_Startdate.dateTime().toString("yyyy-MM-dd HH:mm:ss")
        end_time = ''
        if self.end_stat == 'T':
            times = int(self.Input_Times.text())
            end_time = self.Input_Startdate.dateTime()
            if self.loop_stat == 'D':
                end_time = end_time.addDays(times)
            elif self.loop_stat == 'W':
                end_time = end_time.addDays(times * 7)
            elif self.loop_stat == 'M':
                end_time = end_time.addMonths(times)
            elif self.loop_stat == 'Y':
                end_time = end_time.addYears(times)
            end_time = end_time.toString("yyyy-MM-dd")
        elif self.end_stat == 'D':
            end_time = self.Input_Enddate.dateTime().toString("yyyy-MM-dd")
        if self.Duration_Ctrl.isChecked():
            duration = '%s:%s:%s' % (
                self.Input_Duration_hours.text().zfill(2),
                self.Input_Duration_minutes.text().zfill(2),
                self.Input_Duration_seconds.text().zfill(2)
            )
        else:
            duration = ''
        event = Events(title=title, start_time=start_time, is_loop=self.loop_stat, end_time=end_time, duration=duration)
        event.save()
        event_content.append(model_to_dict(event))
        self.row_count += 1
        self.Data_Table.setRowCount(self.row_count)
        data = self.table_resolver(event)
        for col in range(len(data)):
            one = QTableWidgetItem(str(data[col]))
            self.Data_Table.setItem(self.row_count - 1, col, one)
        self.init_Inputfield()

    def loop_ctrl_enable(self, data):
        self.loop_stat = data
        if data == 'N':
            self.End_Ctrl_date.setEnabled(False)
            self.End_Ctrl_Never.setEnabled(False)
            self.End_Ctrl_Times.setEnabled(False)
            self.end_ctrl_enable('N')
        else:
            self.End_Ctrl_date.setEnabled(True)
            self.End_Ctrl_Never.setEnabled(True)
            self.End_Ctrl_Times.setEnabled(True)

    def end_ctrl_enable(self, data):
        self.end_stat = data
        if data == 'N':
            self.Input_Times.setEnabled(False)
            self.Input_Enddate.setEnabled(False)
        elif data == 'T':
            self.Input_Times.setEnabled(True)
            self.Input_Enddate.setEnabled(False)
        else:
            self.Input_Times.setEnabled(False)
            self.input_date_change_event()
            self.Input_Enddate.setEnabled(True)

    def html_updater(self, data):
        self.Result_View.setText(data)

    def __init__(self, parent=None):
        super(Main_ui, self).__init__(parent)
        self.setupUi(self)

        self.Loop_Ctrl_Never.toggled.connect(lambda: self.loop_ctrl_enable('N'))
        self.Loop_Ctrl_Day.toggled.connect(lambda: self.loop_ctrl_enable('D'))
        self.Loop_Ctrl_Month.toggled.connect(lambda: self.loop_ctrl_enable('M'))
        self.Loop_Ctrl_Week.toggled.connect(lambda: self.loop_ctrl_enable('W'))
        self.Loop_Ctrl_Year.toggled.connect(lambda: self.loop_ctrl_enable('Y'))

        self.End_Ctrl_Times.toggled.connect(lambda: self.end_ctrl_enable('T'))
        self.End_Ctrl_Never.toggled.connect(lambda: self.end_ctrl_enable('N'))
        self.End_Ctrl_date.toggled.connect(lambda: self.end_ctrl_enable('D'))

        self.Input_Startdate.dateChanged.connect(self.input_date_change_event)
        self.Duration_Ctrl.stateChanged.connect(self.duration_check_event)
        self.Data_Table.itemClicked.connect(self.table_select_event)

        self.FN2_Add.clicked.connect(self.fn_additem)
        self.FN1_Modify.clicked.connect(self.fn_modifyitem)
        self.FN0_Delete.clicked.connect(self.fn_delitem)

        self.init_interface()

        self.main_backend = Main_backend()
        self.main_backend.update_date.connect(self.input_date_update)
        self.main_backend.update_html.connect(self.html_updater)
        self.main_backend.start()


def run():
    try:
        db.connect()
    except Exception as e:
        print(e)
    app = QApplication(sys.argv)
    main_window = Main_ui()
    main_window.show()
    sys.exit(app.exec())


if __name__ == '__main__':
    run()

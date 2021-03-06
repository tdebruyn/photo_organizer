from PySide2.QtCore import QThread, QObject, Signal, Slot, Qt, QSize, QUrl
from PySide2.QtWidgets import (QApplication, QWidget, QPushButton,
                             QRadioButton, QVBoxLayout, QLineEdit, QSlider,
                             QLabel, QHBoxLayout, QFileDialog, QGroupBox, QSizePolicy)
from PySide2 import QtCore
from send2trash import send2trash
from PySide2.QtGui import QDesktopServices, QPixmap, QPixmapCache, QImageReader
import sys
from pathlib import Path
from dataclasses import dataclass
from pkg_resources import resource_filename
from datetime import datetime
deleted_picture = resource_filename(__name__, 'bitmaps/deleted-picture.png')


@dataclass
class image(object):
    path: Path
    date: datetime = datetime.fromtimestamp(0)
    new_path: Path = None
    size: QSize = QSize(0, 0)
    to_delete: bool = False
    deleted: bool = False

class CacheMgr(QObject):
    def __init__(self, image_names):
        super().__init__()
        self.image_names = image_names
        self.update_cache(0)

    @Slot(int)
    def update_cache(self, position):
        pm = QPixmap()

        for pos in range(max(position - 2, 0), min(position + 2, len(self.image_names))):
            cur_img_name = str(self.image_names[pos].path)
            if not QPixmapCache.find(cur_img_name):
                reader = QImageReader(cur_img_name)
                self.image_names[pos].size = reader.size()
                reader.setAutoTransform(True)
                pm = QPixmap.fromImageReader(reader)
                QPixmapCache.insert(cur_img_name, pm)


class CommitMgr(QObject):
    def __init__(self, image_names):
        super().__init__()
        self.image_names = image_names

    @Slot(list)
    def update_images_names(self, image_names):
        self.image_names = image_names


class DirCrawler(QObject):
    new_image_signal = Signal(image)
    finished_signal = Signal()

    def __init__(self, root_dir):
        super().__init__()
        self.root_dir = root_dir
        self.running = True

    def crawl(self):
        for ext in ('*.PNG', '*.png', '*.jpg', '*.JPG', '*.jpeg', '*.JPEG'):
            for path in self.root_dir.rglob(ext):
                self.new_image_signal.emit(image(path))
                if self.running == False:
                    exit()

        self.finished_signal.emit()

class AppWindow(QWidget):
    update_cache_signal = Signal(int)

    def __init__(self):
        super().__init__()
        self.images = []
        self.current_image = 0

        self.build_UI()
        self.init_crawling()

        self.cache_mgr = CacheMgr(self.images)

        self.cache_thread = QThread()
        self.cache_thread.started.connect(self.cache_mgr.update_cache)
        self.update_cache_signal.connect(self.cache_mgr.update_cache)
        self.cache_mgr.moveToThread(self.cache_thread)
        self.cache_thread.start()
        self.showFullScreen()

    def build_UI(self):
        self.setWindowFlags(QtCore.Qt.FramelessWindowHint | QtCore.Qt.WindowStaysOnTopHint)
        self.setStyleSheet("QWidget{background-color: rgb(100,100,100)}")

        # app title
        title = QLabel(self)
        title.setStyleSheet("color: rgb(170, 200, 255);"
                            "font: 40px;")
        title.setText("Photos Organizer")
        title.openExternalLinks()

        # current file name
        self.fnlbl = QLabel(self)
        self.fnlbl.setStyleSheet("font: 20px;")

        self.lbl2 = QLabel(self)
        self.lbl2.setStyleSheet("color: rgb(170, 200, 255);"
                               "font: 14px;")

        # new name text box
        self.new_name = QLineEdit()
        self.new_name.setStyleSheet("font: 20px;")
        self.new_name.setPlaceholderText("Enter new name, min 3 chars, \"del\" to delete picture")
        self.new_name.returnPressed.connect(self.rename_pict)

        self.new_dir = QLineEdit()
        self.new_dir.setStyleSheet("font: 20px;")
        self.new_dir.setPlaceholderText("Enter new directory name")
        self.new_dir.returnPressed.connect(self.rename_pict)

        self.new_dir.setHidden(True)

        self.picture_slider = QSlider(Qt.Horizontal)
        self.picture_slider.setMinimum(0)
        self.picture_slider.valueChanged.connect(self.slider_moved)

        # next button
        next_btn = QPushButton("Next", self)
        next_btn.setFlat(True)
        next_btn.setStyleSheet("border-style: outset;"
                              "background-color: rgb(60,60,60);"
                              "color: rgb(150,150,150)")
        next_btn.clicked.connect(self.next_image)

        # prev button
        prev_btn = QPushButton("Previous", self)
        prev_btn.setFlat(True)
        prev_btn.setStyleSheet("border-style: outset;"
                              "background-color: rgb(60,60,60);"
                              "color: rgb(150,150,150)")
        prev_btn.clicked.connect(self.prev_image)

        # Open External
        open_btn = QPushButton("Open in external", self)
        open_btn.setFlat(True)
        open_btn.setStyleSheet("border-style: outset;"
                              "background-color: rgb(60,60,60);"
                              "color: rgb(150,150,150)")
        open_btn.clicked.connect(self.open_external)

        # prev button
        del_btn = QPushButton("(Un-)delete", self)
        del_btn.setFlat(True)
        del_btn.setStyleSheet("border-style: outset;"
                              "background-color: rgb(60,60,60);"
                              "color: rgb(150,150,150)")
        del_btn.clicked.connect(self.del_image)

        dir_btn = QPushButton("Discard and select directory", self)
        dir_btn.setFlat(True)
        dir_btn.setStyleSheet("border-style: outset;"
                              "background-color: rgb(60,60,60);"
                              "color: rgb(150,150,150)")
        dir_btn.clicked.connect(self.re_init_crawling)

        commit_btn = QPushButton("Commit changes", self)
        commit_btn.setFlat(True)
        commit_btn.setStyleSheet("border-style: outset;"
                              "background-color: rgb(60,60,60);"
                              "color: rgb(150,150,150)")
        commit_btn.clicked.connect(self.commit_changes)

        r_fn = QRadioButton("Filename")
        r_fn.setChecked(True)
        r_fn.toggled.connect(self.new_name.setVisible)

        r_fn.toggled.connect(self.new_name.setFocus)
        r_fn.toggled.connect(self.new_dir.setHidden)


        r_dir = QRadioButton("Directory")
        r_dir.toggled.connect(self.new_name.setHidden)

        r_dir.toggled.connect(self.new_dir.setVisible)
        r_dir.toggled.connect(self.new_dir.setFocus)


        r_fn_dir = QRadioButton("Filename and Directory")
        r_fn_dir.toggled.connect(self.new_name.setVisible)
        r_fn_dir.toggled.connect(self.new_dir.setVisible)


        # set up the label widget to display the pic
        self.picture_height = 600
        self.picture = QLabel(self)
        self.picture.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.MinimumExpanding)

        group_box = QGroupBox()
        self.pic_id = QLabel()
        self.pic_size = QLabel()
        self.pic_action = QLabel()
        group_box_layout = QVBoxLayout()
        group_box_layout.addWidget(self.pic_id)
        group_box_layout.addWidget(self.pic_size)
        group_box_layout.addWidget(self.pic_action)

        group_box.setLayout(group_box_layout)
        group_box.setFixedWidth(200)
        group_box.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)


        stopbtn = QPushButton("Stop", self)
        stopbtn.setFlat(True)
        stopbtn.setStyleSheet("border-style: outset;"
                              "background-color: rgb(60,60,60);"
                              "color: rgb(150,150,150)")
        stopbtn.clicked.connect(self.closeall)

        vbox = QVBoxLayout()
        h_buttons = QHBoxLayout()
        v_radio = QVBoxLayout()
        v_line_edit = QVBoxLayout()
        h_work = QHBoxLayout()

        v_radio.addWidget(r_fn)
        v_radio.addWidget(r_dir)
        v_radio.addWidget(r_fn_dir)

        v_line_edit.addWidget(self.fnlbl)
        v_line_edit.addWidget(self.lbl2)
        v_line_edit.addWidget(self.new_name)
        v_line_edit.addWidget(self.new_dir)

        h_work.addLayout(v_line_edit)
        h_work.addLayout(v_radio)

        group_picture = QHBoxLayout()
        group_picture.addWidget(group_box, alignment=Qt.AlignTop)
        group_picture.addWidget(self.picture)

        h_buttons.addWidget(prev_btn)
        h_buttons.addWidget(next_btn)
        h_buttons.addWidget(del_btn)
        h_buttons.addWidget(commit_btn)
        h_buttons.addWidget(dir_btn)
        h_buttons.addWidget(open_btn)
        h_buttons.addWidget(stopbtn)

        vbox.addWidget(title)
        vbox.addLayout(group_picture)
        vbox.addWidget(self.picture_slider)
        vbox.addLayout(h_work)
        vbox.addLayout(h_buttons)
        self.setLayout(vbox)

    @Slot()
    def del_image(self):
        p = self.current_image
        self.images[p].to_delete = not self.images[p].to_delete
        self.to_image(p)

    @Slot()
    def rename_pict(self):
        if len(self.new_name.text()) > 2 or len(self.new_dir.text()) > 2:
            p = self.current_image
            if self.new_name.text() == "del":
                self.images[p].to_delete = True
            else:
                if self.new_dir.isHidden():
                    self.images[p].new_path = Path(self.images[p].path.parent / (self.new_name.text() + self.images[p].path.suffix))
                elif self.new_name.isHidden():
                    self.images[p].new_path = Path(self.dir_crawler.root_dir / self.new_dir.text() / self.images[p].path.name)
                else:
                    self.images[p].new_path = Path(self.dir_crawler.root_dir / self.new_dir.text() / (self.new_name.text() + self.images[p].path.suffix))

        self.next_image()
        self.new_name.clear()


    @Slot()
    def closeall(self):
        self.lbl2.setText("STOPPING, please wait")
        self.dir_crawler.running = False
        self.lbl2.repaint()
        QApplication.instance().processEvents()
        self.crawler_thread.exit()
        self.crawler_thread.wait()
        self.cache_thread.exit()
        self.cache_thread.wait()
        self.close()

    @Slot(int)
    def slider_moved(self, val):
        self.current_image = val
        self.to_image(val)

    @Slot(int)
    def queuetolabel(self, val):
        self.lbl.setText(val)

    @Slot()
    def next_image(self):
        if len(self.images) > 0:
            self.current_image = (self.current_image + 1) % len(self.images)
            self.to_image(self.current_image)
        else:
            self.current_image = 0

    @Slot()
    def prev_image(self):
        if self.current_image > 0:
            self.current_image -= 1
            self.to_image(self.current_image)
        else:
            self.current_image = len(self.images) - 1
            self.to_image(self.current_image)

    @Slot()
    def open_external(self):
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(self.images[self.current_image].path)))

    @Slot()
    def commit_changes(self):
        for i, image in enumerate(self.images):
            if self.images[i].new_path:
                self.images[i].new_path.parent.mkdir(parents=True, exist_ok=True)
                image.path.rename(image.new_path)
                self.images[i].path = self.images[i].new_path
                self.images[i].new_path = None
            elif self.images[i].to_delete == True:
                send2trash(str(image.path))
                self.images[i].deleted = True
                self.next_image()

    def to_image(self, position):
        self.current_image = position
        cur_img_name = self.images[self.current_image].path
        s_cur_img_name = str(cur_img_name)
        if len(str(cur_img_name.parent)) > self.size().width()//30:
            s_cur_img_name_parent = f"[...]{str(cur_img_name.parent)[-self.size().width()//30:]}"
        else:
            s_cur_img_name_parent = cur_img_name.parent
        text_to_set = f"<font color=\"#aac8ff\">{s_cur_img_name_parent}<font>/<font color=\"#fc5a5a\">{cur_img_name.stem}<font><font color=\"#aac8ff\">{cur_img_name.suffix}<font>"
        self.fnlbl.setText(text_to_set)
        self.pic_id.setText(f"Photo {position + 1}/{len(self.images)}")

        if self.images[position].deleted == True:
            self.pic_action.setText("This photo is deleted")
            pm = QPixmap()
            if not QPixmapCache.find("deleted_ycfvfsAwXLMw6wB", pm):
                reader = QImageReader(deleted_picture)
                pm = QPixmap.fromImageReader(reader)
                QPixmapCache.insert("deleted_ycfvfsAwXLMw6wB", pm)
            self.picture.setPixmap(pm)
            self.picture_slider.setValue(self.current_image)
        else:
            pm = QPixmap()
            if not QPixmapCache.find(s_cur_img_name, pm):
                reader = QImageReader(s_cur_img_name)
                reader.setAutoTransform(True)
                pm = QPixmap.fromImageReader(reader)
                QPixmapCache.insert(s_cur_img_name, pm)
                self.images[self.current_image].size = reader.size()
            pm = pm.scaled(min(pm.size().width(), self.picture.size().width()),
                           min(pm.size().height(), self.picture.size().height()),
                           aspectMode=QtCore.Qt.KeepAspectRatio)
            self.update_cache_signal.emit(self.current_image)
            self.picture.setPixmap(pm)
            self.picture_slider.setValue(self.current_image)
            if self.images[self.current_image].to_delete == True:
                self.pic_action.setText("To be delete")
            elif self.images[self.current_image].new_path:
                self.pic_action.setText(f"New name: {self.images[self.current_image].new_path.stem}")
            else:
                self.pic_action.clear()
        if self.images[self.current_image].size.width() < 1:
            self.pic_size.setText("Size unknown")
        else:
            self.pic_size.setText(f"Size: {self.images[self.current_image].size.width()}x{self.images[self.current_image].size.height()}")

    def select_dir(self):
        return Path(QFileDialog.getExistingDirectory(self))

    def load_image(self, image):
        self.images.append(image)
        if len(self.images) == 1:
            self.to_image(0)
        self.pic_id.setText(f"Photo {self.current_image + 1}/{len(self.images)} (loading)")

    def dir_crawler_finished(self):
        self.pic_id.setText(f"Photo {self.current_image + 1}/{len(self.images)}")
        self.picture_slider.setMaximum(len(self.images)-1)

    def init_crawling(self):
        self.dir_crawler = DirCrawler(self.select_dir())
        self.crawler_thread = QThread()
        self.dir_crawler.moveToThread(self.crawler_thread)
        self.dir_crawler.new_image_signal.connect(self.load_image)
        self.dir_crawler.finished_signal.connect(self.dir_crawler_finished)

        self.crawler_thread.started.connect(self.dir_crawler.crawl)
        self.crawler_thread.start()

    def re_init_crawling(self):
        self.crawler_thread.exit()
        self.crawler_thread.wait()
        self.images = []
        self.init_crawling()


def main():
    app = QApplication(sys.argv)
    app.setStyleSheet("QMainWindow{background-color: rgb(100,100,100)}")

    ex = AppWindow()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()



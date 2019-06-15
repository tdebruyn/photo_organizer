from PySide2.QtCore import QThread, QObject, Signal, Slot, Qt, QSize, QUrl
from PySide2.QtWidgets import (QApplication, QWidget, QPushButton,
                             QDesktopWidget, QVBoxLayout, QLineEdit, QSlider,
                             QLabel, QHBoxLayout, QFileDialog, QGroupBox)
from PySide2 import QtCore
from send2trash import send2trash
from PySide2.QtGui import QDesktopServices, QPixmap, QPixmapCache, QImageReader
import sys, os
from pathlib import Path
from dataclasses import dataclass
from pkg_resources import resource_filename
deleted_picture = resource_filename(__name__, 'bitmaps/deleted-picture.png')

@dataclass
class image(object):
    path: Path
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
            if not QPixmapCache.find(cur_img_name, pm):
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
        self.new_name.setPlaceholderText("Enter new name, minimum 3 characters")
        self.new_name.setFixedWidth(400)
        self.new_name.returnPressed.connect(self.rename_pict)

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
        open_btn = QPushButton("Open", self)
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

        # set up the label widget to display the pic
        self.picture_height = 600
        self.picture = QLabel(self)
        self.picture.setFixedHeight(self.picture_height)

        group_box = QGroupBox()
        self.pic_id = QLabel()
        self.pic_size = QLabel()
        self.pic_action = QLabel()
        group_box_layout = QVBoxLayout()
        group_box_layout.addWidget(self.pic_id)
        group_box_layout.addWidget(self.pic_size)
        group_box_layout.addWidget(self.pic_action)
        group_box_layout.addStretch(1)
        group_box.setLayout(group_box_layout)
        group_box.setFixedWidth(200)

        stopbtn = QPushButton("Stop", self)
        stopbtn.setFlat(True)
        stopbtn.setStyleSheet("border-style: outset;"
                              "background-color: rgb(60,60,60);"
                              "color: rgb(150,150,150)")
        stopbtn.clicked.connect(self.closeall)


        vbox = QVBoxLayout()
        hbox = QHBoxLayout()
        group_picture = QHBoxLayout()
        group_picture.addWidget(group_box)
        group_picture.addWidget(self.picture)


        hbox.addWidget(prev_btn)
        hbox.addWidget(next_btn)
        hbox.addWidget(del_btn)
        hbox.addWidget(commit_btn)
        hbox.addWidget(dir_btn)
        hbox.addWidget(open_btn)
        hbox.addWidget(stopbtn)


        vbox.addWidget(title)
        vbox.addLayout(group_picture)
        self.picture_slider.setFixedWidth(self.picture_height + group_box.width())
        vbox.addWidget(self.picture_slider)
        vbox.addWidget(self.fnlbl)
        vbox.addWidget(self.lbl2)
        vbox.addWidget(self.new_name)
        vbox.addStretch(1)
        vbox.addLayout(hbox)
        self.setLayout(vbox)

    @Slot()
    def del_image(self):
        p = self.current_image
        self.images[p].to_delete = not self.images[p].to_delete
        self.to_image(p)

    @Slot()
    def rename_pict(self):
        if len(self.new_name.text()) > 2:
            p = self.current_image
            if self.new_name.text() == "del":
                self.images[p].to_delete = True
            else:
                self.images[p].new_path = Path(self.images[p].path.parent / (self.new_name.text() + self.images[p].path.suffix))
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
                os.rename(image.path, image.new_path)
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
        self.fnlbl.setText(
            f"<font color=\"#aac8ff\">{cur_img_name.parent}<font>/<font color=\"#fc5a5a\">{cur_img_name.stem}<font><font color=\"#aac8ff\">{cur_img_name.suffix}<font>")
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


            pm = pm.scaled(self.picture_height, self.picture_height, aspectMode=QtCore.Qt.KeepAspectRatio)
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



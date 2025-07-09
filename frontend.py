import sys
import csv
import cv2
from PySide6.QtCore import Qt, QRect, QRectF, QPoint, QSize, QTimer
from PySide6.QtGui import QPixmap, QImage, QPen, QBrush, QColor, QKeySequence, QStandardItemModel, QStandardItem, QShortcut
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QFileDialog, QLabel, QGraphicsScene, QGraphicsView, QGraphicsRectItem,
    QRubberBand, QSplitter, QTableView, QHeaderView, QSlider
)

class BoundingBoxView(QGraphicsView):
    def __init__(self, scene, parent=None):
        super().__init__(scene, parent)
        self._current_rect_item = None
        self._rubberBand = QRubberBand(QRubberBand.Rectangle, self)
        self._origin = QPoint()
        self.setMouseTracking(True)
        self.setAlignment(Qt.AlignLeft | Qt.AlignTop)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._origin = event.pos()
            self._rubberBand.setGeometry(QRect(self._origin, QSize()))
            self._rubberBand.show()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._rubberBand.isVisible():
            rect = QRect(self._origin, event.pos()).normalized()
            self._rubberBand.setGeometry(rect)
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton and self._rubberBand.isVisible():
            self._rubberBand.hide()
            start_scene = self.mapToScene(self._origin)
            end_scene = self.mapToScene(event.pos())
            rect = QRectF(start_scene, end_scene).normalized()
            if self._current_rect_item:
                try:
                    self.scene().removeItem(self._current_rect_item)
                except Exception:
                    pass
            pen = QPen(QColor(255, 255, 255, 200), 2)
            brush = QBrush(QColor(255, 255, 255, 50))
            self._current_rect_item = QGraphicsRectItem(rect)
            self._current_rect_item.setPen(pen)
            self._current_rect_item.setBrush(brush)
            self.scene().addItem(self._current_rect_item)
            if hasattr(self.parent(), 'update_info'):
                self.parent().update_info()
        super().mouseReleaseEvent(event)

    def clearBoundingBox(self):
        if self._current_rect_item:
            try:
                self.scene().removeItem(self._current_rect_item)
            except Exception:
                pass
            self._current_rect_item = None
            if hasattr(self.parent(), 'update_info'):
                self.parent().update_info()

    def getBoundingBox(self):
        if self._current_rect_item:
            return self._current_rect_item.rect()
        return None

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Video Tagger")
        self.resize(1000, 600)
        self.video_paths = []
        self.current_index = -1
        self.annotations = {}
        self.cap = None
        self.frame_count = 0
        self.current_frame = 0
        self.playing = False

        self.splitter = QSplitter(Qt.Horizontal, self)

        left = QWidget()
        left_layout = QVBoxLayout(left)
        controls = QHBoxLayout()

        self.load_btn = QPushButton("Load Videos")
        self.load_btn.clicked.connect(self.load_videos)
        controls.addWidget(self.load_btn)

        self.next_btn = QPushButton("Next Video")
        self.next_btn.setEnabled(False)
        self.next_btn.clicked.connect(self.next_video)
        controls.addWidget(self.next_btn)

        self.process_btn = QPushButton("Save Frame")
        self.process_btn.setEnabled(False)
        self.process_btn.clicked.connect(self.save_annotation)
        controls.addWidget(self.process_btn)

        self.play_btn = QPushButton("Play")
        self.play_btn.setEnabled(False)
        self.play_btn.clicked.connect(self.toggle_play)
        controls.addWidget(self.play_btn)

        self.finish_btn = QPushButton("Finish")
        self.finish_btn.setEnabled(False)
        self.finish_btn.clicked.connect(self.finish_annotation)
        controls.addWidget(self.finish_btn)

        controls.addStretch()
        self.info_label = QLabel("Frame: 0 | BBox: None")
        controls.addWidget(self.info_label)

        left_layout.addLayout(controls)

        self.scene = QGraphicsScene(self)
        self.view = BoundingBoxView(self.scene, self)
        self.view.setObjectName("videoView")
        left_layout.addWidget(self.view)

        self.slider = QSlider(Qt.Horizontal)
        self.slider.setEnabled(False)
        self.slider.sliderMoved.connect(self.on_slider_moved)
        left_layout.addWidget(self.slider)

        self.apply_styles()
        self.splitter.addWidget(left)

        self.table = QTableView()
        self.table_model = QStandardItemModel()
        self.table.setModel(self.table_model)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.hide()
        self.splitter.addWidget(self.table)
        self.splitter.setSizes([600, 0])

        self.setCentralWidget(self.splitter)

        self.timer = QTimer(self)
        self.timer.setInterval(33)
        self.timer.timeout.connect(self.playback)

        QShortcut(QKeySequence('R'), self, activated=self.reset_box)
        QShortcut(QKeySequence('S'), self, activated=self.save_annotation)
        QShortcut(QKeySequence('Right'), self, activated=lambda: self.step_frame(1))
        QShortcut(QKeySequence('Left'), self, activated=lambda: self.step_frame(-1))
        QShortcut(QKeySequence('Space'), self, activated=self.toggle_play)

    def apply_styles(self):
        self.setStyleSheet("""
        QMainWindow { background-color: rgba(30,30,30,220); }
        QWidget#centralWidget, QWidget { background-color: transparent; }
        QGraphicsView#videoView { background-color: rgba(40,40,40,200); border: none; }
        QPushButton {
            background-color: rgba(255,255,255,15%);
            color: #fff;
            border: none;
            padding: 8px 16px;
            border-radius: 8px;
        }
        QPushButton:hover { background-color: rgba(255,255,255,25%); }
        QPushButton:pressed { background-color: rgba(255,255,255,30%); }
        QSlider::groove:horizontal {
            background: rgba(255,255,255,20%);
            height: 6px;
            border-radius: 3px;
        }
        QSlider::handle:horizontal {
            background: rgba(255,255,255,80%);
            width: 12px;
            margin: -3px 0;
            border-radius: 6px;
        }
        QLabel { color: #fff; }
        QTableView { background-color: rgba(30,30,30,200); color: #fff; gridline-color: #555; }
        """)

    def load_videos(self):
        paths, _ = QFileDialog.getOpenFileNames(self, "Select Videos", "", "Videos (*.mp4 *.avi *.mov)")
        if not paths:
            return
        self.video_paths = paths
        self.annotations.clear()
        self.current_index = 0
        self.open_video(self.video_paths[0])
        self.next_btn.setEnabled(True)
        self.process_btn.setEnabled(True)
        self.play_btn.setEnabled(True)
        self.finish_btn.setEnabled(True)

    def open_video(self, path):
        if self.cap:
            self.cap.release()
        self.cap = cv2.VideoCapture(path)
        self.frame_count = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
        self.slider.setRange(0, self.frame_count - 1)
        self.slider.setValue(0)
        self.slider.setEnabled(True)
        self.playing = False
        self.play_btn.setText("Play")
        self.timer.stop()
        self.load_frame(0)

    def load_frame(self, frame_no):
        if not self.cap:
            return
        self.cap.set(cv2.CAP_PROP_POS_FRAMES, frame_no)
        ret, frame = self.cap.read()
        if ret:
            self.current_frame = frame_no
            self.display_frame(frame)
            self.slider.blockSignals(True)
            self.slider.setValue(frame_no)
            self.slider.blockSignals(False)
            self.update_info()

    def display_frame(self, frame):
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, ch = frame_rgb.shape
        img = QImage(frame_rgb.data, w, h, ch*w, QImage.Format_RGB888)
        pix = QPixmap.fromImage(img)
        self.scene.clear()
        self.view.clearBoundingBox()
        self.scene.addPixmap(pix)
        self.view.fitInView(self.scene.sceneRect(), Qt.KeepAspectRatio)

    def next_video(self):
        self.save_annotation()
        if self.current_index + 1 < len(self.video_paths):
            self.current_index += 1
            self.open_video(self.video_paths[self.current_index])
        else:
            self.next_btn.setEnabled(False)

    def on_slider_moved(self, pos):
        self.load_frame(pos)

    def playback(self):
        next_frame = self.current_frame + 1
        if next_frame < self.frame_count:
            self.load_frame(next_frame)
        else:
            self.toggle_play()

    def toggle_play(self):
        self.playing = not self.playing
        if self.playing:
            self.play_btn.setText("Pause")
            self.timer.start()
        else:
            self.play_btn.setText("Play")
            self.timer.stop()

    def step_frame(self, delta):
        new = max(0, min(self.frame_count - 1, self.current_frame + delta))
        self.load_frame(new)

    def reset_box(self):
        self.view.clearBoundingBox()

    def save_annotation(self):
        rect = self.view.getBoundingBox()
        if rect is not None:
            coords = (self.current_frame, int(rect.x()), int(rect.y()), int(rect.width()), int(rect.height()))
            path = self.video_paths[self.current_index]
            self.annotations[path] = coords
        self.update_info()

    def update_info(self):
        rect = self.view.getBoundingBox()
        bbox_text = f"{int(rect.x())},{int(rect.y())},{int(rect.width())},{int(rect.height())}" if rect else "None"
        self.info_label.setText(f"Video {self.current_index+1}/{len(self.video_paths)} | Frame {self.current_frame+1}/{self.frame_count} | BBox: {bbox_text}")

    def finish_annotation(self):
        self.save_annotation()
        save_path, _ = QFileDialog.getSaveFileName(self, "Save Annotations CSV", "", "CSV (*.csv)")
        if not save_path:
            return
        with open(save_path, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['video_path','frame','x','y','width','height'])
            for p, data in self.annotations.items():
                writer.writerow([p, *data])
        self.load_csv_to_table(save_path)
        self.table.show()
        self.splitter.setSizes([600,400])
        self.finish_btn.setEnabled(False)

    def load_csv_to_table(self, path):
        with open(path, 'r', newline='') as f:
            reader = csv.reader(f)
            headers = next(reader, [])
            self.table_model.clear()
            self.table_model.setHorizontalHeaderLabels(headers)
            for row in reader:
                items = [QStandardItem(field) for field in row]
                self.table_model.appendRow(items)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    win = MainWindow()
    win.show()
    sys.exit(app.exec())

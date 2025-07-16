import sys
import subprocess
import csv
import cv2
import os
import threading
import time
from PySide6.QtCore import Qt, QRect, QRectF, QPoint, QSize, QTimer, QThread, Signal
from PySide6.QtGui import QPixmap, QImage, QPen, QBrush, QColor, QKeySequence, QStandardItemModel, QStandardItem, QShortcut
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QFileDialog, QLabel, QGraphicsScene, QGraphicsView, QGraphicsRectItem,
    QRubberBand, QSplitter, QTableView, QHeaderView, QSlider, QMessageBox, QProgressDialog
)

class ProcessingWorker(QThread):
    finished = Signal(int, str, str)  # returncode, stdout, stderr
    progress = Signal(str)  # progress message
    
    def __init__(self, script_dir):
        super().__init__()
        self.script_dir = script_dir
        
    def run(self):
        import os
        import subprocess
        original_cwd = os.getcwd()
        os.chdir(self.script_dir)
        
        # Set environment variable to avoid OpenMP conflicts
        env = os.environ.copy()
        env['KMP_DUPLICATE_LIB_OK'] = 'TRUE'
        
        try:
            self.progress.emit("Starting SAM2 video tracking...")
            
            # Run the backend script
            result = subprocess.run(["python", "scripts/demo2.py"], 
                                  capture_output=True, text=True, check=False, env=env)
            
            self.finished.emit(result.returncode, result.stdout, result.stderr)
            
        except Exception as e:
            self.finished.emit(-1, "", str(e))
        finally:
            os.chdir(original_cwd)

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
        self.worker = None  # Processing worker thread

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
        
        # Save to boxes.csv in the current directory for the backend to process
        save_path = "boxes.csv"
        with open(save_path, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['video_path','frame','x','y','width','height'])
            for p, data in self.annotations.items():
                writer.writerow([p, *data])
        
        # Also save a backup with timestamp to preserve data
        import datetime
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = f"boxes_backup_{timestamp}.csv"
        with open(backup_path, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['video_path','frame','x','y','width','height'])
            for p, data in self.annotations.items():
                writer.writerow([p, *data])
        
        print(f"Bounding box data saved to {save_path}")
        print(f"Backup saved to {backup_path}")
        
        self.load_csv_to_table(save_path)
        self.table.show()
        self.splitter.setSizes([600,400])
        
        # Now start the backend processing
        self.finish_function()
    
    def finish_function(self):
        # Check if already processing
        if self.worker is not None and self.worker.isRunning():
            QMessageBox.warning(self, "Processing", "Processing is already in progress!")
            return
        
        # Disable UI controls during processing
        self.load_btn.setEnabled(False)
        self.next_btn.setEnabled(False)
        self.process_btn.setEnabled(False)
        self.play_btn.setEnabled(False)
        self.finish_btn.setEnabled(False)
        
        # Show progress dialog
        self.progress_dialog = QMessageBox(self)
        self.progress_dialog.setWindowTitle("Processing Videos")
        self.progress_dialog.setText("Starting SAM2 video tracking...\n\nThis may take a few minutes depending on video length.\nPlease wait...")
        self.progress_dialog.setStandardButtons(QMessageBox.NoButton)
        self.progress_dialog.show()
        
        # Start worker thread
        script_dir = os.path.dirname(os.path.abspath(__file__))
        self.worker = ProcessingWorker(script_dir)
        self.worker.progress.connect(self.update_progress)
        self.worker.finished.connect(self.processing_finished)
        self.worker.start()
    
    def update_progress(self, message):
        """Update progress dialog with current status"""
        if hasattr(self, 'progress_dialog'):
            self.progress_dialog.setText(message)
    
    def processing_finished(self, returncode, stdout, stderr):
        """Handle completion of background processing"""
        # Close progress dialog
        if hasattr(self, 'progress_dialog'):
            self.progress_dialog.close()
            self.progress_dialog = None
        
        # Re-enable UI controls
        self.load_btn.setEnabled(True)
        self.next_btn.setEnabled(True)
        self.process_btn.setEnabled(True)
        self.play_btn.setEnabled(True)
        self.finish_btn.setEnabled(True)
        
        # Show result message
        if returncode == 0:
            # Success
            success_msg = QMessageBox(self)
            success_msg.setWindowTitle("Success")
            success_msg.setText("Video tracking completed successfully!\n\n"
                               "Check the 'outputs' folder for tracked videos\n"
                               "and 'tracking_results.csv' for detailed results.\n\n"
                               "Application will now exit.")
            success_msg.setIcon(QMessageBox.Information)
            success_msg.exec()
            
            # Exit the application after successful processing
            # Use QTimer to delay the quit call slightly
            QTimer.singleShot(100, QApplication.quit)
        else:
            # Error occurred
            error_msg = QMessageBox(self)
            error_msg.setWindowTitle("Error")
            error_msg.setText(f"An error occurred during tracking:\n\n{stderr}")
            error_msg.setIcon(QMessageBox.Critical)
            error_msg.exec()
        
        # Clean up worker
        self.worker = None

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
#!/usr/bin/env python3
"""
Test script to verify the threading functionality works correctly
"""

import sys
import os
import subprocess
from PySide6.QtCore import QThread, Signal, QTimer
from PySide6.QtWidgets import QApplication, QMainWindow, QPushButton, QVBoxLayout, QWidget, QLabel, QMessageBox

class TestWorker(QThread):
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
        
        try:
            self.progress.emit("Testing subprocess call...")
            
            # Test with a simple command first
            result = subprocess.run(["python", "--version"], 
                                  capture_output=True, text=True, check=False)
            
            if result.returncode == 0:
                self.progress.emit("Python version check successful")
                
                # Now test if the demo2.py script exists and can be called
                if os.path.exists("scripts/demo2.py"):
                    self.progress.emit("Found demo2.py, testing call...")
                    # Just check if it can be called without running it fully
                    result = subprocess.run(["python", "scripts/demo2.py", "--help"], 
                                          capture_output=True, text=True, check=False, timeout=10)
                else:
                    self.progress.emit("demo2.py not found")
                    result = subprocess.run(["echo", "demo2.py not found"], 
                                          capture_output=True, text=True, check=False)
            
            self.finished.emit(result.returncode, result.stdout, result.stderr)
            
        except Exception as e:
            self.finished.emit(-1, "", str(e))
        finally:
            os.chdir(original_cwd)

class TestWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Threading Test")
        self.resize(400, 300)
        
        self.worker = None
        
        # Create UI
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        self.status_label = QLabel("Ready to test")
        layout.addWidget(self.status_label)
        
        self.test_btn = QPushButton("Test Threading")
        self.test_btn.clicked.connect(self.run_test)
        layout.addWidget(self.test_btn)
        
    def run_test(self):
        if self.worker is not None and self.worker.isRunning():
            QMessageBox.warning(self, "Test", "Test is already running!")
            return
        
        self.test_btn.setEnabled(False)
        self.status_label.setText("Running test...")
        
        script_dir = os.path.dirname(os.path.abspath(__file__))
        self.worker = TestWorker(script_dir)
        self.worker.progress.connect(self.update_status)
        self.worker.finished.connect(self.test_finished)
        self.worker.start()
    
    def update_status(self, message):
        self.status_label.setText(message)
    
    def test_finished(self, returncode, stdout, stderr):
        self.test_btn.setEnabled(True)
        
        if returncode == 0:
            self.status_label.setText("Test completed successfully!")
            QMessageBox.information(self, "Success", f"Test passed!\n\nOutput:\n{stdout}")
        else:
            self.status_label.setText("Test failed")
            QMessageBox.critical(self, "Error", f"Test failed!\n\nError:\n{stderr}")
        
        self.worker = None

if __name__ == '__main__':
    app = QApplication(sys.argv)
    win = TestWindow()
    win.show()
    sys.exit(app.exec())

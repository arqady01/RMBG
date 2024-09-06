import os
from PyQt5.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QPushButton, QFileDialog, QProgressBar, QLabel, QListWidget, QHBoxLayout, QListWidgetItem
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QMimeData, QPropertyAnimation, QEasingCurve, QPoint, QTimer, QRect
from PyQt5.QtGui import QDragEnterEvent, QDropEvent, QPixmap, QIcon  # Add QIcon here
from image_processor import process_image
from utils import get_image_files

class WorkerThread(QThread):
    progress = pyqtSignal(int)
    finished = pyqtSignal()

    def __init__(self, input_images, output_folder):
        super().__init__()
        self.input_images = input_images
        self.output_folder = output_folder

    def run(self):
        total = len(self.input_images)
        for i, image in enumerate(self.input_images):
            process_image(image, self.output_folder, lambda x: self.progress.emit(int((i + x/100) / total * 100)))
        self.finished.emit()

class MainWindow(QMainWindow):
    def __init__(self):
        self.delete_mode = False
        super().__init__()
        self.setWindowTitle("Background Remover")
        self.setGeometry(100, 100, 1536, 864)
        self.setAcceptDrops(True)
        self.setStyleSheet("""
            QMainWindow {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                                            stop:0 #FF8A7B, stop:0.3 #FF5A78, stop:0.7 #FF5A78, stop:1 #FF8A7B);
            }
        """)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        layout.setSpacing(20)  # Set the default spacing between widgets

        self.input_button = QPushButton("Select Input Images")
        self.input_button.clicked.connect(self.select_input_images)
        self.style_button(self.input_button)
        layout.addWidget(self.input_button)

        layout.addSpacing(10)  # Add extra spacing

        self.image_list = QListWidget()
        self.image_list.setStyleSheet("""
            QListWidget {
                background-color: rgba(255, 255, 255, 0.2);
                border: 1px solid rgba(255, 255, 255, 0.3);
                border-radius: 5px;
                color: #FFFFFF;
            }
            QListWidget::item {
                padding: 5px;
            }
            QListWidget::item:selected {
                background-color: rgba(255, 106, 136, 0.5);
            }
        """)

        # Create a horizontal layout for the delete buttons
        delete_buttons_layout = QHBoxLayout()

        self.delete_selected_button = QPushButton("Delete Selected Images")
        self.delete_selected_button.clicked.connect(self.delete_selected_images)
        self.style_button(self.delete_selected_button)
        delete_buttons_layout.addWidget(self.delete_selected_button)

        self.delete_all_button = QPushButton("Delete All Images")
        self.delete_all_button.clicked.connect(self.delete_all_images)
        self.style_button(self.delete_all_button)
        delete_buttons_layout.addWidget(self.delete_all_button)

        # Create a vertical layout for the image list and delete buttons
        image_list_layout = QVBoxLayout()
        image_list_layout.addWidget(self.image_list)
        image_list_layout.addLayout(delete_buttons_layout)

        # Add the image list layout to the main layout
        layout.addLayout(image_list_layout)

        layout.addSpacing(10)  # Add extra spacing

        self.output_button = QPushButton("Select Output Folder")
        self.output_button.clicked.connect(self.select_output_folder)
        self.style_button(self.output_button)
        layout.addWidget(self.output_button)

        self.process_button = QPushButton("Process Images")
        self.process_button.clicked.connect(self.process_images)
        self.style_button(self.process_button)
        layout.addWidget(self.process_button)

        layout.addSpacing(10)  # Add extra spacing

        self.progress_bar = QProgressBar()
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                background-color: rgba(255, 255, 255, 0.3);
                border: 1px solid rgba(255, 255, 255, 0.5);
                border-radius: 5px;
                text-align: center;
            }
            QProgressBar::chunk {
                background-color: rgba(255, 106, 136, 0.7);
                width: 10px;
                margin: 0.5px;
            }
        """)
        layout.addWidget(self.progress_bar)

        self.status_label = QLabel()
        layout.addWidget(self.status_label)

        self.input_images = []
        self.output_folder = os.path.join(os.path.dirname(os.path.dirname(__file__)), "output")
        if not os.path.exists(self.output_folder):
            os.makedirs(self.output_folder)
        self.status_label.setText(f"Default output folder: {self.output_folder}")

        layout.addSpacing(10)  # Add extra spacing

    def style_button(self, button):
        button.setStyleSheet("""
            QPushButton {
                background-color: rgba(255, 255, 255, 0.2);
                border: 1px solid rgba(255, 255, 255, 0.3);
                border-radius: 5px;
                padding: 10px;
                color: #FFFFFF;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 0.3);
            }
        """)

    def select_input_images(self):
        files, _ = QFileDialog.getOpenFileNames(self, "Select Input Images", "", "Image Files (*.png *.jpg *.jpeg)")
        self.add_input_images(files)

    def add_input_images(self, files):
        self.input_images.extend(files)
        self.image_list.clear()
        for file in self.input_images:
            item = QListWidgetItem(os.path.basename(file))
            self.image_list.addItem(item)
        self.status_label.setText(f"Selected {len(self.input_images)} images")

    def select_output_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Output Folder")
        if folder:
            self.output_folder = folder
            self.status_label.setText(f"Output folder: {self.output_folder}")

    def process_images(self):
        if not self.input_images:
            self.status_label.setText("Please select input images.")
            return

        # Filter out non-existent files
        existing_images = [img for img in self.input_images if os.path.exists(img)]
        non_existing_images = set(self.input_images) - set(existing_images)

        if non_existing_images:
            self.status_label.setText(f"Warning: {len(non_existing_images)} image(s) not found and will be skipped.")

        if not existing_images:
            self.status_label.setText("No valid images to process.")
            return

        self.worker = WorkerThread(existing_images, self.output_folder)
        self.worker.progress.connect(self.update_progress)
        self.worker.finished.connect(self.processing_finished)
        self.worker.start()

        self.input_button.setEnabled(False)
        self.output_button.setEnabled(False)
        self.process_button.setEnabled(False)

    def update_progress(self, value):
        self.progress_bar.setValue(value)

    def processing_finished(self):
        self.status_label.setText("Processing completed!")
        self.input_button.setEnabled(True)
        self.output_button.setEnabled(True)
        self.process_button.setEnabled(True)
        self.progress_bar.setValue(0)
        self.show_fireworks()

    def show_fireworks(self):
        def create_firework(x, y):
            firework = QLabel(self)
            firework.setGeometry(x, y, 10, 10)
            firework.setStyleSheet("""
                background: radial-gradient(circle, #FF6A88 20%, #FF8A7B 40%, transparent 70%);
                border-radius: 5px;
            """)
            firework.raise_()
            return firework

        left_firework = create_firework(-10, self.height() // 2)
        right_firework = create_firework(self.width() + 10, self.height() // 2)

        def animate_firework(firework, start_x, end_x):
            anim = QPropertyAnimation(firework, b"geometry")
            anim.setDuration(2000)  # Increase duration to 2 seconds
            anim.setStartValue(QRect(start_x, self.height() // 2, 10, 10))
            anim.setEndValue(QRect(end_x, self.height() // 2, 100, 100))
            anim.setEasingCurve(QEasingCurve.OutBack)
            return anim

        left_anim = animate_firework(left_firework, self.width() // 4, self.width() // 2 - 50)
        right_anim = animate_firework(right_firework, 3 * self.width() // 4, self.width() // 2 + 50)

        left_anim.start()
        right_anim.start()

        QTimer.singleShot(3000, left_firework.deleteLater)
        QTimer.singleShot(3000, right_firework.deleteLater)

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event: QDropEvent):
        files = [u.toLocalFile() for u in event.mimeData().urls() if u.toLocalFile().lower().endswith(('.png', '.jpg', '.jpeg'))]
        self.add_input_images(files)

    def delete_selected_images(self):
        for item in self.image_list.selectedItems():
            index = self.image_list.row(item)
            del self.input_images[index]
            self.image_list.takeItem(index)
        self.status_label.setText(f"Selected {len(self.input_images)} images")

    def delete_all_images(self):
        self.input_images.clear()
        self.image_list.clear()
        self.status_label.setText("All images deleted")

    def toggle_delete_mode(self):
        self.delete_mode = not self.delete_mode
        if self.delete_mode:
            self.image_list.itemClicked.connect(self.remove_image)
        else:
            self.image_list.itemClicked.disconnect(self.remove_image)

    def remove_image(self, item):
        index = self.image_list.row(item)
        del self.input_images[index]
        self.image_list.takeItem(index)
        self.status_label.setText(f"Selected {len(self.input_images)} images")
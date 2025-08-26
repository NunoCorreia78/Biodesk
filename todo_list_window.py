import json
import os
import sys
from datetime import datetime
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton, 
    QListWidget, QListWidgetItem, QCheckBox, QLabel, QTextEdit,
    QDialog, QDialogButtonBox, QSplitter, QFrame
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QIcon
from biodesk_dialogs import BiodeskMessageBox
from biodesk_ui_kit import BiodeskUIKit

# 🎨 SISTEMA DE ESTILOS CENTRALIZADO
try:
    from biodesk_styles import BiodeskStyles, ButtonType
    STYLES_AVAILABLE = True
except ImportError:
    STYLES_AVAILABLE = False

"""
To-Do List Window para Biodesk
Lista de tarefas integrada de forma não-intrusiva
"""

class TodoItem:
    def __init__(self, text, completed=False, created_date=None, priority="Normal"):
        self.text = text
        self.completed = completed
        self.created_date = created_date or datetime.now().strftime("%Y-%m-%d %H:%M")
        self.priority = priority
    
    def to_dict(self):
        return {
            'text': self.text,
            'completed': self.completed,
            'created_date': self.created_date,
            'priority': self.priority
        }
    
    @classmethod
    def from_dict(cls, data):
        return cls(
            data['text'], 
            data.get('completed', False),
            data.get('created_date'),
            data.get('priority', 'Normal')
        )

class TodoListWidget(QListWidget):
    item_changed = pyqtSignal()
    
    def __init__(self):
        super().__init__()
        self.setStyleSheet("""
            QListWidget {
                border: 1px solid #e0e0e0;
                border-radius: 8px;
                background-color: white;
                padding: 8px;
                font-size: 14px;
                alternate-background-color: #f8f9fa;
            }
            QListWidget::item {
                padding: 15px;
                border-bottom: 1px solid #f0f0f0;
                border-radius: 6px;
                margin: 4px 2px;
                min-height: 60px;
                background-color: white;
            }
            QListWidget::item:hover {
                background-color: #f8f9fa;
                border: 1px solid #e3f2fd;
            }
            QListWidget::item:selected {
                background-color: #e3f2fd;
                color: #1976d2;
                border: 2px solid #2196F3;
            }
        """)
        self.setAlternatingRowColors(True)

class AddTodoDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("➕ Nova Tarefa")
        self.setFixedSize(400, 300)
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout()
        
        # Campo de texto
        layout.addWidget(QLabel("📝 Descrição da tarefa:"))
        self.text_edit = QTextEdit()
        self.text_edit.setMaximumHeight(100)
        self.text_edit.setPlaceholderText("Descreva a tarefa...")
        layout.addWidget(self.text_edit)
        
        # Prioridade
        layout.addWidget(QLabel("⚡ Prioridade:"))
        priority_layout = QHBoxLayout()
        
        self.priority_buttons = {}
        priorities = [("🔴 Alta", "Alta"), ("🟡 Normal", "Normal"), ("⚪ Baixa", "Baixa")]
        
        for text, value in priorities:
            btn = QPushButton(text)
            btn.setCheckable(True)
            if value == "Normal":  # Prioridade padrão
                btn.setChecked(True)
            btn.clicked.connect(lambda checked, v=value: self.set_priority(v))
            self.priority_buttons[value] = btn
            priority_layout.addWidget(btn)
        
        layout.addLayout(priority_layout)
        
        # Botões
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
        
        self.setLayout(layout)
        self.text_edit.setFocus()
    
    def set_priority(self, priority):
        for btn in self.priority_buttons.values():
            btn.setChecked(False)
        self.priority_buttons[priority].setChecked(True)
    
    def get_priority(self):
        for priority, btn in self.priority_buttons.items():
            if btn.isChecked():
                return priority
        return "Normal"
    
    def get_text(self):
        return self.text_edit.toPlainText().strip()

class TodoListWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("📝 Lista de Tarefas - Biodesk")
        self.setGeometry(200, 200, 600, 500)
        self.todos = []
        self.load_todos()
        self.setup_ui()
        self.refresh_list()
    
    def setup_ui(self):
        layout = QVBoxLayout()
        
        # Cabeçalho
        header = QLabel("📝 Lista de Tarefas")
        header.setStyleSheet("""
            font-size: 24px;
            font-weight: bold;
            color: #2196F3;
            padding: 10px;
            background-color: #f8f9fa;
            border-radius: 8px;
            margin-bottom: 10px;
        """)
        header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(header)
        
        # Botões de ação
        btn_layout = QHBoxLayout()
        
        if STYLES_AVAILABLE:
            add_btn = BiodeskStyles.create_button("➕ Nova Tarefa", ButtonType.SAVE)
        else:
            add_btn = QPushButton("➕ Nova Tarefa")
            BiodeskUIKit.apply_universal_button_style(add_btn)
        add_btn.clicked.connect(self.add_todo)
        btn_layout.addWidget(add_btn)
        
        if STYLES_AVAILABLE:
            clear_completed_btn = BiodeskStyles.create_button("🗑️ Limpar Concluídas", ButtonType.DELETE)
        else:
            clear_completed_btn = QPushButton("🗑️ Limpar Concluídas")
            BiodeskUIKit.apply_universal_button_style(clear_completed_btn)
        clear_completed_btn.clicked.connect(self.clear_completed)
        btn_layout.addWidget(clear_completed_btn)
        
        if STYLES_AVAILABLE:
            delete_btn = BiodeskStyles.create_button("❌ Deletar Selecionada", ButtonType.DELETE)
        else:
            delete_btn = QPushButton("❌ Deletar Selecionada")
            BiodeskUIKit.apply_universal_button_style(delete_btn)
        delete_btn.clicked.connect(self.delete_selected_item)
        btn_layout.addWidget(delete_btn)
        
        btn_layout.addStretch()
        
        # Instruções
        instructions = QLabel("💡 Duplo clique para marcar/desmarcar • Tecla Delete para apagar")
        instructions.setStyleSheet("font-size: 11px; color: #888; font-style: italic;")
        btn_layout.addWidget(instructions)
        
        # Contador
        self.counter_label = QLabel()
        self.counter_label.setStyleSheet("font-size: 14px; color: #666; padding: 10px;")
        btn_layout.addWidget(self.counter_label)
        
        layout.addLayout(btn_layout)
        
        # Lista de tarefas
        self.list_widget = TodoListWidget()
        layout.addWidget(self.list_widget)
        
        self.setLayout(layout)
        
        # Aplicar estilo geral
        self.setStyleSheet("""
            QWidget {
                background-color: white;
                font-family: 'Segoe UI', Arial, sans-serif;
            }
        """)
    
    def add_todo(self):
        dialog = AddTodoDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            text = dialog.get_text()
            if text:
                priority = dialog.get_priority()
                todo = TodoItem(text, priority=priority)
                self.todos.append(todo)
                self.save_todos()
                self.refresh_list()
    
    def clear_completed(self):
        completed_count = sum(1 for todo in self.todos if todo.completed)
        if completed_count == 0:
            BiodeskMessageBox.information(self, "Info", "Não há tarefas concluídas para limpar.")
            return
        
        reply = BiodeskMessageBox.question(
            self, "Confirmar", 
            f"Deseja remover {completed_count} tarefa(s) concluída(s)?"
        )
        
        if reply:
            self.todos = [todo for todo in self.todos if not todo.completed]
            self.save_todos()
            self.refresh_list()
    
    def refresh_list(self):
        self.list_widget.clear()
        
        # Ordenar: não concluídas primeiro, depois por prioridade
        priority_order = {'Alta': 0, 'Normal': 1, 'Baixa': 2}
        sorted_todos = sorted(
            self.todos, 
            key=lambda x: (x.completed, priority_order.get(x.priority, 1))
        )
        
        for i, todo in enumerate(sorted_todos):
            # Criar texto formatado para o item
            priority_symbols = {'Alta': '🔴', 'Normal': '🟡', 'Baixa': '⚪'}
            status_symbol = '✅' if todo.completed else '⏳'
            
            # Texto principal
            display_text = f"{status_symbol} {priority_symbols.get(todo.priority, '🟡')} {todo.text}"
            if todo.completed:
                display_text = f"~~{display_text}~~"  # Riscado
            
            # Adicionar data
            date_str = todo.created_date.split()[0] if todo.created_date else "N/A"
            display_text += f"\n    📅 {date_str}"
            
            # Criar item da lista
            item = QListWidgetItem(display_text)
            
            # Definir fonte e estilo
            font = QFont()
            font.setPointSize(12)
            if todo.completed:
                font.setStrikeOut(True)
                item.setForeground(Qt.GlobalColor.gray)
            else:
                font.setStrikeOut(False)
                item.setForeground(Qt.GlobalColor.black)
            
            item.setFont(font)
            
            # Armazenar referência ao todo no item
            item.setData(Qt.ItemDataRole.UserRole, i)
            
            # Adicionar à lista
            self.list_widget.addItem(item)
        
        # Conectar duplo clique para alternar status
        self.list_widget.itemDoubleClicked.connect(self.toggle_item_status)
        
        self.update_counter()
    
    def toggle_item_status(self, item):
        """Alterna o status de concluído ao fazer duplo clique"""
        index = item.data(Qt.ItemDataRole.UserRole)
        if index is not None and 0 <= index < len(self.todos):
            # Encontrar o todo original na lista não ordenada
            todo_to_toggle = None
            priority_order = {'Alta': 0, 'Normal': 1, 'Baixa': 2}
            sorted_todos = sorted(
                self.todos, 
                key=lambda x: (x.completed, priority_order.get(x.priority, 1))
            )
            if 0 <= index < len(sorted_todos):
                todo_to_toggle = sorted_todos[index]
                todo_to_toggle.completed = not todo_to_toggle.completed
                self.save_todos()
                self.refresh_list()
    
    def keyPressEvent(self, event):
        """Permite deletar itens com a tecla Delete"""
        if event.key() == Qt.Key.Key_Delete:
            current_item = self.list_widget.currentItem()
            if current_item:
                self.delete_selected_item()
        else:
            super().keyPressEvent(event)
    
    def delete_selected_item(self):
        """Deleta o item selecionado"""
        current_item = self.list_widget.currentItem()
        if current_item:
            index = current_item.data(Qt.ItemDataRole.UserRole)
            if index is not None:
                priority_order = {'Alta': 0, 'Normal': 1, 'Baixa': 2}
                sorted_todos = sorted(
                    self.todos, 
                    key=lambda x: (x.completed, priority_order.get(x.priority, 1))
                )
                if 0 <= index < len(sorted_todos):
                    todo_to_delete = sorted_todos[index]
                    reply = BiodeskMessageBox.question(
                        self, "Confirmar", 
                        f"Deseja deletar a tarefa:\n'{todo_to_delete.text}'?"
                    )
                    
                    if reply:
                        self.todos.remove(todo_to_delete)
                        self.save_todos()
                        self.refresh_list()
    
    def update_counter(self):
        total = len(self.todos)
        completed = sum(1 for todo in self.todos if todo.completed)
        pending = total - completed
        self.counter_label.setText(f"📊 Total: {total} | ✅ Concluídas: {completed} | ⏳ Pendentes: {pending}")
    
    def save_todos(self):
        try:
            data = [todo.to_dict() for todo in self.todos]
            with open('todos.json', 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Erro ao salvar todos: {e}")
    
    def load_todos(self):
        try:
            if os.path.exists('todos.json'):
                with open('todos.json', 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.todos = [TodoItem.from_dict(item) for item in data]
        except Exception as e:
            print(f"Erro ao carregar todos: {e}")
            self.todos = []
    
    def closeEvent(self, event):
        self.save_todos()
        event.accept()

# Este módulo é importado pelo main_window.py
if __name__ == "__main__":
    print("⚠️  Este módulo deve ser executado através do main_window.py")
    print("🚀 Execute: python main_window.py")
    sys.exit(1)

import sys
import copy

from binaryninja import LowLevelILOperation, PluginCommand, log_debug, log_info, log_error, log_alert
from PySide6.QtCore import Qt, QModelIndex, QAbstractTableModel
from PySide6.QtWidgets import (QDialog, QApplication, QTableView, QVBoxLayout, QHBoxLayout,
                               QPushButton, QLabel, QLineEdit)


class IndirectBranchModel(QAbstractTableModel):
    COL_ARCH = 0
    COL_ADDRESS = 1

    def __init__(self, initial_data, default_branch, parent=None):
        QAbstractTableModel.__init__(self, parent)
        self.default_branch = default_branch
        self.headers = ['arch', 'address']
        self.branches = initial_data

    def append_row(self, addr_str):
        row = self.rowCount(None)
        addr = self.parse_int(addr_str)
        if addr is None:
            return

        # Avoid duplicate entries
        if any([branch[self.COL_ADDRESS] == addr for branch in self.branches]):
            return

        self.insertRows(row)
        self.setData(self.index(row, self.COL_ARCH), self.default_branch[self.COL_ARCH])
        self.setData(self.index(row, self.COL_ADDRESS), hex(addr))

    def parse_int(self, val):
        try:
            if val.startswith("0x"):
                res = int(val, 16)
            else:
                res = int(val)
        except ValueError:
            log_error("Couldn't cast '%s' to int" % (val))
            res = None

        return res

    # -----
    def rowCount(self, _):
        return len(self.branches)

    def columnCount(self, _):
        return len(self.headers)

    def headerData(self, col, orientation, role):
        if role == Qt.DisplayRole and orientation == Qt.Orientation.Horizontal:
            return self.headers[col]

    def data(self, index, role):
        row = index.row()
        col = index.column()

        if role == Qt.DisplayRole:
            branch = self.branches[row]
            if col == self.COL_ARCH:
                return branch[col].name
            elif col == self.COL_ADDRESS:
                return hex(int(branch[col]))

    def flags(self, index):
        col = index.column()

        original_flags = super(IndirectBranchModel, self).flags(index)
        if col == self.COL_ADDRESS:
            return original_flags | Qt.ItemIsEditable | Qt.ItemIsEnabled | Qt.ItemIsSelectable
        else:
            return original_flags

    def setData(self, index, value, role=Qt.EditRole):
        row = index.row()
        col = index.column()

        branch = self.branches[row]
        if value != "" and col == self.COL_ADDRESS:
            addr = self.parse_int(value)
            if addr is None:
                return False

            branch[col] = addr
            return True

        return False

    def insertRows(self, row, rows=1, index=QModelIndex()):
        self.beginInsertRows(QModelIndex(), row, row + rows - 1)

        for i in range(rows):
            self.branches.insert(row + i, copy.copy(self.default_branch))

        self.endInsertRows()
        return True

    def removeRows(self, row, rows=1, index=QModelIndex()):
        self.beginRemoveRows(QModelIndex(), row, row + rows - 1)

        del self.branches[row:row + rows]

        self.endRemoveRows()
        return True


class IndirectBranchSetterWidget(QDialog):
    def __init__(self, bv, addr, parent=None):
        super(IndirectBranchSetterWidget, self).__init__(parent)

        self.bv = bv
        self.indirect_jmp_addr = addr
        # @@FIXME: What happens when there is more than one function for the same addr
        self.func = self.bv.get_functions_containing(self.indirect_jmp_addr)[0]

        # Setup widget properties
        self.setWindowModality(Qt.NonModal)
        self.showNormal()  # Makes 'Qt.NonModal' work. Why?

        title = QLabel(self.tr("Indirect Branch Editor (for 0x%x)" % (self.indirect_jmp_addr)))
        self.setWindowTitle(title.text())

        # Table
        initial_data = []
        for i in self.func.get_indirect_branches_at(self.indirect_jmp_addr):
            initial_data.append([i.dest_arch, int(i.dest_addr)])

        self.table_model = IndirectBranchModel(initial_data, [self.bv.arch, 0], parent=self)
        self.table_view = QTableView()
        self.table_view.setModel(self.table_model)

        # Buttons and line edit
        self.line_edit_new_branch = QLineEdit()

        button_insert_row = QPushButton("Insert branch")
        button_insert_row.clicked.connect(self.insert_row_clicked)

        button_remove_row = QPushButton("Remove selected")
        button_remove_row.clicked.connect(self.remove_row_clicked)

        button_set_indirect_branches = QPushButton("Done")
        button_set_indirect_branches.clicked.connect(self.set_indirect_branches_clicked)

        # Buttons layout
        buttons_layout = QHBoxLayout()
        buttons_layout.addWidget(self.line_edit_new_branch)
        buttons_layout.addWidget(button_insert_row)
        buttons_layout.addWidget(button_remove_row)
        buttons_layout.addWidget(button_set_indirect_branches)

        # Main layout
        layout = QVBoxLayout(self)
        layout.addWidget(self.table_view)
        layout.addLayout(buttons_layout)
        self.setLayout(layout)

    def insert_row_clicked(self):
        new_addrs_str = self.line_edit_new_branch.text().strip()
        new_addrs_str = new_addrs_str.split(",")
        for addr_str in new_addrs_str:
            self.table_model.append_row(addr_str.strip())

    def remove_row_clicked(self):
        select = self.table_view.selectionModel()
        if select.hasSelection():
            rows_selected = set()
            for i in select.selectedIndexes():
                rows_selected.add(i.row())
            assert len(rows_selected) >= 1

            # Hopefully this sort is enough to delete the correct rows.
            sorted_rows_selected = sorted(list(rows_selected), reverse=True)
            for row in sorted_rows_selected:
                self.table_model.removeRows(row)
        else:
            log_error("No selection to remove")

    def set_indirect_branches_clicked(self):
        branches = self.table_model.branches
        log_debug("Setting 0x%x's indirect branches to: %s" % (self.indirect_jmp_addr, branches))

        self.func.set_user_indirect_branches(self.indirect_jmp_addr, branches)

        self.accept()


def launch_plugin(bv, addr):
    widget = IndirectBranchSetterWidget(bv, addr)
    widget.exec_()


_name = "Indirect branches setter"
_description = "A plugin for setting indirect branches more easily, when binja fails to recognized a jump table"
PluginCommand.register_for_address(_name, _description, launch_plugin)

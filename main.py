import asyncio
import json
import os
import sys

import aiohttp
import requests
from PyQt5 import QtCore, QtGui, QtWidgets
from pynput import keyboard
from qasync import QEventLoop, asyncSlot

from app import API_KEY
from app.custom_dialog import CustomDialog
from app.mylabel import MyLabel
from app.mystatustray import MySystemTray

APIKEY: str = API_KEY
LIMIT: int = 15
FILTER: str = 'minimal'
BUFFERS: list = []
TRENDING_GIFS: list = []
SEARCH_RESULTS: list = []

label_style: str = '''
            font-family: "Lucida Sans Unicode", "Lucida Grande", sans-serif;
            font-size: 20px;
            font-weight: 700;
            text-decoration: rgb(68, 68, 68);
            font-style: normal;
            font-variant: small-caps;'''
trend_label_style: str = '''
            font-family: "Lucida Sans Unicode", "Lucida Grande", sans-serif;
            font-size: 14px;
            font-weight: 700;
            font-variant: small-caps;
            padding: 9px;
            margin: 2px;
            border: 1px inset #D6D6D6;
            '''


class MainWindow(QtWidgets.QMainWindow):
    loop: QEventLoop = None

    def __init__(self, event_loop: QEventLoop = None):
        super(MainWindow, self).__init__()
        self.setWindowTitle("Tenor Statusbar Gifs")
        self.setWindowIcon(QtGui.QIcon(QtGui.QPixmap(f"{os.path.abspath(os.path.dirname(__file__))}/app/res/logo.png")))
        QtWidgets.qApp.focusChanged.connect(self.on_focus_changed)
        self.setWindowFlag(QtCore.Qt.WindowStaysOnTopHint)

        # Menubar
        self.menubar = self.menuBar()
        self.trending_gifs_action = self.menubar.addAction('Back to &Trending GIFs')
        self.settings_menu = self.menubar.addMenu('&Settings')
        self.quit_menu = self.menubar.addAction('&Quit')
        self.trending_gifs_action.setVisible(False)
        self.hide_menu = QtWidgets.QAction('&Hide on focus lost', self)
        self.hide_menu.setCheckable(True)
        self.hide_menu.setChecked(True)
        self.hide_menu.toggled.connect(self.set_hide_on_focus_lost_toggle)
        self.col_count_menu = QtWidgets.QMenu('&Column Count', self)
        self.one_col_menu = QtWidgets.QAction('&1', self)
        self.two_col_menu = QtWidgets.QAction('&2', self)
        self.three_col_menu = QtWidgets.QAction('&3', self)
        self.four_col_menu = QtWidgets.QAction('&4', self)
        self.five_col_menu = QtWidgets.QAction('&5', self)

        self.settings_menu.addMenu(self.col_count_menu)
        self.settings_menu.addAction(self.hide_menu)
        self.col_count_menu.addAction(self.one_col_menu)
        self.col_count_menu.addAction(self.two_col_menu)
        self.col_count_menu.addAction(self.three_col_menu)
        self.col_count_menu.addAction(self.four_col_menu)
        self.col_count_menu.addAction(self.five_col_menu)

        self.one_col_menu.triggered.connect(lambda: self.adjust_cols(1))
        self.two_col_menu.triggered.connect(lambda: self.adjust_cols(2))
        self.three_col_menu.triggered.connect(lambda: self.adjust_cols(3))
        self.four_col_menu.triggered.connect(lambda: self.adjust_cols(4))
        self.five_col_menu.triggered.connect(lambda: self.adjust_cols(5))
        self.trending_gifs_action.triggered.connect(self.get_startup_view)

        # Shortcut to quit application
        self.quit = QtWidgets.QShortcut(QtGui.QKeySequence('Ctrl+Q'), self)
        self.quit_menu.triggered.connect(lambda: sys.exit(qt_application.exec_()))
        self.quit.activated.connect(lambda: sys.exit(qt_application.exec_()))

        # Dif. Variables
        self.loop: QEventLoop = event_loop or asyncio.get_event_loop()
        self.search_type: str = 'Ranked'
        self.type_of_search: str = 'search'
        self.global_shortcut: str = '<ctrl>+<shift>+g'
        self.prev_search: str = ''
        self.is_signal_connected: bool = False
        self.switched_search_type: bool = False
        self.should_hide_on_focus_lost: bool = True
        self.new_search_term: bool = False
        self.follow_up_search: bool = False
        self.row: int = 0
        self.col: int = 0
        self.col_choice: int = 3
        self.search_pos: int = 0
        self.start_pos: int = 0

        # Labels
        self.trending_gifs_label: QtWidgets.QLabel = QtWidgets.QLabel("Trending Gifs")
        self.trending_terms_label: QtWidgets.QLabel = QtWidgets.QLabel("Trending searches")
        self.trending_gifs_label.setStyleSheet(label_style)
        self.trending_terms_label.setStyleSheet(label_style)

        # Scrollareas
        self.scroll_area: QtWidgets.QScrollArea = QtWidgets.QScrollArea()
        self.scroll_area.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFixedSize(275 * self.col_choice, 600)
        self.horizontal_scroll_area: QtWidgets.QScrollArea = QtWidgets.QScrollArea()
        self.horizontal_scroll_area.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.horizontal_scroll_area.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOn)
        self.horizontal_scroll_area.setWidgetResizable(True)
        self.horizontal_scroll_area.setFixedHeight(80)

        # Widgets
        self.main_widget: QtWidgets.QWidget = QtWidgets.QWidget()
        self.trending_terms_widget: QtWidgets.QWidget = QtWidgets.QWidget()
        self.gif_grid_layout = QtWidgets.QWidget()

        # Buttons
        self.button_for_more: QtWidgets.QPushButton = QtWidgets.QPushButton("More...")
        self.button_for_more.clicked.connect(self.load_more)
        self.search_button: QtWidgets.QPushButton = QtWidgets.QPushButton("Ranked")
        self.search_button.setToolTip("Click to change the search results from ranked to random!")
        self.search_button.clicked.connect(self.change_search_type)

        # Icon for Searchbar
        # Thanks to eyllanesc in https://stackoverflow.com/questions/51649332/how-to-make-size-of-button-in-the-lineedit-smaller
        load_icon = QtGui.QPixmap(f"{os.path.abspath(os.path.dirname(__file__))}/app/res/clear.png")
        fixed_icon = QtGui.QPixmap(load_icon.size() * 10 / 7)
        rect = QtCore.QRect(load_icon.rect())
        rect.moveCenter(fixed_icon.rect().center())
        fixed_icon.fill(QtCore.Qt.transparent)
        painter = QtGui.QPainter(fixed_icon)
        painter.drawPixmap(rect, load_icon)
        painter.end()

        # Searchbar
        self.searchbar: QtWidgets.QLineEdit = QtWidgets.QLineEdit()
        self.searchbar.addAction(QtGui.QIcon(fixed_icon),
                                 QtWidgets.QLineEdit.ActionPosition.TrailingPosition).triggered.connect(
            self.searchbar.clear)
        self.searchbar.setPlaceholderText('Search Tenor...')
        self.searchbar.returnPressed.connect(self.search_gif)
        self.searchbar.textEdited.connect(lambda x: self.get_autocomplete_data(x))
        self.autocompleter = QtWidgets.QCompleter()
        self.autocompleter.setCompletionMode(QtWidgets.QCompleter.CompletionMode.UnfilteredPopupCompletion)
        self.autocompleter.activated.connect(self.search_gif)
        self.searchbar.setCompleter(self.autocompleter)
        self.autocomplete_model = QtCore.QStringListModel()
        self.autocompleter.setModel(self.autocomplete_model)

        # Layouts
        self.main_layout: QtWidgets.QGridLayout = QtWidgets.QGridLayout()
        self.trending_terms_layout: QtWidgets.QHBoxLayout = QtWidgets.QHBoxLayout()

        self.main_layout.addWidget(self.searchbar, 0, 0)
        self.main_layout.addWidget(self.search_button, 0, 2)
        self.main_layout.addWidget(self.trending_terms_label, 1, 0, 1, 3)
        self.main_layout.addWidget(self.horizontal_scroll_area, 2, 0, 1, 3)
        self.main_layout.addWidget(self.trending_gifs_label, 3, 0, 1, 3)
        self.main_layout.addWidget(self.gif_grid_layout, 4, 0, 1, 3)
        self.main_layout.addWidget(self.button_for_more, 5, 0, 1, 4)

        self.trending_terms_widget.setLayout(self.trending_terms_layout)
        self.main_widget.setLayout(self.main_layout)

        self.horizontal_scroll_area.setWidget(self.trending_terms_widget)
        self.scroll_area.setWidget(self.main_widget)
        self.setCentralWidget(self.scroll_area)
        self.setMaximumSize(self.scroll_area.size())

        # Center Window for first startup
        self.geo = self.frameGeometry()
        self.geo.moveCenter(QtWidgets.QDesktopWidget().availableGeometry().center())
        self.last_window_position: QtCore.QPoint = self.geo.topLeft()
        self.move(self.geo.topLeft())

        # START
        self.load_settings()

    def changeEvent(self, event: QtCore.QEvent) -> None:
        if event.type() == QtCore.QEvent.Type.WindowStateChange:
            if self.windowState() & QtCore.Qt.WindowState.WindowMinimized:
                self.closeEvent(event)

    def closeEvent(self, event: QtGui.QCloseEvent) -> None:
        self.last_window_position = self.pos()
        mainwindow_handler(False)

    def set_hide_on_focus_lost_toggle(self) -> None:
        self.should_hide_on_focus_lost = not self.should_hide_on_focus_lost
        self.save_settings()

    def load_settings(self) -> None:
        load_path = f'{os.path.abspath(os.path.dirname(__file__))}/app/settings.json'
        try:
            with open(load_path, 'r') as load_file:
                load_data = json.load(load_file)
                self.global_shortcut = load_data['global_shortcut']
                self.hide_menu.setChecked(load_data['should_hide'])
                self.adjust_cols(int(load_data['col_count']))
                self.get_trending_search_terms()
        except Exception:
            self.get_startup_view()
            self.get_trending_search_terms()

    def save_settings(self) -> None:
        save_path = f'{os.path.abspath(os.path.dirname(__file__))}/app/settings.json'
        save_data = {'col_count': self.col_choice,
                     'should_hide': self.should_hide_on_focus_lost,
                     'global_shortcut': self.global_shortcut}
        fd = os.open(save_path, os.O_CREAT | os.O_RDWR)
        if fd != -1:
            f = os.fdopen(fd, 'w+')
            json.dump(save_data, f)
            f.truncate()

    def adjust_cols(self, new_col: int) -> None:
        global LIMIT
        self.col_choice = new_col
        self.scroll_area.setFixedSize(275 * self.col_choice, 600)
        self.setMaximumSize(self.scroll_area.size())
        LIMIT = 5 * self.col_choice
        self.save_settings()
        self.get_startup_view()

    def change_search_type(self) -> None:
        if self.search_type == "Ranked":
            self.search_type = "Random"
            self.search_button.setToolTip("Click to change the search results from random to ranked!")
            self.switched_search_type = True
        else:
            self.search_type = "Ranked"
            self.search_button.setToolTip("Click to change the search results from ranked to random!")
            self.switched_search_type = True
        self.search_button.setText(self.search_type)
        if self.is_signal_connected:
            self.scroll_area.verticalScrollBar().rangeChanged.disconnect(self.scroll_to_bottom)
            self.is_signal_connected = False
        if len(self.searchbar.text()) > 0:
            self.searchbar.returnPressed.emit()

    def on_focus_changed(self, old: object, new: object) -> None:
        if new is None and self.should_hide_on_focus_lost:
            self.closeEvent(QtGui.QCloseEvent)

    def scroll_to_bottom(self) -> None:
        scroll_bar = self.scroll_area.verticalScrollBar()
        if self.new_search_term:
            scroll_bar.setValue(0)
        else:
            scroll_bar.setValue(scroll_bar.maximum())

    def copy_gif_to_clipboard(self, button: str, gif: MyLabel) -> None:
        if gif.data is not None:
            if button == "left":
                clipboard = QtWidgets.QApplication.clipboard()
                clipboard.setText(gif.data['gif']['url'])
            else:
                ctx_menu_gif: QtWidgets.QMenu = QtWidgets.QMenu()
                save_gif: QtWidgets.QAction = QtWidgets.QAction("Save Gif")
                ctx_menu_gif.addAction(save_gif)
                action = ctx_menu_gif.exec_(QtGui.QCursor.pos())
                if action == save_gif:
                    self.save_gif(gif)

    def save_gif(self, gif: MyLabel) -> None:
        desktop = os.path.join(os.path.join(os.path.expanduser('~')), 'Desktop')
        file_name, _ = QtWidgets.QFileDialog.getSaveFileName(self, "Save Gif", desktop, "GIF (*.gif)")
        if file_name:
            if not file_name.endswith(".gif"):
                file_name += ".gif"
                if os.path.isfile(file_name):
                    custom_dialog = CustomDialog(dialog_title="Filename Exists",
                                                 dialog_text=f"{file_name.split('/')[-1]} already exists.\n"
                                                             f"Do you want to replace it?")
                    if not custom_dialog.exec_():
                        return
            with open(file_name, 'wb') as user_file_name:
                user_file_name.write(requests.get(gif.data['gif']['url']).content)

    def get_trending_term(self, mouse_button: str, label_data: MyLabel) -> None:
        self.searchbar.setText(label_data.name)
        self.searchbar.returnPressed.emit()

    @asyncSlot()
    async def get_autocomplete_data(self, text: str) -> None:
        url = "https://g.tenor.com/v1/autocomplete?q=%s&key=%s&limit=%s" % (text, APIKEY, LIMIT)
        async with aiohttp.ClientSession() as session:
            response: dict = await self.fetch(session, url, 'json')
            self.autocomplete_model.setStringList(response['results'])

    @asyncSlot()
    async def load_more(self) -> None:
        self.scroll_area.verticalScrollBar().rangeChanged.connect(self.scroll_to_bottom)
        self.is_signal_connected = True
        self.follow_up_search = True
        self.start_pos += LIMIT
        await self.search_gif()

    @asyncSlot()
    async def get_trending_search_terms(self) -> None:
        async with aiohttp.ClientSession() as session:
            url = "https://g.tenor.com/v1/trending_terms?key=%s&limit=%s&locale=%s&" % (APIKEY, LIMIT, 'en_US')
            response: dict = await self.fetch(session, url, 'json')
        for result in response['results']:
            trend_button: MyLabel = MyLabel(result)
            trend_button.setToolTip("")
            trend_button.setStyleSheet(trend_label_style)
            trend_button.got_clicked.connect(self.get_trending_term)
            trend_button.setText(result.title())
            self.trending_terms_layout.addWidget(trend_button)

    @asyncSlot()
    async def get_startup_view(self) -> None:
        self.trending_gifs_label.setText('Trending Gifs')
        self.searchbar.clear()
        url = "https://g.tenor.com/v1/trending?key=%s&limit=%s&media_filter=%s&" % (APIKEY, LIMIT, FILTER)
        self.trending_gifs_action.setVisible(False)
        await self.query_tenor(url=url, array_to_append=TRENDING_GIFS)

    @asyncSlot()
    async def search_gif(self) -> None:
        if len(self.searchbar.text()) == 0:
            await self.get_startup_view()
            return
        if (self.searchbar.text() != self.prev_search) and self.searchbar.text() != '':
            self.new_search_term = True
            self.prev_search = self.searchbar.text()
        else:
            self.new_search_term = False
        self.type_of_search = "search" if self.search_type == "Ranked" else 'random'
        self.trending_gifs_label.setText(f"Search Results for {self.searchbar.text()} {self.search_type}")
        url = "https://g.tenor.com/v1/%s?q=%s&key=%s&limit=%s&media_filter=%s&" % (
            self.type_of_search, self.searchbar.text(), APIKEY, LIMIT, FILTER)
        self.trending_gifs_action.setVisible(True)
        if self.new_search_term or self.follow_up_search or self.switched_search_type:
            self.switched_search_type = False
            await self.query_tenor(url=url, array_to_append=SEARCH_RESULTS)

    @asyncSlot()
    async def query_tenor(self, url: str, array_to_append: list) -> None:
        global LIMIT
        async with aiohttp.ClientSession() as session:
            if not self.follow_up_search:
                response: dict = await self.fetch(session, url, 'json')
            else:
                response: dict = await self.fetch(session, url + "pos=%s" % self.search_pos, 'json')
        self.search_pos = response["next"]
        for r in response['results']:
            array_to_append.append(r)
        if len(array_to_append) < LIMIT:
            self.button_for_more.setEnabled(False)
        else:
            self.button_for_more.setEnabled(True)
        await self.set_gifs(data_to_append=array_to_append, length=len(array_to_append))

    @asyncSlot()
    async def set_gifs(self, data_to_append: list, length: int) -> None:
        global BUFFERS, TRENDING_GIFS, SEARCH_RESULTS, LIMIT
        if not self.follow_up_search:
            BUFFERS = []
            self.start_pos = 0
            self.gif_grid_layout.deleteLater()
            self.gif_grid_layout = QtWidgets.QWidget()
            self.gif_grid_layout.layout = QtWidgets.QGridLayout()
            self.gif_grid_layout.setLayout(self.gif_grid_layout.layout)
            self.row = 0
            self.col = 0
        async with aiohttp.ClientSession() as session:
            for i in range(length):
                gif_url = data_to_append[i]['media'][0]['tinygif']['url']
                BUFFERS.append(QtCore.QBuffer())
                if self.col == self.col_choice:
                    self.col = 0
                    self.row += 1
                gif_label = MyLabel(name=f'test{i}', data=data_to_append[i]['media'][0])
                gif_label.got_clicked.connect(self.copy_gif_to_clipboard)
                BUFFERS[i + self.start_pos].setData(await self.fetch(session, gif_url, 'content'))
                movie = QtGui.QMovie(BUFFERS[i + self.start_pos], QtCore.QByteArray())
                gif_label.setMovie(movie)
                movie.start()
                self.gif_grid_layout.layout.addWidget(gif_label, self.row, self.col)
                self.col += 1
        self.main_layout.addWidget(self.gif_grid_layout, 4, 0, 1, 3)
        TRENDING_GIFS = []
        SEARCH_RESULTS = []
        self.follow_up_search = False

    @asyncSlot()
    async def fetch(self, session: aiohttp.ClientSession, url: str, kind: str) -> aiohttp.ClientResponse:
        async with session.get(url) as response:
            if response.status == 200:
                if kind == "json":
                    return await response.json()
                if kind == "content":
                    return await response.read()


def mainwindow_handler(open_bool: bool) -> None:
    if open_bool:
        window.scroll_area.verticalScrollBar().setValue(0)
        window.move(window.last_window_position)
        window.show()
    else:
        window.hide()


def on_activate() -> None:
    mainwindow_handler(True)


def for_canonical(f) -> None:
    return lambda k: f(listener.canonical(k))


if __name__ == '__main__':
    qt_application: QtWidgets.QApplication = QtWidgets.QApplication(sys.argv)
    loop: QEventLoop = QEventLoop(qt_application)

    main_tray: MySystemTray = MySystemTray()
    main_tray.setIcon(QtGui.QIcon(QtGui.QPixmap(f"{os.path.abspath(os.path.dirname(__file__))}/app/res/logo.png")))
    main_tray.setVisible(True)

    menu: QtWidgets.QMenu = QtWidgets.QMenu()
    quit_tray: QtWidgets.QAction = QtWidgets.QAction("Quit")

    main_tray.open_main_signal.connect(mainwindow_handler)
    quit_tray.triggered.connect(lambda: sys.exit(qt_application.exec_()))
    menu.addAction(quit_tray)
    main_tray.setContextMenu(menu)

    asyncio.set_event_loop(loop)
    window: MainWindow = MainWindow(loop)
    window.show()

    hotkey: keyboard.HotKey = keyboard.HotKey(keyboard.HotKey.parse(window.global_shortcut), on_activate)
    listener: keyboard.Listener = keyboard.Listener(on_press=for_canonical(hotkey.press),
                                                    on_release=for_canonical(hotkey.release))
    listener.start()

    qt_application.setQuitOnLastWindowClosed(False)
    qt_application.exec_()

    with loop:
        loop.run_forever()

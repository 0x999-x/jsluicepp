from burp import IBurpExtender, IHttpListener, ITab, IExtensionStateListener, IContextMenuFactory
from threading import Thread, Timer, Semaphore
from time import time
from javax.swing.table import DefaultTableCellRenderer
from javax.swing.filechooser import FileNameExtensionFilter
from java.awt import Toolkit
from java.awt.datatransfer import StringSelection
import javax.swing.event
import java.awt.event
from java.net import URL
from javax.imageio import ImageIO
from java.io import ByteArrayInputStream
from base64 import b64decode
from hashlib import md5
from datetime import datetime, timedelta
from urlparse import urlparse
import javax.swing as swing
import java.awt as awt
import re
import os
import subprocess
import json
import distutils.spawn

class PopupMenu(awt.event.ActionListener, awt.event.MouseAdapter):
    def __init__(self, component, callbacks=None, selected_host="",file_names_list=None, processed_file_details=None, monitored_urls=None, logo_image=None, directory=None, monitored_urls_path=None, monitored_urls_directory=None):
        self.callbacks = callbacks
        self.popup = swing.JPopupMenu()
        self.component = component
        self.selected_host = selected_host
        self.file_names_list = file_names_list
        self.processed_file_details = processed_file_details
        self.monitored_urls = monitored_urls
        self.logo_image = logo_image
        self.directory = directory
        self.monitored_urls_path = monitored_urls_path
        self.monitored_urls_directory = monitored_urls_directory
        if isinstance(self.component, swing.JTable):
            self.menu_item_send_to_repeater = swing.JMenuItem("Send to Repeater")
            self.menu_item_send_to_repeater.addActionListener(self.sendToRepeater)
            self.popup.add(self.menu_item_send_to_repeater)
        elif isinstance(self.component, swing.JList):
            self.menu_item_copy_url = swing.JMenuItem("Copy URL")
            self.menu_item_copy_url.addActionListener(self.copyURL)
            self.popup.add(self.menu_item_copy_url)
            self.menu_item_monitor_url = swing.JMenuItem("Monitor URL")
            self.menu_item_monitor_url.addActionListener(self.monitor_url)
            self.popup.add(self.menu_item_monitor_url)

    def mouseReleased(self, e):
        self.showPopup(e)

    def mousePressed(self, e):
        self.showPopup(e)

    def showPopup(self, event):
        if event.isPopupTrigger():
            if isinstance(self.component, swing.JTable):
                row = self.component.rowAtPoint(event.getPoint())
                self.component.getSelectionModel().setSelectionInterval(row, row)
            elif isinstance(self.component, swing.JList):
                if self.component.getSelectedIndex() == -1:
                    return
                index = self.component.locationToIndex(event.getPoint())
                self.component.setSelectedIndex(index)
                url_monitored = False
                if self.monitored_urls is not None:
                    for url in self.monitored_urls:
                        if self.monitored_urls[url]['host'] == self.selected_host and self.monitored_urls[url]['file_name'] == self.file_names_list.getSelectedValue():
                            url_monitored = True
                            break
                    if url_monitored:
                        self.menu_item_monitor_url.setText("Stop Monitoring URL")
                    else:
                        self.menu_item_monitor_url.setText("Monitor URL")
            self.popup.show(self.component, event.getX(), event.getY())

    def monitor_url(self, event):
        if event.getSource() == self.menu_item_monitor_url:
            if self.file_names_list is None:
                return
            selected_file = self.file_names_list.getSelectedValue()
            selected_file_hash = md5(selected_file).hexdigest()
            for details in self.processed_file_details.values():
                if details.get('file_name') == selected_file and details.get('host') == self.selected_host:
                    processed_file_details = details
                    break
            if processed_file_details is not None:
                origin_url = processed_file_details['origin_url']
                host = processed_file_details['host']
                monitor_urls_file = open(self.directory + self.monitored_urls_path, "a+")
                monitor_urls_file.seek(0)
                for line in monitor_urls_file:
                    json_line = json.loads(line)
                    if json_line.get('origin_url') == origin_url and json_line.get('host') == host:
                        stop_monitor_confirmation_dialog = swing.JDialog()
                        stop_monitor_confirmation_dialog.setTitle("jsluice++ | Monitored URLs")
                        stop_monitor_confirmation_dialog.setModal(True)
                        stop_monitor_confirmation_dialog.setAlwaysOnTop(True)
                        stop_monitor_confirmation_dialog.setSize(644, 244)
                        label_font = awt.Font("Cantarell", awt.Font.BOLD, 14)
                        logo_label = swing.JLabel(swing.ImageIcon(self.logo_image))
                        logo_label.setVerticalAlignment(swing.JLabel.TOP)
                        stop_monitor_confirmation_dialog.getContentPane().add(logo_label, awt.BorderLayout.NORTH)
                        confirmation_label = swing.JLabel('Are you sure you want to stop monitoring "' + origin_url + '"?', swing.JLabel.CENTER)
                        confirmation_label.setFont(label_font)
                        stop_monitor_confirmation_dialog.getContentPane().add(confirmation_label, awt.BorderLayout.CENTER)
                        stop_monitor_confirmation_dialog.setLocationRelativeTo(None)
                        stop_monitor_confirmation_dialog.setDefaultCloseOperation(swing.WindowConstants.DISPOSE_ON_CLOSE)

                        button_panel = swing.JPanel()
                        button_panel.setLayout(swing.BoxLayout(button_panel, swing.BoxLayout.X_AXIS))

                        def stop_monitoring(event):
                            monitor_urls_file.seek(0)
                            lines = monitor_urls_file.readlines()
                            monitor_urls_file.seek(0)
                            for line in lines:
                                json_line = json.loads(line)
                                if json_line.get('origin_url') != origin_url:
                                    monitor_urls_file.write(line)
                            monitor_urls_file.truncate()
                            monitor_urls_file.close()
                            if os.path.exists(self.directory + self.monitored_urls_directory + host + "_" + selected_file_hash):
                                os.remove(self.directory + self.monitored_urls_directory + host + "_" + selected_file_hash)
                            if os.path.exists(self.directory + self.monitored_urls_directory + host + "_" + selected_file_hash + ".old"):
                                os.remove(self.directory + self.monitored_urls_directory + host + "_" + selected_file_hash + ".old")
                            del self.monitored_urls[origin_url]
                            self.file_names_list.repaint()
                            self.file_names_list.revalidate()
                            print("Stopped monitoring: " + origin_url)
                            stop_monitor_confirmation_dialog.dispose()

                        button = swing.JButton("Yes", actionPerformed=stop_monitoring)
                        button2 = swing.JButton("No", actionPerformed=lambda event: (stop_monitor_confirmation_dialog.dispose(), monitor_urls_file.close()))

                        button_panel.add(button)
                        button_panel.add(swing.Box.createHorizontalStrut(10))
                        button_panel.add(button2)

                        center_panel = swing.JPanel()
                        center_panel.setLayout(swing.BoxLayout(center_panel, swing.BoxLayout.Y_AXIS))
                        center_panel.add(swing.Box.createVerticalGlue())
                        center_panel.add(button_panel)
                        center_panel.add(swing.Box.createVerticalGlue())

                        stop_monitor_confirmation_dialog.getContentPane().add(center_panel, awt.BorderLayout.SOUTH)
                        stop_monitor_confirmation_dialog.pack()
                        stop_monitor_confirmation_dialog.setVisible(True)

                        return
                monitor_urls_file.write(json.dumps({'origin_url': origin_url, 'file_name': selected_file, 'host': host}) + "\n")
                monitor_urls_file.close()
                if not os.path.exists(self.directory + self.monitored_urls_directory):
                    os.makedirs(self.directory + self.monitored_urls_directory)
                monitor_url_file = open(self.directory + self.monitored_urls_directory + host + "_" + selected_file_hash, "w+")
                monitor_url_file.write(json.dumps(processed_file_details['output']))
                monitor_url_file.close()
                if origin_url not in self.monitored_urls:
                    print("Adding monitored URL: " + str(origin_url))
                    self.monitored_urls[origin_url] = {'origin_url': origin_url, 'file_name': selected_file, 'host': host}
                self.file_names_list.repaint()
                self.file_names_list.revalidate()

    def copyURL(self, event):
        if event.getSource() == self.menu_item_copy_url:
            if self.file_names_list is None:
                return
            selected_file = self.file_names_list.getSelectedValue()
            for details in self.processed_file_details.values():
                if details.get('file_name') == selected_file and details.get('host') == self.selected_host:
                    processed_file_details = details
                    break
            if processed_file_details is not None:
                origin_url = processed_file_details['origin_url']
                Toolkit.getDefaultToolkit().getSystemClipboard().setContents(StringSelection(origin_url), None)

    def sendToRepeater(self, event):
        if event.getSource() == self.menu_item_send_to_repeater:
            row = self.component.getSelectedRow()
            self.scheme = ''
            self.host = ''
            self.query_params = ''
            self.port = None
            use_https = False
            if row != -1:
                url = str(self.component.getValueAt(row, 0))
                if url.startswith("http:") or url.startswith("https:") or url.startswith("//"):
                    parsed_url = urlparse(url)
                    self.scheme = parsed_url.scheme
                    self.host = parsed_url.netloc if parsed_url.port not in [80, 443] else parsed_url.hostname
                    if "@" in self.host:
                        self.host = self.host.split("@")[1]
                    self.port = parsed_url.port
                    self.query_params = parsed_url.query
                    use_https = True if parsed_url.scheme == "https" else False
                    url = parsed_url.path
                if not url.startswith("/"):
                    url = "/" + url
                if self.host == '':
                    self.host = self.selected_host
                    self.port = int(self.host.split(':')[1]) if ':' in self.host else None
                port = self.port if self.port != None else 80 if self.scheme == "http" else 443
                if ":" in self.host:
                    port = int(self.host.split(":")[1])
                    self.host = self.host.split(":")[0]
                use_https = True if self.port == None and self.scheme != "http" else use_https
                bodyParams = str(self.component.getValueAt(row, 2))
                method = str(self.component.getValueAt(row, 3))
                headers_str = str(self.component.getValueAt(row, 4))
                is_json = False
                is_xml = False
                try:
                    headers_dict = json.loads(headers_str)
                except ValueError:
                    headers_dict = {}
                if method is None or method == "":
                    method = "GET"
                default_headers = [
                    "{method} {url}{query_params} HTTP/1.1".format(method=method, url=url, query_params="?" + self.query_params if self.query_params != '' else ''),
                    "Host: " + self.host,
                    "User-Agent: Mozilla/5.0 (Windows NT 10.0; rv:102.0) Gecko/20100101 Firefox/102.0",
                    "Accept: */*",
                    "Accept-Language: en-US,en;q=0.5",
                    "Accept-Encoding: gzip, deflate, br",
                    "Connection: close",
                    "Cache-Control: max-age=0",
                ]
                if headers_dict:
                    headers = default_headers + ["{}: {}".format(k, v) for k, v in headers_dict.items()]
                    for header in headers:
                        if header.lower().startswith('content-type'):
                            if 'application/json' in header:
                                is_json = True
                            elif any(mime_type in header for mime_type in ['application/xml', 'text/xml']):
                                is_xml = True
                            break
                else:
                    headers = default_headers
                if bodyParams.startswith('[') and bodyParams.endswith(']'):
                    bodyParams = bodyParams.strip('][').split(', ')
                    if is_json:
                        bodyParams = "{" + ",".join(['"{}":"{}"'.format(val.strip('"'), 'x') for val in bodyParams]) + "}"
                    elif is_xml:
                        bodyParams = "<root>" + "".join(["<{}>{}</{}>".format(val.strip('"'), 'x', val.strip('"')) for val in bodyParams]) + "</root>"
                    else:
                        bodyParams = "&".join(["{}={}".format(val.strip('"'), 'x') for val in bodyParams])
                else:
                    bodyParams = {}
                request = self.callbacks.getHelpers().buildHttpMessage(headers, bodyParams)
                self.callbacks.sendToRepeater(self.host, port, use_https, request, None)

class TextFieldsListener(swing.event.DocumentListener, awt.event.MouseAdapter):
    def __init__(self, callback, search_text_field, negative_match_text_field, positive_match_text_field, panel):
        self.callback = callback
        self.search_text_field = search_text_field
        self.negative_match_text_field = negative_match_text_field
        self.positive_match_text_field = positive_match_text_field
        self.search_text_field.setEditable(False)
        self.negative_match_text_field.setEditable(False)
        self.positive_match_text_field.setEditable(False)
        self.panel = panel

    def insertUpdate(self, event):
        self.callback(event)

    def removeUpdate(self, event):
        self.callback(event)

    def changedUpdate(self, event):
        self.callback(event)

    def handleTextFieldClick(self, textField, defaultText):
        field_text = textField.getText()
        if field_text == defaultText:
            textField.setText("")
            textField.setEditable(True)
            textField.setCaretPosition(0)
        elif field_text == "":
            textField.setText(defaultText)
            textField.setEditable(False)
            textField.setCaretPosition(0)

    def mouseClicked(self, event):
        if event.getSource() == self.search_text_field:
            self.handleTextFieldClick(self.search_text_field, "Search:")
        elif event.getSource() == self.negative_match_text_field:
            self.handleTextFieldClick(self.negative_match_text_field, "Negative Match:")
        elif event.getSource() == self.positive_match_text_field:
            self.handleTextFieldClick(self.positive_match_text_field, "Positive Match:")
        else:
            def set_default_text(field, default_text):
                if field.getText() == "":
                    field.setText(default_text)
                    field.setEditable(False)
                    self.panel.requestFocusInWindow()
                    field.setCaretPosition(0)

            search_text = self.search_text_field
            negative_match_text = self.negative_match_text_field
            positive_match_text = self.positive_match_text_field

            set_default_text(search_text, "Search:")
            set_default_text(negative_match_text, "Negative Match:")
            set_default_text(positive_match_text, "Positive Match:")

class ColorFiles(swing.DefaultListCellRenderer):
    def __init__(self, monitored_urls, processed_file_details, selected_host, directory, monitored_urls_directory):
        self.monitored_urls = monitored_urls
        self.selected_host = selected_host
        self.directory = directory
        self.monitored_urls_directory = monitored_urls_directory
        self.processed_file_details = {details['file_name']: details for details in processed_file_details.values() if details.get('host') == self.selected_host}
    
    def getListCellRendererComponent(self, list, value, index, isSelected, cellHasFocus):
        component = super(ColorFiles, self).getListCellRendererComponent(
            list, value, index, isSelected, cellHasFocus
        )
        if os.path.exists(self.directory+self.monitored_urls_directory+self.selected_host+"_"+md5(value).hexdigest()):
            component.setFont(component.getFont().deriveFont(awt.Font.BOLD))
            component.setForeground(awt.Color(110, 204, 154))
        else:
            component.setForeground(list.getForeground() if not isSelected else list.getSelectionForeground())

        component.setBackground(list.getSelectionBackground() if isSelected else list.getBackground())
        return component

class ColorFilters(swing.DefaultListCellRenderer):
    def __init__(self, results_filters):
        self.results_filters = results_filters
    def getListCellRendererComponent(self, list, value, index, isSelected, cellHasFocus):
        component = super(ColorFilters, self).getListCellRendererComponent(
            list, value, index, isSelected, cellHasFocus
        )
        component.setForeground(awt.Color.BLACK)
        filter_type = self.results_filters.get(value)
        color_map = {'negative': awt.Color(240,128,128), 'positive': awt.Color(201,255,229)}
        component.setBackground(color_map.get(filter_type, list.getBackground()))
        if isSelected:
            component.setForeground(color_map.get(filter_type, list.getForeground()))
            component.setBackground(list.getSelectionBackground())
        return component

class ColorHosts(swing.DefaultListCellRenderer):
    def __init__(self, hosts_with_secrets, secret_image_base64):
        self.hosts_with_secrets = hosts_with_secrets
        secret_image_base64 = secret_image_base64
        secret_image_bytes = b64decode(secret_image_base64)
        secret_image_stream = ByteArrayInputStream(secret_image_bytes)
        secret_image_resized = ImageIO.read(secret_image_stream).getScaledInstance(16, 16, awt.Image.SCALE_SMOOTH)
        self.icon = swing.ImageIcon(secret_image_resized)
    def getListCellRendererComponent(self, listbox, value, index, isSelected, cellHasFocus):
        icon = None
        if value in self.hosts_with_secrets:
            self.setText(str(value))
            if self.getIcon() is None:
                self.setIcon(self.icon)
            icon = self.icon
            if isSelected:
                self.setBackground(listbox.getSelectionBackground())
                self.setForeground(awt.Color(255, 102, 102))
            else:
                self.setBackground(swing.UIManager.getColor("Label.background"))
                self.setForeground(awt.Color(255, 102, 102))
            font_metrics = self.getFontMetrics(self.getFont())
            text_width = font_metrics.stringWidth(str(value))
            icon_width = icon.getIconWidth()
            self.setHorizontalAlignment(swing.JLabel.LEFT)
            self.setHorizontalTextPosition(swing.JLabel.RIGHT)
            label_width = self.getSize().width
            icon_text_gap = label_width - (text_width + icon_width)
            self.setIconTextGap(icon_text_gap)
            return self
        else:
            label = swing.JLabel(str(value))
            label.setBackground(swing.UIManager.getColor("Label.background"))
            label.setOpaque(True)
            icon = None
            if isSelected:
                label.setForeground(listbox.getSelectionForeground())
                label.setBackground(listbox.getSelectionBackground())
            label.setBorder(javax.swing.BorderFactory.createEmptyBorder(0, 6, 0, 0))
            return label

class ColorResults(DefaultTableCellRenderer):
    def __init__(self, differences, deleted_lines):
        self.differences = differences
        self.deleted_lines = deleted_lines
    def getTableCellRendererComponent(self, table, value, isSelected, hasFocus, row, column):
        component = super(ColorResults, self).getTableCellRendererComponent(table, value, isSelected, hasFocus, row, column)
        view_row = table.convertRowIndexToModel(row)
        row_data = tuple(table.getModel().getValueAt(view_row, col) for col in range(table.getColumnCount()))
        if row_data in self.differences:
            component.setBackground(awt.Color(201,255,229))
            component.setForeground(awt.Color.BLACK)
        elif row_data in self.deleted_lines:
            component.setBackground(awt.Color(255, 204, 204))
            component.setForeground(awt.Color.BLACK)
        else:
            if row % 2 == 0:
                component.setBackground(swing.UIManager.getColor("Table.background"))
                component.setForeground(swing.UIManager.getColor("Table.foreground"))
            else:
                component.setBackground(swing.UIManager.getColor("Table.alternateRowColor"))
                component.setForeground(swing.UIManager.getColor("Table.foreground"))
        if isSelected:
            component.setBackground(table.getSelectionBackground())
            if row_data in self.differences:
                component.setForeground(awt.Color(201,255,229))
            elif row_data in self.deleted_lines:
                component.setForeground(awt.Color(255, 204, 204))
            else:
                component.setForeground(table.getSelectionForeground())

        return component

class BurpExtender(IBurpExtender, IHttpListener, ITab, IExtensionStateListener, IContextMenuFactory):
    def registerExtenderCallbacks(self, callbacks):
        self._callbacks = callbacks
        self._helpers = callbacks.getHelpers()
        callbacks.setExtensionName("jsluice++")
        self.monitored_urls = {}
        self.processed_file_details = {}
        self.results_filters = {}
        self.unique_secrets = set()
        self.seen_endpoints = set()
        self.hosts_list = set()
        self.hosts_with_secrets = set()
        self.selected_host = ""
        self.directory = ".jsluicepp"
        self.monitored_urls_path = "/monitored_urls.txt"
        self.monitored_urls_directory = "/monitored_files/"
        self.cancelled = False
        if not os.path.exists(self.directory):
            os.makedirs(self.directory)
        self.red_border = swing.BorderFactory.createLineBorder(awt.Color(240,128,128), 1)
        self.green_border = swing.BorderFactory.createLineBorder(awt.Color(110, 204, 154), 1)
        black_border = swing.BorderFactory.createLineBorder(awt.Color.BLACK, 1)
        light_red = awt.Color(255, 102, 102)
        self.orange = awt.Color(216, 102, 51)
        swing.ToolTipManager.sharedInstance().setDismissDelay(30000)
        self.tooltips_dict = {
            "on_off_button": "Toggle Passive Scan On/Off - When toggled on responses from Burp Suite's Proxy will be processed.",

            "search_text_field": "Filter the hosts list by search term (case insensitive)",

            "monitor_interval_selector": "Select how often a request should be sent to Monitored URLs (if any exist)\nOff - Don't monitor\nOnce - Once when the extension loads\nHourly - Once every hour\nDaily - Once every day\nWeekly - Once every week\nMonthly - Once every month",
            
            "autoselectall_button": "Automatically select all files in the Files list when a host is selected.",

            "negative_match_text_field": "Filter the results table by the URL/Path column,\nOnly rows that do not contain the specified negative match filter in the URL/Path column will be displayed (case sensitive),\nMultiple filters can be applied.",

            "positive_match_text_field": "Filter the results table by the URL/Path column,\nOnly rows that contain the specified positive match filter in the URL/Path column will be displayed (case sensitive),\nMultiple filters can be applied.",

            "include_inline_tags_checkbox": "If selected the extension will also process responses with an HTML mime type.",

            "in_scope_checkbox": "If selected the extension will only process URLs that are in Burp Suite's Scope,\nadditionally only hosts that are in-scope will be displayed in the Hosts list.",

            "hide_duplicates_checkbox": "If selected duplicate rows will be hidden from the results tables (Type & File columns excluded).",

            "show_parameterized": "If selected only rows that contain Query Params / Body Params / Headers will be displayed in the URL/Paths results table.",

            "secrets_checkbox": "If selected the extension will use jsluice's secrets mode on every processed file after the urls mode has finished\nHosts with secrets will be colored red in the Hosts list.",

            "secret_notifications_checkbox": "If selected and the Secrets checkbox is selected a popup dialog will appear whenever a unique secret is found (the dialog will self close after 15 seconds).",

            "save_settings_button": "Save current selected settings using Burp Suite's API (persists across restarts)",
            
            "import_results_button": "Import results from a JSON file",

            "export_results_button": "Export results to a JSON file",
            
            "import_settings_button": "Import settings from a JSON file",

            "export_settings_button": "Export settings to a JSON file",
        }
        self.on_off_button = swing.JToggleButton("Off",actionPerformed=lambda event: self.toggle_on_off(event))
        self.on_off_button.setFont(awt.Font("Cantarell", awt.Font.BOLD, 13))
        self.on_off_button.setSelected(False)
        self.on_off_button.setBorder(self.red_border)
        self.on_off_button.setPreferredSize(awt.Dimension(74, 40))

        self.host_list_model = swing.DefaultListModel()
        self.host_list = swing.JList(self.host_list_model)
        self.host_list.addListSelectionListener(lambda event: self.on_host_selected(event))
        self.host_list_scroll_pane = swing.JScrollPane(self.host_list)
        self.host_list_scroll_pane.setPreferredSize(awt.Dimension(300, 240))
        self.host_list.setSelectionMode(swing.ListSelectionModel.SINGLE_SELECTION)

        self.tabbed_pane_hosts = swing.JTabbedPane()
        self.tabbed_pane_files = swing.JTabbedPane()
        self.tabbed_pane_results = swing.JTabbedPane()
        self.tabbed_pane_filters = swing.JTabbedPane()
        self.tabbed_pane_negative_positive = swing.JTabbedPane()
        self.layout = swing.SpringLayout()
        self.panel = swing.JPanel(self.layout)

        self.panel.add(self.on_off_button, None)
        self.layout.putConstraint(swing.SpringLayout.HORIZONTAL_CENTER, self.on_off_button, -10, swing.SpringLayout.HORIZONTAL_CENTER, self.panel)
        self.layout.putConstraint(swing.SpringLayout.NORTH, self.on_off_button, 265, swing.SpringLayout.NORTH, self.panel)

        self.loading_label = swing.JLabel("Loading files...")
        self.loading_label.setFont(awt.Font("Cantarell", awt.Font.BOLD, 14))
        self.layout.putConstraint(swing.SpringLayout.HORIZONTAL_CENTER, self.loading_label, 244, swing.SpringLayout.HORIZONTAL_CENTER, self.panel)
        self.layout.putConstraint(swing.SpringLayout.NORTH, self.loading_label, 184, swing.SpringLayout.NORTH, self.panel)
        self.panel.add(self.loading_label)
        self.loading_label.setVisible(False)

        self.panel.add(self.tabbed_pane_hosts, None)
        self.search_text_field = swing.JTextField()
        self.negative_match_text_field = swing.JTextField()
        self.positive_match_text_field = swing.JTextField()
        self.tabbed_pane_negative_positive.setPreferredSize(awt.Dimension(180, 46))
        self.tabbed_pane_negative_positive.addTab("Negative", self.negative_match_text_field)
        self.tabbed_pane_negative_positive.addTab("Positive", self.positive_match_text_field)
        textfield_listener = TextFieldsListener(self.on_search_changed, self.search_text_field, self.negative_match_text_field, self.positive_match_text_field, self.panel)

        self.search_text_field.getDocument().addDocumentListener(textfield_listener)
        self.search_text_field.addMouseListener(textfield_listener)
        self.panel.addMouseListener(textfield_listener)
        self.search_text_field.setText("Search:")
        self.search_text_field.setPreferredSize(awt.Dimension(134, 24))
        self.panel.add(self.search_text_field, None)
        self.layout.putConstraint(swing.SpringLayout.HORIZONTAL_CENTER, self.search_text_field, -326, swing.SpringLayout.HORIZONTAL_CENTER, self.panel)
        self.layout.putConstraint(swing.SpringLayout.NORTH, self.search_text_field, 14, swing.SpringLayout.NORTH, self.panel)

        self.tabbed_pane_hosts.addTab("Hosts", self.host_list_scroll_pane)
        self.panel.add(self.tabbed_pane_files, None)
        self.layout.putConstraint(swing.SpringLayout.HORIZONTAL_CENTER, self.tabbed_pane_hosts, -244, swing.SpringLayout.HORIZONTAL_CENTER, self.panel)
        self.layout.putConstraint(swing.SpringLayout.NORTH, self.tabbed_pane_hosts, 44, swing.SpringLayout.NORTH, self.panel)

        self.layout.putConstraint(swing.SpringLayout.HORIZONTAL_CENTER, self.tabbed_pane_files, 244, swing.SpringLayout.HORIZONTAL_CENTER, self.panel)
        self.layout.putConstraint(swing.SpringLayout.NORTH, self.tabbed_pane_files, 44, swing.SpringLayout.NORTH, self.panel)

        self.panel.add(self.tabbed_pane_results, None)
        self.layout.putConstraint(swing.SpringLayout.HORIZONTAL_CENTER, self.tabbed_pane_results, 0, swing.SpringLayout.HORIZONTAL_CENTER, self.panel)
        self.layout.putConstraint(swing.SpringLayout.NORTH, self.tabbed_pane_results, 324, swing.SpringLayout.NORTH, self.panel)
        self.tabbed_pane_results.setPreferredSize(awt.Dimension(1200, 264))
        self.result_table_model = swing.table.DefaultTableModel([], ["URL/Path", "Query Params", "Body Params", "Method", "Headers", "Type"])
        self.result_table = swing.JTable(self.result_table_model)
        self.result_table.setAutoCreateRowSorter(True)
        scroll_pane_result = swing.JScrollPane(self.result_table)
        self.tabbed_pane_results.addTab("Results", scroll_pane_result)
        self.results_table_popupmenu = PopupMenu(self.result_table, callbacks=self._callbacks)
        self.result_table.addMouseListener(self.results_table_popupmenu)

        self.file_names_model = swing.DefaultListModel()
        self.file_names_list = swing.JList(self.file_names_model)
        self.file_names_list.setCellRenderer(ColorFiles(self.monitored_urls, self.processed_file_details, self.selected_host, self.directory, self.monitored_urls_directory))
        self.file_names_list.setSelectionMode(swing.ListSelectionModel.MULTIPLE_INTERVAL_SELECTION)
        self.file_names_list.addListSelectionListener(lambda event: (self.file_names_list.setValueIsAdjusting(True),self.display_result(event, self.file_names_list)))
        
        self.secrets_table_model = swing.table.DefaultTableModel([], ["kind", "data", "severity", "context"])
        self.secrets_table = swing.JTable(self.secrets_table_model)
        self.scroll_pane_secrets = swing.JScrollPane(self.secrets_table)
        self.tabbed_pane_results.addTab("Secrets", self.scroll_pane_secrets)
        self.logo_base64 = "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"
        logo_bytes = b64decode(self.logo_base64)
        logo_image_stream = ByteArrayInputStream(logo_bytes)
        self.logo_image = ImageIO.read(logo_image_stream)
        logo_label = swing.JLabel(swing.ImageIcon(self.logo_image))
        self.layout.putConstraint(swing.SpringLayout.HORIZONTAL_CENTER, logo_label, 0, swing.SpringLayout.HORIZONTAL_CENTER, self.panel)
        self.layout.putConstraint(swing.SpringLayout.NORTH, logo_label, 0, swing.SpringLayout.NORTH, self.panel)
        self.panel.add(logo_label)
        self.secret_image_base64data = "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"

        self.file_names_scroll_pane = swing.JScrollPane(self.file_names_list)
        self.file_names_scroll_pane.setPreferredSize(awt.Dimension(300, 240))
        self.file_list_popupmenu = PopupMenu(self.file_names_list, callbacks=self._callbacks, logo_image=self.logo_image, directory=self.directory, monitored_urls_path=self.monitored_urls_path, monitored_urls_directory=self.monitored_urls_directory)
        self.file_names_list.addMouseListener(self.file_list_popupmenu)
        self.tabbed_pane_files.addTab("Files", self.file_names_scroll_pane)

        self.results_filters_list = swing.JList()
        self.results_filters_list.setCellRenderer(ColorFilters(self.results_filters))
        self.results_filters_list.setSelectionMode(swing.ListSelectionModel.MULTIPLE_INTERVAL_SELECTION)
        self.results_filters_list_model = swing.DefaultListModel()
        self.results_filters_list.setModel(self.results_filters_list_model)
        self.results_filters_scroll_pane = swing.JScrollPane(self.results_filters_list)
        self.results_filters_scroll_pane.setPreferredSize(awt.Dimension(80, 80))
        self.panel.add(self.tabbed_pane_filters, None)
        self.layout.putConstraint(swing.SpringLayout.HORIZONTAL_CENTER, self.tabbed_pane_filters, -436, swing.SpringLayout.HORIZONTAL_CENTER, self.panel)
        self.layout.putConstraint(swing.SpringLayout.NORTH, self.tabbed_pane_filters, 190, swing.SpringLayout.NORTH, self.panel)

        self.remove_filter_button = swing.JButton("X", actionPerformed=self.remove_filter)
        self.remove_filter_button.setFont(awt.Font("Arial Black", awt.Font.BOLD, 10))
        self.remove_filter_button.setOpaque(True)
        self.remove_filter_button.setBackground(light_red)
        self.remove_filter_button.setForeground(awt.Color.BLACK)
        self.remove_filter_button.setPreferredSize(awt.Dimension(80, 12))
        self.remove_filter_button.setBorder(black_border)
        
        self.negative_match_text_field.getDocument().addDocumentListener(textfield_listener)
        self.negative_match_text_field.addMouseListener(textfield_listener)
        self.negative_match_text_field.setPreferredSize(awt.Dimension(124, 24))
        self.negative_match_text_field.setText("Negative Match:")
        self.positive_match_text_field.getDocument().addDocumentListener(textfield_listener)
        self.positive_match_text_field.addMouseListener(textfield_listener)
        self.positive_match_text_field.setPreferredSize(awt.Dimension(124, 24))
        self.positive_match_text_field.setText("Positive Match:")
        self.panel.add(self.tabbed_pane_negative_positive, None)
        self.layout.putConstraint(swing.SpringLayout.HORIZONTAL_CENTER, self.tabbed_pane_negative_positive, -508, swing.SpringLayout.HORIZONTAL_CENTER, self.panel)
        self.layout.putConstraint(swing.SpringLayout.NORTH, self.tabbed_pane_negative_positive, 594, swing.SpringLayout.NORTH, self.panel)

        self.add_filter_button = swing.JButton("Add Filter", actionPerformed=self.add_filter)
        self.add_filter_button.setOpaque(True)
        self.add_filter_button.setBorder(None)
        self.add_filter_button.setFont(awt.Font("Cantarell", awt.Font.BOLD, 13))
        self.add_filter_button.setBackground(self.orange)
        self.add_filter_button.setForeground(awt.Color.WHITE)
        self.add_filter_button.setPreferredSize(awt.Dimension(94, 24))
        self.panel.add(self.add_filter_button, None)
        self.layout.putConstraint(swing.SpringLayout.HORIZONTAL_CENTER, self.add_filter_button, -364, swing.SpringLayout.HORIZONTAL_CENTER, self.panel)
        self.layout.putConstraint(swing.SpringLayout.NORTH, self.add_filter_button, 616, swing.SpringLayout.NORTH, self.panel)

        self.autoselectall_button = swing.JToggleButton("Auto-Select All", actionPerformed=self.toggle_autoselectall)
        self.autoselectall_button.setFont(awt.Font("Cantarell", awt.Font.BOLD, 13))
        self.autoselectall_button.setBorder(self.green_border)
        self.autoselectall_button.setPreferredSize(awt.Dimension(114, 24))
        self.autoselectall_button.setSelected(True)
        self.panel.add(self.autoselectall_button, None)
        self.layout.putConstraint(swing.SpringLayout.HORIZONTAL_CENTER, self.autoselectall_button, 454, swing.SpringLayout.HORIZONTAL_CENTER, self.panel)
        self.layout.putConstraint(swing.SpringLayout.NORTH, self.autoselectall_button, 280, swing.SpringLayout.NORTH, self.panel)

        checkboxesPanel = swing.JPanel()
        checkboxesPanel.setLayout(swing.BoxLayout(checkboxesPanel, swing.BoxLayout.X_AXIS))
        largeRoundedBorder = swing.BorderFactory.createLineBorder(awt.Color(216, 102, 51), 2, True)
        checkboxesPanel.setBorder(swing.BorderFactory.createCompoundBorder(largeRoundedBorder, swing.BorderFactory.createEmptyBorder(10, 10, 10, 10)))

        self.include_inline_tags_checkbox = swing.JCheckBox("In-line Tags")
        self.include_inline_tags_checkbox.setFont(awt.Font("Cantarell", awt.Font.BOLD, 12))
        self.include_inline_tags_checkbox.setSelected(False)

        self.in_scope_checkbox = swing.JCheckBox("In-scope only")
        self.in_scope_checkbox.setFont(awt.Font("Cantarell", awt.Font.BOLD, 12))
        self.in_scope_checkbox.addActionListener(lambda event: self.filter_hosts())
        self.in_scope_checkbox.setSelected(False)

        self.hide_duplicates_checkbox = swing.JCheckBox("Hide Duplicates")
        self.hide_duplicates_checkbox.setFont(awt.Font("Cantarell", awt.Font.BOLD, 12))
        self.hide_duplicates_checkbox.addActionListener(lambda event: self.display_result(event, self.file_names_list))
        self.hide_duplicates_checkbox.setSelected(True)

        self.secret_notifications_checkbox = swing.JCheckBox("Secret Notifications")
        self.secret_notifications_checkbox.setFont(awt.Font("Cantarell", awt.Font.BOLD, 12))
        self.secret_notifications_checkbox.setSelected(False)

        self.secrets_checkbox = swing.JCheckBox("Secrets")
        self.secrets_checkbox.setFont(awt.Font("Cantarell", awt.Font.BOLD, 12))
        self.secrets_checkbox.setSelected(True)
        self.secrets_checkbox.addActionListener(self.update_secrets_checkbox)

        self.show_parameterized = swing.JCheckBox("Show Parameterized")
        self.show_parameterized.setFont(awt.Font("Cantarell", awt.Font.BOLD, 12))
        self.show_parameterized.setSelected(False)
        self.show_parameterized.addActionListener(lambda event: self.display_result(event, self.file_names_list))

        checkboxes = [
            self.include_inline_tags_checkbox,
            self.in_scope_checkbox,
            self.hide_duplicates_checkbox,
            self.show_parameterized,
            self.secret_notifications_checkbox,
            self.secrets_checkbox
        ]
        for checkbox in checkboxes:
            checkboxesPanel.add(checkbox)
            self.add_horizontal_strut(checkboxesPanel, 10)
            if checkbox == checkboxes[-1]:
                break
            self.add_vertical_line(checkboxesPanel)
            self.add_horizontal_strut(checkboxesPanel, 10)
        self.panel.add(checkboxesPanel, None)

        self.layout.putConstraint(swing.SpringLayout.WEST, checkboxesPanel, 114, swing.SpringLayout.WEST, self.add_filter_button)
        self.layout.putConstraint(swing.SpringLayout.NORTH, checkboxesPanel, 604, swing.SpringLayout.NORTH, self.panel)

        self.monitor_interval_selector = swing.JComboBox(["Off", "Once", "Hourly", "Daily", "Weekly", "Monthly"])
        self.monitor_interval_selector.setSelectedItem("Off")
        self.panel.add(self.monitor_interval_selector, None)
        self.layout.putConstraint(swing.SpringLayout.HORIZONTAL_CENTER, self.monitor_interval_selector, 384, swing.SpringLayout.HORIZONTAL_CENTER, self.panel)
        self.layout.putConstraint(swing.SpringLayout.NORTH, self.monitor_interval_selector, 246, swing.SpringLayout.NORTH, self.panel)

        self.settings_dict = {
        "Hide Duplicates": "hide_duplicates_checkbox",
        "In-scope only": "in_scope_checkbox",
        "In-line Tags": "include_inline_tags_checkbox",
        "Secrets": "secrets_checkbox",
        "Secrets Notifications": "secret_notifications_checkbox",
        "On/Off": "on_off_button",
        "Auto-Select": "autoselectall_button",
        "Monitor Interval": "monitor_interval_selector",
        "Show Parameterized": "show_parameterized"
        }
        
        self.save_settings_button = swing.JButton("Save Settings", actionPerformed=self.save_settings)
        self.save_settings_button.setOpaque(True)
        self.save_settings_button.setBorder(swing.BorderFactory.createLineBorder(None, 1))
        self.save_settings_button.setFont(awt.Font("Cantarell", awt.Font.BOLD, 12))
        self.save_settings_button.setPreferredSize(awt.Dimension(94, 34))
        self.panel.add(self.save_settings_button, None)
        self.layout.putConstraint(swing.SpringLayout.EAST, self.save_settings_button, 124, swing.SpringLayout.EAST, checkboxesPanel)
        self.layout.putConstraint(swing.SpringLayout.NORTH, self.save_settings_button, 606, swing.SpringLayout.NORTH, self.panel)

        self.settings_saved_label = swing.JLabel("Settings saved")
        self.layout.putConstraint(swing.SpringLayout.HORIZONTAL_CENTER, self.settings_saved_label, 0, swing.SpringLayout.HORIZONTAL_CENTER, self.panel)
        self.layout.putConstraint(swing.SpringLayout.NORTH, self.settings_saved_label, 34, swing.SpringLayout.NORTH, self.panel)
        self.settings_saved_label.setVisible(False)
        self.settings_saved_label.setFont(awt.Font("Cantarell", awt.Font.BOLD, 14))
        self.settings_saved_label.setForeground(awt.Color(110, 204, 154))
        self.panel.add(self.settings_saved_label, None)
        
        self.export_settings_button = swing.JButton("Export", actionPerformed=lambda x: self.export_import("export", "settings"))
        self.export_settings_button.setOpaque(True)
        self.export_settings_button.setBorder(swing.BorderFactory.createLineBorder(None, 1))
        self.export_settings_button.setFont(awt.Font("Cantarell", awt.Font.BOLD, 12))
        self.export_settings_button.setPreferredSize(awt.Dimension(64, 24))
        self.panel.add(self.export_settings_button, None)
        self.layout.putConstraint(swing.SpringLayout.HORIZONTAL_CENTER, self.export_settings_button, 144, swing.SpringLayout.HORIZONTAL_CENTER, self.panel)
        self.layout.putConstraint(swing.SpringLayout.NORTH, self.export_settings_button, 0, swing.SpringLayout.NORTH, self.panel)
        
        self.import_settings_button = swing.JButton("Import", actionPerformed=lambda x: self.export_import("import", "settings"))
        self.import_settings_button.setOpaque(True)
        self.import_settings_button.setBorder(swing.BorderFactory.createLineBorder(None, 1))
        self.import_settings_button.setFont(awt.Font("Cantarell", awt.Font.BOLD, 12))
        self.import_settings_button.setPreferredSize(awt.Dimension(64, 24))
        self.panel.add(self.import_settings_button, None)
        self.layout.putConstraint(swing.SpringLayout.HORIZONTAL_CENTER, self.import_settings_button, 244, swing.SpringLayout.HORIZONTAL_CENTER, self.panel)
        self.layout.putConstraint(swing.SpringLayout.NORTH, self.import_settings_button, 0, swing.SpringLayout.NORTH, self.panel)
        
        self.import_results_button = swing.JButton("Import", actionPerformed=lambda x: self.export_import("import", "results"))
        self.import_results_button.setOpaque(True)
        self.import_results_button.setBorder(swing.BorderFactory.createLineBorder(None, 1))
        self.import_results_button.setFont(awt.Font("Cantarell", awt.Font.BOLD, 12))
        self.import_results_button.setPreferredSize(awt.Dimension(64, 24))
        self.panel.add(self.import_results_button, None)
        self.layout.putConstraint(swing.SpringLayout.HORIZONTAL_CENTER, self.import_results_button, -144, swing.SpringLayout.HORIZONTAL_CENTER, self.panel)
        self.layout.putConstraint(swing.SpringLayout.NORTH, self.import_results_button, 0, swing.SpringLayout.NORTH, self.panel)
        
        self.export_results_button = swing.JButton("Export", actionPerformed=lambda x: self.export_import("export", "results"))
        self.export_results_button.setOpaque(True)
        self.export_results_button.setBorder(swing.BorderFactory.createLineBorder(None, 1))
        self.export_results_button.setFont(awt.Font("Cantarell", awt.Font.BOLD, 12))
        self.export_results_button.setPreferredSize(awt.Dimension(64, 24))
        self.panel.add(self.export_results_button, None)
        self.layout.putConstraint(swing.SpringLayout.HORIZONTAL_CENTER, self.export_results_button, 0, swing.SpringLayout.HORIZONTAL_CENTER, self.panel)
        self.layout.putConstraint(swing.SpringLayout.NORTH, self.export_results_button, 0, swing.SpringLayout.NORTH, self.panel)

        mainPanel = swing.JPanel()
        mainPanel.setLayout(swing.BoxLayout(mainPanel, swing.BoxLayout.Y_AXIS))
        mainPanel.setBorder(swing.BorderFactory.createCompoundBorder(swing.BorderFactory.createLineBorder(awt.Color(216, 102, 51), 1, True), swing.BorderFactory.createEmptyBorder(0, 0, 0, 0)))
        resultsButtons = [self.import_results_button, self.export_results_button]
        settingsButtons = [self.import_settings_button, self.export_settings_button]
        def add_horizontal_line(self, panel):
            separator = swing.JSeparator(swing.SwingConstants.HORIZONTAL)
            separator.setForeground(awt.Color(216, 102, 51))
            separator.setMaximumSize(awt.Dimension(184, 184))
            panel.add(separator)

        def createButtonPanel(title, buttons):
            panel = swing.JPanel()
            panel.setLayout(awt.BorderLayout())
            titlePanel = swing.JPanel()
            titlePanel.setLayout(awt.FlowLayout(awt.FlowLayout.CENTER, 0, 0))
            titleLabel = swing.JLabel(title)
            titleLabel.setFont(awt.Font("Cantarell", awt.Font.BOLD, 12))
            titlePanel.add(titleLabel)
            panel.add(titlePanel, awt.BorderLayout.PAGE_START)
            buttonsPanel = swing.JPanel()
            buttonsPanel.setLayout(awt.FlowLayout(awt.FlowLayout.CENTER, 0, 0))
            for i, button in enumerate(buttons):
                self.add_horizontal_strut(buttonsPanel, 10)
                self.add_vertical_strut(buttonsPanel, 20)
                buttonsPanel.add(button)
                self.add_horizontal_strut(buttonsPanel, 10)
            panel.add(buttonsPanel, awt.BorderLayout.CENTER)
            return panel

        self.add_vertical_strut(mainPanel, 10)
        mainPanel.add(createButtonPanel("Results", resultsButtons))
        self.add_vertical_strut(mainPanel, 10)
        add_horizontal_line(self, mainPanel)
        self.add_vertical_strut(mainPanel, 10)
        mainPanel.add(createButtonPanel("Settings", settingsButtons))
        self.add_vertical_strut(mainPanel, 10)
        add_horizontal_line(self, mainPanel)
        self.add_vertical_strut(mainPanel, 10)
        mainPanel.add(createButtonPanel("Passive Scan", [self.on_off_button]))
        self.add_vertical_strut(mainPanel, 10)
        add_horizontal_line(self, mainPanel)
        self.add_vertical_strut(mainPanel, 10)
        mainPanel.add(createButtonPanel("Monitor Interval", [self.monitor_interval_selector]))
        self.add_vertical_strut(mainPanel, 10)
        self.layout.putConstraint(swing.SpringLayout.HORIZONTAL_CENTER, mainPanel, 0, swing.SpringLayout.HORIZONTAL_CENTER, self.panel)
        self.layout.putConstraint(swing.SpringLayout.NORTH, mainPanel, 52, swing.SpringLayout.NORTH, self.panel)
        self.panel.add(mainPanel, None)
        
        for key, value in self.tooltips_dict.items():
            getattr(self, key).setToolTipText(value)

        callbacks.customizeUiComponent(self.panel)
        callbacks.addSuiteTab(self)
        callbacks.registerExtensionStateListener(self)
        callbacks.registerContextMenuFactory(self)
        self.load_settings()
        print("Extension loaded")
        if not distutils.spawn.find_executable("jsluice"):
            print("[WARNING] jsluice binary not found, please install it and ensure it is in your $PATH otherwise the extension will not work.")
        self.threads = []
        if os.path.exists(self.directory + self.monitored_urls_path):
            self.monitored_urls = self.get_monitored_urls()
            if len(self.monitored_urls) > 0:
                if self.monitor_interval_selector.getSelectedItem() != "Off":
                    self.schedule_event(0, self.schedule_monitor)


    def export_import(self, option, type):
        file_chooser = swing.JFileChooser()
        file_chooser.setFileFilter(FileNameExtensionFilter("JSON", ["json"]))
        file_chooser.setFileSelectionMode(swing.JFileChooser.FILES_ONLY)
        file_chooser.setFileHidingEnabled(False)
        if option == "export":
            file_chooser.setDialogTitle("Export Results" if type == "results" else "Export Settings")
            file_chooser.setSelectedFile(java.io.File("results.json" if type == "results" else "settings.json"))
            if file_chooser.showSaveDialog(self.panel) == swing.JFileChooser.APPROVE_OPTION:
                file = file_chooser.getSelectedFile()
                if file.exists():
                    dialog = swing.JOptionPane.showConfirmDialog(self.panel, str(file.getAbsolutePath()) + " already exists. Overwrite?", "jsluice++", swing.JOptionPane.YES_NO_OPTION)
                    if dialog != swing.JOptionPane.YES_OPTION:
                        return
                if type == "results":
                    self.export_results(file)
                elif type == "settings":
                    self.export_settings(file)
        elif option == "import":
            file_chooser.setDialogTitle("Import Results" if type == "results" else "Import Settings")
            if file_chooser.showOpenDialog(self.panel) == swing.JFileChooser.APPROVE_OPTION:
                file = file_chooser.getSelectedFile()
                if type == "results":
                    self.import_results(file)
                elif type == "settings":
                    self.import_settings(file)

    def export_results(self, file):
        results = {
            "seen_endpoints": list(self.seen_endpoints),
            "processed_file_details": self.processed_file_details
        }
        with open(file.getAbsolutePath(), "w") as f:
            f.write(json.dumps(results, indent=4))
        print("Results saved to " + file.getAbsolutePath())

    def import_results(self, file):
        with open(file.getAbsolutePath(), "r") as f:
            results = json.loads(f.read())
        try:
            self.seen_endpoints.update(results["seen_endpoints"])
            self.processed_file_details.update(results["processed_file_details"])
            for value in self.processed_file_details.values():
                if value["host"] not in self.hosts_list:
                    self.hosts_list.add(value["host"])
                    self.host_list_model.addElement(value["host"])
                if value["secrets"]:
                    if value["host"] not in self.hosts_with_secrets:
                        self.hosts_with_secrets.add(value["host"])
                        self.add_image_to_host(self.hosts_with_secrets, self.secret_image_base64data)
            self.tabbed_pane_hosts.setTitleAt(0, str(self.host_list_model.getSize()) + " Hosts" if self.host_list_model.getSize() > 0 else "Hosts")
            print(str(len(self.processed_file_details.keys())) + " items imported from: " + file.getAbsolutePath())
        except KeyError:
            print("Invalid results file: " + file.getAbsolutePath())
            return

    def export_settings(self, file):
        settings = {}
        for display_name, key in self.settings_dict.items():
            component = getattr(self, key)
            if isinstance(component, swing.JToggleButton):
                settings[display_name] = component.isSelected()
            elif isinstance(component, swing.JComboBox):
                settings[display_name] = component.getSelectedItem()

        with open(file.getAbsolutePath(), "w") as f:
            f.write(json.dumps(settings, indent=4))
        print("Settings saved to " + file.getAbsolutePath())

    def import_settings(self, file):
        with open(file.getAbsolutePath(), "r") as f:
            settings = json.loads(f.read())
            for key, value in settings.items():
                if key in self.settings_dict:
                    component = getattr(self, self.settings_dict[key])
                    if key == "On/Off" or key == "Auto-Select":
                        if value == False:
                            component.setBorder(self.red_border)
                            component.setSelected(False)
                            if key == "On/Off":
                                self.on_off_button.setText("Off")
                                if self._callbacks.getHttpListeners() != []:
                                    self._callbacks.removeHttpListener(self)
                        elif value == True:
                            component.setBorder(self.green_border)
                            component.setSelected(True)
                            if key == "On/Off":
                                self.on_off_button.setText("On")
                                if self._callbacks.getHttpListeners() == []:
                                    self._callbacks.registerHttpListener(self)
                    elif key == "Monitor Interval":
                        component.setSelectedItem(value)
                    else:
                        component.setSelected(value == True)
                        if key == "Secrets":
                            self.update_secrets_checkbox(self)
                        elif key == "In-scope only" and value == True:
                            self.filter_hosts()
            print("Settings imported from: " + file.getAbsolutePath())

    def extensionUnloaded(self):
        self.cancelled = True
        if self.threads != []:
            print("Cancelling threads")
            for thread in self.threads:
                try:
                    thread.cancel()
                except:
                    continue
        print("Extension unloaded")

    def toggle_on_off(self, event):
        http_listeners = self._callbacks.getHttpListeners()
        if self.on_off_button.isSelected():
            self.on_off_button.setText("On")
            self.on_off_button.setBorder(self.green_border)
            if http_listeners == []:
                self._callbacks.registerHttpListener(self)
        else:
            self.on_off_button.setText("Off")
            self.on_off_button.setBorder(self.red_border)
            if http_listeners != []:
                for listener in http_listeners:
                    self._callbacks.removeHttpListener(listener)

    def get_monitored_urls(self):
        if os.path.exists(self.directory+self.monitored_urls_path):
            with open(self.directory+self.monitored_urls_path, "r") as f:
                for line in f:
                    try:
                        json_object = json.loads(line)
                        self.monitored_urls[json_object["origin_url"]] = json_object
                        if json_object["origin_url"] in self.seen_endpoints:
                            self.seen_endpoints.remove(json_object["origin_url"])
                    except:
                        print("Error parsing line: " + line)
                        continue
            f.close()
            return self.monitored_urls

    def save_settings(self, event):
        for setting, var in self.settings_dict.items():
            checkbox = getattr(self, var)
            if setting == "Monitor Interval":
                value = str(checkbox.getSelectedItem())
                print("Cancelling threads")
                for thread in self.threads:
                    try:
                        thread.cancel()
                    except:
                        continue
                if (value != "Off" and value != "Once") and len(self.monitored_urls) > 0:
                    self.schedule_monitor()
            else:
                value = str(checkbox.isSelected())
            self._callbacks.saveExtensionSetting(setting, value)
        print("Settings saved")
        if self.settings_saved_label.isVisible() == False:
            self.settings_saved_label.setVisible(True)
            self.panel.revalidate()
            self.panel.repaint()
            timer = swing.Timer(3000, lambda event: self.settings_saved_label.setVisible(False))
            timer.setRepeats(False)
            timer.start()
        self.load_settings()
    
    def load_settings(self):
        for setting, var in self.settings_dict.items():
            checkbox = getattr(self, var)
            value = self._callbacks.loadExtensionSetting(setting)
            if value is None:
                continue
            if (setting == "On/Off" or setting == "Auto-Select"):
                if value == "False":
                    checkbox.setBorder(self.red_border)
                    checkbox.setSelected(False)
                    if setting == "On/Off":
                        self.on_off_button.setText("Off")
                elif value == "True":
                    checkbox.setBorder(self.green_border)
                    checkbox.setSelected(True)
                    if setting == "On/Off":
                        self.on_off_button.setText("On")
                        if self._callbacks.getHttpListeners() == []:
                            self._callbacks.registerHttpListener(self)
            elif setting == "Monitor Interval":
                checkbox.setSelectedItem(value)
            else:
                checkbox.setSelected(value == "True")
                if setting == "Secrets":
                    self.update_secrets_checkbox(self)

    def add_image_to_host(self, hosts_with_secrets, secret_image_base64):
        self.host_list.setCellRenderer(ColorHosts(hosts_with_secrets, secret_image_base64))

    def send_http_request(self, url, host, port, is_https, request_info):
        http_service = self._helpers.buildHttpService(host, port, is_https)
        request = self._callbacks.makeHttpRequest(http_service, request_info)
        if request.getResponse() is None:
            print("Got no response from monitored url: " + url)
            return
        
        response_info = self._helpers.analyzeResponse(request.getResponse())
        status_code = response_info.getStatusCode()
        if (not (200 <= status_code <= 299)) and  status_code != 0:
            self.show_dialogs(host=host, url=url, reason_label="Returned status code: " + str(status_code))
        self.process_with_jsluice(request)
        return

    def schedule_monitor(self):
        monitor_interval_value = self.monitor_interval_selector.getSelectedItem()
        interval_mapping = {
            "Hourly": 3600,
            "Daily": 86400,
            "Weekly": 604800,
            "Monthly": 2592000,
        }

        if monitor_interval_value == "Once":
            self.handle_monitored_urls()
        elif monitor_interval_value in interval_mapping:
            last_monitored_date_str = self._callbacks.loadExtensionSetting("Last Monitored Date")
            if last_monitored_date_str:
                try:
                    last_monitored_date = datetime.strptime(last_monitored_date_str, "%Y-%m-%d %H:%M:%S.%f")
                except ValueError:
                    last_monitored_date = datetime.strptime(last_monitored_date_str, "%Y-%m-%d %H:%M:%S")
            else:
                last_monitored_date = None

            last_monitored_date = last_monitored_date if last_monitored_date_str else datetime.now() - timedelta(seconds=interval_mapping[monitor_interval_value])
            current_date = datetime.now()
            difference = current_date - last_monitored_date
            difference_in_seconds = difference.total_seconds()
            interval_duration = interval_mapping[monitor_interval_value]
            if difference_in_seconds >= interval_duration:
                self.schedule_event(0, self.handle_monitored_urls)
                self.schedule_event(interval_duration, self.schedule_monitor)
            else:
                remaining_seconds = interval_duration - difference_in_seconds
                print("["+str(current_date)+"] Sending " + str(len(self.monitored_urls)) + " requests to monitored URLs in " + str(remaining_seconds) + " seconds.")
                self.schedule_event(remaining_seconds, self.handle_monitored_urls)
                self.schedule_event(remaining_seconds + interval_duration, self.schedule_monitor)
        else:
            print("Stopped monitoring URLs, monitor interval value: " + monitor_interval_value)
            return

    def handle_monitored_urls(self):
        if os.path.exists(self.directory+self.monitored_urls_path) and os.path.getsize(self.directory+self.monitored_urls_path) > 0:
            self._callbacks.saveExtensionSetting("Last Monitored Date", str(datetime.now()))
            self.monitored_urls = self.get_monitored_urls()
            for url in self.monitored_urls:
                try:
                    request_info = self._helpers.buildHttpRequest(URL(url))
                    host = URL(url).getHost()
                    port = URL(url).getPort()
                    is_https = URL(url).getProtocol() == "https"
                    Thread(target=self.send_http_request, args=(url, host, port, is_https, request_info)).start()
                except Exception as e:
                    print("Error sending request to url: " + url)
                    print(e)
                    continue
            print("["+str(datetime.now())+"] Sent " + str(len(self.monitored_urls)) + " requests to monitored URLs.")
        else:
            return

    def schedule_event(self, interval, action, args=()):
        event = Timer(interval, action, args=(args))
        event.start()
        self.threads.append(event)


    def add_horizontal_strut(self, panel, width):
        strut = swing.Box.createHorizontalStrut(width)
        panel.add(strut)
    
    def add_vertical_strut(self, panel, height):
        strut = swing.Box.createVerticalStrut(height)
        panel.add(strut)

    def add_vertical_line(self, panel):
        separator = swing.JSeparator(swing.SwingConstants.VERTICAL)
        separator.setForeground(awt.Color(216, 102, 51))
        separator.setMaximumSize(awt.Dimension(1, 1000))
        panel.add(separator)

    def update_secrets_checkbox(self, event):
        isSecretsSelected = self.secrets_checkbox.isSelected()
        tabIndex = self.tabbed_pane_results.indexOfComponent(self.scroll_pane_secrets)
        if isSecretsSelected:
            self.display_result(event, self.file_names_list)
            if tabIndex == -1:
                self.tabbed_pane_results.addTab("Secrets", self.scroll_pane_secrets)
                self.tabbed_pane_results.setTitleAt(self.tabbed_pane_results.indexOfComponent(self.scroll_pane_secrets), "Secrets ({} rows)".format(self.secrets_table_model.getRowCount()))
        else:
            if tabIndex != -1:
                self.tabbed_pane_results.removeTabAt(tabIndex)

    def add_filter(self, event):
        def handle_match_text_field(match_text_field, match_type):
            match = match_text_field.getText()
            if match == match_type + ":" or match == "":
                return

            if match not in self.results_filters:
                self.results_filters[match] = match_type

            if self.tabbed_pane_filters.indexOfComponent(self.results_filters_scroll_pane) == -1:
                self.tabbed_pane_filters.addTab("Filters", self.results_filters_scroll_pane)
                self.panel.add(self.remove_filter_button, None)
                self.layout.putConstraint(swing.SpringLayout.HORIZONTAL_CENTER, self.remove_filter_button, -436, swing.SpringLayout.HORIZONTAL_CENTER, self.panel)
                self.layout.putConstraint(swing.SpringLayout.NORTH, self.remove_filter_button, 294, swing.SpringLayout.NORTH, self.panel)

            self.results_filters_list_model.addElement(match)
            match_text_field.setText(match_type.title() + " Match:")
            match_text_field.setCaretPosition(0)
            match_text_field.setFocusable(False)
            match_text_field.setFocusable(True)
            self.results_filters_list.setSelectedIndex(len(self.results_filters) - 1)
            swing.SwingUtilities.invokeLater(lambda: self.display_result(event, self.file_names_list))
            match_text_field.setEditable(False)

        negative_match = self.negative_match_text_field.getText()
        positive_match = self.positive_match_text_field.getText()

        if negative_match != "Negative Match:" and negative_match != "" and negative_match not in self.results_filters:
            handle_match_text_field(self.negative_match_text_field, 'negative')
        elif positive_match != "Positive Match:" and positive_match != "" and positive_match not in self.results_filters:
            handle_match_text_field(self.positive_match_text_field, 'positive')



    def remove_filter(self, event):
        selected_filters = self.results_filters_list.getSelectedValuesList()
        for selected_filter in selected_filters:
            self.results_filters.pop(selected_filter)
            self.results_filters_list_model.removeElement(selected_filter)
        if self.results_filters_list_model.isEmpty():
            self.tabbed_pane_filters.removeTabAt(self.tabbed_pane_filters.indexOfComponent(self.results_filters_scroll_pane))
            self.panel.remove(self.remove_filter_button)
            self.panel.repaint()
            self.panel.revalidate()
        else:
            self.results_filters_list.setSelectedIndex(len(self.results_filters) - 1)
        swing.SwingUtilities.invokeLater(lambda: self.display_result(event, self.file_names_list))

    def on_search_changed(self, event):
        search_text = self.search_text_field.getText().lower()
        if search_text != "search:":
            current_selection = self.host_list.getSelectedValue()
            filtered_hosts = [host for host in list(self.hosts_list) if search_text in host.lower()]
            if self.in_scope_checkbox.isSelected():
                filtered_hosts = [host for host in filtered_hosts if self._callbacks.isInScope(URL(str("http://" + host))) or self._callbacks.isInScope(URL(str("https://" + host)))]
            self.host_list_model.clear()
            for host in filtered_hosts:
                self.host_list_model.addElement(host)
            index = 0
            if current_selection in filtered_hosts:
                index = filtered_hosts.index(current_selection)
            else:
                self.file_names_model.clear()
                self.tabbed_pane_results.setTitleAt(0, "Results")
                self.tabbed_pane_files.setTitleAt(0, "Files")
                self.result_table_model.setRowCount(0)
                if self.secrets_checkbox.isSelected():
                    self.tabbed_pane_results.setTitleAt(1, "Secrets")
                    self.secrets_table_model.setRowCount(0)
            self.tabbed_pane_hosts.setTitleAt(0, str(self.host_list_model.getSize()) + " Hosts" if self.host_list_model.getSize() > 0 else "Hosts")
            self.host_list.setSelectedIndex(index)

    def show_dialogs(self, url=None, host=None, reason_label=None):
        if url and host == None and reason_label == None:
            change_in_monitored_dialog = swing.JDialog(None, "jsluice++ | Monitored URLs", False)
            change_in_monitored_dialog.setSize(644, 244)
            logo_icon = swing.ImageIcon(self.logo_image)
            change_in_monitored_dialog.setIconImage(self.logo_image)
            label_font = awt.Font("Cantarell", awt.Font.BOLD, 14)
            change_in_monitored_label = swing.JLabel("The following monitored URL has changed:", swing.JLabel.CENTER)
            url_label = swing.JLabel(url, swing.JLabel.CENTER)
            url_label.setForeground(self.orange)
            change_in_monitored_label.setVerticalTextPosition(swing.JLabel.BOTTOM)
            change_in_monitored_label.setHorizontalTextPosition(swing.JLabel.CENTER)
            change_in_monitored_label.setIcon(logo_icon)
            change_in_monitored_label.setFont(label_font)
            url_label.setFont(awt.Font("Cantarell", awt.Font.BOLD, 18))
            change_in_monitored_dialog.getContentPane().add(change_in_monitored_label, awt.BorderLayout.NORTH)
            change_in_monitored_dialog.getContentPane().add(url_label, awt.BorderLayout.CENTER)
            change_in_monitored_dialog.setLocationRelativeTo(None)
            change_in_monitored_dialog.setDefaultCloseOperation(swing.WindowConstants.DISPOSE_ON_CLOSE)
            button = swing.JButton("OK", actionPerformed=lambda x: change_in_monitored_dialog.dispose())
            change_in_monitored_dialog.getContentPane().add(button, awt.BorderLayout.SOUTH)
            change_in_monitored_dialog.setVisible(True)
        elif host and url == None and reason_label == None:
            secret_image_bytes = b64decode(self.secret_image_base64data)
            secret_image_stream = ByteArrayInputStream(secret_image_bytes)
            secret_image = ImageIO.read(secret_image_stream)
            self.secret_icon = swing.ImageIcon(secret_image)
            secrets_found_dialog = swing.JDialog(None, "jsluice++ | Secrets found", False)
            secrets_found_dialog.setSize(340, 140)
            secrets_found_dialog.setIconImage(secret_image)
            label_font = awt.Font("Cantarell", awt.Font.BOLD, 14)
            label = swing.JLabel("New secret(s) found in " + host, swing.JLabel.CENTER)
            label.setFont(label_font)
            label.setIcon(self.secret_icon)
            label.setVerticalTextPosition(swing.JLabel.BOTTOM)
            label.setHorizontalTextPosition(swing.JLabel.CENTER)
            secrets_found_dialog.getContentPane().add(label)
            secrets_found_dialog.setLocationRelativeTo(None)
            secrets_found_dialog.setDefaultCloseOperation(swing.WindowConstants.DISPOSE_ON_CLOSE)
            button = swing.JButton("OK", actionPerformed=lambda x: secrets_found_dialog.dispose())
            secrets_found_dialog.getContentPane().add(button, awt.BorderLayout.SOUTH)
            secrets_found_dialog.setVisible(True)
            swing.Timer(15000, lambda x: secrets_found_dialog.dispose()).start()
        elif host and url and reason_label:
            logo_icon = swing.ImageIcon(self.logo_image)
            bad_status_code_dialog = swing.JDialog(None, "jsluice++ | Monitored URLs", False)
            bad_status_code_dialog.setSize(400, 200)
            bad_status_code_dialog.setIconImage(self.logo_image)
            status_label_font = awt.Font("Cantarell", awt.Font.BOLD, 14)
            status_label = swing.JLabel("The following URL: " + str(url), swing.JLabel.CENTER)
            status_label2 = swing.JLabel(reason_label, swing.JLabel.CENTER)
            status_label3 = swing.JLabel("Would you like to stop monitoring it?", swing.JLabel.CENTER)
            status_label.setIcon(logo_icon)
            status_label.setFont(status_label_font)
            status_label2.setFont(status_label_font)
            status_label3.setFont(status_label_font)
            labels_panel = swing.JPanel()
            labels_panel.setLayout(swing.BoxLayout(labels_panel, swing.BoxLayout.Y_AXIS))
            status_label.setVerticalTextPosition(swing.JLabel.BOTTOM)
            status_label.setHorizontalTextPosition(swing.JLabel.CENTER)
            status_label.setAlignmentX(0.5)
            status_label2.setAlignmentX(0.5)
            status_label3.setAlignmentX(0.5)
            labels_panel.add(status_label)
            labels_panel.add(status_label2)
            labels_panel.add(status_label3)
            bad_status_code_dialog.setLocationRelativeTo(None)
            bad_status_code_dialog.setDefaultCloseOperation(swing.WindowConstants.DISPOSE_ON_CLOSE)
            bad_status_code_dialog.add(labels_panel)
            button_panel = swing.JPanel()
            button_panel.setLayout(swing.BoxLayout(button_panel, swing.BoxLayout.X_AXIS))
            def stop_monitoring(event):
                file_name = ""
                monitor_urls_file = open(self.directory + self.monitored_urls_path, "a+")
                monitor_urls_file.seek(0)
                lines = monitor_urls_file.readlines()
                monitor_urls_file.seek(0)

                for line in lines:
                    json_line = json.loads(line)
                    if json_line.get('origin_url') == url:
                        file_name = json_line.get('file_name')
                    else:
                        monitor_urls_file.write(line)
                file_name_hash = md5(file_name.encode('utf-8')).hexdigest()
                monitor_urls_file.truncate()
                monitor_urls_file.close()
                if os.path.exists(self.directory + self.monitored_urls_directory + host + "_" + file_name_hash + ".old"):
                    os.remove(self.directory + self.monitored_urls_directory + host + "_" + file_name_hash + ".old")
                if os.path.exists(self.directory + self.monitored_urls_directory + host + "_" + file_name_hash):
                    os.remove(self.directory + self.monitored_urls_directory + host + "_" + file_name_hash)
                del self.monitored_urls[url]
                self.file_names_list.repaint()
                self.file_names_list.revalidate()
                bad_status_code_dialog.dispose()
            button = swing.JButton("Yes", actionPerformed=stop_monitoring)
            button2 = swing.JButton("No", actionPerformed=lambda event: bad_status_code_dialog.dispose())
            button_panel.add(button)
            button_panel.add(swing.Box.createHorizontalStrut(10))
            button_panel.add(button2)
            center_panel = swing.JPanel()
            center_panel.setLayout(swing.BoxLayout(center_panel, swing.BoxLayout.Y_AXIS))
            center_panel.add(swing.Box.createVerticalGlue())
            center_panel.add(button_panel)
            center_panel.add(swing.Box.createVerticalGlue())
            bad_status_code_dialog.getContentPane().add(center_panel, awt.BorderLayout.SOUTH)
            bad_status_code_dialog.pack()
            bad_status_code_dialog.setVisible(True)
        
    def process_with_jsluice(self, messageInfo):
        response = messageInfo.getResponse()
        status_code = self._helpers.analyzeResponse(response).getStatusCode()
        url = self._helpers.analyzeRequest(messageInfo).getUrl()
        url_str = str(url)
        parsed_url = urlparse(url_str)
        port = parsed_url.port
        host = parsed_url.netloc if port not in [80, 443] else parsed_url.hostname
        file_extension = os.path.splitext(parsed_url.path)[1]
        url_split = parsed_url.scheme + "://" + parsed_url.netloc + parsed_url.path
        is_text_html = False
        is_javascript = False
        javascript_mime_types = ["application/javascript", "text/javascript", "application/ecmascript", "text/ecmascript", "application/x-javascript", "application/x-ecmascript"]
        if self.in_scope_checkbox.isSelected():
            if not self._callbacks.isInScope(url):
                print("URL is not in scope: " + url_str)
                return
        if url_split not in self.seen_endpoints and file_extension != ".js":
            headers = self._helpers.analyzeResponse(response).getHeaders()
            for header in headers:
                if header.lower().startswith("content-type:"):
                    if self.include_inline_tags_checkbox.isSelected() and header.lower().startswith("content-type: text/html"):
                        is_text_html = True
                    elif any(mime_type in header.lower() for mime_type in javascript_mime_types):
                        is_javascript = True
                    break
        if ((file_extension == ".js" or is_javascript) and url_split not in self.seen_endpoints and (200 <= status_code <= 299)) or (self.include_inline_tags_checkbox.isSelected() and (200 <= status_code <= 299) and is_text_html and url_split not in self.seen_endpoints):
            analyzed_response = self._helpers.analyzeResponse(response)
            response_body = response[analyzed_response.getBodyOffset():].tostring()
            file_name = parsed_url.path
            if self.include_inline_tags_checkbox.isSelected() and is_text_html:
                script_tags = re.findall(r'<script.*?>(.*?)</script>', response_body, re.DOTALL)
                response_body = "\n".join(script_tags)
            file_name_hash = md5(file_name.encode()).hexdigest()
            file_path = self.directory + "/" + host + "_" + file_name_hash
            monitor_file_path = self.directory + self.monitored_urls_directory + host + "_" + file_name_hash
            urls_command = "jsluice urls " + file_path
            with open(file_path, "w") as f:
                f.write(response_body)
            process_urls = subprocess.Popen(urls_command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            urls_stdout, stderr = process_urls.communicate()
            urls_stdout_list = (json.loads(line) for line in urls_stdout.splitlines())
            sorted_stdout = []
            for line in urls_stdout_list:
                if "queryParams" in line:
                    line["queryParams"] = sorted(line["queryParams"])
                if "bodyParams" in line:
                    line["bodyParams"] = sorted(line["bodyParams"])
                sorted_stdout.append(json.dumps(line))
            urls_stdout = "\n".join(sorted_stdout)
            if os.path.exists(monitor_file_path):
                monitored_file = ""                    
                with open(monitor_file_path, "r") as f:
                    monitored_file = json.load(f) if os.stat(monitor_file_path).st_size > 0 else ""
                if urls_stdout.decode("utf-8") != monitored_file.decode("utf-8"):
                    self.show_dialogs(url=url_str)
                    if os.path.exists(monitor_file_path + ".old"):
                        os.remove(monitor_file_path + ".old")
                    os.rename(monitor_file_path, monitor_file_path + ".old")
                    with open(monitor_file_path, "w") as f:
                        f.write(json.dumps(urls_stdout))
            if self.secrets_checkbox.isSelected():
                secrets_command = "jsluice secrets " + file_path
                process_secrets = subprocess.Popen(secrets_command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                secrets_stdout, stderr2 = process_secrets.communicate()

            if (not self.secrets_checkbox.isSelected() and urls_stdout == '') or (self.secrets_checkbox.isSelected() and urls_stdout == '' and secrets_stdout == ''):
                try:
                    os.remove(file_path)
                except OSError:
                    pass
                if url_str in self.monitored_urls:
                    self.show_dialogs(host=host, url=url_str, reason_label="Returned no endpoints or secrets")
                self.seen_endpoints.add(url_split)
                return
            
            if host not in self.hosts_list:
                if self.in_scope_checkbox.isSelected():
                    if self._callbacks.isInScope(url):
                        self.hosts_list.add(host)
                        self.host_list_model.addElement(host)
                else:
                    self.hosts_list.add(host)
                    self.host_list_model.addElement(host)
                self.tabbed_pane_hosts.setTitleAt(0, str(self.host_list_model.size()) + " Hosts")

            if self.secrets_checkbox.isSelected():
                processed_file_details = {"host": host, "file_name": file_name, "output": urls_stdout.encode('utf-8'), "secrets": secrets_stdout.encode('utf-8'), "origin_url": url_str}
                lines = secrets_stdout.strip().split("\n")
                found_secret = False
                for line in lines:
                    if line == '':
                        continue
                    data = json.loads(line, encoding='utf-8')
                    match = data["data"].get("match")
                    key = data["data"].get("key")
                    if match and str(match.encode('utf-8')) not in self.unique_secrets:
                        self.unique_secrets.add(match)
                        found_secret = True
                    elif key and str(key.encode('utf-8')) not in self.unique_secrets:
                        self.unique_secrets.add(key)
                        found_secret = True
                    else:
                        pass    
                if found_secret:
                    if host not in self.hosts_with_secrets:
                        self.hosts_with_secrets.add(host)
                        self.add_image_to_host(self.hosts_with_secrets, self.secret_image_base64data)
                    if self.secret_notifications_checkbox.isSelected():
                        self.show_dialogs(host=host)
            else:
                processed_file_details = {"host": host, "file_name": file_name, "output": urls_stdout.encode('utf-8'), "origin_url": url_str}
            self.processed_file_details[url_split] = processed_file_details
            try:
                os.remove(file_path)
            except OSError:
                pass
            self.seen_endpoints.add(url_split)
            if host == self.selected_host:
                if file_name not in self.file_names_model.toArray():
                    self.file_names_model.addElement(file_name)
                    self.file_names_list.setCellRenderer(ColorFiles(self.monitored_urls, self.processed_file_details, self.selected_host, self.directory, self.monitored_urls_directory))

    def processHttpMessage(self, toolFlag, messageIsRequest, messageInfo):
        if not messageIsRequest and ((self.on_off_button.isSelected() and toolFlag == self._callbacks.TOOL_PROXY)):
            self.process_with_jsluice(messageInfo)

    def createMenuItems(self, invocation):
        menuList = []
        if invocation.getToolFlag() == self._callbacks.TOOL_TARGET:
            if invocation.getInvocationContext() in [invocation.CONTEXT_TARGET_SITE_MAP_TREE, invocation.CONTEXT_TARGET_SITE_MAP_TABLE]:
                menuItem = swing.JMenuItem("Process selected item(s)", actionPerformed=lambda x: self.schedule_event(0, self.action, args=[invocation]))
                menuList.append(menuItem)
        return menuList

    def show_dialog2(self, site_map, invocation):
        self.dialog = swing.JDialog()
        self.dialog.setTitle("jsluice++")
        self.dialog.setDefaultCloseOperation(swing.JDialog.DISPOSE_ON_CLOSE)
        self.dialog.setSize(300, 124)
        self.dialog.setLocationRelativeTo(None)
        self.dialog.setLayout(swing.BoxLayout(self.dialog.getContentPane(), swing.BoxLayout.Y_AXIS))
        self.dialog.setModal(True)
        self.dialog.setAlwaysOnTop(True)
        self.dialog.setResizable(False)

        self.label1 = swing.JLabel("Processing " + str(len(site_map)) + " items...")
        self.dialog.add(self.label1)

        self.progress_bar = swing.JProgressBar(0, len(site_map))
        self.progress_bar.setStringPainted(True)
        self.progress_bar.setString("0/" + str(len(site_map)))
        self.dialog.add(self.progress_bar)

        self.buttons_panel = swing.JPanel()
        self.buttons_panel.setLayout(swing.BoxLayout(self.buttons_panel, swing.BoxLayout.X_AXIS))
        self.buttons_panel.add(swing.Box.createHorizontalGlue())

        self.threads_panel = swing.JPanel()
        self.threads_panel.setLayout(swing.BoxLayout(self.threads_panel, swing.BoxLayout.X_AXIS))
        self.threads_panel.add(swing.Box.createHorizontalGlue())

        self.threads_label = swing.JLabel("Threads:")
        spinner_model = swing.SpinnerNumberModel(1, 1, 20, 1)
        self.threads_spinner = swing.JSpinner(spinner_model)
        self.threads_spinner.preferredSize = java.awt.Dimension(64, 24)
        self.threads_spinner.setMaximumSize(java.awt.Dimension(64, 24))

        self.threads_panel.add(self.threads_label)
        self.threads_panel.add(self.threads_spinner)
        self.threads_panel.add(swing.Box.createHorizontalGlue())
        self.dialog.add(self.threads_panel)

        self.start_button = swing.JButton("Start", actionPerformed=lambda x: self.schedule_event(0, self.process_site_map, args=(site_map, invocation)))
        self.start_button.setForeground(awt.Color.BLACK)
        self.start_button.setBackground(awt.Color(110, 204, 154))
        self.buttons_panel.add(self.start_button)
        self.buttons_panel.add(swing.Box.createHorizontalGlue())
        self.cancel_button = swing.JButton("Cancel", actionPerformed=lambda x:  (self.cancel_progress(site_map, invocation), self.dialog.dispose()))
        self.buttons_panel.add(self.cancel_button)
        self.buttons_panel.add(swing.Box.createHorizontalGlue())
        self.dialog.add(self.buttons_panel)
        self.dialog.setVisible(True)
        
    def cancel_progress(self, site_map, invocation):
        self.cancelled = True
        self.start_button.setText("Start")
        self.start_button.setBackground(awt.Color(110, 204, 154))
        self.start_button.actionPerformed = lambda x: self.schedule_event(0, self.process_site_map, args=(site_map, invocation))
        self.threads_spinner.setEnabled(True)

    def process_site_map(self, site_map, invocation):
        self.cancelled = False
        self.threads_spinner.setEnabled(False)
        self.start_button.setText("Stop")
        self.start_button.setBackground(awt.Color(240,128,128))
        self.start_button.actionPerformed = lambda x: self.cancel_progress(site_map, invocation)
        if len(site_map) < self.threads_spinner.getValue():
            self.threads_spinner.setValue(len(site_map))
        start_time = time()
        semaphore = Semaphore(int(self.threads_spinner.getValue()))
        def process_item(item):
            self.process_with_jsluice(item)
            self.update_progress(index, len(site_map), invocation, start_time)
            semaphore.release()
        for index, item in enumerate(site_map, start=1):
            semaphore.acquire()
            if self.cancelled:
                semaphore.release()
                break
            Thread(target=process_item, args=(item,)).start()
        return

    def update_progress(self, current, total, invocation, start_time):
        if current == total:
            self.dialog.remove(self.threads_spinner)
            self.threads_panel.remove(self.threads_spinner)
            self.threads_panel.remove(self.threads_label)
            self.buttons_panel.remove(self.start_button)
            end_time = time()
            if invocation.getInvocationContext() in [invocation.CONTEXT_TARGET_SITE_MAP_TREE, invocation.CONTEXT_TARGET_SITE_MAP_TABLE]:
                self.label1.setText(str(total) + " items processed in " + str(round(end_time - start_time, 2)) + " seconds")
            self.cancel_button.setText("Close")
            self.dialog.setSize(self.dialog.getPreferredSize())
            self.dialog.revalidate()
            self.dialog.repaint()
        percent = int((float(current) / float(total)) * 100)
        self.progress_bar.setValue(current)
        self.progress_bar.setString(str(current) + "/" + str(total) + " (" + str(percent) + "%)")
        self.dialog.revalidate()
        self.dialog.repaint()

    def action(self, invocation):
        self.cancelled = False
        selected_messages = invocation.getSelectedMessages()
        if invocation.getInvocationContext() in [invocation.CONTEXT_TARGET_SITE_MAP_TREE]:  
            if len(selected_messages) == 1:
                site_map = [item for item in self._callbacks.getSiteMap(str(selected_messages[0].getUrl())) if item.getResponse() != None]
            else:
                selected_messages = [msg.getUrl() for msg in selected_messages if urlparse(unicode(msg.getUrl())).path == "/"]
                site_map = [item for item in [self._callbacks.getSiteMap(str(selected_messages[i])) for i in range(len(selected_messages))] for item in item if item.getResponse() != None]
        elif invocation.getInvocationContext() in [invocation.CONTEXT_TARGET_SITE_MAP_TABLE]:
            site_map = [item for item in selected_messages if item.getResponse() != None]
        swing.SwingUtilities.invokeLater(lambda: self.show_dialog2(site_map, invocation))
        
    def on_host_selected(self, event):
        if self.host_list.getSelectedValue() == None:
            return
        self.file_names_model.clear()
        self.loading_label.setVisible(True)
        self.tabbed_pane_files.setTitleAt(0, "Loading...")
        swing.SwingUtilities.invokeLater(lambda: self.handle_selected_host(event))
        return

    def handle_selected_host(self, event):
        if isinstance(event, swing.event.ListSelectionEvent) and event.getValueIsAdjusting():
            return
        selected_host = self.host_list.getSelectedValue()
        if selected_host:
            self.file_names_model.clear()
            file_names = self.get_processed_file_names(selected_host)
            
            def update_file_names():
                self.loading_label.setVisible(False)
                for file_name in file_names:
                    if file_name not in self.file_names_model.toArray():
                        self.file_names_model.addElement(file_name)
                if file_names and not self.autoselectall_button.isSelected():
                    self.file_names_list.setSelectedIndex(0)
                elif file_names and self.autoselectall_button.isSelected():
                    self.file_names_list.setSelectionInterval(0, self.file_names_model.size() - 1)
                self.file_list_popupmenu.selected_host = selected_host
                self.file_list_popupmenu.file_names_list = self.file_names_list
                self.file_list_popupmenu.processed_file_details = self.processed_file_details
                self.file_list_popupmenu.monitored_urls = self.monitored_urls
                self.file_names_list.setCellRenderer(ColorFiles(self.monitored_urls, self.processed_file_details, self.selected_host, self.directory, self.monitored_urls_directory))
                self.file_names_list.revalidate()
                self.file_names_list.repaint()
                self.tabbed_pane_files.setTitleAt(0, str(len(file_names)) + " File" + ("s" if len(file_names) > 1 else ""))
                self.file_names_list.setValueIsAdjusting(False)
            swing.SwingUtilities.invokeLater(lambda: update_file_names())

    def toggle_autoselectall(self, event):
        if self.autoselectall_button.isSelected():
            self.autoselectall_button.setBorder(self.green_border)
        else:
            self.autoselectall_button.setBorder(self.red_border)
        if self.host_list.getSelectedValue():
            self.loading_label.setVisible(True)
            swing.SwingUtilities.invokeLater(lambda: self.handle_selected_host(event))

    def process_lines(self, lines, selected_files_length, selected_file_name):
        processed_rows = []
        for line in lines:
            if line == '':
                continue
            try:
                data = json.loads(line)
                queryParams = '' if data["queryParams"] == [] else json.dumps(data["queryParams"])
                bodyParams = '' if data["bodyParams"] == [] else json.dumps(data["bodyParams"])
                method = '' if data["method"] == '' else json.dumps(data["method"])
                headers = json.dumps(data["headers"]) if data.get("headers") is not None else ''
                row_data = (
                    json.dumps(data["url"]).replace('"', ''),
                    queryParams[1:-1],
                    bodyParams,
                    method[1:-1],
                    headers,
                    json.dumps(data["type"]).replace('"', ''),
                )
                if selected_files_length > 1:
                    row_data = row_data + (selected_file_name,)
                processed_rows.append(row_data)
            except ValueError:
                print("Error parsing the line: " + line)
        return processed_rows

    def display_result(self, event, file_names_list):
        if isinstance(event, swing.event.ListSelectionEvent) and "invalid" in str(event) and event.getValueIsAdjusting() and len(self.file_names_model.toArray()) != 0:
            return
        deleted_lines = set()
        differences = set()
        self.selected_host = self.host_list.getSelectedValue()
        self.results_table_popupmenu.selected_host = self.selected_host
        selected_files = file_names_list.getSelectedValuesList()
        selected_files_length = len(selected_files)
        if self.selected_host:
            self.result_table_model.setRowCount(0)
            self.tabbed_pane_results.setTitleAt(0, str(self.selected_host) + " - Loading...")
            if self.secrets_checkbox.isSelected():
                if self.tabbed_pane_results.indexOfComponent(self.scroll_pane_secrets) == -1:
                    self.tabbed_pane_results.addTab("Secrets", self.scroll_pane_secrets)
                self.tabbed_pane_results.setTitleAt(1, "Secrets - Loading...")
            rows = []
            if selected_files_length > 0:
                rows = self.get_results_rows(selected_files, selected_files_length, rows, differences, deleted_lines)
                for row in rows:
                    self.result_table_model.addRow(row)
                for column in range(self.result_table_model.getColumnCount()):
                    self.result_table.getColumnModel().getColumn(column).setCellRenderer(ColorResults(differences, deleted_lines))
                self.tabbed_pane_results.setTitleAt(0, self.get_result_tab_name())
                if self.secrets_checkbox.isSelected():
                    rows = self.get_secrets_rows(selected_files_length, selected_files)
                    for row in rows:
                        self.secrets_table_model.addRow(row)
                    self.tabbed_pane_results.setTitleAt(1, "Secrets ({} rows)".format(self.secrets_table_model.getRowCount()))
                self.tabbed_pane_results.revalidate()
                self.tabbed_pane_results.repaint()

    def get_results_rows(self, selected_files, selected_files_length, rows, differences, deleted_lines):
        for selected_file_name in selected_files:
            selected_file_details = None
            for file in self.processed_file_details.values():
                if file["host"] == self.selected_host and file["file_name"] == selected_file_name:
                    selected_file_details = file
                    break
            if selected_file_details and selected_file_details["output"]:
                monitor_filter_name_hash = md5(selected_file_details["file_name"].encode('utf-8')).hexdigest()
                monitor_file_name = selected_file_details["host"] + "_" + monitor_filter_name_hash
                monitor_file_path = self.directory + self.monitored_urls_directory + monitor_file_name + ".old" if os.path.exists(self.directory + self.monitored_urls_directory + monitor_file_name + ".old") else self.directory + self.monitored_urls_directory + monitor_file_name
                lines = selected_file_details["output"].strip().split("\n")
                rows.extend(self.process_lines(lines=lines, selected_files_length=selected_files_length, selected_file_name=selected_file_name))
                if os.path.exists(monitor_file_path):
                        with open(monitor_file_path, "r") as f:
                            monitor_file_content = json.loads(f.read())
                            try:
                                monitor_file_lines = set(monitor_file_content.strip().split("\n"))
                            except ValueError:
                                print("Error parsing the monitor file. Please ensure it contains valid JSON.")
                                monitor_file_lines = set()
                        selected_file_lines = set(selected_file_details["output"].strip().split("\n"))
                        new_or_changed_lines = selected_file_lines - monitor_file_lines
                        removed_lines = monitor_file_lines - selected_file_lines
                        new_or_changed_rows = self.process_lines(lines=new_or_changed_lines, selected_files_length=selected_files_length, selected_file_name=selected_file_name)
                        removed_rows = self.process_lines(lines=removed_lines, selected_files_length=selected_files_length, selected_file_name=selected_file_name)
                        differences.update(new_or_changed_rows)
                        deleted_lines.update(removed_rows)
                        if len(removed_rows) > 0:
                            rows.extend(removed_rows)
                self.result_table_model.setColumnIdentifiers(["URL/Path", "Query Params", "Body Params", "Method", "Headers", "Type"] + (["File"] if selected_files_length > 1 else []))
                if self.hide_duplicates_checkbox.isSelected():
                    type_column_index = self.result_table_model.findColumn("Type")
                    seen_rows = set()
                    rows = [row for row in rows if tuple(row[:type_column_index]) not in seen_rows and not seen_rows.add(tuple(row[:type_column_index]))]
                if len(self.results_filters) > 0:
                    filtered_rows = []
                    for row in rows:
                        if all((self.results_filters.get(f) == 'negative' and f not in row[0]) or
                            (self.results_filters.get(f) == 'positive' and f in row[0]) for f in self.results_filters):
                            filtered_rows.append(row)
                    rows = filtered_rows
                if self.show_parameterized.isSelected():
                    rows = [row for row in rows if row[1] != '' or row[2] != '' or row[4] != '']
        return rows

    def get_secrets_rows(self, selected_files_length, selected_files):
        rows = []
        if self.selected_host and selected_files_length > 0:
            self.secrets_table_model.setRowCount(0)
            for selected_file_name in selected_files:
                selected_file_details = None
                for key, value in self.processed_file_details.items():
                    if value["host"] == self.selected_host and value["file_name"] == selected_file_name:
                        selected_file_details = value
                        break
                if selected_file_details and "secrets" in selected_file_details and selected_file_details["secrets"]:
                    self.secrets_table_model.setColumnIdentifiers(["kind", "data", "severity", "context"] + (["File"] if selected_files_length > 1 else []))
                    lines = selected_file_details["secrets"].strip().split("\n")
                    for line in lines:
                        if line == "":
                            continue
                        data = json.loads(line, encoding='utf-8')
                        data_string = ", ".join(["{}:{}".format(key.encode('utf-8'), value.encode('utf-8')) for key, value in data["data"].items()])
                        context_string = ""
                        if data.get("context") is not None:
                            context_string = ", ".join([u"{}:{}".format(key.encode('utf-8'), value.encode('utf-8')) for key, value in data["context"].items()])
                        row_data = [
                            data["kind"],
                            data_string,
                            data["severity"],
                            context_string,
                            selected_file_name
                        ]
                        rows.append(row_data)
            if self.hide_duplicates_checkbox.isSelected():
                if selected_files_length > 1:
                    file_column_index = self.secrets_table_model.findColumn("File")
                    seen_rows = set()
                    rows = [row for row in rows if tuple(row[:file_column_index] + row[file_column_index+1:]) not in seen_rows and not seen_rows.add(tuple(row[:file_column_index] + row[file_column_index+1:]))]
                else:
                    rows = [list(x) for x in set(tuple(x) for x in rows)]
        return rows

    def filter_hosts(self):
        selected_hosts = list(self.hosts_list)
        current_selection = self.host_list.getSelectedValue()
        in_scope_hosts = []
        if self.in_scope_checkbox.isSelected():
            in_scope_hosts = [host for host in selected_hosts if self._callbacks.isInScope(URL(str("http://" + host))) or self._callbacks.isInScope(URL(str("https://" + host)))]
            current_selection = current_selection if current_selection in in_scope_hosts else None
            self.host_list_model.clear()
            for host in in_scope_hosts:
                self.host_list_model.addElement(host)
        else:
            current_selection = current_selection if current_selection in selected_hosts else None
            self.host_list_model.clear()
            for host in selected_hosts:
                self.host_list_model.addElement(host)
        self.tabbed_pane_hosts.setTitleAt(0, str(self.host_list_model.size()) + " Hosts" if self.host_list_model.size() > 0 else "Hosts")
        self.host_list_scroll_pane.setViewportView(self.host_list)
        if current_selection:
            index = in_scope_hosts.index(current_selection) if self.in_scope_checkbox.isSelected() else selected_hosts.index(current_selection)
            self.host_list.setSelectedIndex(index)
        elif len(in_scope_hosts) > 0:
            self.host_list.setSelectedIndex(0)
        else:
            self.file_names_model.clear()
            self.file_names_scroll_pane.setViewportView(self.file_names_list)
            self.result_table_model.setRowCount(0)
            self.tabbed_pane_results.setTitleAt(0, "Results")
            self.tabbed_pane_files.setTitleAt(0, "Files")
            if self.secrets_checkbox.isSelected():
                self.secrets_table_model.setRowCount(0)
                self.tabbed_pane_results.setTitleAt(1, "Secrets")
            self.host_list.clearSelection()

    def get_processed_file_names(self, selected_host):
        return [value["file_name"] for value in self.processed_file_details.values() if value["host"] == selected_host]

    def get_result_tab_name(self):
        selected_host = self.host_list.getSelectedValue()
        selected_files = self.file_names_list.getSelectedValuesList()
        num_rows = self.result_table_model.getRowCount()
        if len(selected_files) == 1:
            return "{} - {} ({} rows)".format(selected_host, selected_files[0], num_rows)
        else:
            return "{} - {} Files ({} rows)".format(selected_host, len(selected_files), num_rows)

    def getTabCaption(self):
        return "jsluice++"

    def getUiComponent(self):
        return self.panel







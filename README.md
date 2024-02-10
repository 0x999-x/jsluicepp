<div align="center">
  
[![jsluice++ Logo](https://raw.githubusercontent.com/0x999-x/jsluicepp/main/.github/images/logo.png)](#)

</div>

## 📄 Table of Contents
- [👋 Introduction](#-introduction)
- [🛠️ Setup](#%EF%B8%8F-setup)
- [📝 Usage](#-usage)
- [📜 Features](#-features)
  - <sub>[Monitor URLs](#monitor-urls)</sub>
  - <sub>[Send to Repeater](#send-to-repeater)</sub>
  - <sub>[Secrets](#secrets)</sub>
  - <sub>[Secret Notifications](#secret-notifications)</sub>
  - <sub>[Copy URL](#copy-url)</sub>
  - <sub>[Positive/Negative Match](#positivenegative-match)</sub>
  - <sub>[In-scope only](#in-scope-only)</sub>
  - <sub>[In-line Tags](#in-line-tags)</sub>
  - <sub>[Hide Duplicates](#hide-duplicates)</sub>
  - <sub>[Show Parameterized](#show-parameterized)</sub>
  - <sub>[Import/Export](#importexport)</sub>
  - <sub>[Save Settings](#save-settings)</sub>
- [🤝 Contributors](#-contributors)


## 👋 Introduction

jsluice++ is a Burp Suite extension designed for passive and active scanning of JavaScript traffic using the CLI tool [jsluice](https://github.com/BishopFox/jsluice/tree/main/cmd/jsluice).<br>
The extension utilizes jsluice's capabilities to extract URLs, paths, and secrets from static JavaScript files and integrates it with Burp Suite, allowing you to easily scan javascript traffic from Burp Suite's Sitemap or Proxy while also offering a user-friendly interface for data inspection and a variety of additional useful features

<p align="center">
<img src="https://raw.githubusercontent.com/0x999-x/jsluicepp/main/.github/images/jsluicepp.png" alt="jsluice++">
</p>

## 🛠️ Setup

Requirements:
- jsluice CLI
- Jython(2.7.3)

if this isn't your first time installing a jython extension you can skip to step 3.<br>
1. Visit [Jython's Official Website](https://www.jython.org/download) and download Jython's standalone JAR
2. In Burp Suite -> "Extensions" -> "Extensions Settings" -> under "Python environment" select the "Location of Jython standalone JAR file"
3. Download and install [jsluice's](https://github.com/BishopFox/jsluice/tree/main/cmd/jsluice) CLI <code>go install github.com/BishopFox/jsluice/cmd/jsluice@latest</code> (ensure that the jsluice binary is in your <code>$PATH</code> otherwise the extension won't work)
4. Download jsluicepp.py, then in Burp Suite go to "Extensions" -> "Installed" -> Click "Add" -> under "Extension type" select "Python" -> Select the jsluicepp.py file.

## 📝 Usage

##### Active scan

The extension adds an item to Burp Suite's context menu which allows you to easily process responses from Burp Suite's Sitemap tab</br>
                                                                                                                                     
to do so simply right click any host in the sitemap tree or any item in the sitemap table and select <code>Extensions->jsluice++->Process selected item(s)</code> in Burp Suite's context menu.
When processing items from the site map tree the extension will get the site map of every selected item (Multiple hosts can be processed)

![Process from Sitemap](https://raw.githubusercontent.com/0x999-x/jsluicepp/main/.github/images/jsluicepp-process-from-sitemap.gif)

##### Passive scan
<code>Default: Off</code>

When Passive scan is toggled on the extension will register an http handler and process responses from traffic flowing through Burp Suite's Proxy (it's recommended to use the in-scope only feature when enabling passive scan to reduce noise)

---

The extension will process any URL with a .js file extension or a JavaScript mime type and a success status code (2xx) using jsluice's urls mode.</br>

The processed JavaScript file is temporarily saved locally in the ".jsluicepp" directory and gets removed after jsluice has finished processing it,

If jsluice returns any data, the host associated with the URL will be added to the Hosts list, to view the results from jsluice simply select the host and the desired file (multiple files can be selected).

Note: the same URL (GET parameters excluded) will not be processed more than once until the extension is reloaded, this doesn't apply to monitored urls.

---
## 📜 Features

<details open><summary><h4>Monitor URLs</h4></summary><a name="#monitor-urls"></a>

Every file in the Files list can be monitored by the extension, to do so simply right-click the file and select the "Monitor URL" option from the popup menu (repeat this step if you wish to Stop Monitoring the URL),<br>
When a new URL is monitored it's details are saved to <code>.jsluicepp/monitored_urls.txt</code> and a copy of the output from jsluice is saved locally to <code>.jsluicepp/monitored_files/{host}_{filename_hash}</code>(Secrets excluded),<br>
Monitored files are colored green in the Files list,<br>
The rate at which requests are sent to the monitored URLs is determined by the selected value in the Monitor Interval selector,

Monitor interval options are:
- Off - Don't monitor
- Once - Once when the extension loads
- Hourly - Once every hour
- Daily - Once every day
- Weekly - Once every week
- Monthly - Once every month
<br>
if jsluice has returned data that is different from the locally saved copy you will be notified with the following popup dialog:

![Change in Monitored URL](https://raw.githubusercontent.com/0x999-x/jsluicepp/main/.github/images/change_in_monitored.png)

the locally saved copy of the file will get moved to <code>.jsluicepp/monitored_files/{host}_{filename_hash}.old</code> and a new copy of the new file will be saved,
When selecting the monitored file in the extension new/modified rows will be colored green and previous versions of modified rows/deleted rows will be colored red, example: 

![Change in Monitored URL 2](https://raw.githubusercontent.com/0x999-x/jsluicepp/main/.github/images/change_in_monitored2.png)


if a Monitored URL responds with a non-success status code(2xx) or if jsluice returns no output you will be prompted with a popup dialog asking if you wish to Stop Monitoring the URL, if "Yes" is selected all local copies of the file will be removed.

![No results from Monitored URL](https://raw.githubusercontent.com/0x999-x/jsluicepp/main/.github/images/no_results_monitored.png)
</details>
<details open><summary><h4>Send to Repeater</h4></summary><a name="#send-to-repeater"></a>

Every row in the URL/Paths results table can be sent to Burp Suite's Repeater by right clicking any row and selecting the "Send to Repeater" option in the popup menu.<br>
Query Params, Body Params & Headers will be included if any exist,
if the URL/Path column starts with "http://" or "https://" or "//" the host will be extracted from the URL/Path column otherwise the selected host will be used, 
if a content-type header with a value of <code>application/json or application/xml or text/xml</code> is present in the Headers column the body of the request will be formatted accordingly.
</details>
<details open><summary><h4>Secrets</h4></summary><a name="#secrets"></a>
<code>Default: On</code>

If selected a "Secrets" results table is added to the UI and the extension will use jsluice's secrets mode on the file after the urls mode has finished, if any unique secrets are found the host will be colored red with a 🤫 emoji next to it, example: 

![Colored Hosts](https://raw.githubusercontent.com/0x999-x/jsluicepp/main/.github/images/hosts.png)

if you wish to use a custom patterns config you can do so by modifying the 'secrets_command' variable in the code.
</details>
<details open><summary><h4>Secret Notifications</h4></summary><a name="#secret-notifications"></a>
<code>Default: Off</code>

If selected and the Secrets checkbox is also selected you will be notified with a popup dialog when a new unique secret is found, the dialog is closed automatically after 15 seconds , example dialog:<br>
![Example secret notification](https://raw.githubusercontent.com/0x999-x/jsluicepp/main/.github/images/secret_notification.png)
</details>
<details open><summary><h4>Copy URL</h4></summary><a name="#copy-url"></a>

The URL of every processed file can be copied to clipboard by right-clicking the file in the Files list and selecting the "Copy URL" option from the popup menu.
</details>
<details open><summary><h4>Positive/Negative Match</h4></summary><a name="#positivenegative-match"></a>

The positive/negative match filter feature is designed to target the URL/Path column within the results table, When adding a positive filter, only rows that contain the positive match filter within the URL/Path column will be included in the results table. Conversely, when adding a negative filter, rows that have the negative match filter in the URL/Path column will be excluded from the results,
Multiple filters can be applied.
![Positive-Negative Match](https://raw.githubusercontent.com/0x999-x/jsluicepp/main/.github/images/jsluicepp-filters.gif)
</details>
<details open><summary><h4>In-scope only</h4></summary><a name="#in-scope-only"></a>
<code>Default: Off</code>

If selected the extension will use Burp Suite's scope to determine whether a URL should be processed, additionally out of scope hosts will not be displayed in the hosts list.
</details>
<details open><summary><h4>In-line Tags</h4></summary><a name="#in-line-tags"></a>
<code>Default: Off</code>

When selected, in addition to URLs with a .js file extension/mime type, the extension will look for responses with HTML mime type, if such response is found the extension will attempt to extract any and all <code><script></code> tags from the response body, the script tags are then concatenated using new lines and saved to a file which then gets processed by jsluice.
</details>
<details open><summary><h4>Hide Duplicates</h4></summary><a name="#hide-duplicates"></a>
<code>Default: On</code>

If selected duplicate rows will be hidden from the results tables(excluding the Type & File columns)
</details>
<details open><summary><h4>Show Parameterized</h4></summary><a name="#show-parameterized"></a>
<code>Default: Off</code>

If selected only rows that contain Query Params / Body Params / Headers will be displayed in the URL/Paths results table
</details>

<details open><summary><h4>Import/Export</h4></summary><a name="#importexport"></a>
  
Import/Export results or currently selected settings as JSON
</details>

<details open><summary><h4>Save Settings</h4></summary><a name="#save-settings"></a>

Save current selected settings using Burp Suite's API (persists across restarts)
</details>

## 🤝 Contributors

[TomNomNom](https://github.com/tomnomnom) for creating jsluice 💖 [![TomNomNom](https://raw.githubusercontent.com/0x999-x/jsluicepp/main/.github/images/tomnomnom_X.png)](https://twitter.com/intent/follow?screen_name=tomnomnom)<br>[Me](https://github.com/0x999-x) [![0x999](https://raw.githubusercontent.com/0x999-x/jsluicepp/main/.github/images/0x999_X.png)](https://twitter.com/intent/follow?screen_name=_0x999)<br>You?


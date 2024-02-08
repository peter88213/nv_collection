[Project homepage](https://peter88213.github.io/noveltree_collection) > Instructions for use

--- 

A [noveltree](https://peter88213.github.io/noveltree/) plugin providing a book/series collection manager. 

---

# Installation

If [noveltree](https://peter88213.github.io/noveltree/) is installed, the setup script auto-installs the *noveltree_collection* plugin in the *noveltree* plugin directory.

The plugin adds a **Collection** entry to the *noveltree* **File** menu, and a **Collection plugin Online help** entry to the **Help** menu. 

---

# Operation

---

## Launch the program

- Open the collection manager from the main menu: **File > Collection**.

---

## Open a collection

- By default, the latest collection selected is preset. You can change it with **File > Open**.

---

## Create a new collection

- You can create a new collection with **File > New**. This will close the current collection
  and open a file dialog asking for the location and file name of the collection to create.
- Once you specified a valid file path, a blank collection appears.

---

## Create a new series

- You can add a new series with **Series > Add**. Edit the series' title and description in the right window.

---

## Add books to the collection

- You can add the current noveltree project as a book to the collection. Use **Book > Add current project to the collection**.
- If a series is selected, the book is added as a part of this series.

---

## Update book description

- You can update the book description from the current project. Use **Book > Update book data from the current project**. 
  Be sure not to change the book title, because it is used as identifier. 
- You can update the current project description from the book. Use **Book > Update project data from the selected project**. 

---

## Remove books from the collection

- You can remove the selected book from the collection. Use **Book > Remove selected book from the collection**.

---

## Move series and books

Drag and drop while pressing the **Alt** key. Be aware, there is no "Undo" feature. 

---

## Remove books

Either select item and hit the **Del** key, or use **Book > Remove selected book from the collection**.

- When removing a book from the collection, the project file associated is kept on disc. 

---

## Delete a series

Either select series and hit the **Del** key, or use **Series > Remove selected series but keep the books**.

- When deleting a collection, the books are kept by default.
- Use **Series > Remove selected series** to delete the selected series and remove all its books from the collection. 

---

## Quit/Exit

- Under Windows you can exit with **File > Exit** or **Alt-F4**.
- Otherwise you can exit with **File > Quit** or **Ctrl-Q**.
- When exiting the collection manager, you will be asked for saving the project, if it has changed.

---

# License

This is Open Source software, and the *noveltree_collection* plugin is licensed under GPLv3. See the
[GNU General Public License website](https://www.gnu.org/licenses/gpl-3.0.en.html) for more
details, or consult the [LICENSE](https://github.com/peter88213/noveltree_collection/blob/main/LICENSE) file.

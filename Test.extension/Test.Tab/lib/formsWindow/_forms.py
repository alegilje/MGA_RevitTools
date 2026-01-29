# encoding: utf-8
#  _  _      ____  ____  ____  _____ 
# / \/ \__/|/  __\/  _ \/  __\/__ __\
# | || |\/|||  \/|| / \||  \/|  / \  
# | || |  |||  __/| \_/||    /  | |  
# \_/\_/  \|\_/   \____/\_/\_\  \_/  
# IMPORTS
#===========================================================================================================#
from math import e
from pyrevit import forms
import clr
import sys

clr.AddReference('System.Windows.Forms')
clr.AddReference('System.Drawing')
from System.Windows.Forms import Form, Button, CheckBox, TextBox, FormBorderStyle, DockStyle, Padding, TableLayoutPanel, AnchorStyles, Label, ScrollBars
from System.Drawing import Size, Point


#  _____ _     _      ____  _____  _  ____  _      ____ 
# /    // \ /\/ \  /|/   _\/__ __\/ \/  _ \/ \  /|/ ___\
# |  __\| | ||| |\ |||  /    / \  | || / \|| |\ |||    \
# | |   | \_/|| | \|||  \__  | |  | || \_/|| | \||\___ |
# \_/   \____/\_/  \|\____/  \_/  \_/\____/\_/  \|\____/
# FUNCTIONS
#==============================================================================================================================================================================================#
def dialogwindow_TextInput(exText,explainText,windowTitle):
    dialogWindow = forms.ask_for_string(exText,explainText,windowTitle)
    result = str(dialogWindow)
    return result


class InputElement:
    def __init__(self, label, value=None, output_name=None):
        self.label = label
        print(self.label)
        self.value = value
        print(self.value)
        self.output_name = output_name
        print(self.output_name)
        self.textbox = None
        print(self.textbox)
        self.checkbox = None
        print(self.checkbox)
        self.folder_button = None
        print(self.folder_button)

class InputForm(Form):
    def __init__(self, title, components):
        self.Text = title
        self.Size = Size(600, 500)
        self.MaximizeBox = False
        self.FormBorderStyle = FormBorderStyle.FixedDialog

        self.components = []
        self.folder_path = None  # Initialize folder_path

        self.table_layout = TableLayoutPanel()
        self.table_layout.Dock = DockStyle.Fill
        self.table_layout.Padding = Padding(20)
        self.table_layout.ColumnCount = 2
        self.table_layout.RowCount = 0

        print("Components received:", components)

        # Legg til elementene fra komponentene
        for component in components:
            print("Processing component:", component)  # Utskrift for hvert element
            if isinstance(component, dict):
                self.create_element(
                    component.get('label', ''),
                    component.get('value', ''),
                    component.get('output_name', ''),
                    component.get('checkbox', False),
                    component.get('folder_button', False)
                )
            else:
                raise ValueError("Each component must be a dictionary")
            

        self.error_textbox = self.create_error_textbox()

        self.ok_button = self.create_ok_button()
        self.cancel_button = self.create_cancel_button()

        self.Controls.Add(self.table_layout)

    def create_element(self, label, value=None, output_name=None, checkbox=False, folder_button=False):

        print(label, value, output_name)
        element = InputElement(label, value, output_name)

        if not checkbox:
            label_control = self.create_label(label)
            self.table_layout.Controls.Add(label_control, 0, self.table_layout.RowCount)

        if checkbox:
            element.checkbox = CheckBox()
            element.checkbox.Text = label
            element.checkbox.Margin = Padding(10)
            element.checkbox.AutoSize = True
            element.checkbox.Anchor = AnchorStyles.Top | AnchorStyles.Left
            self.table_layout.Controls.Add(element.checkbox, 0, self.table_layout.RowCount)
            

        elif folder_button:
            button = self.create_storage_button()
            self.table_layout.Controls.Add(button, 1, self.table_layout.RowCount)
            

        else:
            element.textbox = TextBox()
            element.textbox.Text = output_name
            element.textbox.Margin = Padding(10)
            element.textbox.AutoSize = True
            element.textbox.Anchor = AnchorStyles.Top | AnchorStyles.Right
            self.table_layout.Controls.Add(element.textbox, 1, self.table_layout.RowCount)
            
        self.components.append(element)
        self.table_layout.RowCount += 1  # Increment row count after adding the element

    def create_storage_button(self):
        button = Button()
        button.Text = "Browse"
        button.Margin = Padding(10)
        button.AutoSize = True
        button.Anchor = AnchorStyles.Bottom | AnchorStyles.Right
        button.Click += self.storage_button_clicked
        return button

    def create_ok_button(self):
        button = Button()
        button.Text = "Ok"
        button.Anchor = AnchorStyles.Bottom | AnchorStyles.Right
        button.Margin = Padding(10)
        button.Click += self.ok_button_clicked

        self.table_layout.RowCount += 1
        self.table_layout.Controls.Add(button, 1, self.table_layout.RowCount - 1)
        return button

    def create_cancel_button(self):
        button = Button()
        button.Text = "Cancel"
        button.Anchor = AnchorStyles.Bottom | AnchorStyles.Left
        button.Margin = Padding(10)
        button.Click += self.cancel_button_clicked

        self.table_layout.RowCount += 1
        self.table_layout.Controls.Add(button, 1, self.table_layout.RowCount - 1)
        return button

    def storage_button_clicked(self, sender, event):
        self.folder_path = forms.pick_folder()
        self.error_textbox.Text = self.folder_path if self.folder_path else "No folder selected."

    def ok_button_clicked(self, sender, event):
        output = self.get_output()
        if not self.folder_path or self.folder_path == "No folder selected.":
            self.error_textbox.Text = "No folder selected."
        else:
            self.error_textbox.Text = "Output: {}".format(output)  # Display output dictionary
        self.Close()  # Close the form after processing

    def cancel_button_clicked(self, sender, event):
        self.Close()  # Close the form after processing

    def create_label(self, text):
        label = Label()
        label.Text = text
        label.AutoSize = True
        label.Margin = Padding(10)

        return label

    def create_error_textbox(self):
        error_textbox = TextBox()
        error_textbox.Multiline = True
        error_textbox.Dock = DockStyle.Fill
        error_textbox.ReadOnly = True
        error_textbox.ScrollBars = ScrollBars.Both
        error_textbox.Height = 200
        self.table_layout.Controls.Add(error_textbox, 0, self.table_layout.RowCount)
        self.table_layout.SetColumnSpan(error_textbox, 2)
        self.table_layout.RowCount += 1
        return error_textbox

    def get_output(self):
        """
        Gathers all the input values from the form and returns them as a dictionary

        Returns:
            dict: A dictionary with the output values
        """
        output = {}
        for element in self.components:
            if element.checkbox:
                output[element.output_name] = element.checkbox.Checked if element.output_name else element.label
            elif element.textbox:
                output[element.output_name] = element.textbox.Text if element.output_name else element.label

        if self.folder_path:
            output['folder_path'] = self.folder_path

        return output



# Redirect stdout and stderr to the form's TextBox
class RedirectText(object):
    def __init__(self, widget):
        self.widget = widget

    def write(self, string):
        if self.widget and not self.widget.IsDisposed:
            self.widget.AppendText(string)
    
    def flush(self):
        pass  # Needed for compatibility with file-like behavior

# OutputForm class
class OutputForm(Form):
    def __init__(self):
        self.Text = "Output Form"
        self.Size = Size(400, 300)

        self.label = Label()
        self.label.Text = "Output:"
        self.label.Location = Point(10, 20)
        self.Controls.Add(self.label)

        self.output_text = TextBox()
        self.output_text.Location = Point(10, 50)
        self.output_text.Size = Size(360, 200)
        self.output_text.Multiline = True
        self.output_text.ScrollBars = ScrollBars.Vertical
        self.Controls.Add(self.output_text)

        # Save original stdout and stderr
        self.original_stdout = sys.stdout
        self.original_stderr = sys.stderr

        # Redirect stdout and stderr to the form's TextBox
        sys.stdout = RedirectText(self.output_text)
        sys.stderr = RedirectText(self.output_text)

        # Restore stdout and stderr when the form is closed
        self.FormClosed += self.on_form_closed

    def on_form_closed(self, sender, event):
        sys.stdout = self.original_stdout  # Restore original stdout
        sys.stderr = self.original_stderr  # Restore original stderr

    def run_process(self):
        print("OutputForm is running...")


import pandas as pd
import sys
import pathlib as pl
import tkinter as tk
from tkinter import filedialog
from tkinter.ttk import Treeview
from tkinter import ttk

class CycloMeter():
    '''Object that reads Strava CSV file. Due to Strava using meter/per second convention,
    object directly overwrites nonintuitive conventions to metric system.'''
    def __init__(self, path):
        self.pathAssign(path)
        self.msToKM('average speed')
        self.msToKM('max speed')
        self.secsToHour('moving time')
        self.condition=None
        self.sort_column = None
        self.sort_ascending = True

    def pathAssign(self, path: str):
        '''Assign path to user selected dir'''
        path = pl.Path(path)
        try:
            df = pd.read_csv(path)
        except Exception as e:
            raise IOError(f"Failed to read CSV: {e}") from e
        df.columns = [c.lower() for c in df.columns]
        df['activity date'] = pd.to_datetime(df['activity date'], format="%b %d, %Y, %I:%M:%S %p") #Activity date column to datetime format for accurate sorting
        self.data = df.copy()   # keep copy
        return self
        
    def sortValues(self, column):
        '''Sort columns when clicked'''
        if self.sort_column==column:
            self.sort_ascending=not self.sort_ascending
        else:
            self.sort_ascending=True
        self.sort_column=column

    def setCondition(self, condition):
        '''Condition property for filterization'''
        if condition is None:
            self.condition=None
        else:
            self.condition=condition
    
    def filterResults(self, column: str, operator: str, value: float, reset: bool):
        '''Filters results logic'''
        try:value=float(value)
        except:
            print('Value error, please enter valid characters.')
            return False
        
        if reset:
            condition=None
            pass

        elif operator == ">":
            condition=self.data[column]>value
        elif operator == "<":
            condition=self.data[column]<value
        elif operator == "<=":
            condition=self.data[column]<=value
        elif operator == ">=":
            condition=self.data[column]>=value
        elif operator == "==":
            condition=self.data[column]==value
        else:
            print('Invalid operation.')
            return False
        
        #Feedback to CLI/GUI
        if condition is None:print('Filter is removed, insert table for default view.')
        else:print('Filterization is complete!')
        self.setCondition(condition)
        return True
    
    def extractColumn(self, column:str):
        '''Returns column, mutates self.data obj'''
        column=column.lower()
        if column in self.data.columns:
            return self.data[f"{column}"]
        else:
            raise KeyError("Column not found.")

    def extractMultiColumns(self, column:list):
        '''Takes list with items as column str'''
        return self.data[column]

    def msToKM(self, column:str):
        '''Convert from meter/second to kph'''
        col = column.lower()
        if col not in self.data.columns:
            raise KeyError(col)
        self.data = self.data.assign(**{f"{col} kmh": (self.data[col].astype(float) * 3.6).round(2)})

    def secsToHour(self, column):
        '''Converts speed format to kmh'''
        if column in self.data.columns:
            meter=self.extractColumn(column)
            meter=meter/3600
            meter=round(meter, 3)
            self.data[f"{column}/h"]=meter

class TextRedirector():
    '''Displays cmd line on GUI via sys.stdout is calling write. (Python auto calls write functions at any time in need of display or write an output)'''
    def __init__(self, text_widget:tk.Text, delay=40):
        self.text_widget = text_widget
        self.delay = delay
        self.text = ""
        self.index = 0

    def write(self,text):
        '''Insert a char and make a nextChar call'''
        if self.index == 0:
            self.text_widget.configure(state='normal')
            self.text_widget.delete("1.0", "end")
            self.text_widget.configure(state='disabled')
            self.text = text
            self.insertNextChar()

    def insertNextChar(self):
        '''Insert a char, and recursively call itself until end exhausted self.text.'''
        if self.index < len(self.text):
            char = self.text[self.index]
            self.text_widget.configure(state='normal')
            self.text_widget.insert("end", char)
            self.text_widget.see("end")
            self.text_widget.configure(state='disabled')
            self.index += 1
            self.text_widget.after(self.delay, self.insertNextChar)
        else:
            self.index = 0

    def flush(self):
        pass

class EntryField():
    '''Object that has tk objects as properties like Frame, Entry and Label. 
    Used for systematic approach to the tk fields.'''
    def __init__(self, parent:tk.Tk, text:str):
        self.frame=tk.Frame(parent)
        self.entry=tk.Entry(self.frame)
        self.text=text
        self.label=tk.Label(self.frame, text=self.text)
    
    def packButtonHelper(self):
        '''Pack the called entry'''
        self.entry.pack(side=tk.RIGHT)
        self.label.pack(side=tk.LEFT)
        self.frame.pack(side="top")

class ButtonField():
    '''Object similar to EntryField, designed for Text version that has 2 tk objects as properties'''
    def __init__(self, parent:tk.Tk, text:str):
        self.frame=tk.Frame(parent)
        self.entry=ttk.Button(self.frame, text=text)
    
    def packButtonHelper(self):
        '''Pack the called button'''
        self.entry.pack()
        self.frame.pack(side="top")

def loadFile(cyclingObj):
    '''Open .csv file and append items as valid columns'''
    items=['activity id', 'activity date', 'moving time/h', 'distance', 'max heart rate', 'average heart rate', 'average speed kmh', 'max speed kmh', 'average watts', 'calories'] 
    path=filedialog.askopenfilename()

    if path:
        cyclingObj=cyclingObj(path)
        cyclingObj.data=cyclingObj.data[items]
    else:
        raise ValueError('Failed to open user given path.')
    return cyclingObj

def displayData(cyclingObj:CycloMeter):
    '''Copying current data, and return filtered data if filterization has taken place'''
    if cyclingObj.condition is not None and cyclingObj.sort_column is not None: #Data filtered and sorted.
            display_data:pd.Dataframe=cyclingObj.data[cyclingObj.condition].sort_values(by=cyclingObj.sort_column, ascending= cyclingObj.sort_ascending)
    elif cyclingObj.condition is not None: #Filtered not sorted
            display_data:pd.Dataframe=cyclingObj.data[cyclingObj.condition]
    elif cyclingObj.sort_column is not None: #Sorted not filtered
            display_data:pd.Dataframe=cyclingObj.data.sort_values(by=cyclingObj.sort_column, ascending= cyclingObj.sort_ascending)
    else: #Unfiltered, raw data copy.
        display_data:pd.Dataframe=cyclingObj.data #iterate dataframe records and get Series
    return display_data

def displayHelp():
    '''Helper function for displaying text in status bar to guide the user.'''
    text="To filter results; add a valid column, operator (>,<,>=,<=,==), and a value.\nTo remove the filter, click X button."
    print(text)

def updateStatusBar(status_bar:tk.Text):
    '''Reroutes sys print statements to TextRedirector object'''
    sys.stdout=TextRedirector(status_bar)

def treeviewInit(tree_view:Treeview, scroll_bar:ttk.Scrollbar, display_data, pandasGenerator, cyclingObj:CycloMeter):
    '''Initiliazes treeview. Remove children, format size of the treeview, and insert values of cyclingObj'''
    for t in tree_view.get_children(): tree_view.delete(t)
    treeviewAdjustTable(display_data, tree_view, scroll_bar, cyclingObj)
    treeviewInsertValues(tree_view, pandasGenerator)
    initScrollBarOntoTreeview(tree_view, scroll_bar)
    treeviewCopyFeature(tree_view)
    return cyclingObj

def treeviewAdjustTable(display_data:pd.DataFrame, tree_view:Treeview, scroll_bar:ttk.Scrollbar, cyclingObj:CycloMeter):
    '''Helper function to adjust the properties of treeview like width of column and the functionality of the click to heading.'''
    for i in list(display_data.columns): 
        tree_view.heading(i, text=i, command=lambda col=i: (cyclingObj.sortValues(col), insertTable(tree_view, scroll_bar,cyclingObj))) 
        tree_view.column(i, width=180) #column sorting

def treeviewInsertValues(tree_view:Treeview,pandasGenerator):
    '''Helper function to insert values to treeview, used by main treeview function.'''
    for index, value in pandasGenerator: #Iterating through panda rows
        raw_values=value.values #Series obj (bool T/F) to raw values
        tree_view.insert('','end',values=raw_values.tolist()) #''(start) to end insertion of columns not records
    print(f"Table insertion is complete!") #debugging needs removed on scaffolding

def treeviewCopyFeature(tree_view:Treeview):
    '''Add copy feature via Ctrl+C to treeview rows'''
    tree_view.bind("<Control-c>", lambda event:treeviewCopyHelper(event, tree_view))

def treeviewCopyHelper(_event:tk.Event, tree_view:Treeview):
    action=tree_view.selection()
    if len(action)==0:pass
    else:
        row_dictionary=tree_view.item(action[0])
        row_tuple=row_dictionary['values']
        row_tuple=list(map(str, row_tuple)) #Map returns iterable map object, turn it into list
        row=', '.join(row_tuple)
        treeviewExtractCopyHelper(row,tree_view)

def treeviewExtractCopyHelper(row,tree_view:Treeview):
        window=tree_view.winfo_toplevel()
        window.clipboard_clear()
        columns_tuple=tree_view.cget('columns')
        columns=', '.join(columns_tuple)
        line=columns+'\n'+row
        window.clipboard_append(line)

def insertTable(tree_view, scroll_bar, cyclingObj:CycloMeter):
    '''Insert table with filtered or unfiltered results packed, and initialize treeView.'''
    display_data:pd.DataFrame=displayData(cyclingObj)
    tree_view['columns']=list(display_data.columns) #update tree_view obj
    tree_view.column('#0', width=0, stretch=False)
    pandasGenerator=display_data.iterrows() #iterate dataframe records and get Series
    treeviewInit(tree_view, scroll_bar, display_data, pandasGenerator, cyclingObj)

def initScrollBarOntoTreeview(tree_view:Treeview, scroll_bar:ttk.Scrollbar):
    '''
    Adjusting scroll bar and Treeview via configuration and packing.
    '''
    #Unpack both widgets
    tree_view.pack_forget()
    scroll_bar.pack_forget()
    # Repack in correct order (scrollbar FIRST, then treeview)
    scroll_bar.pack(side='right', fill='y')
    tree_view.pack(side='left', fill='both', expand=True)
    # Connect
    tree_view.configure(yscrollcommand=scroll_bar.set)
    scroll_bar.configure(command=tree_view.yview)

def retrieveEntry(column_name:tk.Entry,operator:tk.Entry,value_entry:tk.Entry, cyclingObj:CycloMeter, reset=False):
    '''Return input of textBox'''
    column_name=column_name.get()
    operator=operator.get()
    value=value_entry.get()
    cyclingObj.filterResults(column_name,operator,value, reset)
    
def packTextButtonHelper(window):
    '''User status bar packing'''
    status_bar_frame=tk.Frame(window)
    status_bar=tk.Text(status_bar_frame, state='disabled', height=3, width=57)
    return status_bar, status_bar_frame

def iconAdder(window:tk.Tk):
    '''Adds icon to tk object'''
    script_dir=pl.Path(__file__).parent
    icon_path=script_dir / "ico" / "helmet.ico"
    window.iconbitmap(icon_path)

def initEntryBoxes(window, label_names:list):
    '''label_names: list with strings that matches lenght of count
       Creates len label_names number of entry buttons and returns list of all entry buttons'''
    items=[]
    for i in label_names:
        entry_field=EntryField(window,i)
        items.append(entry_field)
    return items

def initStatusBar(window):
    '''Adjust and pack user status bar.'''
    status_bar_tuple=packTextButtonHelper(window)
    updateStatusBar(status_bar_tuple[0])
    displayHelp()
    return status_bar_tuple

def initButtonsConfig(tree_scroll:list, input_boxes:list, window, cycling_container:list):
    '''Dict style configurations to pass on initButtons function
    Returns button configuration for the main window.'''
    column_field, operator_field, value_field=input_boxes
    tree_view,scroll_bar=tree_scroll
    button_config=[
        {
            "parent": window,
            "type": "single",
            "text": "Load CSV File",
            "command": lambda: cycling_container.__setitem__(0, loadFile(CycloMeter)) #CHECK Later
        },
        {
            "parent": window,
            "type": "single",
            "text": "Insert Table",
            "command": lambda:insertTable(tree_view, scroll_bar, cycling_container[0])
        },
        {
            "parent": window,
            "type": "group",
            "buttons":[
                {
                    "text": "Filter", "command": lambda:retrieveEntry(column_field.entry,operator_field.entry,value_field.entry, cycling_container[0], reset=False)},
                {
                    "text": "X", "command": lambda:retrieveEntry(column_field.entry,operator_field.entry,value_field.entry, cycling_container[0], reset=True)}]
        }
    ]
    return button_config

def initButtons(button_config):
    '''Pack buttons and the frames in applicable groups'''
    for config in button_config:
        if config["type"] == "single":
            button=ttk.Button(config["parent"], 
                             text=config["text"], 
                             command=config["command"])
            button.pack()
        elif config["type"] == "group":
            frame_filter=tk.Frame(config["parent"])
            for button_cfg in config["buttons"]:
                buttons_filter=ttk.Button(frame_filter, 
                                         text=button_cfg["text"], 
                                         command=button_cfg["command"]) #text box
                buttons_filter.pack(side='left')
            frame_filter.pack()

def configureMainFields():
    '''Initialize main fields like window, treeview and apply themes.'''
    background_color_main,text_color,button_backg_color='#262624',"#FFFFFF","#302F2E"
    window=tk.Tk(className=" Strava Stats Viewer")
    iconAdder(window)
    tree_frame=tk.Frame(window)
    tree_view=Treeview(tree_frame, height=24)
    scroll_bar=ttk.Scrollbar(tree_frame,orient='vertical')
    window.configure(background=background_color_main)
    window.geometry('1200x800')
    style=ttk.Style(master=window)
    window.option_add('*Text.font', ('Segoe UI', 12))
    style.theme_use('clam')
    
    layers=['*Text', '*Label', '*Entry']
    for i in layers: 
            window.option_add(f'{i}.foreground', text_color)
            window.option_add(f'{i}.background', button_backg_color)

#Applying styles via nested dicts. Clean, sweet, warm... :D
    background='#262624'
    foreground='#E9E9E9'
    fieldbackground="#262524"
    dictionary={
        'Treeview':
        {
            'foreground':foreground,
            'background':background,
            'fieldbackground':fieldbackground,
            'font':('Segoe UI', 12)
        },
        'Treeview.Heading':
        {
            'foreground':foreground,
            'background':background,
            'fieldbackground':fieldbackground
        },
    }
    for widget_names, properties in dictionary.items():
            style.configure(widget_names,**properties) #KWARGS is where magic happens, makes key value pairs form variable. e.g. background='#262624'
    
    dictionary={
        'TButton': 
        {
            'foreground':foreground,
            'background':background,
            'width': 0
        },
        'Vertical.TScrollbar': 
        {
            'foreground':foreground,
            'background':background,
            'troughcolor':background,
            'arrowcolor':foreground,
            'bordercolor':background,
        }
    }
    for widget_names, properties in dictionary.items():
            style.configure(widget_names,**properties) #KWARGS is where magic happens, makes key value pairs form variable. e.g. background='#262624'
    
    background=('pressed', '!disabled', "#D8642E"), ('active', '#D8642E')
    foreground=('pressed', '#E9E9E9'), ('active', '#E9E9E9')
    dictionary={
        'Treeview': 
        {
            'foreground':foreground,
            'background':(('selected','#D8642E'),)+background
        },
        'Treeview.Heading':
        {
            'foreground':foreground,
            'background':background,
        },
        'TButton': {
    'background': (('pressed', '#D8642E'), ('active', '#D8642E'))
        },
        'Vertical.TScrollbar': {
    'background': (('pressed', '#D8642E'), ('active', '#D8642E'))
        }
    }
    for widget_name, properties in dictionary.items():
        style.map(widget_name,**properties)

    return window,tree_view,scroll_bar,tree_frame

def packInitializeAll(window,tree_frame,tree_view,scroll_bar,cycling_container):
    input_boxes=initEntryBoxes(window,["column:","operator:","value:"]) #input boxes
    button_config=initButtonsConfig([tree_view,scroll_bar],input_boxes,window, cycling_container)
    status_bar, status_bar_frame=initStatusBar(window)
    tree_frame.pack()
    tree_view.pack()
    initButtons(button_config) #packs clickables
    for i in input_boxes:i.packButtonHelper() #Pack all special EntryField objects (object that has frame, label and tk.entry as property). 
    for i in status_bar_frame,status_bar: i.pack() #Packing status bar frame and the tk.text field
    
def programInitialize():
    cycling_container = [None]
    window,tree_view, scroll_bar,tree_frame=configureMainFields()
    packInitializeAll(window,tree_frame,tree_view,scroll_bar,cycling_container)
    window.mainloop()

if __name__ == "__main__":
    programInitialize()